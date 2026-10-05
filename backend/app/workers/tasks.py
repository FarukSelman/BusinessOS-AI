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


@celery_app.task(name="insights.generate_all")
def generate_business_insights_task() -> dict:
    """Nightly task (Celery beat, 03:00): AI insights for every active business."""
    import app.db.base  # noqa: F401  - registers all models before querying
    from app.db.session import SessionLocal
    from app.modules.insights.service import generate_for_all_businesses

    db = SessionLocal()
    try:
        return generate_for_all_businesses(db)
    finally:
        db.close()

