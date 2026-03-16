"""Shared pytest fixtures.

We use transactional_db (not db) in all fixtures because the FastAPI TestClient
runs route handlers in a worker thread — those threads open separate DB connections
and cannot see uncommitted transactions from the test's connection.
transactional_db commits data so all threads can see it; pytest-django flushes
the DB after each test.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ── Database fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def sede(transactional_db):
    from apps.authentication.models import Sede

    return Sede.objects.create(nombre="Test Sede", ciudad="Test Ciudad")


@pytest.fixture
def doctora(transactional_db, sede):
    from apps.authentication.models import User, UserSede

    user = User.objects.create_user(
        email="doctora@test.com",
        password="testpass123",
        nombre="Test",
        apellido="Doctora",
        role=User.Role.DOCTORA,
        is_active=True,
    )
    UserSede.objects.create(user=user, sede=sede, is_primary=True)
    return user


@pytest.fixture
def secretaria(transactional_db, sede):
    from apps.authentication.models import User, UserSede

    user = User.objects.create_user(
        email="secretaria@test.com",
        password="testpass123",
        nombre="Test",
        apellido="Secretaria",
        role=User.Role.SECRETARIA,
        is_active=True,
    )
    UserSede.objects.create(user=user, sede=sede, is_primary=True)
    return user


@pytest.fixture
def tipo_consulta(transactional_db):
    from apps.agenda.models import TipoConsulta

    return TipoConsulta.objects.create(
        nombre="Endocrinología Test",
        duracion_min=30,
        tarifa_rd="2500.00",
        color_hex="#00B0B9",
    )


@pytest.fixture
def paciente(transactional_db, sede):
    from apps.pacientes.models import Paciente

    return Paciente.objects.create(
        cedula="001-1234567-8",
        nombre="María",
        apellido="García",
        fecha_nacimiento="1985-03-15",
        sexo="F",
        telefono_whatsapp="8091234567",
        sede=sede,
    )


# ── Auth helpers ─────────────────────────────────────────────────────────────


@pytest.fixture
def doctora_token(client, doctora):
    resp = client.post(
        "/auth/token",
        json={"email": "doctora@test.com", "password": "testpass123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def secretaria_token(client, secretaria):
    resp = client.post(
        "/auth/token",
        json={"email": "secretaria@test.com", "password": "testpass123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def auth_doctora(doctora_token):
    return {"Authorization": f"Bearer {doctora_token}"}


@pytest.fixture
def auth_secretaria(secretaria_token):
    return {"Authorization": f"Bearer {secretaria_token}"}
