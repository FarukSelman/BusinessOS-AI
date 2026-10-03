"""
Reminder message templates.

Business owners write templates with {{variable}} placeholders on the
reminder settings page. Values are HTML-escaped for the HTML part, unknown
placeholders are left untouched so a typo is visible instead of silently
disappearing.
"""
import html
import re
from datetime import date, time

PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")

# Variables offered on the settings page (keep in sync with the frontend).
TEMPLATE_VARIABLES = (
    "customer_name",
    "appointment_date",
    "start_time",
    "service_name",
    "staff_name",
    "business_name",
    "branch_name",
    "branch_address",
)

MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
WEEKDAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

DEFAULT_TEMPLATE = (
    "Sayın {{customer_name}}, {{appointment_date}} saat {{start_time}}'da "
    "{{service_name}} randevunuz bulunmaktadır."
)


def format_date_tr(value: date) -> str:
    """date(2026, 10, 6) -> '6 Ekim 2026 Salı'"""
    return f"{value.day} {MONTHS[value.month - 1]} {value.year} {WEEKDAYS[value.weekday()]}"


def format_time(value: time) -> str:
    return value.strftime("%H:%M")


def render(template: str, context: dict[str, str | None], *, escape: bool) -> str:
    def replace(match: re.Match) -> str:
        key = match.group(1)
        if key not in context:
            return match.group(0)
        value = context[key] or ""
        return html.escape(value) if escape else value

    return PLACEHOLDER.sub(replace, template)


def build_reminder_email(template: str, context: dict[str, str | None]) -> tuple[str, str, str]:
    """Returns (subject, html_body, text_body)."""
    business = context.get("business_name") or "İşletmemiz"
    subject = f"Randevu hatırlatması – {business}"

    text_message = render(template, context, escape=False).strip()
    html_message = render(template, context, escape=True).strip().replace("\n", "<br>")

    details = [
        ("Tarih", context.get("appointment_date")),
        ("Saat", context.get("start_time")),
        ("Hizmet", context.get("service_name")),
        ("Personel", context.get("staff_name")),
        ("Şube", context.get("branch_name")),
        ("Adres", context.get("branch_address")),
    ]
    details = [(k, v) for k, v in details if v]

    rows = "".join(
        f'<tr><td style="padding:4px 12px 4px 0;color:#6b7280">{k}</td>'
        f'<td style="padding:4px 0;font-weight:600">{html.escape(v)}</td></tr>'
        for k, v in details
    )
    html_body = f"""<!doctype html>
<html lang="tr"><body style="margin:0;background:#f4f5f7;font-family:Arial,Helvetica,sans-serif;color:#111827">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:24px 0"><tr><td align="center">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:8px;padding:28px">
<tr><td style="font-size:13px;color:#6b7280;padding-bottom:4px">{html.escape(business)}</td></tr>
<tr><td style="font-size:20px;font-weight:700;padding-bottom:16px">Randevu hatırlatması</td></tr>
<tr><td style="font-size:15px;line-height:1.6;padding-bottom:16px">{html_message}</td></tr>
<tr><td><table role="presentation" cellpadding="0" cellspacing="0" style="font-size:14px">{rows}</table></td></tr>
<tr><td style="font-size:12px;color:#9ca3af;padding-top:24px">Randevunuza gelemeyecekseniz lütfen işletmeyle iletişime geçin.</td></tr>
</table></td></tr></table>
</body></html>"""

    text_details = "\n".join(f"{k}: {v}" for k, v in details)
    text_body = f"{text_message}\n\n{text_details}\n\nRandevunuza gelemeyecekseniz lütfen işletmeyle iletişime geçin.\n— {business}"
    return subject, html_body, text_body


def sample_context(business_name: str) -> dict[str, str]:
    """Context used by the 'send test' button: realistic but fake data."""
    from datetime import timedelta

    day = date.today() + timedelta(days=1)
    return {
        "customer_name": "Ayşe Yılmaz (örnek)",
        "appointment_date": format_date_tr(day),
        "start_time": "14:30",
        "service_name": "Örnek Hizmet",
        "staff_name": "Örnek Personel",
        "business_name": business_name,
        "branch_name": "Merkez Şube",
        "branch_address": "Örnek Mah. Örnek Cad. No:1",
    }
