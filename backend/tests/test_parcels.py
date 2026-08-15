"""Parcel CRUD and delivery workflow tests."""


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_create_parcel(client, auth_token):
    resp = await client.post(
        "/api/parcels",
        headers=_auth(auth_token),
        json={
            "pickup_location": "Mumbai Central",
            "drop_location": "Pune Station",
            "item_description": "Two boxes of electronics",
            "item_value": 15000,
            "weight": 12.5,
            "size_tier": "medium",
            "budget": 450,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["public_id"].startswith("P")
    assert data["status"] == "pending"


async def test_sender_lists_own_parcels(client, auth_token):
    await client.post(
        "/api/parcels",
        headers=_auth(auth_token),
        json={
            "pickup_location": "Delhi",
            "drop_location": "Jaipur",
            "item_description": "Documents",
            "weight": 2,
        },
    )
    resp = await client.get("/api/parcels", headers=_auth(auth_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_available_parcels_visible(client, auth_token):
    resp = await client.post(
        "/api/parcels",
        headers=_auth(auth_token),
        json={
            "pickup_location": "Delhi",
            "drop_location": "Jaipur",
            "item_description": "Documents",
            "weight": 2,
        },
    )
    assert resp.status_code == 201
    avail = await client.get("/api/parcels/available")
    assert avail.status_code == 200
    ids = [p["public_id"] for p in avail.json()]
    assert resp.json()["public_id"] in ids


async def test_non_owner_cannot_update(client, auth_token, driver_token):
    resp = await client.post(
        "/api/parcels",
        headers=_auth(auth_token),
        json={
            "pickup_location": "Delhi",
            "drop_location": "Jaipur",
            "item_description": "Documents",
            "weight": 2,
        },
    )
    parcel_id = resp.json()["public_id"]

    resp = await client.patch(
        f"/api/parcels/{parcel_id}",
        headers=_auth(driver_token),
        json={"item_description": "Hijacked"},
    )
    assert resp.status_code == 403


async def test_driver_accepts_and_completes_delivery(client, auth_token, driver_token):
    # Sender creates a parcel
    parcel = await client.post(
        "/api/parcels",
        headers=_auth(auth_token),
        json={
            "pickup_location": "Mumbai",
            "drop_location": "Pune",
            "item_description": "Laptop",
            "weight": 3,
        },
    )
    parcel_id = parcel.json()["public_id"]

    # Driver becomes available and accepts the parcel
    await client.patch(
        "/api/drivers/me/availability",
        headers=_auth(driver_token),
        json={"status": "available", "current_city": "Mumbai"},
    )
    accept = await client.post(
        f"/api/deliveries/accept?parcel_id={parcel_id}",
        headers=_auth(driver_token),
    )
    assert accept.status_code == 200, accept.text
    delivery_id = accept.json()["delivery"]["public_id"]

    # Parcel moved to accepted
    detail = await client.get(f"/api/parcels/{parcel_id}", headers=_auth(auth_token))
    assert detail.status_code == 200
    assert detail.json()["status"] == "accepted"

    # Pickup
    pickup = await client.post(
        f"/api/deliveries/{delivery_id}/pickup", headers=_auth(driver_token)
    )
    assert pickup.status_code == 200
    assert pickup.json()["status"] == "picked_up"

    # Delivered
    delivered = await client.post(
        f"/api/deliveries/{delivery_id}/delivered",
        headers=_auth(driver_token),
        json={"proof_image_url": "/uploads/proofs/test.jpg"},
    )
    assert delivered.status_code == 200
    assert delivered.json()["status"] == "delivered"

    # Duplicate accept rejected
    conflict = await client.post(
        f"/api/deliveries/accept?parcel_id={parcel_id}",
        headers=_auth(driver_token),
    )
    assert conflict.status_code == 409


async def test_cancel_parcel(client, auth_token):
    parcel = await client.post(
        "/api/parcels",
        headers=_auth(auth_token),
        json={
            "pickup_location": "Mumbai",
            "drop_location": "Pune",
            "item_description": "Box",
            "weight": 5,
        },
    )
    parcel_id = parcel.json()["public_id"]
    resp = await client.post(
        f"/api/parcels/{parcel_id}/cancel", headers=_auth(auth_token)
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"
