from app.shared.mail.smtp import SMTPClient
from app.shared.mail.templates import invitation_template


class MailService:

    @staticmethod
    def send_invitation(
        email: str,
        business_name: str,
        invitation_link: str,
    ) -> bool:

        print("=" * 60)
        print("📧 BusinessOS AI Mail Service")
        print(f"Recipient : {email}")
        print(f"Business : {business_name}")
        print(f"Link      : {invitation_link}")

        html = invitation_template(
            business_name,
            invitation_link,
        )

        try:

            SMTPClient.send(
                to_email=email,
                subject="BusinessOS AI Invitation",
                html=html,
            )

            print("✅ Invitation email sent successfully.")
            print("=" * 60)

            return True

        except Exception as e:

            print("❌ Failed to send invitation email.")
            print(type(e).__name__)
            print(str(e))
            print("=" * 60)

            return False