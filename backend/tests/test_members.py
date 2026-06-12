"""
tests/test_members.py
────────────────────────────────────────────────────────────────────────────
Integration tests for the Members REST endpoints.

Each test gets a fresh, rolled-back session (see conftest.py) so tests are
fully independent and order-insensitive.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import make_member_payload


# ── POST /api/v1/members ──────────────────────────────────────────────────────


async def test_create_member_success(client: AsyncClient):
    payload = make_member_payload()
    resp = await client.post("/api/v1/members", json=payload)

    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == payload["email"]
    assert body["name"] == payload["name"]
    assert body["is_active"] is True
    assert "id" in body


async def test_create_member_duplicate_email(client: AsyncClient):
    payload = make_member_payload()
    await client.post("/api/v1/members", json=payload)

    resp = await client.post("/api/v1/members", json=payload)
    assert resp.status_code == 409
    assert "already registered" in resp.json()["detail"]


async def test_create_member_missing_required_field(client: AsyncClient):
    # 'name' is required
    resp = await client.post("/api/v1/members", json={"email": "noname@example.com"})
    assert resp.status_code == 422


async def test_create_member_invalid_email(client: AsyncClient):
    resp = await client.post(
        "/api/v1/members",
        json={"name": "Bad Email", "email": "not-an-email"},
    )
    assert resp.status_code == 422


# ── GET /api/v1/members ───────────────────────────────────────────────────────


async def test_list_members_empty(client: AsyncClient):
    resp = await client.get("/api/v1/members")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


async def test_list_members_returns_created(client: AsyncClient):
    p = make_member_payload()
    await client.post("/api/v1/members", json=p)

    resp = await client.get("/api/v1/members")
    assert resp.status_code == 200
    emails = [m["email"] for m in resp.json()["items"]]
    assert p["email"] in emails


async def test_list_members_search(client: AsyncClient):
    p = make_member_payload(name="UniqueSearchableName")
    await client.post("/api/v1/members", json=p)

    resp = await client.get("/api/v1/members", params={"search": "UniqueSearchableName"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_members_pagination(client: AsyncClient):
    for _ in range(5):
        await client.post("/api/v1/members", json=make_member_payload())

    resp = await client.get("/api/v1/members", params={"page": 1, "size": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) <= 2
    assert body["total"] >= 5


# ── GET /api/v1/members/{id} ──────────────────────────────────────────────────


async def test_get_member_by_id(client: AsyncClient):
    p = make_member_payload()
    created = (await client.post("/api/v1/members", json=p)).json()

    resp = await client.get(f"/api/v1/members/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


async def test_get_member_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/members/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


# ── PATCH /api/v1/members/{id} ────────────────────────────────────────────────


async def test_update_member_name(client: AsyncClient):
    created = (
        await client.post("/api/v1/members", json=make_member_payload())
    ).json()

    resp = await client.patch(
        f"/api/v1/members/{created['id']}", json={"name": "Updated Name"}
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


async def test_update_member_email_conflict(client: AsyncClient):
    p1 = make_member_payload()
    p2 = make_member_payload()
    m1 = (await client.post("/api/v1/members", json=p1)).json()
    await client.post("/api/v1/members", json=p2)

    # Try to set m1's email to m2's email
    resp = await client.patch(
        f"/api/v1/members/{m1['id']}", json={"email": p2["email"]}
    )
    assert resp.status_code == 409


async def test_deactivate_member(client: AsyncClient):
    created = (
        await client.post("/api/v1/members", json=make_member_payload())
    ).json()
    resp = await client.patch(
        f"/api/v1/members/{created['id']}", json={"is_active": False}
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


# ── DELETE /api/v1/members/{id} ───────────────────────────────────────────────


async def test_delete_member(client: AsyncClient):
    created = (
        await client.post("/api/v1/members", json=make_member_payload())
    ).json()
    resp = await client.delete(f"/api/v1/members/{created['id']}")
    assert resp.status_code == 204

    # Confirm gone
    assert (await client.get(f"/api/v1/members/{created['id']}")).status_code == 404


async def test_delete_member_not_found(client: AsyncClient):
    resp = await client.delete("/api/v1/members/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
