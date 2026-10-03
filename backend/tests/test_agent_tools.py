"""
AI agent tools: read tools, approval-required drafts, role rules, tenant
isolation and orchestrator routing.

Runs against real PostgreSQL (see tests/pg_support.py; skipped when no test
database is reachable). The LLM is replaced by a scripted fake that returns
real `openai` ChatCompletionMessage objects, so the agent loop, tool calls,
chat endpoint and approval endpoints run exactly as with OpenAI - only the
model's choices are scripted.
"""
import json
import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function
from sqlalchemy.orm import sessionmaker

from app.ai.agents import orchestrator as orchestrator_module
from app.ai.agents.orchestrator import AGENT_NAMES, CLASSIFICATION_PROMPT, AgentOrchestrator
from app.ai.agents.schemas import AgentContext
from app.db.base import Base
from app.modules.agent_actions.models import AgentAction
from app.modules.appointments.models import Appointment
from app.modules.branches.models import Branch
from app.modules.business.models import Business
from app.modules.business_hours.models import BusinessHours
from app.modules.cash_register.models import CashRegister, CashTransaction
from app.modules.customer_tags.models import CustomerTag, CustomerTagAssignment
from app.modules.customers.models import Customer
from app.modules.expense_categories.models import ExpenseCategory
from app.modules.expenses.models import Expense
from app.modules.invoice.models import Invoice
from app.modules.loyalty.models import LoyaltyRule, LoyaltyWallet
from app.modules.membership.models import Membership
from app.modules.packages.models import CustomerPackage, Installment, ServicePackage
from app.modules.products.models import Product
from app.modules.reviews.models import CustomerReview
from app.modules.schedule_blocks.models import ScheduleBlock
from app.modules.services.models import Service
from app.modules.staff.models import StaffProfile, StaffSchedule, StaffService
from app.modules.surveys.models import Survey, SurveyResponseModel
from app.modules.user.models import User
from app.shared.enums.appointment import AppointmentStatus
from app.shared.enums.cash_register import CashRegisterStatus, CashTransactionType
from app.shared.enums.expense import TransactionDirection
from app.shared.enums.invoice import InvoiceStatus
from app.shared.enums.membership import MembershipRole
from app.shared.enums.package import CustomerPackageStatus, InstallmentStatus, PackageStatus
from app.shared.enums.review import ReviewStatus
from app.shared.enums.user import UserStatus
from tests.pg_support import API, auth, make_client, make_engine, release_client

TODAY = date.today()
NEXT_MONDAY = TODAY + timedelta(days=7 - TODAY.weekday())


# ------------------------------------------------------------------ fake LLM

def _tool_call_message(name: str, arguments: dict, call_id: str = "call_1") -> ChatCompletionMessage:
    return ChatCompletionMessage(
        role="assistant",
        content=None,
        tool_calls=[ChatCompletionMessageToolCall(
            id=call_id, type="function", function=Function(name=name, arguments=json.dumps(arguments)),
        )],
    )


def _text_message(text: str) -> ChatCompletionMessage:
    return ChatCompletionMessage(role="assistant", content=text)


class FakeLLM:
    """Scripted stand-in for OpenAIClient: same two methods, same return types."""

    classification = "customer_support"
    script: list = []
    seen_tools: list = []

    def __init__(self, *args, **kwargs):
        pass

    def chat(self, *, system_prompt, user_prompt, **kwargs):
        return FakeLLM.classification

    def chat_with_tools(self, *, messages, tools=None, **kwargs):
        FakeLLM.seen_tools.append(sorted(t["function"]["name"] for t in (tools or [])))
        FakeLLM.tool_outputs = [m["content"] for m in messages if isinstance(m, dict) and m.get("role") == "tool"]
        return FakeLLM.script.pop(0) if FakeLLM.script else _text_message("Tamam.")

    @classmethod
    def reset(cls, classification="customer_support", script=None):
        cls.classification = classification
        cls.script = list(script or [])
        cls.seen_tools = []
        cls.tool_outputs = []


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch):
    FakeLLM.reset()
    monkeypatch.setattr("app.ai.agents.factory.OpenAIClient", FakeLLM)
    return FakeLLM


