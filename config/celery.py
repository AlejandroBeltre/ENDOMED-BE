"""Celery application for ENDOMED.

Workers:  celery -A config worker -l info
Beat:     celery -A config beat -l info
"""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("endomed")

# Use Django settings prefixed with CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps and the top-level tasks/ package
app.autodiscover_tasks(["tasks"])

# ── Beat schedule ─────────────────────────────────────────────────────────────

app.conf.beat_schedule = {
    # Hourly: refresh ingresos materialized view
    "refresh-mv-ingresos-hourly": {
        "task": "tasks.reportes.refresh_mv_ingresos",
        "schedule": crontab(minute=0),  # top of every hour
    },
    # Daily 3 AM: refresh consultas + prevalencia materialized views
    "refresh-mv-consultas-daily": {
        "task": "tasks.reportes.refresh_mv_consultas",
        "schedule": crontab(hour=3, minute=0),
    },
    "refresh-mv-prevalencia-daily": {
        "task": "tasks.reportes.refresh_mv_prevalencia",
        "schedule": crontab(hour=3, minute=0),
    },
}

app.conf.timezone = "America/Santo_Domingo"
