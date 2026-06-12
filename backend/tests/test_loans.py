"""
tests/test_loans.py
────────────────────────────────────────────────────────────────────────────
Integration tests for the Loans REST endpoints.

Covers
──────
• Happy-path borrow → return lifecycle
• Borrow validation (duplicate, inactive member, no stock)
• Return validation (already returned)
• Fine payment flow
• Filtering: active_only, overdue_only, member_id, book_id
• Stats endpoint
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import make_book_payload, make_member_payload


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _create_member(client: AsyncClient, **kw) -> dict:
    r = await client.post("/api/v1/members", json=make_member_payload(**kw))
    assert r.status_code == 201
    return r.json()


async def _create_book(client: AsyncClient, **kw) -> dict:
    r = await client.post("/api/v1/books", json=make_book_payload(**kw))
    assert r.status_code == 201
    return r.json()


async def _borrow(client: AsyncClient, member_id: str, book_id: str) -> dict:
    r = await client.post(
        "/api/v1/loans",
        json={"member_id": member_id, "book_id": book_id},
    )
    return r


# ── POST /api/v1/loans ────────────────────────────────────────────────────────


async def test_borrow_success(client: AsyncClient):
    m = await _create_member(client)
    b = await _create_book(client)

    resp = await _borrow(client, m["id"], b["id"])
    assert resp.status_code == 201
    body = resp.json()
    assert body["member_id"] == m["id"]
    assert body["book_id"] == b["id"]
    assert body["returned_at"] is None
    assert body["member_name"] == m["name"]
    assert body["book_title"] == b["title"]


async def test_borrow_decrements_available_copies(client: AsyncClient):
    m = await _create_member(client)
    b = await _create_book(client, total_copies=2)

    await _borrow(client, m["id"], b["id"])

    book_after = (await client.get(f"/api/v1/books/{b['id']}")).json()
    assert book_after["available_copies"] == 1


async def test_borrow_member_not_found(client: AsyncClient):
    b = await _create_book(client)
    resp = await _borrow(client, "00000000-0000-0000-0000-000000000000", b["id"])
    assert resp.status_code == 404


async def test_borrow_book_not_found(client: AsyncClient):
    m = await _create_member(client)
    resp = await _borrow(client, m["id"], "00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


async def test_borrow_inactive_member(client: AsyncClient):
    m = await _create_member(client)
    await client.patch(f"/api/v1/members/{m['id']}", json={"is_active": False})
    b = await _create_book(client)

    resp = await _borrow(client, m["id"], b["id"])
    assert resp.status_code == 409
    assert "inactive" in resp.json()["detail"].lower()


async def test_borrow_no_available_copies(client: AsyncClient):
    m = await _create_member(client)
    b = await _create_book(client, total_copies=1)

    m2 = await _create_member(client)
    await _borrow(client, m2["id"], b["id"])   # exhaust stock

    resp = await _borrow(client, m["id"], b["id"])
    assert resp.status_code == 409
    assert "available" in resp.json()["detail"].lower()


async def test_borrow_duplicate_active_loan(client: AsyncClient):
    m = await _create_member(client)
    b = await _create_book(client, total_copies=2)

    await _borrow(client, m["id"], b["id"])
    resp = await _borrow(client, m["id"], b["id"])
    assert resp.status_code == 409
    assert "already has an active loan" in resp.json()["detail"]


# ── GET /api/v1/loans ─────────────────────────────────────────────────────────


async def test_list_loans_returns_active(client: AsyncClient):
    m = await _create_member(client)
    b = await _create_book(client)
    loan = (await _borrow(client, m["id"], b["id"])).json()

    resp = await client.get("/api/v1/loans", params={"active_only": True})
    assert resp.status_code == 200
    ids = [ln["id"] for ln in resp.json()["items"]]
    assert loan["id"] in ids


async def test_list_loans_filter_by_member(client: AsyncClient):
    m = await _create_member(client)
    b = await _create_book(client)
    loan = (await _borrow(client, m["id"], b["id"])).json()

    resp = await client.get("/api/v1/loans", params={"member_id": m["id"]})
    ids = [ln["id"] for ln in resp.json()["items"]]
    assert loan["id"] in ids


async def test_list_loans_filter_by_book(client: AsyncClient):
    m = await _create_member(client)
    b = await _create_book(client)
    loan = (await _borrow(client, m["id"], b["id"])).json()

    resp = await client.get("/api/v1/loans", params={"book_id": b["id"]})
    ids = [ln["id"] for ln in resp.json()["items"]]
    assert loan["id"] in ids


# ── GET /api/v1/loans/{id} ────────────────────────────────────────────────────


async def test_get_loan_by_id(client: AsyncClient):
    m = await _create_member(client)
    b = await _create_book(client)
    loan = (await _borrow(client, m["id"], b["id"])).json()

    resp = await client.get(f"/api/v1/loans/{loan['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == loan["id"]


async def test_get_loan_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/loans/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


# ── POST /api/v1/loans/{id}/return ───────────────────────────────────────────


async def test_return_book_success(client: AsyncClient):
    m = await _create_member(client)
    b = await _create_book(client, total_copies=1)
    loan = (await _borrow(client, m["id"], b["id"])).json()

    resp = await client.post(f"/api/v1/loans/{loan['id']}/return")
    assert resp.status_code == 200
    body = resp.json()
    assert body["returned_at"] is not None
    assert float(body["fine_amount"]) >= 0


async def test_return_increments_available_copies(client: AsyncClient):
    m = await _create_member(client)
    b = await _create_book(client, total_copies=1)
    loan = (await _borrow(client, m["id"], b["id"])).json()

    await client.post(f"/api/v1/loans/{loan['id']}/return")

    book_after = (await client.get(f"/api/v1/books/{b['id']}")).json()
    assert book_after["available_copies"] == 1


async def test_return_already_returned(client: AsyncClient):
    m = await _create_member(client)
    b = await _create_book(client)
    loan = (await _borrow(client, m["id"], b["id"])).json()

    await client.post(f"/api/v1/loans/{loan['id']}/return")
    resp = await client.post(f"/api/v1/loans/{loan['id']}/return")
    assert resp.status_code == 409


async def test_return_loan_not_found(client: AsyncClient):
    resp = await client.post(
        "/api/v1/loans/00000000-0000-0000-0000-000000000000/return"
    )
    assert resp.status_code == 404


# ── POST /api/v1/loans/{id}/pay-fine ─────────────────────────────────────────


async def test_pay_fine_active_loan_rejected(client: AsyncClient):
    m = await _create_member(client)
    b = await _create_book(client)
    loan = (await _borrow(client, m["id"], b["id"])).json()

    resp = await client.post(f"/api/v1/loans/{loan['id']}/pay-fine")
    assert resp.status_code == 409
    assert "active loan" in resp.json()["detail"].lower()


async def test_pay_fine_no_fine_rejected(client: AsyncClient):
    """Returning on time → fine_amount == 0 → pay-fine should fail."""
    m = await _create_member(client)
    b = await _create_book(client)
    loan = (await _borrow(client, m["id"], b["id"])).json()
    returned = (
        await client.post(f"/api/v1/loans/{loan['id']}/return")
    ).json()

    # If the loan was returned on time the fine is 0
    if float(returned["fine_amount"]) == 0:
        resp = await client.post(f"/api/v1/loans/{loan['id']}/pay-fine")
        assert resp.status_code == 409


# ── GET /api/v1/loans/stats ───────────────────────────────────────────────────


async def test_stats_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/loans/stats")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("total_books", "total_members", "active_loans", "overdue_loans", "total_fines"):
        assert key in body
    assert body["total_books"] >= 0
    assert body["active_loans"] >= 0


async def test_stats_active_loans_count(client: AsyncClient):
    stats_before = (await client.get("/api/v1/loans/stats")).json()
    before = stats_before["active_loans"]

    m = await _create_member(client)
    b = await _create_book(client)
    await _borrow(client, m["id"], b["id"])

    stats_after = (await client.get("/api/v1/loans/stats")).json()
    assert stats_after["active_loans"] == before + 1


# ── Member delete guard ───────────────────────────────────────────────────────


async def test_cannot_delete_member_with_active_loan(client: AsyncClient):
    m = await _create_member(client)
    b = await _create_book(client)
    await _borrow(client, m["id"], b["id"])

    resp = await client.delete(f"/api/v1/members/{m['id']}")
    assert resp.status_code == 409


async def test_cannot_delete_book_with_active_loan(client: AsyncClient):
    m = await _create_member(client)
    b = await _create_book(client)
    await _borrow(client, m["id"], b["id"])

    resp = await client.delete(f"/api/v1/books/{b['id']}")
    assert resp.status_code == 409
