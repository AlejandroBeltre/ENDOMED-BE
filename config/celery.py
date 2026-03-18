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

# Explicitly register task modules (autodiscover_tasks would look for tasks/tasks.py
# which does not exist — our modules are tasks/reportes.py and tasks/recordatorios.py)
app.conf.include = ["tasks.reportes", "tasks.recordatorios"]

# Retain broker connection retry behaviour on startup (Celery 6 will drop the default)
app.conf.broker_connection_retry_on_startup = True

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
