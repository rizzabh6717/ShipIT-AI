"""Tests for driver reliability, feedback, proof-of-delivery, and budget recs."""

from datetime import datetime, timedelta, timezone


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_parcel(client, token, **overrides):
    payload = {
        "pickup_location": "Mumbai Central",
        "drop_location": "Pune",
        "item_description": "Glassware",
        "weight": 8.0,
        "budget": 400.0,
        "deadline": (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat(),
        "dimensions": {"length": 30, "width": 20, "height": 15},
        **overrides,
    }
    resp = await client.post("/api/parcels", json=payload, headers=_auth(token))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_request(client, sender_token, driver_token):
    parcel = await _create_parcel(client, sender_token)
    resp = await client.get("/api/drivers/me", headers=_auth(driver_token))
    driver = resp.json()
    resp = await client.post(
        "/api/deliveries/request",
        json={"parcel_id": parcel["public_id"], "driver_id": driver["public_id"]},
        headers=_auth(sender_token),
    )
    assert resp.status_code == 200, resp.text
    return parcel, resp.json()["request"]


async def _accept_and_deliver(client, driver_token, request_id):
    resp = await client.post(
        f"/api/deliveries/requests/{request_id}/respond",
        json={"accept": True},
        headers=_auth(driver_token),
    )
    assert resp.status_code == 200, resp.text
    resp = await client.post(
        f"/api/deliveries/requests/{request_id}/pickup",
        headers=_auth(driver_token),
    )
    assert resp.status_code == 200, resp.text
    resp = await client.post(
        f"/api/deliveries/requests/{request_id}/delivered",
        json={"proof_image_url": "/uploads/proofs/demo.jpg"},
        headers=_auth(driver_token),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["request"]


async def test_driver_registration_stores_document_fields(client):
    resp = await client.post(
        "/api/auth/register/driver",
        json={
            "name": "Reg Driver",
            "email": "reg@example.com",
            "password": "password123",
            "phone": "+919888888888",
            "vehicle_type": "van",
            "capacity_kg": 500,
            "license_number": "MH-1234",
            "vehicle_reg_number": "MH12AB1234",
            "current_city": "Mumbai",
        },
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    profile = await client.get("/api/drivers/me", headers=_auth(token))
    assert profile.status_code == 200
    body = profile.json()
    assert body["phone"] == "+919888888888"
    assert body["license_number"] == "MH-1234"
    assert body["vehicle_reg_number"] == "MH12AB1234"


async def test_driver_registration_rejects_missing_documents(client):
    resp = await client.post(
        "/api/auth/register/driver",
        json={
            "name": "No Doc",
            "email": "nodoc@example.com",
            "password": "password123",
            "vehicle_type": "car",
            "capacity_kg": 300,
        },
    )
    assert resp.status_code == 422


async def test_proof_attached_on_delivery(client, auth_token, driver_token):
    parcel, request = await _create_request(client, auth_token, driver_token)
    delivered = await _accept_and_deliver(client, driver_token, request["public_id"])
    assert delivered["status"] == "delivered"
    assert delivered["proof_image_url"] == "/uploads/proofs/demo.jpg"


async def test_delivery_without_proof_rejected(client, auth_token, driver_token):
    parcel, request = await _create_request(client, auth_token, driver_token)
    await client.post(
        f"/api/deliveries/requests/{request['public_id']}/respond",
        json={"accept": True},
        headers=_auth(driver_token),
    )
    resp = await client.post(
        f"/api/deliveries/requests/{request['public_id']}/delivered",
        headers=_auth(driver_token),
    )
    assert resp.status_code == 422, resp.text
    resp = await client.post(
        f"/api/deliveries/requests/{request['public_id']}/delivered",
        json={"proof_image_url": ""},
        headers=_auth(driver_token),
    )
    assert resp.status_code == 422, resp.text


async def test_feedback_submission_updates_driver_rating(client, auth_token, driver_token):
    parcel, request = await _create_request(client, auth_token, driver_token)
    delivered = await _accept_and_deliver(client, driver_token, request["public_id"])

    resp = await client.post(
        f"/api/deliveries/requests/{request['public_id']}/feedback",
        json={"rating": 4, "comment": "Great service"},
        headers=_auth(auth_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["feedback"]["rating"] == 4
    assert body["feedback"]["comment"] == "Great service"

    driver_profile = await client.get("/api/drivers/me", headers=_auth(driver_token))
    assert driver_profile.status_code == 200
    dbody = driver_profile.json()
    assert dbody["reviews_count"] == 1
    assert dbody["rating"] == 4.0


async def test_feedback_duplicate_rejected(client, auth_token, driver_token):
    parcel, request = await _create_request(client, auth_token, driver_token)
    await _accept_and_deliver(client, driver_token, request["public_id"])
    payload = {"rating": 5, "comment": "First"}
    resp = await client.post(
        f"/api/deliveries/requests/{request['public_id']}/feedback",
        json=payload,
        headers=_auth(auth_token),
    )
    assert resp.status_code == 200, resp.text
    resp = await client.post(
        f"/api/deliveries/requests/{request['public_id']}/feedback",
        json=payload,
        headers=_auth(auth_token),
    )
    assert resp.status_code == 409


async def test_feedback_requires_delivered(client, auth_token, driver_token):
    parcel, request = await _create_request(client, auth_token, driver_token)
    resp = await client.post(
        f"/api/deliveries/requests/{request['public_id']}/feedback",
        json={"rating": 5},
        headers=_auth(auth_token),
    )
    assert resp.status_code == 409


async def test_driver_stats_reflect_real_data(client, auth_token, driver_token):
    parcel, request = await _create_request(client, auth_token, driver_token)
    await _accept_and_deliver(client, driver_token, request["public_id"])

    resp = await client.get("/api/drivers/me/stats", headers=_auth(driver_token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["completed_deliveries"] == 1
    assert body["total_deliveries"] == 1
    assert body["on_time_rate"] == 1.0
    assert body["completion_rate"] == 1.0


async def test_budget_recommendation(client, auth_token):
    resp = await client.post(
        "/api/ai/budget-recommend",
        json={
            "pickup_location": "Mumbai Central",
            "drop_location": "Pune",
            "weight": 8.0,
            "dimensions": {"length": 30, "width": 20, "height": 15},
        },
        headers=_auth(auth_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["currency"] == "INR"
    assert body["base_rate"] == 40.0
    # Weight 8kg => 5-10kg tier ₹20; longest dim 30cm => medium ₹20.
    assert body["weight_charge"] == 20.0
    assert body["size_tier"] == "medium"
    assert body["size_charge"] == 20.0
    # Recommended = 40 + distance + 20 + 20 (rounded to nearest 10).
    assert body["recommended_budget"] > 0
    assert body["total_amount"] == round(body["recommended_budget"] * 0.9, 2)
    assert body["platform_discount_pct"] == 10.0


async def test_budget_weight_tiers(client, auth_token):
    for weight, expected in [(3.0, 0.0), (7.0, 20.0), (15.0, 50.0), (40.0, 80.0)]:
        resp = await client.post(
            "/api/ai/budget-recommend",
            json={
                "pickup_location": "Mumbai",
                "drop_location": "Pune",
                "weight": weight,
            },
            headers=_auth(auth_token),
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["weight_charge"] == expected


async def test_driver_reliability_persisted_after_delivery(client, auth_token, driver_token):
    parcel, request = await _create_request(client, auth_token, driver_token)
    await _accept_and_deliver(client, driver_token, request["public_id"])

    profile = await client.get("/api/drivers/me", headers=_auth(driver_token))
    assert profile.status_code == 200
    dbody = profile.json()
    assert dbody["completed_deliveries"] == 1
    # On-time (delivered before the 48h deadline) and completion rates persist.
    assert dbody["on_time_rate"] == 1.0
    assert dbody["completion_rate"] == 1.0


def test_pickup_detour_zero_when_on_route():
    from types import SimpleNamespace

    from app.utils.geo import estimate_pickup_detour_km

    route = SimpleNamespace(origin="Delhi", destination="Noida", waypoints=[])
    on_route = SimpleNamespace(pickup_location="Delhi", waypoints=[])
    off_route = SimpleNamespace(pickup_location="Chandigarh", waypoints=[])
    assert estimate_pickup_detour_km(on_route, route) == 0.0
    assert estimate_pickup_detour_km(off_route, route) > 0.0


def test_deterministic_reliability_model():
    from types import SimpleNamespace

    from app.ai.explainer import breakdown

    parcel = SimpleNamespace(deadline=None, weight=2.0)
    low = SimpleNamespace(capacity_kg=100, rating=1.0, on_time_rate=0.5, completion_rate=0.6)
    high = SimpleNamespace(capacity_kg=100, rating=5.0, on_time_rate=1.0, completion_rate=1.0)

    bd_low = breakdown(parcel, low, None, route_overlap=1.0, pickup_detour_km=0.0)
    bd_high = breakdown(parcel, high, None, route_overlap=1.0, pickup_detour_km=0.0)

    # reliability = 0.5 * (rating/5) + 0.3 * on_time_rate + 0.2 * completion_rate
    expected_low = 0.5 * (1.0 / 5.0) + 0.3 * 0.5 + 0.2 * 0.6
    assert abs(bd_low.reliability_score - expected_low) < 1e-9
    assert bd_low.reliability_score < bd_high.reliability_score
    assert bd_low.total < bd_high.total


def test_detour_value_matches_ai_score():
    from types import SimpleNamespace

    from app.ai.explainer import breakdown
    from app.utils.geo import estimate_pickup_detour_km

    route = SimpleNamespace(origin="Gurgaon", destination="Delhi", waypoints=[])
    parcel = SimpleNamespace(
        pickup_location="Faridabad", drop_location="Delhi", deadline=None, weight=3.0
    )
    detour = estimate_pickup_detour_km(parcel, route)
    driver = SimpleNamespace(capacity_kg=200, rating=4.5, on_time_rate=0.9, completion_rate=0.9)
    bd = breakdown(parcel, driver, None, route_overlap=0.5, pickup_detour_km=detour)
    # The detour fed into the score equals the detour the API surfaces.
    assert bd.pickup_detour_km == detour
    assert bd.pickup_proximity == max(0.0, 1.0 - detour / 10.0)