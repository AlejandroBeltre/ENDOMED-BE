"""Celery tasks for refreshing analytics materialized views.

Schedule (defined in config/celery.py):
  refresh_mv_ingresos     → hourly
  refresh_mv_consultas    → daily 3 AM
  refresh_mv_prevalencia  → daily 3 AM
"""

import logging

from celery import shared_task
from django.db import connection

logger = logging.getLogger(__name__)


def _refresh_view(view_name: str) -> None:
    """REFRESH MATERIALIZED VIEW CONCURRENTLY requires a unique index."""
    with connection.cursor() as cursor:
        cursor.execute(
            f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}"  # noqa: S608
        )
    logger.info("Refreshed materialized view: %s", view_name)


@shared_task(name="tasks.reportes.refresh_mv_ingresos", bind=True, max_retries=3)
def refresh_mv_ingresos(self) -> str:
    """Refresh mv_ingresos_resumen — runs hourly."""
    try:
        _refresh_view("mv_ingresos_resumen")
        return "mv_ingresos_resumen refreshed"
    except Exception as exc:
        logger.error("Failed to refresh mv_ingresos_resumen: %s", exc)
        raise self.retry(exc=exc, countdown=60)


@shared_task(name="tasks.reportes.refresh_mv_consultas", bind=True, max_retries=3)
def refresh_mv_consultas(self) -> str:
    """Refresh mv_consultas_resumen — runs daily at 3 AM."""
    try:
        _refresh_view("mv_consultas_resumen")
        return "mv_consultas_resumen refreshed"
    except Exception as exc:
        logger.error("Failed to refresh mv_consultas_resumen: %s", exc)
        raise self.retry(exc=exc, countdown=300)


@shared_task(name="tasks.reportes.refresh_mv_prevalencia", bind=True, max_retries=3)
def refresh_mv_prevalencia(self) -> str:
    """Refresh mv_prevalencia_diagnosticos — runs daily at 3 AM."""
    try:
        _refresh_view("mv_prevalencia_diagnosticos")
        return "mv_prevalencia_diagnosticos refreshed"
    except Exception as exc:
        logger.error("Failed to refresh mv_prevalencia_diagnosticos: %s", exc)
        raise self.retry(exc=exc, countdown=300)
