"""Celery tasks for sending appointment reminders via WhatsApp and email.

Schedule:
  - 24 hours before cita: WhatsApp + email
  -  2 hours before cita: WhatsApp only

Tasks are scheduled with ETA when a Cita is created/confirmed via
``programar_recordatorios_cita(cita_id)``.
"""

import logging
from datetime import timedelta
from uuid import UUID

from celery import shared_task
from django.utils import timezone as tz

logger = logging.getLogger(__name__)


# ── helpers ───────────────────────────────────────────────────────────────────


def _get_cita(cita_id: UUID):
    from apps.agenda.models import Cita

    return (
        Cita.objects.select_related("paciente", "tipo_consulta", "sede")
        .filter(id=cita_id, deleted_at__isnull=True)
        .first()
    )


def _mark_recordatorio(
    cita_id: UUID, canal: str, anticipacion_horas: int, *, ok: bool, error: str = ""
) -> None:
    from apps.agenda.models import Recordatorio

    rec = Recordatorio.objects.filter(
        cita_id=cita_id,
        canal=canal,
        anticipacion_horas=anticipacion_horas,
    ).first()
    if rec is None:
        return
    rec.estado = Recordatorio.Estado.ENVIADO if ok else Recordatorio.Estado.FALLIDO
    rec.enviado_at = tz.now() if ok else None
    rec.error_msg = error
    rec.save(update_fields=["estado", "enviado_at", "error_msg", "updated_at"])


def _send_whatsapp(to: str, body: str) -> None:
    """Send a WhatsApp message via Twilio."""
    from decouple import config
    from twilio.rest import Client

    client = Client(
        config("TWILIO_ACCOUNT_SID"),
        config("TWILIO_AUTH_TOKEN"),
    )
    client.messages.create(
        from_=config("TWILIO_WHATSAPP_FROM"),
        to=f"whatsapp:{to}",
        body=body,
    )


def _send_email(to: str, subject: str, body: str) -> None:
    """Send an email via SendGrid."""
    import sendgrid
    from decouple import config
    from sendgrid.helpers.mail import Content, Email, Mail, To

    sg = sendgrid.SendGridAPIClient(api_key=config("SENDGRID_API_KEY"))
    mail = Mail(
        from_email=Email(config("SENDGRID_FROM_EMAIL"), "ENDOMED"),
        to_emails=To(to),
        subject=subject,
        plain_text_content=Content("text/plain", body),
    )
    sg.client.mail.send.post(request_body=mail.get())


def _format_message(cita, anticipacion_horas: int) -> str:
    fecha = cita.fecha_hora.strftime("%d/%m/%Y a las %H:%M")
    return (
        f"Hola {cita.paciente.nombre}, le recordamos su cita de {cita.tipo_consulta.nombre} "
        f"en {cita.sede.nombre} el {fecha}. "
        f"Faltan {anticipacion_horas} hora{'s' if anticipacion_horas > 1 else ''}. "
        f"Si necesita cancelar, comuníquese con nosotros."
    )


# ── main tasks ────────────────────────────────────────────────────────────────


@shared_task(
    name="tasks.recordatorios.enviar_recordatorio_whatsapp", bind=True, max_retries=2
)
def enviar_recordatorio_whatsapp(self, cita_id: str, anticipacion_horas: int) -> str:
    """Send a WhatsApp reminder for the given cita."""
    cid = UUID(cita_id)
    cita = _get_cita(cid)

    if cita is None:
        logger.warning(
            "Cita %s not found or deleted — skipping WhatsApp reminder", cita_id
        )
        return "skipped"

    if cita.estado in ("cancelada", "completada"):
        logger.info("Cita %s is %s — skipping WhatsApp reminder", cita_id, cita.estado)
        return "skipped"

    mensaje = _format_message(cita, anticipacion_horas)

    try:
        _send_whatsapp(cita.paciente.telefono_whatsapp, mensaje)
        _mark_recordatorio(cid, "whatsapp", anticipacion_horas, ok=True)
        logger.info(
            "WhatsApp reminder sent for cita %s (%dh)", cita_id, anticipacion_horas
        )
        return "sent"
    except Exception as exc:
        logger.error("WhatsApp reminder failed for cita %s: %s", cita_id, exc)
        _mark_recordatorio(
            cid, "whatsapp", anticipacion_horas, ok=False, error=str(exc)
        )
        raise self.retry(exc=exc, countdown=300)


@shared_task(
    name="tasks.recordatorios.enviar_recordatorio_email", bind=True, max_retries=2
)
def enviar_recordatorio_email(self, cita_id: str, anticipacion_horas: int) -> str:
    """Send an email reminder for the given cita."""
    cid = UUID(cita_id)
    cita = _get_cita(cid)

    if cita is None:
        logger.warning(
            "Cita %s not found or deleted — skipping email reminder", cita_id
        )
        return "skipped"

    if cita.estado in ("cancelada", "completada"):
        logger.info("Cita %s is %s — skipping email reminder", cita_id, cita.estado)
        return "skipped"

    if not cita.paciente.email:
        logger.info("Cita %s patient has no email — skipping", cita_id)
        return "skipped"

    mensaje = _format_message(cita, anticipacion_horas)
    subject = f"Recordatorio de cita — {cita.tipo_consulta.nombre}"

    try:
        _send_email(cita.paciente.email, subject, mensaje)
        _mark_recordatorio(cid, "email", anticipacion_horas, ok=True)
        logger.info(
            "Email reminder sent for cita %s (%dh)", cita_id, anticipacion_horas
        )
        return "sent"
    except Exception as exc:
        logger.error("Email reminder failed for cita %s: %s", cita_id, exc)
        _mark_recordatorio(cid, "email", anticipacion_horas, ok=False, error=str(exc))
        raise self.retry(exc=exc, countdown=300)


# ── scheduling helper (called from service layer) ─────────────────────────────


def programar_recordatorios_cita(cita_id: UUID) -> None:
    """Schedule WhatsApp + email reminders at 24h and 2h before the cita.

    Creates ``Recordatorio`` DB records (idempotent) and enqueues Celery tasks
    with ETA.  Call this whenever a Cita is created or confirmed.
    """
    from apps.agenda.models import Cita, Recordatorio

    try:
        cita = Cita.objects.get(id=cita_id, deleted_at__isnull=True)
    except Cita.DoesNotExist:
        return

    now = tz.now()
    cita_str = str(cita_id)

    schedule = [
        (24, ["whatsapp", "email"]),
        (2, ["whatsapp"]),
    ]

    for horas, canales in schedule:
        eta = cita.fecha_hora - timedelta(hours=horas)
        if eta <= now:
            continue

        for canal in canales:
            rec, created = Recordatorio.objects.get_or_create(
                cita=cita,
                canal=canal,
                anticipacion_horas=horas,
                defaults={"estado": Recordatorio.Estado.PENDIENTE},
            )
            if not created and rec.estado == Recordatorio.Estado.ENVIADO:
                continue

            if canal == "whatsapp":
                enviar_recordatorio_whatsapp.apply_async(
                    args=[cita_str, horas],
                    eta=eta,
                )
            else:
                enviar_recordatorio_email.apply_async(
                    args=[cita_str, horas],
                    eta=eta,
                )
