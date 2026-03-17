"""Tests for reminder scheduling and task logic."""

import pytest
from unittest.mock import MagicMock, patch
from django.utils import timezone as tz


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def cita_futura(transactional_db, paciente, sede, doctora, tipo_consulta):
    from apps.agenda.models import Cita
    from datetime import timedelta

    return Cita.objects.create(
        paciente=paciente,
        sede=sede,
        profesional=doctora,
        tipo_consulta=tipo_consulta,
        fecha_hora=tz.now() + timedelta(hours=48),
        duracion_min=30,
        estado=Cita.Estado.PENDIENTE,
    )


# ── programar_recordatorios_cita ──────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
def test_programar_crea_recordatorios(cita_futura):
    from apps.agenda.models import Recordatorio
    from tasks.recordatorios import programar_recordatorios_cita

    with patch("tasks.recordatorios.enviar_recordatorio_whatsapp") as mock_wp, \
         patch("tasks.recordatorios.enviar_recordatorio_email") as mock_em:
        mock_wp.apply_async = MagicMock()
        mock_em.apply_async = MagicMock()
        programar_recordatorios_cita(cita_futura.id)

    recs = Recordatorio.objects.filter(cita=cita_futura)
    assert recs.count() == 3  # 24h whatsapp, 24h email, 2h whatsapp


@pytest.mark.django_db(transaction=True)
def test_programar_idempotente(cita_futura):
    from apps.agenda.models import Recordatorio
    from tasks.recordatorios import programar_recordatorios_cita

    with patch("tasks.recordatorios.enviar_recordatorio_whatsapp") as mock_wp, \
         patch("tasks.recordatorios.enviar_recordatorio_email") as mock_em:
        mock_wp.apply_async = MagicMock()
        mock_em.apply_async = MagicMock()
        programar_recordatorios_cita(cita_futura.id)
        programar_recordatorios_cita(cita_futura.id)  # second call

    assert Recordatorio.objects.filter(cita=cita_futura).count() == 3


@pytest.mark.django_db(transaction=True)
def test_programar_skips_past_cita(transactional_db, paciente, sede, doctora, tipo_consulta):
    from apps.agenda.models import Cita, Recordatorio
    from datetime import timedelta
    from tasks.recordatorios import programar_recordatorios_cita

    cita = Cita.objects.create(
        paciente=paciente,
        sede=sede,
        profesional=doctora,
        tipo_consulta=tipo_consulta,
        fecha_hora=tz.now() + timedelta(hours=1),  # less than 2h away
        duracion_min=30,
        estado=Cita.Estado.PENDIENTE,
    )

    with patch("tasks.recordatorios.enviar_recordatorio_whatsapp") as mock_wp:
        mock_wp.apply_async = MagicMock()
        programar_recordatorios_cita(cita.id)

    # Only reminders whose ETA is in the future should be created
    assert Recordatorio.objects.filter(cita=cita).count() == 0


# ── task unit tests ────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
def test_enviar_whatsapp_skips_cancelled(cita_futura):
    from tasks.recordatorios import enviar_recordatorio_whatsapp

    cita_futura.estado = "cancelada"
    cita_futura.save(update_fields=["estado"])

    result = enviar_recordatorio_whatsapp(str(cita_futura.id), 24)
    assert result == "skipped"


@pytest.mark.django_db(transaction=True)
def test_enviar_email_skips_no_email(cita_futura):
    from tasks.recordatorios import enviar_recordatorio_email

    cita_futura.paciente.email = ""
    cita_futura.paciente.save(update_fields=["email"])

    result = enviar_recordatorio_email(str(cita_futura.id), 24)
    assert result == "skipped"


@pytest.mark.django_db(transaction=True)
def test_enviar_whatsapp_marks_sent(transactional_db, cita_futura):
    from apps.agenda.models import Recordatorio
    from tasks.recordatorios import enviar_recordatorio_whatsapp

    Recordatorio.objects.create(
        cita=cita_futura,
        canal="whatsapp",
        anticipacion_horas=24,
        estado=Recordatorio.Estado.PENDIENTE,
    )

    with patch("tasks.recordatorios._send_whatsapp") as mock_send:
        mock_send.return_value = None
        result = enviar_recordatorio_whatsapp(str(cita_futura.id), 24)

    assert result == "sent"
    rec = Recordatorio.objects.get(cita=cita_futura, canal="whatsapp", anticipacion_horas=24)
    assert rec.estado == Recordatorio.Estado.ENVIADO


@pytest.mark.django_db(transaction=True)
def test_enviar_email_marks_sent(transactional_db, cita_futura):
    from apps.agenda.models import Recordatorio
    from tasks.recordatorios import enviar_recordatorio_email

    # Ensure paciente has an email so the task doesn't skip
    cita_futura.paciente.email = "paciente@test.com"
    cita_futura.paciente.save(update_fields=["email"])

    Recordatorio.objects.create(
        cita=cita_futura,
        canal="email",
        anticipacion_horas=24,
        estado=Recordatorio.Estado.PENDIENTE,
    )

    with patch("tasks.recordatorios._send_email") as mock_send:
        mock_send.return_value = None
        result = enviar_recordatorio_email(str(cita_futura.id), 24)

    assert result == "sent"
    rec = Recordatorio.objects.get(cita=cita_futura, canal="email", anticipacion_horas=24)
    assert rec.estado == Recordatorio.Estado.ENVIADO


# ── API: confirmar cita triggers scheduling ───────────────────────────────────


@pytest.mark.django_db(transaction=True)
def test_confirmar_cita_schedules_reminders(client, auth_doctora, cita_futura):
    with patch("tasks.recordatorios.programar_recordatorios_cita") as mock_prog:
        resp = client.patch(
            f"/agenda/citas/{cita_futura.id}/estado/",
            json={"estado": "confirmada"},
            headers=auth_doctora,
        )
    assert resp.status_code == 200
    mock_prog.assert_called_once_with(cita_futura.id)
