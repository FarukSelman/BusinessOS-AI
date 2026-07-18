import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


class SMTPClient:

    @staticmethod
    def send(
        to_email: str,
        subject: str,
        html: str,
    ):

        message = MIMEMultipart()

        message["From"] = (
            f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
        )

        message["To"] = to_email

        message["Subject"] = subject

        message.attach(
            MIMEText(
                html,
                "html",
            )
        )

        server = smtplib.SMTP(
            settings.MAIL_SERVER,
            settings.MAIL_PORT,
        )

        server.starttls()

        server.login(
            settings.MAIL_USERNAME,
            settings.MAIL_PASSWORD,
        )

        server.send_message(message)

        server.quit()