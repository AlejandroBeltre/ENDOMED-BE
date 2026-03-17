"""Integration tests for the /analitica/ endpoints."""

import pytest
from django.utils import timezone as tz

# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def cita_completada(transactional_db, paciente, sede, doctora, tipo_consulta):
    from apps.agenda.models import Cita

    return Cita.objects.create(
        paciente=paciente,
        sede=sede,
        profesional=doctora,
        tipo_consulta=tipo_consulta,
        fecha_hora=tz.now(),
        duracion_min=30,
        estado=Cita.Estado.COMPLETADA,
    )


@pytest.fixture
def consulta(transactional_db, cita_completada, paciente, doctora, tipo_consulta):
    from apps.hce.models import Consulta, HistoriaClinica

    hce = HistoriaClinica.objects.create(paciente=paciente)
    return Consulta.objects.create(
        hce=hce,
        cita=cita_completada,
        tipo_consulta=tipo_consulta,
        fecha_hora=tz.now(),
        motivo_consulta="Control endocrinológico",
        created_by=doctora,
    )


@pytest.fixture
def diagnostico(transactional_db, consulta):
    from apps.hce.models import DiagnosticoConsulta

    return DiagnosticoConsulta.objects.create(
        consulta=consulta,
        codigo_cie10="E11",
        descripcion="Diabetes mellitus tipo 2",
        tipo="principal",
    )


@pytest.fixture
def factura_pagada(transactional_db, paciente, sede, doctora, cita_completada):
    from apps.finanzas.models import Factura
    from apps.finanzas.services import _next_numero_factura

    return Factura.objects.create(
        numero_factura=_next_numero_factura(),
        paciente=paciente,
        sede=sede,
        cita=cita_completada,
        fecha=tz.localdate(),
        subtotal_rd="2500.00",
        descuento_rd="0.00",
        itbis_rd="0.00",
        total_rd="2500.00",
        estado="pagada",
        created_by=doctora,
    )


# ── resumen ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
def test_resumen_kpis(client, auth_doctora):
    resp = client.get("/analitica/resumen/", headers=auth_doctora)
    assert resp.status_code == 200
    body = resp.json()
    assert "total_pacientes" in body
    assert "consultas_este_mes" in body
    assert "ingresos_este_mes" in body
    assert "citas_hoy" in body


@pytest.mark.django_db(transaction=True)
def test_resumen_secretaria_forbidden(client, auth_secretaria):
    resp = client.get("/analitica/resumen/", headers=auth_secretaria)
    assert resp.status_code == 403


@pytest.mark.django_db(transaction=True)
def test_resumen_counts_data(client, auth_doctora, paciente, cita_completada):
    resp = client.get("/analitica/resumen/", headers=auth_doctora)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_pacientes"] >= 1


# ── diagnósticos ──────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
def test_diagnosticos_empty(client, auth_doctora):
    resp = client.get("/analitica/diagnosticos/", headers=auth_doctora)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.django_db(transaction=True)
def test_diagnosticos_con_datos(client, auth_doctora, diagnostico):
    resp = client.get("/analitica/diagnosticos/", headers=auth_doctora)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) >= 1
    assert body[0]["codigo_cie10"] == "E11"
    assert body[0]["frecuencia"] == 1


@pytest.mark.django_db(transaction=True)
def test_diagnosticos_con_filtro_meses(client, auth_doctora, diagnostico):
    resp = client.get("/analitica/diagnosticos/?meses=3", headers=auth_doctora)
    assert resp.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_diagnosticos_secretaria_forbidden(client, auth_secretaria):
    resp = client.get("/analitica/diagnosticos/", headers=auth_secretaria)
    assert resp.status_code == 403


# ── demografía ────────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
def test_demografia(client, auth_doctora, paciente):
    resp = client.get("/analitica/demografia/", headers=auth_doctora)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 5  # 5 age groups
    grupos = [g["grupo_etario"] for g in body]
    assert "0-17" in grupos
    assert "60+" in grupos


@pytest.mark.django_db(transaction=True)
def test_demografia_secretaria_forbidden(client, auth_secretaria):
    resp = client.get("/analitica/demografia/", headers=auth_secretaria)
    assert resp.status_code == 403


# ── prevalencia ───────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
def test_prevalencia_empty(client, auth_doctora):
    resp = client.get("/analitica/prevalencia/", headers=auth_doctora)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.django_db(transaction=True)
def test_prevalencia_con_datos(client, auth_doctora, diagnostico):
    resp = client.get("/analitica/prevalencia/?meses=12", headers=auth_doctora)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) >= 1
    assert body[0]["codigo_cie10"] == "E11"
    assert "mes" in body[0]


@pytest.mark.django_db(transaction=True)
def test_prevalencia_filtro_patologia(client, auth_doctora, diagnostico):
    resp = client.get("/analitica/prevalencia/?patologia=E11", headers=auth_doctora)
    assert resp.status_code == 200
    body = resp.json()
    assert all(r["codigo_cie10"].startswith("E11") for r in body)


# ── rendimiento ───────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
def test_rendimiento(client, auth_doctora, cita_completada):
    resp = client.get("/analitica/rendimiento/", headers=auth_doctora)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert "tipo_consulta" in body[0]
    assert "volumen" in body[0]
    assert "ingresos" in body[0]


@pytest.mark.django_db(transaction=True)
def test_rendimiento_secretaria_forbidden(client, auth_secretaria):
    resp = client.get("/analitica/rendimiento/", headers=auth_secretaria)
    assert resp.status_code == 403


# ── exportar CSV ──────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
def test_exportar_diagnosticos_csv(client, auth_doctora, diagnostico):
    resp = client.get("/analitica/exportar/?tipo=diagnosticos", headers=auth_doctora)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")


@pytest.mark.django_db(transaction=True)
def test_exportar_demografia_csv(client, auth_doctora, paciente):
    resp = client.get("/analitica/exportar/?tipo=demografia", headers=auth_doctora)
    assert resp.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_exportar_rendimiento_csv(client, auth_doctora, cita_completada):
    resp = client.get("/analitica/exportar/?tipo=rendimiento", headers=auth_doctora)
    assert resp.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_exportar_tipo_invalido(client, auth_doctora):
    resp = client.get("/analitica/exportar/?tipo=inventado", headers=auth_doctora)
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_exportar_secretaria_forbidden(client, auth_secretaria):
    resp = client.get("/analitica/exportar/?tipo=diagnosticos", headers=auth_secretaria)
    assert resp.status_code == 403
