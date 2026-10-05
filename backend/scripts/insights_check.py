"""
AI insights with the REAL OpenAI API (run by e2e-test.bat).

    python scripts/insights_check.py

- Creates an isolated demo business with 60 days of history: revenue down
  15 %, cancellations up, new customers up. Customer and staff names are
  distinctive so a privacy check can look for them.
- Builds the metrics, checks that no personal data is in the prompt, asks
  the real model once and validates the answer (format, item count, labels).
- Prints the card the dashboard would show, then soft-deletes the demo.
The API key is never printed.
"""
import os
import sys
import uuid
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

import app.main  # noqa: E402,F401  - registers all models
from app.core.config import settings  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.modules.appointments.models import Appointment  # noqa: E402
from app.modules.business.models import Business  # noqa: E402
from app.modules.customers.models import Customer  # noqa: E402
from app.modules.insights import generator  # noqa: E402
from app.modules.insights.metrics import build_metrics  # noqa: E402
from app.modules.insights.models import InsightStatus, InsightTrigger  # noqa: E402
from app.modules.insights.service import InsightService, local_today  # noqa: E402
from app.modules.invoice.models import Invoice  # noqa: E402
from app.modules.services.models import Service  # noqa: E402
from app.modules.staff.models import StaffProfile  # noqa: E402
from app.shared.enums.appointment import AppointmentStatus  # noqa: E402
from app.shared.enums.invoice import InvoiceStatus  # noqa: E402

engine.echo = False

SECRETS = ["Zeliha Gizlioğlu", "Ahmet Saklıbey", "05559876543", "zeliha.gizli@example.com",
           "Gizem Ustaoğlu", "Kerem Makasçı", "alerjik"]
EMOJI = {"positive": "🟢", "negative": "🔴", "neutral": "⚪", "suggestion": "💡"}


def seed(db, today):
    sfx = uuid.uuid4().hex[:6]
    biz = Business(name="E2E İçgörü Kuaförü", slug=f"e2e-icgoru-{sfx}", industry="Kuaför",
                   email=f"icgoru-{sfx}@example.com", phone="02120000000")
    db.add(biz)
    db.flush()
    cut, color = (Service(business_id=biz.id, name=n, price=p, duration_minutes=60)
                  for n, p in (("Saç Kesimi", 500), ("Boya", 1500)))
    db.add_all([cut, color])
    staff = [StaffProfile(business_id=biz.id, full_name=n) for n in ("Gizem Ustaoğlu", "Kerem Makasçı")]
    db.add_all(staff)
    db.flush()
    customers = [Customer(business_id=biz.id, name="Zeliha Gizlioğlu", phone="05559876543",
                          email="zeliha.gizli@example.com"),
                 Customer(business_id=biz.id, name="Ahmet Saklıbey", phone="05551112299")]
    db.add_all(customers)
    db.flush()

    def appt(days_ago, status, i, svc=cut):
        c = customers[i % 2]
        db.add(Appointment(business_id=biz.id, customer_id=c.id, customer_name=c.name, customer_phone=c.phone,
                           service_id=svc.id, staff_id=staff[i % 2].id, appointment_date=today - timedelta(days=days_ago),
                           start_time=time(10 + i % 6), end_time=time(11 + i % 6), status=status,
                           notes="Müşteri alerjik"))

    for i in range(24):  # previous 30 days: 24 appointments, 2 cancelled
        appt(31 + i, AppointmentStatus.CANCELLED if i < 2 else AppointmentStatus.COMPLETED, i)
    for i in range(22):  # last 30 days: 22 appointments, 6 cancelled
        appt(1 + i, AppointmentStatus.CANCELLED if i < 6 else AppointmentStatus.COMPLETED, i, color if i % 5 == 0 else cut)

    for n, (days_ago, amount) in enumerate([(40, "11000"), (5, "9350")]):
        db.add(Invoice(business_id=biz.id, customer_id=customers[0].id, customer_name="Zeliha Gizlioğlu",
                       invoice_number=f"E2E-{sfx}-{n}", items=[], subtotal=Decimal(amount), tax_rate=0, tax_amount=0,
                       total_amount=Decimal(amount), status=InvoiceStatus.PAID,
                       paid_at=datetime.combine(today - timedelta(days=days_ago), time(12), tzinfo=UTC)))
    db.commit()
    return biz


def main() -> int:
    if not settings.OPENAI_API_KEY:
        print("OPENAI_API_KEY tanımlı değil; içgörü testi atlandı.")
        return 2
    print("OPENAI_API_KEY: tanımlı (değer gösterilmiyor) · model:", settings.INSIGHTS_MODEL)

    db = SessionLocal()
    today = local_today()
    biz = seed(db, today)
    ok = True
    try:
        metrics = build_metrics(db, biz.id, today)
        prompt = generator.build_user_prompt(metrics) + generator.SYSTEM_PROMPT
        leaks = [s for s in SECRETS if s in prompt]
        print("Gizlilik kontrolü:", "TEMİZ (kişisel veri gönderilmiyor)" if not leaks else f"SIZINTI: {leaks}")
        ok &= not leaks
        print(f"Gelir değişimi: %{metrics['changes']['revenue_pct']} · İptal oranı farkı: {metrics['changes']['cancel_rate_pp']} puan")

        started = datetime.now()
        row = InsightService(db).generate_now(biz.id, InsightTrigger.MANUAL)
        seconds = (datetime.now() - started).total_seconds()
        if row is None or row.status != InsightStatus.READY:
            print(f"SONUÇ: BAŞARISIZ — durum {getattr(row, 'status', None)}, hata: {getattr(row, 'error', '')}")
            return 1

        print(f"\nAI İçgörüleri ({seconds:.1f} sn)\n{row.summary}")
        for item in row.items:
            badge = f"  [{item['badge']}]" if item.get("badge") else ""
            print(f"  {EMOJI[item['type']]} {item['title']}{badge}\n     {item['detail']}")

        types = [i["type"] for i in row.items]
        findings = [t for t in types if t != "suggestion"]
        checks = {
            "2-4 bulgu": 2 <= len(findings) <= 4,
            "en fazla 1 öneri": types.count("suggestion") <= 1,
            "gelir düşüşü fark edildi": any(i["metric"] == "revenue" and i["type"] == "negative" for i in row.items),
            "yanıtta kişisel veri yok": not any(s in (row.summary + str(row.items)) for s in SECRETS),
        }
        print()
        for name, passed in checks.items():
            print(("  ✓ " if passed else "  ✗ ") + name)
        ok &= checks["2-4 bulgu"] and checks["en fazla 1 öneri"] and checks["yanıtta kişisel veri yok"]
    finally:
        biz.is_deleted = True
        db.commit()
        db.close()

    print("SONUÇ:", "BAŞARILI" if ok else "BAŞARISIZ")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