# ------------------------------------------------------------------ database & data

@pytest.fixture(scope="module")
def engine():
    eng = make_engine()
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture(scope="module")
def client(engine):
    with make_client(engine) as c:
        yield c
    release_client()


class World:
    pass


@pytest.fixture(scope="module")
def world(engine):
    db = sessionmaker(bind=engine, expire_on_commit=False)()
    w = World()
    sfx = uuid.uuid4().hex[:8]
    add = lambda *objs: (db.add_all(objs), db.flush())  # noqa: E731

    def user(name):
        u = User(first_name=name, last_name="T", email=f"{name}-{sfx}@test.local", password_hash="x", status=UserStatus.ACTIVE)
        add(u)
        return u

    w.owner, w.employee, w.viewer, w.owner_b = user("owner"), user("employee"), user("viewer"), user("ownerb")
    w.a = Business(name="Güzellik Alpha", slug=f"alpha-{sfx}", industry="beauty", email=f"a-{sfx}@t.local", phone="1")
    w.b = Business(name="Beta", slug=f"beta-{sfx}", industry="beauty", email=f"b-{sfx}@t.local", phone="2")
    add(w.a, w.b)
    add(
        Membership(user_id=w.owner.id, business_id=w.a.id, role=MembershipRole.OWNER),
        Membership(user_id=w.employee.id, business_id=w.a.id, role=MembershipRole.EMPLOYEE),
        Membership(user_id=w.viewer.id, business_id=w.a.id, role=MembershipRole.VIEWER),
        Membership(user_id=w.owner_b.id, business_id=w.b.id, role=MembershipRole.OWNER),
    )

    # --- business A
    w.branch = Branch(business_id=w.a.id, name="Kadıköy", address="Moda Cd. 1", phone="0216", is_main=True)
    w.customer = Customer(business_id=w.a.id, name="Ayşe Yılmaz", phone="555")
    w.service = Service(business_id=w.a.id, name="Cilt Bakımı", price=500, duration_minutes=60)
    add(w.branch, w.customer, w.service)
    w.staff = StaffProfile(business_id=w.a.id, branch_id=w.branch.id, full_name="Elif Usta", title="Uzman")
    add(w.staff)
    add(
        StaffService(staff_id=w.staff.id, service_id=w.service.id),
        StaffSchedule(staff_id=w.staff.id, business_id=w.a.id, day_of_week=0, start_time=time(10), end_time=time(16)),
        *[BusinessHours(business_id=w.a.id, day_of_week=d, open_time=time(9), close_time=time(18)) for d in range(6)],
        BusinessHours(business_id=w.a.id, day_of_week=6, is_closed=True),
        Product(business_id=w.a.id, name="Nemlendirici Krem", brand="Derma", category="Bakım", sale_price=350, current_stock=12, min_stock_level=3),
        Product(business_id=w.a.id, name="Güneş Kremi", category="Bakım", sale_price=420, current_stock=1, min_stock_level=5),
    )
    w.package = ServicePackage(business_id=w.a.id, name="6 Seans Cilt Bakımı", total_sessions=6, price=2700, discount_percentage=10,
                               services=[{"service_id": str(w.service.id), "service_name": "Cilt Bakımı", "session_count": 6}],
                               status=PackageStatus.ACTIVE, max_installments=3)
    add(w.package)
    w.cp = CustomerPackage(business_id=w.a.id, customer_id=w.customer.id, package_id=w.package.id, total_sessions=6, used_sessions=4,
                           remaining_sessions=2, total_price=2700, paid_amount=1800, status=CustomerPackageStatus.ACTIVE,
                           expires_at=datetime.now(UTC) + timedelta(days=200))
    add(w.cp)
    w.category = ExpenseCategory(business_id=w.a.id, name="Kira")
    add(
        Installment(customer_package_id=w.cp.id, business_id=w.a.id, customer_id=w.customer.id, installment_number=3, amount=900,
                    due_date=TODAY - timedelta(days=10), status=InstallmentStatus.PENDING),
        w.category,
    )
    add(
        Expense(business_id=w.a.id, category_id=w.category.id, direction=TransactionDirection.EXPENSE, title="Kira", amount=5000, transaction_date=TODAY),
        Invoice(business_id=w.a.id, customer_name="Ayşe Yılmaz", invoice_number=f"A-{sfx}", items=[], subtotal=1200, tax_rate=0,
                tax_amount=0, total_amount=1200, status=InvoiceStatus.PAID, paid_at=datetime.now(UTC)),
    )
    w.review_bad = CustomerReview(business_id=w.a.id, rating=2, comment="Çok bekledim.", reviewer_name="Mehmet K.", status=ReviewStatus.PUBLISHED)
    w.review_good = CustomerReview(business_id=w.a.id, rating=5, comment="Harika!", reviewer_name="Zehra A.", status=ReviewStatus.PUBLISHED)
    w.review_pending = CustomerReview(business_id=w.a.id, rating=4, comment="İyi", reviewer_name="Can B.", status=ReviewStatus.PENDING)
    w.tag = CustomerTag(business_id=w.a.id, name="VIP")
    w.survey = Survey(business_id=w.a.id, title="Memnuniyet Anketi", questions=[], status="ACTIVE")
    w.register = CashRegister(business_id=w.a.id, register_date=TODAY, opening_balance=500, status=CashRegisterStatus.OPEN, opened_at=datetime.now(UTC))
    add(w.review_bad, w.review_good, w.review_pending, w.tag, w.survey, w.register,
        LoyaltyRule(business_id=w.a.id, points_per_currency=1, points_value_in_currency=0.05, min_points_for_spend=100))
    add(
        CustomerTagAssignment(customer_id=w.customer.id, tag_id=w.tag.id),
        LoyaltyWallet(business_id=w.a.id, customer_id=w.customer.id, balance=250, lifetime_earned=300, lifetime_spent=50),
        SurveyResponseModel(survey_id=w.survey.id, business_id=w.a.id, answers=[], overall_rating=4),
        SurveyResponseModel(survey_id=w.survey.id, business_id=w.a.id, answers=[], overall_rating=5),
        CashTransaction(register_id=w.register.id, business_id=w.a.id, transaction_type=CashTransactionType.OPENING, amount=500),
        CashTransaction(register_id=w.register.id, business_id=w.a.id, transaction_type=CashTransactionType.SALE, amount=1200),
        Appointment(business_id=w.a.id, customer_id=w.customer.id, customer_name="Ayşe Yılmaz", service_id=w.service.id,
                    branch_id=w.branch.id, appointment_date=NEXT_MONDAY, start_time=time(12, 30), end_time=time(13),
                    status=AppointmentStatus.CONFIRMED),
    )

    # --- business B (must never leak into A's tools)
    w.customer_b = Customer(business_id=w.b.id, name="Zeynep Gizli", phone="999")
    w.review_b = CustomerReview(business_id=w.b.id, rating=1, comment="B işletmesinin yorumu", reviewer_name="Gizli B", status=ReviewStatus.PUBLISHED)
    w.tag_b = CustomerTag(business_id=w.b.id, name="B-Segment")
    w.category_b = ExpenseCategory(business_id=w.b.id, name="B Kategori")
    add(w.customer_b, w.review_b, w.tag_b, w.category_b,
        Product(business_id=w.b.id, name="Gizli Ürün B", sale_price=1, current_stock=0, min_stock_level=5))
    db.commit()
    w.db = db
    yield w
    db.close()


