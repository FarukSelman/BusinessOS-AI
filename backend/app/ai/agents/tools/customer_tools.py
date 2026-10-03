"""
Customer-relationship tools: segments (tags), loyalty and reviews
(Marketing and Customer Support agents). Read-only; the review reply draft
lives in draft_tools.py.
"""
from app.ai.agents.tools.base import ToolResult
from app.ai.agents.tools.common import MAX_ROWS, BusinessTool, find_customer, money


class ListCustomerSegmentsTool(BusinessTool):
    @property
    def name(self) -> str:
        return "list_customer_segments"

    @property
    def description(self) -> str:
        return "Müşteri etiketlerini (segmentleri) ve her etiketteki müşteri sayısını listeler. Etiket adı verilirse o segmentteki müşterilerin adlarını (en fazla 20) gösterir."

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"tag_name": {"type": "string", "description": "Etiket adı (opsiyonel)"}}}

    def execute(self, **kwargs) -> ToolResult:
        from app.modules.customer_tags.repository import CustomerTagRepository

        repo = CustomerTagRepository(self.db)
        tags = repo.list_by_business(self.business_id)
        if not tags:
            return ToolResult(success=True, output="Henüz müşteri etiketi tanımlanmamış.")
        counts = repo.count_customers_per_tag(self.business_id)
        wanted = (kwargs.get("tag_name") or "").strip().lower()
        if wanted:
            matches = [t for t in tags if wanted in t.name.lower()]
            if len(matches) != 1:
                names = ", ".join(t.name for t in (matches or tags))
                return ToolResult(success=False, output=f"Etiket netleştirilemedi. Mevcut etiketler: {names}")
            tag = matches[0]
            customers = repo.list_customers_with_tag(self.business_id, tag.id, limit=MAX_ROWS)
            total = counts.get(tag.id, 0)
            names = ", ".join(c.name for c in customers) or "-"
            more = f" (+{total - len(customers)} kişi daha)" if total > len(customers) else ""
            return ToolResult(success=True, output=f"'{tag.name}' segmenti: {total} müşteri\n{names}{more}")
        lines = ["Müşteri segmentleri:"]
        for t in tags:
            desc = f" — {t.description}" if t.description else ""
            lines.append(f"- {t.name}: {counts.get(t.id, 0)} müşteri{desc}")
        return ToolResult(success=True, output="\n".join(lines))


class GetLoyaltyInfoTool(BusinessTool):
    @property
    def name(self) -> str:
        return "get_loyalty_info"

    @property
    def description(self) -> str:
        return "Sadakat programının kurallarını, toplam dağıtılan/harcanan puanı ve en yüksek bakiyeli müşterileri getirir. Müşteri adı verilirse o müşterinin puan bakiyesini gösterir. Puan eklemez/harcamaz."

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"customer_name": {"type": "string", "description": "Müşteri adı (opsiyonel)"}}}

    def execute(self, **kwargs) -> ToolResult:
        from app.modules.loyalty.repository import LoyaltyRuleRepository, LoyaltyWalletRepository

        rule = LoyaltyRuleRepository(self.db).get_by_business(self.business_id)
        wallets = LoyaltyWalletRepository(self.db)
        if kwargs.get("customer_name"):
            customer, error = find_customer(self.db, self.business_id, kwargs["customer_name"])
            if error:
                return ToolResult(success=False, output=error)
            w = wallets.get_by_customer_readonly(self.business_id, customer.id)
            if w is None:
                return ToolResult(success=True, output=f"{customer.name} henüz puan kazanmamış.")
            value = f" (≈ {money(w.balance * rule.points_value_in_currency)})" if rule else ""
            return ToolResult(success=True, output=(
                f"{customer.name}: {w.balance} puan{value}; toplam kazanılan {w.lifetime_earned}, harcanan {w.lifetime_spent}"
            ))
        lines = []
        if rule is None:
            lines.append("Sadakat kuralı tanımlanmamış.")
        else:
            lines.append(
                f"Program {'aktif' if rule.is_active else 'pasif'}: her 1 TL harcamaya {rule.points_per_currency:g} puan"
                f"{f' (en az {money(rule.min_spend_for_earn)} harcamada)' if rule.min_spend_for_earn else ''}; "
                f"1 puan = {money(rule.points_value_in_currency)}; en az {rule.min_points_for_spend} puan harcanabilir"
                f"{f'; puanlar {rule.expiry_days} günde sona erer' if rule.expiry_days else ''}."
            )
        totals = wallets.get_totals(self.business_id)
        lines.append(
            f"{totals['wallet_count']} müşteride toplam {totals['outstanding_points']} puan bekliyor; "
            f"şimdiye kadar {totals['lifetime_earned']} puan kazanıldı, {totals['lifetime_spent']} puan harcandı."
        )
        top = wallets.list_top_by_balance(self.business_id, limit=10)
        if top:
            lines.append("En yüksek bakiyeler: " + ", ".join(f"{name} ({balance})" for name, balance in top))
        return ToolResult(success=True, output="\n".join(lines))


REVIEW_FILTERS = ["unreplied", "pending", "published", "all"]


class ListReviewsTool(BusinessTool):
    @property
    def name(self) -> str:
        return "list_reviews"

    @property
    def description(self) -> str:
        return (
            "Müşteri yorumlarını listeler. Filtre: unreplied=yayında ama yanıtlanmamış, pending=onay bekleyen, "
            "published=yayında, all=hepsi. Puana göre filtrelenebilir. Her yorumun bir referans kodu (#abc123) vardır."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "filter": {"type": "string", "enum": REVIEW_FILTERS, "description": "Varsayılan: unreplied"},
                "min_rating": {"type": "integer", "minimum": 1, "maximum": 5},
                "max_rating": {"type": "integer", "minimum": 1, "maximum": 5},
            },
        }

    def execute(self, **kwargs) -> ToolResult:
        from app.modules.reviews.models import CustomerReview
        from app.shared.enums.review import ReviewStatus

        f = kwargs.get("filter") if kwargs.get("filter") in REVIEW_FILTERS else "unreplied"
        q = self.db.query(CustomerReview).filter(
            CustomerReview.business_id == self.business_id, CustomerReview.is_deleted.is_(False)
        )
        if f == "unreplied":
            q = q.filter(CustomerReview.status == ReviewStatus.PUBLISHED, CustomerReview.reply.is_(None))
        elif f == "pending":
            q = q.filter(CustomerReview.status == ReviewStatus.PENDING)
        elif f == "published":
            q = q.filter(CustomerReview.status == ReviewStatus.PUBLISHED)
        if kwargs.get("min_rating"):
            q = q.filter(CustomerReview.rating >= int(kwargs["min_rating"]))
        if kwargs.get("max_rating"):
            q = q.filter(CustomerReview.rating <= int(kwargs["max_rating"]))
        reviews = q.order_by(CustomerReview.created_at.desc()).limit(MAX_ROWS).all()
        if not reviews:
            return ToolResult(success=True, output="Bu kriterlere uyan yorum yok.")
        lines = []
        for r in reviews:
            comment = (r.comment or "(yorum metni yok)").strip()
            if len(comment) > 300:
                comment = comment[:300] + "…"
            status = getattr(r.status, "value", r.status)
            replied = " · yanıtlandı" if r.reply else ""
            lines.append(f"#{str(r.id)[:8]} · {r.reviewer_name} · {r.rating}★ · {r.created_at:%Y-%m-%d} · {status}{replied}\n  \"{comment}\"")
        return ToolResult(success=True, output="\n".join(lines))
