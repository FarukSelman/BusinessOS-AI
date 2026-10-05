"""
Turns aggregated metrics into the "AI İçgörüleri" card with the language model.

- Input: only build_metrics() output (numbers, dates, weekdays, service names,
  anonymous staff labels). Percent changes are computed in Python; the model
  interprets them and must not invent numbers.
- Output: strict JSON (OpenAI structured outputs) validated again here.
- The number badge next to each item ("Gelir −%15") is rendered from the
  metrics by our code, so the figure on screen is right even if the model's
  sentence is off.
"""
import json
from dataclasses import dataclass

from app.ai.agents.tools.common import money

ITEM_TYPES = ("positive", "negative", "neutral", "suggestion")
MAX_FINDINGS = 4
MIN_FINDINGS = 2
MAX_SUGGESTIONS = 1

METRIC_KEYS = (
    "revenue", "expenses", "net", "appointments", "completed", "cancel_rate", "no_show_rate",
    "new_customers", "average_ticket", "online_share", "top_service", "busiest_weekday",
    "quietest_weekday", "busiest_hour", "staff", "upcoming", "pending", "none",
)

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "items"],
    "properties": {
        "summary": {"type": "string", "description": "Tek cümlelik genel değerlendirme"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["type", "title", "detail", "metric"],
                "properties": {
                    "type": {"type": "string", "enum": list(ITEM_TYPES)},
                    "title": {"type": "string", "description": "En fazla 6 kelimelik başlık"},
                    "detail": {"type": "string", "description": "1-2 cümle açıklama"},
                    "metric": {"type": "string", "enum": list(METRIC_KEYS)},
                },
            },
        },
    },
}

SYSTEM_PROMPT = """Sen küçük işletmeler için çalışan bir iş analistisin. Sana bir işletmenin son 30 gününe ait
toplu metrikleri ve önceki 30 günle karşılaştırmasını JSON olarak veriyorum. Türkçe, kısa ve somut
içgörüler üret.

Kurallar:
1. YALNIZCA verilen sayıları kullan. Yeni sayı, yüzde ya da tarih uydurma; hesap yapma, "changes"
   alanındaki hazır yüzdeleri kullan. null olan değişimler için yüzde söyleme.
2. 3 veya 4 bulgu yaz (type: positive, negative ya da neutral) ve en fazla 1 öneri (type: suggestion).
   Önemli değişimlere öncelik ver (gelir, randevu, iptal oranı, yeni müşteri).
3. Neden-sonuç ilişkisini kesinmiş gibi yazma; "muhtemel sebep", "işaret ediyor olabilir" gibi
   ifadeler kullan ve bunu yalnızca veride destekleyen bir sayı varsa yap
   (ör. gelir düştü VE iptal oranı arttı).
4. Kişi adı yazma. Personeli yalnızca verilen etiketlerle ("Personel A") an.
5. Her maddenin "metric" alanına o maddenin dayandığı metriği yaz; uygun değilse "none".
6. Öneri somut ve uygulanabilir olsun (ör. sakin gün/saat için kampanya, onay bekleyen randevuları
   onaylama).
7. Para birimi TL. Başlıklar en fazla 6 kelime, açıklamalar en fazla 2 cümle."""


class InvalidInsight(ValueError):
    pass


@dataclass
class GeneratedInsight:
    summary: str
    items: list[dict]


def build_user_prompt(metrics: dict) -> str:
    return "İşletme metrikleri (JSON):\n" + json.dumps(metrics, ensure_ascii=False, sort_keys=True)


# ---------------------------------------------------------------- badges

def _pct(value) -> str:
    if value is None:
        return ""
    sign = "+" if value > 0 else ("−" if value < 0 else "±")
    return f"{sign}%{abs(value):g}".replace(".", ",")