def orchestrator(world, role="OWNER", user=None) -> AgentOrchestrator:
    from unittest.mock import MagicMock

    return AgentOrchestrator(client=FakeLLM(), db=world.db, business_id=world.a.id,
                             user_id=(user or world.owner).id, embedding_service=MagicMock(), role=role)


def tool(world, name, role="OWNER", user=None):
    for agent in orchestrator(world, role, user).agents.values():
        for t in agent.tools:
            if t.name == name:
                return t
    raise KeyError(name)


def run(world, name, role="OWNER", **kwargs):
    return tool(world, name, role).execute(**kwargs)


# ------------------------------------------------------------------ 1. registry & routing prompt

EXPECTED_TOOLS = {
    "customer_support": {"search_knowledge_base", "get_business_info", "list_services", "get_business_hours", "list_branches",
                         "list_reviews", "draft_review_reply"},
    "appointment": {"get_available_slots", "create_appointment", "list_appointments", "cancel_appointment", "list_services",
                    "get_business_hours", "list_staff", "list_branches", "get_customer_packages", "create_schedule_block_draft"},
    "sales": {"list_services", "get_service_details", "search_knowledge_base", "search_products", "list_low_stock_products",
              "list_service_packages", "get_customer_packages"},
    "analytics": {"get_dashboard_summary", "get_appointment_stats", "get_customer_stats", "get_service_popularity",
                  "get_staff_performance", "get_survey_results", "get_review_stats"},
    "marketing": {"get_business_info", "list_services", "get_service_popularity", "get_customer_stats", "search_knowledge_base",
                  "create_campaign_draft", "list_customer_segments", "get_loyalty_info", "list_reviews"},
    "finance": {"get_revenue_report", "get_expense_summary", "get_cash_register_status", "list_overdue_installments",
                "get_invoice_stats", "create_invoice_draft", "create_expense_draft"},
}


