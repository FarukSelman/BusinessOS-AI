from app.workers.celery_app import celery_app


@celery_app.task(name="reminders.send_due_reminders")
def send_due_reminders_task() -> dict:
    """Periodic task (Celery beat): sends every reminder that is due now."""
    import app.db.base  # noqa: F401  - registers all models before querying
    from app.db.session import SessionLocal
    from app.modules.reminders.delivery import send_due_reminders

    db = SessionLocal()
    try:
        return send_due_reminders(db).as_dict()
    finally:
        db.close()
