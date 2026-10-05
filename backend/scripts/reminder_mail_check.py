"""
Hatırlatma e-postasının gerçek SMTP (ör. Mailtrap) ile uçtan uca kontrolü.

    python scripts/reminder_mail_check.py

- Ayrı bir demo işletme açar: 24 saat önce kuralı + 3 saat sonraya bir randevu.
- Sadece bu demo işletme için send_due_reminders mantığını çalıştırır; gerçek
  işletmelerinin müşterilerine hiçbir şey gönderilmez.
- .env'deki MAIL_* ayarlarıyla gerçekten mail yollar (Mailtrap sandbox'ı mailleri
  kimseye iletmez, sadece kendi gelen kutusunda gösterir).
- Sonra ikinci kez çalıştırıp aynı randevuya tekrar mail gitmediğini kontrol eder,
  demo veriyi temizler. Şifreler hiçbir yere yazdırılmaz.
"""
import os
import sys
import uuid
from datetime import timedelta
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
from app.modules.reminders.delivery import DeliveryReport, SMTPMailer, _process_business, local_now  # noqa: E402
from app.modules.reminders.models import ReminderConfig, ReminderLog  # noqa: E402
from app.modules.services.models import Service  # noqa: E402
from app.shared.enums.appointment import AppointmentStatus  # noqa: E402
from app.shared.enums.reminder import ReminderChannel  # noqa: E402

engine.echo = False  # keep the output readable when DEBUG=True

RECIPIENT = "musteri-demo@example.test"


def main() -> int:
    print("SMTP sunucusu:", settings.MAIL_SERVER, "port", settings.MAIL_PORT,
          "| TLS" if settings.MAIL_USE_TLS else "", "| SSL" if settings.MAIL_USE_SSL else "",
          "| kullanıcı adı:", "tanımlı" if settings.MAIL_USERNAME else "yok")
    if not settings.MAIL_FROM:
        print("MAIL_FROM tanımlı değil; backend/.env dosyasına ekle.")
        return 2

    db = SessionLocal()
    sfx = uuid.uuid4().hex[:6]
    now = local_now()
    start = (now + timedelta(hours=3)).replace(second=0, microsecond=0)
    start = start.replace(minute=(start.minute // 5) * 5)

    biz = Business(name="E2E Hatırlatma Testi", slug=f"e2e-hatirlatma-{sfx}", industry="beauty",
                   email=f"e2e-hatirlatma-{sfx}@example.test", phone="02120000000")
    db.add(biz)
    db.flush()
    service = Service(business_id=biz.id, name="Saç Kesimi", price=350, duration_minutes=60)
    db.add(service)
    db.flush()
    config = ReminderConfig(
        business_id=biz.id, channel=ReminderChannel.EMAIL, hours_before=24, is_active=True,
        message_template=("Sayın {{customer_name}}, {{appointment_date}} saat {{start_time}}'da "
                          "{{business_name}} işletmesinde {{service_name}} randevunuz bulunmaktadır."),
    )
    appt = Appointment(business_id=biz.id, customer_name="Ayşe Kaya (demo)", customer_email=RECIPIENT,
                       service_id=service.id, appointment_date=start.date(), start_time=start.time(),
                       end_time=(start + timedelta(hours=1)).time(), status=AppointmentStatus.CONFIRMED)
    db.add_all([config, appt])
    db.commit()
    print(f"Demo randevu: {start:%d.%m.%Y %H:%M} · alıcı {RECIPIENT}")

    ok = True
    try:
        mailer = SMTPMailer()
        first = DeliveryReport()
        try:
            _process_business(db, biz.id, [config], local_now(), mailer, first)
        finally:
            mailer.close()
        print(f"1. tarama: gönderilen {first.sent}, başarısız {first.failed}, atlanan {first.skipped}")
        for err in first.errors:
            print("   hata:", err)

        second = DeliveryReport()
        mailer = SMTPMailer()
        try:
            _process_business(db, biz.id, [config], local_now(), mailer, second)
        finally:
            mailer.close()
        print(f"2. tarama: gönderilen {second.sent} (0 olmalı: aynı randevuya ikinci mail gitmemeli)")

        db.expire_all()
        log = db.query(ReminderLog).filter(ReminderLog.appointment_id == appt.id).one()
        print(f"Kayıt: durum {log.status.value}, deneme {log.attempts}, gönderim {log.sent_at:%H:%M:%S}" if log.sent_at
              else f"Kayıt: durum {log.status.value}, hata: {log.error_message}")
        ok = first.sent == 1 and second.sent == 0
    finally:
        # Cleanup: the demo business disappears from the app; logs stay for audit.
        appt.status = AppointmentStatus.CANCELLED
        config.is_active = False
        biz.is_deleted = True
        db.commit()
        db.close()

    if ok:
        print("SONUÇ: BAŞARILI — Mailtrap gelen kutusunda 'Randevu hatırlatması – E2E Hatırlatma Testi' konulu maili gör.")
        return 0
    print("SONUÇ: BAŞARISIZ — yukarıdaki hatayı kontrol et (genelde MAIL_USERNAME / MAIL_PASSWORD / port).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
