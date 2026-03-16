import pytest


@pytest.mark.django_db(transaction=True)
def test_get_hce_creates_if_missing(client, auth_doctora, paciente):
    resp = client.get(f"/hce/{paciente.id}/", headers=auth_doctora)
    assert resp.status_code == 200
    body = resp.json()
    assert body["paciente_id"] == str(paciente.id)
    assert body["consultas"] == []


@pytest.mark.django_db(transaction=True)
def test_create_consulta(client, auth_doctora, paciente, tipo_consulta):
    resp = client.post(
        "/hce/consultas/",
        json={
            "paciente_id": str(paciente.id),
            "tipo_consulta_id": str(tipo_consulta.id),
            "fecha_hora": "2026-04-01T10:30:00",
            "motivo_consulta": "Control mensual",
            "examen_fisico": {"apariencia": "buen estado general"},
            "plan_terapeutico": "Continuar medicación",
            "signos_vitales": {
                "peso_kg": 65.5,
                "talla_cm": 162.0,
                "pa_sistolica": 120,
                "pa_diastolica": 80,
                "fc": 72,
            },
            "medicamentos": [
                {
                    "nombre": "Metformina",
                    "presentacion": "Tableta 850mg",
                    "dosis": "850mg",
                    "frecuencia": "2 veces al día",
                    "duracion": "3 meses",
                    "indicaciones": "Tomar con comida",
                }
            ],
        },
        headers=auth_doctora,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["motivo_consulta"] == "Control mensual"
    assert body["signos_vitales"]["peso_kg"] == "65.50"
    assert len(body["medicamentos"]) == 1
    assert body["medicamentos"][0]["nombre"] == "Metformina"


@pytest.mark.django_db(transaction=True)
def test_consulta_appears_in_hce(client, auth_doctora, paciente, tipo_consulta):
    client.post(
        "/hce/consultas/",
        json={
            "paciente_id": str(paciente.id),
            "tipo_consulta_id": str(tipo_consulta.id),
            "fecha_hora": "2026-04-01T10:30:00",
            "motivo_consulta": "Primera consulta",
        },
        headers=auth_doctora,
    )

    resp = client.get(f"/hce/{paciente.id}/", headers=auth_doctora)
    assert resp.status_code == 200
    assert len(resp.json()["consultas"]) == 1


@pytest.mark.django_db(transaction=True)
def test_secretaria_cannot_access_hce(client, auth_secretaria, paciente):
    resp = client.get(f"/hce/{paciente.id}/", headers=auth_secretaria)
    assert resp.status_code == 403


@pytest.mark.django_db(transaction=True)
def test_get_consulta(client, auth_doctora, paciente, tipo_consulta):
    create_resp = client.post(
        "/hce/consultas/",
        json={
            "paciente_id": str(paciente.id),
            "tipo_consulta_id": str(tipo_consulta.id),
            "fecha_hora": "2026-04-01T11:00:00",
            "motivo_consulta": "Seguimiento",
        },
        headers=auth_doctora,
    )
    consulta_id = create_resp.json()["id"]

    resp = client.get(f"/hce/consultas/{consulta_id}/", headers=auth_doctora)
    assert resp.status_code == 200
    assert resp.json()["id"] == consulta_id