def test_six_agents_with_expected_tools(world):
    agents = orchestrator(world).agents
    assert set(agents) == set(AGENT_NAMES) == set(EXPECTED_TOOLS)
    for name, agent in agents.items():
        names = [t.name for t in agent.tools]
        assert set(names) == EXPECTED_TOOLS[name], name
        assert len(names) == len(set(names)), f"duplicate tool in {name}"
        assert len(names) <= 10, f"{name} has too many tools for reliable selection"


def test_no_tool_lets_the_llm_choose_the_business(world):
    for agent in orchestrator(world).agents.values():
        for t in agent.tools:
            json.dumps(t.to_openai_schema())
            assert "business_id" not in t.parameters.get("properties", {}), t.name


def test_classification_prompt_describes_every_agent():
    for name in AGENT_NAMES:
        assert f"{name} —" in CLASSIFICATION_PROMPT
    for keyword in ("Ürün", "stok", "paket", "gider", "kasa", "taksit", "yorum", "sadakat", "personel", "Çalışma saatleri"):
        assert keyword.lower() in CLASSIFICATION_PROMPT.lower(), keyword


@pytest.mark.parametrize("llm_answer,expected", [
    ("finance", "finance"), ("Sales", "sales"), ("ajan: analytics", "analytics"),
    ("marketing\n", "marketing"), ("bilmiyorum", "customer_support"), ("", "customer_support"),
])
def test_intent_parsing(world, llm_answer, expected):
    FakeLLM.reset(classification=llm_answer)
    assert orchestrator(world)._classify_intent(question="x") == expected


# ------------------------------------------------------------------ 2. read tools

def test_sales_tools(world):
    out = run(world, "search_products", query="krem").output
    assert "Nemlendirici Krem" in out and "350,00 TL" in out and "Güneş Kremi" in out
    assert "1 adet (azaldı)" in out
    assert "Güneş Kremi" in run(world, "list_low_stock_products").output
    out = run(world, "list_service_packages").output
    assert "6 Seans Cilt Bakımı" in out and "%10 indirim" in out and "3 taksite kadar" in out
    out = run(world, "get_customer_packages", customer_name="ayşe").output
    assert "2/6 seans kaldı" in out and "ödenen 1.800,00 TL" in out