def badge_for(metric: str, metrics: dict) -> str | None:
    """Short figure shown next to an item, computed from the metrics (never from model text)."""
    cur = metrics.get("current", {})
    appts = cur.get("appointments", {})
    ch = metrics.get("changes", {})

    def with_change(label, value_text, change):
        return f"{label} {_pct(change)}" if change is not None else f"{label} {value_text}"

    if metric == "revenue":
        return with_change("Gelir", money(cur.get("revenue")), ch.get("revenue_pct"))
    if metric == "expenses":
        return with_change("Gider", money(cur.get("expenses")), ch.get("expenses_pct"))
    if metric == "net":
        return with_change("Net", money(cur.get("net")), ch.get("net_pct"))
    if metric == "appointments":
        return with_change("Randevu", str(appts.get("total", 0)), ch.get("appointments_pct"))
    if metric == "completed":
        return with_change("Tamamlanan", str(appts.get("completed", 0)), ch.get("completed_pct"))
    if metric == "cancel_rate" and appts.get("cancel_rate") is not None:
        pp = ch.get("cancel_rate_pp")
        extra = f" ({'+' if pp > 0 else ''}{pp:g} puan)".replace(".", ",") if pp else ""
        return f"İptal %{appts['cancel_rate']:g}{extra}".replace(".", ",")
    if metric == "no_show_rate" and appts.get("no_show_rate") is not None:
        return f"Gelmeyen %{appts['no_show_rate']:g}".replace(".", ",")
    if metric == "new_customers":
        return with_change("Yeni müşteri", str(cur.get("new_customers", 0)), ch.get("new_customers_pct"))
    if metric == "average_ticket" and cur.get("average_ticket"):
        return with_change("Ort. sepet", money(cur["average_ticket"]), ch.get("average_ticket_pct"))
    if metric == "online_share" and appts.get("online_share") is not None:
        return f"Online %{appts['online_share']:g}".replace(".", ",")
    if metric == "top_service" and metrics.get("top_services"):
        top = metrics["top_services"][0]
        return f"{top['service']} · {top['appointments']}"
    if metric == "busiest_weekday" and metrics.get("busiest_weekday"):
        return f"En yoğun: {metrics['busiest_weekday']}"
    if metric == "quietest_weekday" and metrics.get("quietest_weekday"):
        return f"En sakin: {metrics['quietest_weekday']}"
    if metric == "busiest_hour" and metrics.get("busiest_hour"):
        return f"En yoğun saat {metrics['busiest_hour']}"
    if metric == "upcoming":
        return f"7 gün: {metrics.get('upcoming_7_days', 0)} randevu"
    if metric == "pending":
        total = metrics.get("pending_appointment_approvals", 0) + metrics.get("pending_agent_drafts", 0)
        return f"Onay bekleyen {total}"
    return None


# ---------------------------------------------------------------- validation

def _clean(text, limit: int) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def parse_and_validate(raw: str, metrics: dict) -> GeneratedInsight:
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        raise InvalidInsight("Model yanıtı JSON değil.") from None
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise InvalidInsight("Model yanıtı beklenen biçimde değil.")

    findings, suggestions = [], []
    for item in data["items"]:
        if not isinstance(item, dict) or item.get("type") not in ITEM_TYPES:
            continue
        title, detail = _clean(item.get("title"), 80), _clean(item.get("detail"), 320)
        if not title or not detail:
            continue
        metric = item.get("metric") if item.get("metric") in METRIC_KEYS else "none"
        clean = {"type": item["type"], "title": title, "detail": detail, "metric": metric,
                 "badge": badge_for(metric, metrics)}
        (suggestions if item["type"] == "suggestion" else findings).append(clean)

    findings, suggestions = findings[:MAX_FINDINGS], suggestions[:MAX_SUGGESTIONS]
    if len(findings) < MIN_FINDINGS:
        raise InvalidInsight("Model yeterli sayıda geçerli madde üretmedi.")
    summary = _clean(data.get("summary"), 300)
    if not summary:
        raise InvalidInsight("Model özet cümlesi üretmedi.")
    return GeneratedInsight(summary=summary, items=findings + suggestions)


def generate(client, metrics: dict, model: str, timeout: float) -> GeneratedInsight:
    """Calls the model once and validates the answer. Raises on any problem."""
    raw = client.chat_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(metrics),
        schema=SCHEMA,
        schema_name="business_insights",
        model=model,
        timeout=timeout,
    )
    return parse_and_validate(raw, metrics)
