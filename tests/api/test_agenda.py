import pytest


def _cita_payload(paciente, sede, doctora, tipo_consulta):
    return {
        "paciente_id": str(paciente.id),
        "sede_id": str(sede.id),
        "profesional_id": str(doctora.id),
        "tipo_consulta_id": str(tipo_consulta.id),
        "fecha_hora": "2026-04-01T10:00:00",
        "duracion_min": 30,
        "modalidad": "presencial",
    }


@pytest.mark.django_db(transaction=True)
def test_create_cita(client, auth_doctora, paciente, sede, doctora, tipo_consulta):
    resp = client.post(
        "/agenda/citas/",
        json=_cita_payload(paciente, sede, doctora, tipo_consulta),
        headers=auth_doctora,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["estado"] == "pendiente"
    assert body["paciente"]["id"] == str(paciente.id)


@pytest.mark.django_db(transaction=True)
def test_get_cita(client, auth_doctora, paciente, sede, doctora, tipo_consulta):
    create_resp = client.post(
        "/agenda/citas/",
        json=_cita_payload(paciente, sede, doctora, tipo_consulta),
        headers=auth_doctora,
    )
    cita_id = create_resp.json()["id"]

    resp = client.get(f"/agenda/citas/{cita_id}/", headers=auth_doctora)
    assert resp.status_code == 200
    assert resp.json()["id"] == cita_id


@pytest.mark.django_db(transaction=True)
def test_update_cita_estado(
    client, auth_doctora, paciente, sede, doctora, tipo_consulta
):
    create_resp = client.post(
        "/agenda/citas/",
        json=_cita_payload(paciente, sede, doctora, tipo_consulta),
        headers=auth_doctora,
    )
    cita_id = create_resp.json()["id"]

    resp = client.patch(
        f"/agenda/citas/{cita_id}/estado/",
        json={"estado": "confirmada"},
        headers=auth_doctora,
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "confirmada"


@pytest.mark.django_db(transaction=True)
def test_update_cita_estado_invalido(
    client, auth_doctora, paciente, sede, doctora, tipo_consulta
):
    create_resp = client.post(
        "/agenda/citas/",
        json=_cita_payload(paciente, sede, doctora, tipo_consulta),
        headers=auth_doctora,
    )
    cita_id = create_resp.json()["id"]

    resp = client.patch(
        f"/agenda/citas/{cita_id}/estado/",
        json={"estado": "inventado"},
        headers=auth_doctora,
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_list_citas_hoy(client, auth_doctora):
    resp = client.get("/agenda/hoy/", headers=auth_doctora)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.django_db(transaction=True)
def test_secretaria_can_create_cita(
    client, auth_secretaria, paciente, sede, doctora, tipo_consulta
):
    resp = client.post(
        "/agenda/citas/",
        json=_cita_payload(paciente, sede, doctora, tipo_consulta),
        headers=auth_secretaria,
    )
    assert resp.status_code == 201