def test_appointment_and_support_tools(world):
    out = run(world, "get_business_hours", date=NEXT_MONDAY.isoformat()).output
    assert "Pazartesi: 09:00–18:00" in out and "Pazar: Kapalı" in out and "09:00–18:00 arası açık" in out
    out = run(world, "list_staff", service_name="cilt").output
    assert "Elif Usta (Uzman) — Kadıköy" in out and "Pzt 10:00-16:00" in out
    assert "Kadıköy (merkez): Moda Cd. 1 — 0216" in run(world, "list_branches").output
    assert "2/6 seans kaldı" in run(world, "get_customer_packages", customer_name="Ayşe Yılmaz").output


def test_analytics_tools(world):
    assert "Bu ay ciro" in run(world, "get_dashboard_summary").output
    assert "Elif Usta" in run(world, "get_staff_performance").output
    assert "Memnuniyet Anketi [ACTIVE]: 2 yanıt, ortalama puan 4.5/5" in run(world, "get_survey_results").output
    out = run(world, "get_review_stats").output
    assert "Yayınlanmış yorum: 2" in out and "Onay bekleyen: 1, yanıtlanmamış (yayında): 2" in out
    assert "Toplam:" in run(world, "get_appointment_stats", period="all").output   # old 'all' value still works
    assert "Toplam müşteri: 1" in run(world, "get_customer_stats").output
    assert "Cilt Bakımı" in run(world, "get_service_popularity").output


def test_marketing_tools(world):
    assert "VIP: 1 müşteri" in run(world, "list_customer_segments").output
    assert "Ayşe Yılmaz" in run(world, "list_customer_segments", tag_name="vip").output
    out = run(world, "get_loyalty_info").output
    assert "1 puan = 0,05 TL" in out and "Ayşe Yılmaz (250)" in out
    assert "250 puan" in run(world, "get_loyalty_info", customer_name="Ayşe").output
    out = run(world, "list_reviews", filter="published", min_rating=4).output
    assert "Zehra A." in out and "Mehmet K." not in out


def test_loyalty_lookup_does_not_create_wallets(world):
    from app.modules.loyalty.models import LoyaltyWallet as W

    before = world.db.query(W).count()
    world.db.add(Customer(business_id=world.a.id, name="Puansız Kişi"))
    world.db.commit()
    assert "henüz puan kazanmamış" in run(world, "get_loyalty_info", customer_name="Puansız Kişi").output
    assert world.db.query(W).count() == before


def test_finance_tools_for_owner(world):
    assert "Kira | 5.000,00 TL | 1" in run(world, "get_expense_summary").output
    out = run(world, "get_cash_register_status").output
    assert "Açık" in out and "Satış: 1.200,00 TL" in out and "Beklenen kapanış: 1.700,00 TL" in out
    out = run(world, "list_overdue_installments").output
    assert "Ayşe Yılmaz | 3 | 900,00 TL" in out and "10 gün" in out
    assert "Tahsil edilen toplam: 1.200,00 TL" in run(world, "get_invoice_stats").output
    assert "Toplam gelir: 1.200,00 TL" in run(world, "get_revenue_report").output


# ------------------------------------------------------------------ 3. roles

@pytest.mark.parametrize("role", ["VIEWER", "EMPLOYEE"])
def test_money_is_hidden_from_non_admin_roles(world, role):
    out = run(world, "get_dashboard_summary", role=role).output
    assert "ciro" not in out.lower() and "yöneticilere gösterilir" in out
    assert "ciro" not in run(world, "get_staff_performance", role=role).output
    assert "TL" not in run(world, "get_service_popularity", role=role).output
    assert "ödenen" not in run(world, "get_customer_packages", role=role, customer_name="Ayşe").output
    assert "stok değeri" not in run(world, "list_low_stock_products", role=role).output.lower()
    for name in ("get_revenue_report", "get_expense_summary", "get_cash_register_status", "list_overdue_installments",
                 "get_invoice_stats", "create_expense_draft"):
        r = run(world, name, role=role, title="x", amount=1)
        assert r.success is False and "yalnızca işletme sahibi" in r.output, name


