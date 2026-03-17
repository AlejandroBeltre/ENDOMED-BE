"""Integration tests for the /finanzas/ endpoints."""

import pytest
from django.utils import timezone as tz

# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def cita(transactional_db, paciente, sede, doctora, tipo_consulta):
    from apps.agenda.models import Cita

    return Cita.objects.create(
        paciente=paciente,
        sede=sede,
        profesional=doctora,
        tipo_consulta=tipo_consulta,
        fecha_hora=tz.now(),
        duracion_min=30,
    )


@pytest.fixture
def factura(transactional_db, paciente, sede, doctora, cita):
    from apps.finanzas.models import Factura
    from apps.finanzas.services import _next_numero_factura

    return Factura.objects.create(
        numero_factura=_next_numero_factura(),
        paciente=paciente,
        sede=sede,
        cita=cita,
        fecha=tz.localdate(),
        subtotal_rd="2500.00",
        descuento_rd="0.00",
        itbis_rd="0.00",
        total_rd="2500.00",
        estado=Factura.Estado.EMITIDA,
        created_by=doctora,
    )


@pytest.fixture
def inventario_item(transactional_db):
    from apps.finanzas.models import Inventario

    return Inventario.objects.create(
        nombre_producto="Suero Fisiológico 0.9%",
        categoria="suero",
        stock_actual=20,
        stock_minimo=5,
        precio_unitario_rd="150.00",
        proveedor="Distribuidora Médica SRL",
    )


def _factura_payload(paciente, sede, cita):
    return {
        "paciente_id": str(paciente.id),
        "sede_id": str(sede.id),
        "cita_id": str(cita.id),
        "fecha": str(tz.localdate()),
        "subtotal_rd": "3000.00",
        "descuento_rd": "0.00",
        "itbis_rd": "0.00",
    }


# ── caja ─────────────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
def test_get_caja_hoy(client, auth_doctora):
    resp = client.get("/finanzas/caja/", headers=auth_doctora)
    assert resp.status_code == 200
    body = resp.json()
    assert "facturas" in body
    assert "total_general" in body
    assert "total_pagado" in body


@pytest.mark.django_db(transaction=True)
def test_get_caja_hoy_secretaria(client, auth_secretaria):
    resp = client.get("/finanzas/caja/", headers=auth_secretaria)
    assert resp.status_code == 200


