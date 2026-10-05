"""
Messages sent after an online booking.

- In-app notification (navbar bell) for every OWNER / ADMIN of the business.
- Confirmation e-mail to the customer when an address was given. Sent from a
  FastAPI background task after the response, so a slow or broken SMTP
  server never delays or fails the booking itself.
"""
import html
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.membership.models import Membership
from app.modules.notifications.models import Notification
from app.modules.reminders.templating import format_date_tr, format_time
from app.shared.enums.appointment import AppointmentStatus
from app.shared.enums.membership import MembershipRole
from app.shared.enums.notification import NotificationType
from app.shared.mail.smtp import SMTPClient

logger = logging.getLogger(__name__)

NOTIFY_ROLES = (MembershipRole.OWNER, MembershipRole.ADMIN)


def _when(result) -> str:
    appt = result.appointment
    return f"{format_date_tr(appt.appointment_date)} {format_time(appt.start_time)}"


def notify_business(db: Session, result) -> int:
    """Creates one bell notification per owner/admin. Returns how many were created."""
    appt = result.appointment
    confirmed = appt.status == AppointmentStatus.CONFIRMED
    staff = f" · {result.staff.full_name}" if result.staff else ""
    message = (
        f"{appt.customer_name} · {result.service.name} · {_when(result)}{staff}. "
        + ("Otomatik onaylandı." if confirmed else "Onayınızı bekliyor (Randevu Yönetimi).")
    )
    user_ids = db.scalars(
        select(Membership.user_id).where(
            Membership.business_id == appt.business_id,
            Membership.role.in_(NOTIFY_ROLES),
            Membership.is_deleted.is_(False),
        )
    ).all()
    for user_id in user_ids:
        db.add(Notification(
            business_id=appt.business_id,
            user_id=user_id,
            title="Yeni online randevu",
            message=message,
            type=NotificationType.APPOINTMENT_CREATED,
            reference_id=appt.id,
            reference_type="appointment",
            is_read=False,
        ))
    db.commit()
    return len(user_ids)


def build_customer_email(result) -> tuple[str, str, str]:
    """Returns (subject, html, text) in Turkish."""
    appt, business = result.appointment, result.business
    confirmed = appt.status == AppointmentStatus.CONFIRMED
    headline = "Randevunuz onaylandı" if confirmed else "Randevu talebiniz alındı"
    status_line = (
        "Randevunuz onaylandı, sizi bekliyoruz."
        if confirmed
        else "Talebiniz işletmeye iletildi. İşletme onayladığında randevunuz kesinleşecektir."
    )
    rows = [
        ("İşletme", business.name),
        ("Hizmet", result.service.name),
        ("Tarih", format_date_tr(appt.appointment_date)),
        ("Saat", format_time(appt.start_time)),
    ]
    if result.staff:
        rows.append(("Personel", result.staff.full_name))
    if business.phone:
        rows.append(("İletişim", business.phone))

    subject = f"{headline} – {business.name}"
    text = (
        f"Merhaba {appt.customer_name},\n\n{status_line}\n\n"
        + "\n".join(f"{k}: {v}" for k, v in rows)
        + "\n\nRandevunuza gelemeyecekseniz lütfen işletmeyle iletişime geçin.\n"
    )
    table = "".join(
        f'<tr><td style="padding:4px 12px 4px 0;color:#6b7280">{html.escape(k)}</td>'
        f'<td style="padding:4px 0;font-weight:600">{html.escape(str(v))}</td></tr>'
        for k, v in rows
    )
    body = f"""<!doctype html>
<html lang="tr"><body style="margin:0;background:#f4f5f7;font-family:Arial,Helvetica,sans-serif;color:#111827">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:24px 0"><tr><td align="center">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:8px;padding:28px">
<tr><td style="font-size:13px;color:#6b7280;padding-bottom:4px">{html.escape(business.name)}</td></tr>
<tr><td style="font-size:20px;font-weight:700;padding-bottom:12px">{headline}</td></tr>
<tr><td style="font-size:15px;line-height:1.6;padding-bottom:16px">Merhaba {html.escape(appt.customer_name)},<br>{status_line}</td></tr>
<tr><td><table role="presentation" cellpadding="0" cellspacing="0" style="font-size:14px">{table}</table></td></tr>
<tr><td style="font-size:12px;color:#9ca3af;padding-top:24px">Randevunuza gelemeyecekseniz lütfen işletmeyle iletişime geçin.</td></tr>
</table></td></tr></table>
</body></html>"""
    return subject, body, text


def send_customer_email(to_email: str, subject: str, html_body: str, text_body: str) -> None:
    """Background task: never raises. Silent when mail is not configured."""
    if not settings.MAIL_FROM:
        return
    try:
        SMTPClient.send(to_email=to_email, subject=subject, html=html_body, text=text_body)
    except Exception as exc:
        logger.warning("Online booking confirmation e-mail failed: %s: %s", type(exc).__name__, exc)