def test_finance_agent_refused_for_viewer_before_any_llm_tool_call(world):
    FakeLLM.reset(classification="finance", script=[_tool_call_message("get_revenue_report", {})])
    o = orchestrator(world, role="VIEWER")
    resp = o.route(question="Bu ay ciro ne?", context=AgentContext(business_id=world.a.id, user_id=world.viewer.id, role="VIEWER"))
    assert resp.agent_name == "finance" and resp.metadata.get("access_denied")
    assert resp.tools_used == [] and FakeLLM.seen_tools == []


def test_finance_agent_guards_itself_too(world):
    agent = orchestrator(world, role="OWNER").agents["finance"]
    resp = agent.execute(question="ciro?", context=AgentContext(business_id=world.a.id, user_id=world.viewer.id, role="EMPLOYEE"))
    assert resp.metadata.get("access_denied") and FakeLLM.seen_tools == []


# ------------------------------------------------------------------ 4. tenant isolation of tools

def test_tools_of_business_a_never_see_business_b(world):
    assert "bulunamadı" in run(world, "search_products", query="Gizli").output
    assert "Gizli B" not in run(world, "list_reviews", filter="all").output
    assert "B-Segment" not in run(world, "list_customer_segments").output
    assert run(world, "get_customer_packages", customer_name="Zeynep Gizli").success is False
    r = run(world, "draft_review_reply", review_ref=str(world.review_b.id)[:8], reply="merhaba")
    assert r.success is False and "bulunamadı" in r.output
    r = run(world, "create_expense_draft", title="x", amount=10, category_name="B Kategori")
    assert r.success is False and r.output.endswith("Mevcut kategoriler: Kira")  # only A's categories are offered


# ------------------------------------------------------------------ 5. drafts and approval

def _approve(client, world, action_id, user):
    return client.post(f"{API}/businesses/{world.a.id}/agent-actions/{action_id}/approve", headers=auth(user))


def test_expense_draft_needs_owner_or_admin_approval(client, world):
    r = run(world, "create_expense_draft", title="Ekim elektrik", amount=842.5, category_name="kira", payment_method="BANK_TRANSFER")
    assert r.success and r.data["action_type"] == "CREATE_EXPENSE"
    assert r.data["payload"]["category_name"] == "Kira" and r.data["payload"]["payment_method_label"] == "Havale/EFT"
    world.db.expire_all()
    assert world.db.query(Expense).filter_by(title="Ekim elektrik").count() == 0  # nothing written yet

    assert _approve(client, world, r.data["action_id"], world.employee).status_code == 403
    resp = _approve(client, world, r.data["action_id"], world.owner)
    assert resp.status_code == 200 and resp.json()["status"] == "EXECUTED"
    world.db.expire_all()
    expense = world.db.query(Expense).filter_by(title="Ekim elektrik").one()
    assert float(expense.amount) == 842.5 and expense.category_id == world.category.id and expense.business_id == world.a.id


def test_invoice_draft_approval_now_requires_owner_or_admin(client, world):
    r = run(world, "create_invoice_draft", customer_name="Ayşe Yılmaz", items=[{"description": "Bakım", "quantity": 1, "unit_price": 500}])
    assert r.success
    assert _approve(client, world, r.data["action_id"], world.employee).status_code == 403
    assert _approve(client, world, r.data["action_id"], world.owner).json()["status"] == "EXECUTED"


@pytest.mark.parametrize("kwargs,error", [
    ({"title": "x", "amount": 0}, "sıfırdan büyük"),
    ({"title": "x", "amount": 10, "transaction_date": (TODAY + timedelta(days=3)).isoformat()}, "Gelecek tarihli"),
    ({"title": "x", "amount": 10, "transaction_date": "03/10/2026"}, "YYYY-MM-DD"),
])
def test_expense_draft_validation(world, kwargs, error):
    r = run(world, "create_expense_draft", **kwargs)
    assert r.success is False and error in r.output