# ── facturas ─────────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
def test_create_factura(client, auth_doctora, paciente, sede, cita):
    resp = client.post(
        "/finanzas/facturas/",
        json=_factura_payload(paciente, sede, cita),
        headers=auth_doctora,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["estado"] == "borrador"
    assert body["total_rd"] == "3000.00"
    assert body["paciente"]["id"] == str(paciente.id)


@pytest.mark.django_db(transaction=True)
def test_create_factura_secretaria(client, auth_secretaria, paciente, sede, cita):
    resp = client.post(
        "/finanzas/facturas/",
        json=_factura_payload(paciente, sede, cita),
        headers=auth_secretaria,
    )
    assert resp.status_code == 201


@pytest.mark.django_db(transaction=True)
def test_create_factura_computes_total(client, auth_doctora, paciente, sede, cita):
    payload = {
        "paciente_id": str(paciente.id),
        "sede_id": str(sede.id),
        "fecha": str(tz.localdate()),
        "subtotal_rd": "3000.00",
        "descuento_rd": "300.00",
        "itbis_rd": "252.00",
    }
    resp = client.post("/finanzas/facturas/", json=payload, headers=auth_doctora)
    assert resp.status_code == 201
    # total = 3000 - 300 + 252 = 2952
    assert resp.json()["total_rd"] == "2952.00"


@pytest.mark.django_db(transaction=True)
def test_list_facturas(client, auth_doctora, factura):
    resp = client.get("/finanzas/facturas/", headers=auth_doctora)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


@pytest.mark.django_db(transaction=True)
def test_get_factura_detail(client, auth_doctora, factura):
    resp = client.get(f"/finanzas/facturas/{factura.id}/", headers=auth_doctora)
    assert resp.status_code == 200
    assert resp.json()["id"] == str(factura.id)


@pytest.mark.django_db(transaction=True)
def test_update_factura_estado(client, auth_doctora, factura):
    resp = client.patch(
        f"/finanzas/facturas/{factura.id}/estado/",
        json={"estado": "pagada"},
        headers=auth_doctora,
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "pagada"


@pytest.mark.django_db(transaction=True)
def test_update_factura_estado_invalido(client, auth_doctora, factura):
    resp = client.patch(
        f"/finanzas/facturas/{factura.id}/estado/",
        json={"estado": "inventado"},
        headers=auth_doctora,
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_update_factura_estado_requires_doctora(client, auth_secretaria, factura):
    resp = client.patch(
        f"/finanzas/facturas/{factura.id}/estado/",
        json={"estado": "pagada"},
        headers=auth_secretaria,
    )
    assert resp.status_code == 403


@pytest.mark.django_db(transaction=True)
def test_get_factura_otro_sede_forbidden(client, auth_doctora, transactional_db):
    from apps.authentication.models import Sede, User, UserSede
    from apps.finanzas.models import Factura
    from apps.pacientes.models import Paciente

    otra_sede = Sede.objects.create(nombre="Otra Sede", ciudad="Otra Ciudad")
    otra_doctora = User.objects.create_user(
        email="otra@test.com",
        password="pass123",
        nombre="Otra",
        apellido="Doctora",
        role=User.Role.DOCTORA,
        is_active=True,
    )
    UserSede.objects.create(user=otra_doctora, sede=otra_sede, is_primary=True)
    paciente_otro = Paciente.objects.create(
        cedula="001-9999999-9",
        nombre="Otro",
        apellido="Paciente",
        fecha_nacimiento="1990-01-01",
        sexo="M",
        telefono_whatsapp="8090000000",
        sede=otra_sede,
    )
    from apps.finanzas.services import _next_numero_factura

    factura_otro = Factura.objects.create(
        numero_factura=_next_numero_factura(),
        paciente=paciente_otro,
        sede=otra_sede,
        fecha=tz.localdate(),
        subtotal_rd="1000.00",
        descuento_rd="0.00",
        itbis_rd="0.00",
        total_rd="1000.00",
        created_by=otra_doctora,
    )
    resp = client.get(f"/finanzas/facturas/{factura_otro.id}/", headers=auth_doctora)
    assert resp.status_code == 404


# ── pagos ─────────────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
def test_create_pago(client, auth_doctora, factura):
    resp = client.post(
        "/finanzas/pagos/",
        json={
            "factura_id": str(factura.id),
            "monto_rd": "2500.00",
            "metodo": "efectivo",
            "fecha_pago": str(tz.localdate()),
        },
        headers=auth_doctora,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["metodo"] == "efectivo"
    assert body["monto_rd"] == "2500.00"


@pytest.mark.django_db(transaction=True)
def test_create_pago_auto_marca_pagada(client, auth_doctora, factura):
    """Paying full amount should auto-transition factura to pagada."""
    resp = client.post(
        "/finanzas/pagos/",
        json={
            "factura_id": str(factura.id),
            "monto_rd": str(factura.total_rd),
            "metodo": "tarjeta",
            "fecha_pago": str(tz.localdate()),
        },
        headers=auth_doctora,
    )
    assert resp.status_code == 201

    factura.refresh_from_db()
    assert factura.estado == "pagada"


@pytest.mark.django_db(transaction=True)
def test_create_pago_secretaria(client, auth_secretaria, factura):
    resp = client.post(
        "/finanzas/pagos/",
        json={
            "factura_id": str(factura.id),
            "monto_rd": "500.00",
            "metodo": "transferencia",
            "fecha_pago": str(tz.localdate()),
        },
        headers=auth_secretaria,
    )
    assert resp.status_code == 201


# ── inventario ────────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
def test_list_inventario_doctora(client, auth_doctora, inventario_item):
    resp = client.get("/finanzas/inventario/", headers=auth_doctora)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


@pytest.mark.django_db(transaction=True)
def test_list_inventario_secretaria_forbidden(client, auth_secretaria):
    resp = client.get("/finanzas/inventario/", headers=auth_secretaria)
    assert resp.status_code == 403


@pytest.mark.django_db(transaction=True)
def test_create_inventario(client, auth_doctora):
    resp = client.post(
        "/finanzas/inventario/",
        json={
            "nombre_producto": "Vitamina D3 2000 UI",
            "categoria": "suplemento",
            "stock_actual": 50,
            "stock_minimo": 10,
            "precio_unitario_rd": "350.00",
            "proveedor": "NutriMed SRL",
        },
        headers=auth_doctora,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["nombre_producto"] == "Vitamina D3 2000 UI"
    assert body["stock_actual"] == 50


@pytest.mark.django_db(transaction=True)
def test_update_inventario(client, auth_doctora, inventario_item):
    resp = client.patch(
        f"/finanzas/inventario/{inventario_item.id}/",
        json={"stock_minimo": 10, "precio_unitario_rd": "175.00"},
        headers=auth_doctora,
    )
    assert resp.status_code == 200
    assert resp.json()["stock_minimo"] == 10


@pytest.mark.django_db(transaction=True)
def test_movimiento_entrada(client, auth_doctora, inventario_item):
    stock_inicial = inventario_item.stock_actual
    resp = client.post(
        f"/finanzas/inventario/{inventario_item.id}/movimiento/",
        json={"tipo": "entrada", "cantidad": 10, "motivo": "Compra mensual"},
        headers=auth_doctora,
    )
    assert resp.status_code == 201
    assert resp.json()["tipo"] == "entrada"

    inventario_item.refresh_from_db()
    assert inventario_item.stock_actual == stock_inicial + 10


@pytest.mark.django_db(transaction=True)
def test_movimiento_salida(client, auth_doctora, inventario_item):
    stock_inicial = inventario_item.stock_actual
    resp = client.post(
        f"/finanzas/inventario/{inventario_item.id}/movimiento/",
        json={"tipo": "salida", "cantidad": 5, "motivo": "Uso en consulta"},
        headers=auth_doctora,
    )
    assert resp.status_code == 201
    inventario_item.refresh_from_db()
    assert inventario_item.stock_actual == stock_inicial - 5


@pytest.mark.django_db(transaction=True)
def test_movimiento_salida_sin_stock(client, auth_doctora, inventario_item):
    resp = client.post(
        f"/finanzas/inventario/{inventario_item.id}/movimiento/",
        json={"tipo": "salida", "cantidad": 9999, "motivo": "Test"},
        headers=auth_doctora,
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_movimiento_ajuste(client, auth_doctora, inventario_item):
    resp = client.post(
        f"/finanzas/inventario/{inventario_item.id}/movimiento/",
        json={"tipo": "ajuste", "cantidad": 100, "motivo": "Inventario físico"},
        headers=auth_doctora,
    )
    assert resp.status_code == 201
    inventario_item.refresh_from_db()
    assert inventario_item.stock_actual == 100


# ── reportes ──────────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
def test_get_reportes_doctora(client, auth_doctora):
    resp = client.get("/finanzas/reportes/", headers=auth_doctora)
    assert resp.status_code == 200
    body = resp.json()
    assert "total_general" in body
    assert "por_sede" in body
    assert "por_tipo_consulta" in body
    assert "por_estado" in body


@pytest.mark.django_db(transaction=True)
def test_get_reportes_secretaria_forbidden(client, auth_secretaria):
    resp = client.get("/finanzas/reportes/", headers=auth_secretaria)
    assert resp.status_code == 403


@pytest.mark.django_db(transaction=True)
def test_get_reportes_con_datos(client, auth_doctora, factura):
    resp = client.get(
        f"/finanzas/reportes/?fecha_desde={tz.localdate()}&fecha_hasta={tz.localdate()}",
        headers=auth_doctora,
    )
    assert resp.status_code == 200
    body = resp.json()
    # Should include the fixture factura
    assert float(body["total_general"]) >= float(factura.total_rd)
