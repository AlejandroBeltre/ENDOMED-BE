import pytest


@pytest.mark.django_db(transaction=True)
def test_login_success(client, doctora):
    resp = client.post(
        "/auth/token",
        json={"email": "doctora@test.com", "password": "testpass123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "doctora@test.com"
    assert body["user"]["role"] == "doctora"
    assert isinstance(body["sedes"], list)
    assert "refresh_token" in resp.cookies


@pytest.mark.django_db(transaction=True)
def test_login_wrong_password(client, doctora):
    resp = client.post(
        "/auth/token",
        json={"email": "doctora@test.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


@pytest.mark.django_db(transaction=True)
def test_login_unknown_email(client):
    resp = client.post(
        "/auth/token",
        json={"email": "noone@test.com", "password": "testpass123"},
    )
    assert resp.status_code == 401


@pytest.mark.django_db(transaction=True)
def test_refresh_token(client, doctora):
    # Login to get the cookie
    login_resp = client.post(
        "/auth/token",
        json={"email": "doctora@test.com", "password": "testpass123"},
    )
    assert login_resp.status_code == 200

    # Use the cookie to refresh
    resp = client.post("/auth/refresh")
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.django_db(transaction=True)
def test_refresh_without_cookie(client):
    # Fresh client — no cookie
    resp = client.post("/auth/refresh", cookies={})
    assert resp.status_code == 401


@pytest.mark.django_db(transaction=True)
def test_logout(client, doctora):
    client.post(
        "/auth/token",
        json={"email": "doctora@test.com", "password": "testpass123"},
    )
    resp = client.post("/auth/logout")
    assert resp.status_code == 204


@pytest.mark.django_db(transaction=True)
def test_protected_route_without_token(client):
    resp = client.get("/pacientes/")
    assert resp.status_code == 403  # FastAPI HTTPBearer returns 403 on missing token


@pytest.mark.django_db(transaction=True)
def test_protected_route_with_invalid_token(client):
    resp = client.get(
        "/pacientes/", headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert resp.status_code == 401
