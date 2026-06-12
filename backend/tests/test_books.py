"""
tests/test_books.py
────────────────────────────────────────────────────────────────────────────
Integration tests for the Books REST endpoints.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import make_book_payload


# ── POST /api/v1/books ────────────────────────────────────────────────────────


async def test_create_book_success(client: AsyncClient):
    payload = make_book_payload()
    resp = await client.post("/api/v1/books", json=payload)

    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == payload["title"]
    assert body["author"] == payload["author"]
    assert body["available_copies"] == payload["total_copies"]
    assert "id" in body


async def test_create_book_duplicate_isbn(client: AsyncClient):
    payload = make_book_payload()
    await client.post("/api/v1/books", json=payload)

    resp = await client.post("/api/v1/books", json=payload)
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"]


async def test_create_book_no_isbn_allowed(client: AsyncClient):
    """ISBN is optional — two books without ISBNs should both be created."""
    p1 = make_book_payload()
    p2 = make_book_payload()
    del p1["isbn"]
    del p2["isbn"]
    r1 = await client.post("/api/v1/books", json=p1)
    r2 = await client.post("/api/v1/books", json=p2)
    assert r1.status_code == 201
    assert r2.status_code == 201


async def test_create_book_missing_title(client: AsyncClient):
    resp = await client.post("/api/v1/books", json={"author": "Someone"})
    assert resp.status_code == 422


async def test_create_book_invalid_year(client: AsyncClient):
    resp = await client.post(
        "/api/v1/books",
        json={**make_book_payload(), "published_year": 999},
    )
    assert resp.status_code == 422


# ── GET /api/v1/books ─────────────────────────────────────────────────────────


async def test_list_books_empty(client: AsyncClient):
    resp = await client.get("/api/v1/books")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


async def test_list_books_returns_created(client: AsyncClient):
    p = make_book_payload()
    await client.post("/api/v1/books", json=p)

    resp = await client.get("/api/v1/books")
    titles = [b["title"] for b in resp.json()["items"]]
    assert p["title"] in titles


async def test_list_books_search(client: AsyncClient):
    p = make_book_payload(title="SearchableTitle99")
    await client.post("/api/v1/books", json=p)

    resp = await client.get("/api/v1/books", params={"search": "SearchableTitle99"})
    assert resp.json()["total"] >= 1


async def test_list_books_available_only(client: AsyncClient):
    # Create a book with 1 copy, then borrow it so available=0
    from tests.conftest import make_member_payload
    book_p = make_book_payload(total_copies=1)
    book = (await client.post("/api/v1/books", json=book_p)).json()
    member = (
        await client.post("/api/v1/members", json=make_member_payload())
    ).json()
    await client.post(
        "/api/v1/loans",
        json={"member_id": member["id"], "book_id": book["id"]},
    )

    resp = await client.get("/api/v1/books", params={"available_only": True})
    available_ids = [b["id"] for b in resp.json()["items"]]
    assert book["id"] not in available_ids


# ── GET /api/v1/books/{id} ────────────────────────────────────────────────────


async def test_get_book_by_id(client: AsyncClient):
    created = (await client.post("/api/v1/books", json=make_book_payload())).json()
    resp = await client.get(f"/api/v1/books/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


async def test_get_book_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/books/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


# ── PATCH /api/v1/books/{id} ──────────────────────────────────────────────────


async def test_update_book_title(client: AsyncClient):
    created = (await client.post("/api/v1/books", json=make_book_payload())).json()
    resp = await client.patch(
        f"/api/v1/books/{created['id']}", json={"title": "New Title"}
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "New Title"


async def test_update_book_increase_copies(client: AsyncClient):
    created = (
        await client.post("/api/v1/books", json=make_book_payload(total_copies=2))
    ).json()
    resp = await client.patch(
        f"/api/v1/books/{created['id']}", json={"total_copies": 5}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_copies"] == 5
    assert body["available_copies"] == 5   # +3 because none are on loan


async def test_update_book_isbn_conflict(client: AsyncClient):
    b1 = (await client.post("/api/v1/books", json=make_book_payload())).json()
    b2_p = make_book_payload()
    await client.post("/api/v1/books", json=b2_p)

    resp = await client.patch(
        f"/api/v1/books/{b1['id']}", json={"isbn": b2_p["isbn"]}
    )
    assert resp.status_code == 409


# ── DELETE /api/v1/books/{id} ─────────────────────────────────────────────────


async def test_delete_book(client: AsyncClient):
    created = (await client.post("/api/v1/books", json=make_book_payload())).json()
    resp = await client.delete(f"/api/v1/books/{created['id']}")
    assert resp.status_code == 204
    assert (await client.get(f"/api/v1/books/{created['id']}")).status_code == 404


async def test_delete_book_not_found(client: AsyncClient):
    resp = await client.delete("/api/v1/books/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
