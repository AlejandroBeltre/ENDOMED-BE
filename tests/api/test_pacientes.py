import pytest


@pytest.mark.django_db(transaction=True)
def test_list_pacientes_empty(client, auth_doctora):
    resp = client.get("/pacientes/", headers=auth_doctora)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.django_db(transaction=True)
def test_create_paciente(client, auth_doctora, sede):
    resp = client.post(
        "/pacientes/",
        json={
            "cedula": "001-9999999-0",
            "nombre": "Ana",
            "apellido": "Pérez",
            "fecha_nacimiento": "1990-06-01",
            "sexo": "F",
            "telefono_whatsapp": "8090000001",
            "sede_id": str(sede.id),
        },
        headers=auth_doctora,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["cedula"] == "001-9999999-0"
    assert body["nombre"] == "Ana"


@pytest.mark.django_db(transaction=True)
def test_create_paciente_duplicate_cedula(client, auth_doctora, paciente, sede):
    resp = client.post(
        "/pacientes/",
        json={
            "cedula": paciente.cedula,
            "nombre": "Otro",
            "apellido": "Nombre",
            "fecha_nacimiento": "1990-01-01",
            "sexo": "M",
            "telefono_whatsapp": "8090000002",
            "sede_id": str(sede.id),
        },
        headers=auth_doctora,
    )
    assert resp.status_code == 409


@pytest.mark.django_db(transaction=True)
def test_get_paciente(client, auth_doctora, paciente):
    resp = client.get(f"/pacientes/{paciente.id}/", headers=auth_doctora)
    assert resp.status_code == 200
    assert resp.json()["id"] == str(paciente.id)


@pytest.mark.django_db(transaction=True)
def test_search_pacientes(client, auth_doctora, paciente):
    resp = client.get(f"/pacientes/?q={paciente.apellido}", headers=auth_doctora)
    assert resp.status_code == 200
    results = resp.json()
    assert any(p["id"] == str(paciente.id) for p in results)


@pytest.mark.django_db(transaction=True)
def test_paciente_not_accessible_by_other_sede(client, auth_doctora):
    from apps.authentication.models import Sede
    from apps.pacientes.models import Paciente

    # Create a sede the doctora does NOT belong to
    other_sede = Sede.objects.create(nombre="Other Sede", ciudad="Other")
    p = Paciente.objects.create(
        cedula="002-0000000-1",
        nombre="Otro",
        apellido="Paciente",
        fecha_nacimiento="2000-01-01",
        sexo="M",
        telefono_whatsapp="8090000003",
        sede=other_sede,
    )
    resp = client.get(f"/pacientes/{p.id}/", headers=auth_doctora)
    assert resp.status_code == 404
