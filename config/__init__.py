# Make Celery app available when Django starts (required for @shared_task)
from config.celery import app as celery_app

__all__ = ["celery_app"]
