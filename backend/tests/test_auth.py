"""Authentication flow tests."""


async def test_register_sender(client):
    resp = await client.post(
        "/api/auth/register/sender",
        json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "password123",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["user"]["role"] == "sender"
    assert data["user"]["email"] == "alice@example.com"
    assert data["access_token"]


async def test_register_driver_creates_profile(client):
    resp = await client.post(
        "/api/auth/register/driver",
        json={
            "name": "Bob",
            "email": "bob@example.com",
            "password": "password123",
            "vehicle_type": "truck",
            "capacity_kg": 2000,
            "phone": "+919888888888",
            "license_number": "MH01-2026-1234",
            "vehicle_reg_number": "MH12AB1234",
            "current_city": "Pune",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["role"] == "driver"

    headers = {"Authorization": f"Bearer {data['access_token']}"}
    profile = await client.get("/api/drivers/me", headers=headers)
    assert profile.status_code == 200
    body = profile.json()
    assert body["vehicle_type"] == "truck"
    assert body["capacity_kg"] == 2000
    assert body["name"] == "Bob"


async def test_register_driver_invalid_vehicle_type(client):
    resp = await client.post(
        "/api/auth/register/driver",
        json={
            "name": "Carol",
            "email": "carol@example.com",
            "password": "password123",
            "vehicle_type": "hovercraft",
            "capacity_kg": 500,
        },
    )
    assert resp.status_code == 422


async def test_login_success(client, auth_token):
    resp = await client.post(
        "/api/auth/login",
        json={"email": "sender@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["email"] == "sender@example.com"


async def test_login_wrong_password(client, auth_token):
    resp = await client.post(
        "/api/auth/login",
        json={"email": "sender@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401


async def test_duplicate_email_conflict(client, auth_token):
    resp = await client.post(
        "/api/auth/register/sender",
        json={
            "name": "Duplicate",
            "email": "sender@example.com",
            "password": "password123",
        },
    )
    assert resp.status_code == 409


async def test_me(client, auth_token):
    resp = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "sender@example.com"


async def test_me_without_token(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_user_exists_check(client, auth_token):
    resp = await client.get("/api/auth/user/sender@example.com")
    assert resp.status_code == 200
    data = resp.json()
    assert data["userExists"] is True
    assert data["role"] == "sender"

    resp = await client.get("/api/auth/user/U-UNKNOWN")
    assert resp.json()["userExists"] is False