def test_review_reply_draft_and_approval(client, world):
    ref = "#" + str(world.review_bad.id)[:8]
    assert ref in run(world, "list_reviews").output  # unreplied filter is the default
    r = run(world, "draft_review_reply", review_ref=ref, reply="Bekleme için özür dileriz, randevu sistemimizi iyileştirdik.")
    assert r.success and r.data["payload"]["review_comment"] == "Çok bekledim." and r.data["payload"]["rating"] == 2
    world.db.expire_all()
    assert world.db.get(CustomerReview, world.review_bad.id).reply is None  # not published yet
    assert _approve(client, world, r.data["action_id"], world.employee).json()["status"] == "EXECUTED"
    world.db.expire_all()
    assert world.db.get(CustomerReview, world.review_bad.id).reply.startswith("Bekleme için özür")
    again = run(world, "draft_review_reply", review_ref=ref, reply="tekrar")
    assert again.success is False and "zaten yanıtlanmış" in again.output


def test_review_reply_only_for_published_reviews(world):
    r = run(world, "draft_review_reply", review_ref=str(world.review_pending.id)[:8], reply="teşekkürler")
    assert r.success is False and "yayınlanmış" in r.output


def test_schedule_block_draft_warns_and_closes_slots_after_approval(client, world):
    slots_url = f"{API}/businesses/{world.a.id}/appointments/available-slots"
    params = {"date": NEXT_MONDAY.isoformat(), "branch_id": str(world.branch.id)}
    before = client.get(slots_url, params=params, headers=auth(world.owner)).json()["available_slots"]
    assert "14:00" in before and "15:00" in before

    r = run(world, "create_schedule_block_draft", block_type="TIME_RANGE", date=NEXT_MONDAY.isoformat(),
            start_time="14:00", end_time="16:00", branch_name="kadıköy", title="Eğitim", user=world.owner)
    assert r.success and r.data["payload"]["branch_name"] == "Kadıköy"
    assert r.data["payload"]["conflicting_appointments"] == 0
    assert world.db.query(ScheduleBlock).filter_by(title="Eğitim").count() == 0

    assert _approve(client, world, r.data["action_id"], world.employee).json()["status"] == "EXECUTED"
    after = client.get(slots_url, params=params, headers=auth(world.owner)).json()["available_slots"]
    assert "14:00" not in after and "15:00" not in after and "16:00" in after
    block = world.db.query(ScheduleBlock).filter_by(title="Eğitim").one()
    assert block.branch_id == world.branch.id and block.business_id == world.a.id


def test_schedule_block_draft_reports_conflicting_appointments(world):
    r = run(world, "create_schedule_block_draft", block_type="TIME_RANGE", date=NEXT_MONDAY.isoformat(),
            start_time="12:00", end_time="13:00")
    assert r.success and r.data["payload"]["conflicting_appointments"] == 1 and "1 mevcut randevu" in r.output


@pytest.mark.parametrize("kwargs,error", [
    ({"block_type": "TIME_RANGE", "date": (TODAY - timedelta(days=1)).isoformat(), "start_time": "10:00", "end_time": "11:00"}, "Geçmiş"),
    ({"block_type": "TIME_RANGE", "date": NEXT_MONDAY.isoformat(), "start_time": "15:00", "end_time": "11:00"}, "önce olmalı"),
    ({"block_type": "RECURRING", "start_time": "12:00", "end_time": "13:00"}, "recurrence_day"),
    ({"block_type": "FULL_DAY"}, "tarih"),
    ({"block_type": "FULL_DAY", "date": NEXT_MONDAY.isoformat(), "branch_name": "Olmayan Şube"}, "şube bulunamadı"),
])
def test_schedule_block_draft_validation(world, kwargs, error):
    r = run(world, "create_schedule_block_draft", **kwargs)
    assert r.success is False and error in r.output


