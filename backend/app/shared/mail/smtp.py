import smtplib
from contextlib import contextmanager
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, make_msgid

from app.core.config import settings


class SMTPClient:
    """
    Thin wrapper around smtplib driven by the MAIL_* settings.

    - MAIL_USE_SSL=true  -> implicit TLS (SMTP_SSL, usually port 465)
    - MAIL_USE_TLS=true  -> STARTTLS after connecting (usually 587 / 2525)
    - login only when MAIL_USERNAME is set (local catchers like Mailpit need none)
    - every network call has MAIL_TIMEOUT_SECONDS
    """

    @staticmethod
    def build_message(to_email: str, subject: str, html: str, text: str | None = None) -> MIMEMultipart:
        message = MIMEMultipart("alternative")
        message["From"] = formataddr((settings.MAIL_FROM_NAME, settings.MAIL_FROM))
        message["To"] = to_email
        message["Subject"] = subject
        message["Message-ID"] = make_msgid(domain=(settings.MAIL_FROM.split("@")[-1] or None))
        # Plain text first, HTML last: clients show the last part they support.
        if text:
            message.attach(MIMEText(text, "plain", "utf-8"))
        message.attach(MIMEText(html, "html", "utf-8"))
        return message

    @staticmethod
    @contextmanager
    def connection():
        """Opens one authenticated SMTP connection; reuse it to send several messages."""
        timeout = settings.MAIL_TIMEOUT_SECONDS
        if settings.MAIL_USE_SSL:
            server = smtplib.SMTP_SSL(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=timeout)
        else:
            server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=timeout)
        try:
            if settings.MAIL_USE_TLS and not settings.MAIL_USE_SSL:
                server.starttls()
            if settings.MAIL_USERNAME:
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            yield server
        finally:
            try:
                server.quit()
            except smtplib.SMTPException:
                server.close()

    @staticmethod
    def send(to_email: str, subject: str, html: str, text: str | None = None) -> None:
        """Sends a single message on its own connection. Raises on failure."""
        message = SMTPClient.build_message(to_email, subject, html, text)
        with SMTPClient.connection() as server:
            server.send_message(message)
