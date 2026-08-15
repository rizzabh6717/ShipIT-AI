"""AI matching pipeline tests: route embedding + explainable matches."""


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _register_driver(client, email: str, name: str, capacity: float = 500):
    resp = await client.post(
        "/api/auth/register/driver",
        json={
            "name": name,
            "email": email,
            "password": "password123",
            "phone": "+919888888888",
            "vehicle_type": "van",
            "capacity_kg": capacity,
            "license_number": "DL-01-2025-000001",
            "vehicle_reg_number": "MH12AB1234",
            "current_city": "Mumbai",
        },
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    await client.patch(
        "/api/drivers/me/availability",
        headers=_auth(token),
        json={"status": "available", "current_city": "Mumbai"},
    )
    return token


async def test_route_embedding_pipeline(client, driver_token):
    resp = await client.post(
        "/api/routes",
        headers=_auth(driver_token),
        json={"origin": "Mumbai Central", "destination": "Pune Station"},
    )
    assert resp.status_code == 201, resp.text
    route = resp.json()
    assert route["has_embedding"] is True

    embed = await client.post("/api/routes/me/embed", headers=_auth(driver_token))
    assert embed.status_code == 200, embed.text
    assert embed.json()["dimensions"] == 2048


async def test_ai_match_returns_explainable_results(client, auth_token):
    await _register_driver(client, "d1@example.com", "Pune Driver", capacity=2000)
    d2 = await _register_driver(client, "d2@example.com", "Delhi Driver", capacity=50)

    # Only driver 1 is on the parcel's route (Mumbai -> Pune).
    await client.post(
        "/api/routes",
        headers=_auth(d2),
        json={"origin": "Delhi", "destination": "Chandigarh"},
    )

    parcel = await client.post(
        "/api/parcels",
        headers=_auth(auth_token),
        json={
            "pickup_location": "Mumbai Central",
            "drop_location": "Pune Station",
            "item_description": "Shipment of books",
            "weight": 10,
            "budget": 300,
        },
    )
    parcel_id = parcel.json()["public_id"]

    resp = await client.post(
        "/api/ai/match", headers=_auth(auth_token), json={"parcel_id": parcel_id}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["parcel_id"] == parcel_id
    assert len(data["matches"]) > 0
    first = data["matches"][0]
    assert first["driver_id"].startswith("D")
    assert 0 <= first["score"] <= 1
    assert first["eta"]
    joined = " ".join(first["reason"]).lower()
    assert "route overlap" in joined
    assert "capacity" in joined

    # Matches are persisted and visible afterwards.
    history = await client.get(
        f"/api/ai/matches/{parcel_id}", headers=_auth(auth_token)
    )
    assert history.status_code == 200
    assert len(history.json()["matches"]) == len(data["matches"])

    # Parcel detail exposes best_driver.
    detail = await client.get(f"/api/parcels/{parcel_id}", headers=_auth(auth_token))
    assert detail.status_code == 200
    assert detail.json()["best_driver"] is not None
    assert len(detail.json()["matches"]) == len(data["matches"])


async def test_ai_status_reports_provider(client, auth_token):
    resp = await client.get("/api/ai/status", headers=_auth(auth_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "llm_provider" in body
    assert "embedding_provider" in body