def test_rejected_draft_changes_nothing(client, world):
    r = run(world, "create_expense_draft", title="Reddedilecek", amount=99)
    resp = client.post(f"{API}/businesses/{world.a.id}/agent-actions/{r.data['action_id']}/reject",
                       json={"reason": "Yanlış tutar"}, headers=auth(world.owner))
    assert resp.status_code == 200 and resp.json()["status"] == "REJECTED"
    assert _approve(client, world, r.data["action_id"], world.owner).json()["status"] == "REJECTED"  # no late execution
    world.db.expire_all()
    assert world.db.query(Expense).filter_by(title="Reddedilecek").count() == 0


# ------------------------------------------------------------------ 6. end to end through the chat endpoint

def test_chat_finance_question_runs_tool_and_returns_answer(client, world):
    FakeLLM.reset(classification="finance", script=[
        _tool_call_message("get_expense_summary", {"period": "month"}),
        _text_message("Bu ay en büyük gider kalemi kira (5.000 TL)."),
    ])
    r = client.post(f"{API}/businesses/{world.a.id}/chat", json={"question": "Bu ay en çok neye harcadık?"}, headers=auth(world.owner))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["agent_name"] == "finance" and body["tools_used"] == ["get_expense_summary"]
    assert any(o.startswith("Gelir/gider kayıtları — Bu ay") and "Kira |" in o for o in FakeLLM.tool_outputs)
    assert "get_revenue_report" in FakeLLM.seen_tools[0]


def test_chat_finance_question_refused_for_viewer(client, world):
    FakeLLM.reset(classification="finance", script=[_tool_call_message("get_revenue_report", {})])
    r = client.post(f"{API}/businesses/{world.a.id}/chat", json={"question": "Ciro?"}, headers=auth(world.viewer))
    assert r.status_code == 200
    assert "yalnızca işletme sahibi" in r.json()["answer"] and not r.json()["tools_used"]


def test_chat_draft_shows_up_as_pending_action_and_can_be_approved(client, world):
    FakeLLM.reset(classification="appointment", script=[
        _tool_call_message("create_schedule_block_draft", {"block_type": "RECURRING", "recurrence_day": "WEDNESDAY",
                                                             "start_time": "12:00", "end_time": "13:00", "title": "Öğle arası"}),
        _text_message("Her çarşamba 12:00-13:00 için kapatma taslağı hazırladım, onayınızı bekliyor."),
    ])
    r = client.post(f"{API}/businesses/{world.a.id}/chat", json={"question": "Çarşambaları öğlen 12-1 arası kapat"}, headers=auth(world.owner))
    body = r.json()
    assert body["agent_name"] == "appointment"
    [pending] = body["pending_actions"]
    assert pending["action_type"] == "CREATE_SCHEDULE_BLOCK" and pending["payload"]["recurrence_day_label"] == "Çarşamba"
    action = world.db.get(AgentAction, uuid.UUID(pending["action_id"]))
    assert action.requested_by == world.owner.id and action.business_id == world.a.id
    assert _approve(client, world, pending["action_id"], world.owner).json()["status"] == "EXECUTED"


def test_agent_survives_unknown_tool_and_bad_arguments(world):
    FakeLLM.reset(script=[
        _tool_call_message("delete_everything", {}),
        _tool_call_message("get_business_hours", {"date": "yarın"}),
        _text_message("Tarihi anlayamadım."),
    ])
    agent = orchestrator(world).agents["customer_support"]
    resp = agent.execute(question="yarın açık mısınız", context=AgentContext(business_id=world.a.id, user_id=world.owner.id, role="OWNER"))
    assert resp.answer == "Tarihi anlayamadım."
    assert any("Bilinmeyen araç" in o for o in FakeLLM.tool_outputs)
    assert any("Geçersiz tarih" in o for o in FakeLLM.tool_outputs)
