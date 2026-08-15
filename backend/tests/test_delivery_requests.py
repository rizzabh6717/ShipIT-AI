"""Delivery request (sender-initiated) workflow tests."""


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_parcel(client, token: str) -> str:
    resp = await client.post(
        "/api/parcels",
        headers=_auth(token),
        json={
            "pickup_location": "Mumbai",
            "drop_location": "Pune",
            "item_description": "Documents",
            "weight": 2,
        },
    )
    assert resp.status_code == 201
    return resp.json()["public_id"]


async def test_sender_requests_driver_and_driver_accepts(client, auth_token, driver_token):
    # Driver creates an active route so they are a valid match target.
    route = await client.post(
        "/api/routes",
        headers=_auth(driver_token),
        json={"origin": "Mumbai", "destination": "Pune"},
    )
    assert route.status_code == 201

    # Driver profile public id (not the user public id).
    driver = await client.get("/api/drivers/me", headers=_auth(driver_token))
    assert driver.status_code == 200
    driver_pub = driver.json()["public_id"]

    parcel_id = await _create_parcel(client, auth_token)

    # Sender creates a delivery request.
    created = await client.post(
        "/api/deliveries/request",
        headers=_auth(auth_token),
        json={
            "parcel_id": parcel_id,
            "driver_id": driver_pub,
            "route_id": str(route.json()["id"]),
        },
    )
    assert created.status_code == 200, created.text
    req = created.json()["request"]
    assert req["status"] == "pending_driver_approval"
    request_id = req["public_id"]

    # Parcel parked awaiting driver approval.
    detail = await client.get(f"/api/parcels/{parcel_id}", headers=_auth(auth_token))
    assert detail.json()["status"] == "pending_driver_approval"

    # Duplicate request is blocked.
    dup = await client.post(
        "/api/deliveries/request",
        headers=_auth(auth_token),
        json={"parcel_id": parcel_id, "driver_id": driver_pub},
    )
    assert dup.status_code == 409

    # Sender cannot respond to the request.
    forbidden = await client.post(
        f"/api/deliveries/requests/{request_id}/respond",
        headers=_auth(auth_token),
        json={"accept": True},
    )
    assert forbidden.status_code == 403

    # Driver sees the pending request.
    pending = await client.get(
        "/api/deliveries/requests/me?scope=pending", headers=_auth(driver_token)
    )
    assert pending.status_code == 200
    assert any(r["public_id"] == request_id for r in pending.json())

    # Driver accepts.
    accepted = await client.post(
        f"/api/deliveries/requests/{request_id}/respond",
        headers=_auth(driver_token),
        json={"accept": True},
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["request"]["status"] == "matched"

    # Parcel now matched.
    detail = await client.get(f"/api/parcels/{parcel_id}", headers=_auth(auth_token))
    assert detail.json()["status"] == "matched"

    # Responding again is blocked.
    again = await client.post(
        f"/api/deliveries/requests/{request_id}/respond",
        headers=_auth(driver_token),
        json={"accept": True},
    )
    assert again.status_code == 409

    # Driver active list includes the matched request.
    active = await client.get(
        "/api/deliveries/requests/me?scope=active", headers=_auth(driver_token)
    )
    assert active.status_code == 200
    assert any(r["public_id"] == request_id for r in active.json())

    # Pickup then deliver.
    pickup = await client.post(
        f"/api/deliveries/requests/{request_id}/pickup", headers=_auth(driver_token)
    )
    assert pickup.status_code == 200
    assert pickup.json()["request"]["status"] == "in_transit"

    delivered = await client.post(
        f"/api/deliveries/requests/{request_id}/delivered",
        headers=_auth(driver_token),
        json={"proof_image_url": "/uploads/proofs/test.jpg"},
    )
    assert delivered.status_code == 200
    assert delivered.json()["request"]["status"] == "delivered"
    assert delivered.json()["request"]["proof_image_url"] == "/uploads/proofs/test.jpg"

    # Parcel fully delivered.
    detail = await client.get(f"/api/parcels/{parcel_id}", headers=_auth(auth_token))
    assert detail.json()["status"] == "delivered"


async def test_driver_rejects_request_returns_parcel_to_pending(client, auth_token, driver_token):
    driver = await client.get("/api/drivers/me", headers=_auth(driver_token))
    driver_pub = driver.json()["public_id"]

    parcel_id = await _create_parcel(client, auth_token)

    created = await client.post(
        "/api/deliveries/request",
        headers=_auth(auth_token),
        json={"parcel_id": parcel_id, "driver_id": driver_pub},
    )
    assert created.status_code == 200
    request_id = created.json()["request"]["public_id"]

    rejected = await client.post(
        f"/api/deliveries/requests/{request_id}/respond",
        headers=_auth(driver_token),
        json={"accept": False},
    )
    assert rejected.status_code == 200
    assert rejected.json()["request"]["status"] == "rejected"

    # Parcel returns to pending so the sender can request another driver.
    detail = await client.get(f"/api/parcels/{parcel_id}", headers=_auth(auth_token))
    assert detail.json()["status"] == "pending"

    # Sender can request again.
    again = await client.post(
        "/api/deliveries/request",
        headers=_auth(auth_token),
        json={"parcel_id": parcel_id, "driver_id": driver_pub},
    )
    assert again.status_code == 200


async def test_sender_cannot_request_others_parcels(client, auth_token, driver_token):
    driver = await client.get("/api/drivers/me", headers=_auth(driver_token))
    driver_pub = driver.json()["public_id"]

    parcel_id = await _create_parcel(client, auth_token)

    # Register a second sender who does not own the parcel.
    other = await client.post(
        "/api/auth/register/sender",
        json={
            "name": "Other",
            "email": "other@example.com",
            "password": "password123",
        },
    )
    other_token = other.json()["access_token"]

    resp = await client.post(
        "/api/deliveries/request",
        headers=_auth(other_token),
        json={"parcel_id": parcel_id, "driver_id": driver_pub},
    )
    assert resp.status_code == 403
