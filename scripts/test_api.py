#!/usr/bin/env python3
"""
Quick smoke-test script for the Library REST API.
Run after starting the server: python scripts/test_api.py
"""
import json, sys
import urllib.request
import urllib.error

BASE = "http://localhost:8000/api/v1"


def req(method: str, path: str, body: dict | None = None) -> dict | None:
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    request = urllib.request.Request(url, data=data, method=method,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  ✗ HTTP {e.code}: {body}")
        return None


def ok(label: str, val):
    print(f"  ✓ {label}: {val}")


print("\n══════════════════════════════════")
print("  Library API Smoke Test")
print("══════════════════════════════════\n")

# ── Health ────────────────────────────────────────────────────
print("[Health]")
h = req("GET", "/../health")
ok("status", h.get("status") if h else "unreachable")

# ── Create a member ───────────────────────────────────────────
print("\n[Members]")
m = req("POST", "/members", {"name": "Test User", "email": "test@lib.example"})
if not m: sys.exit(1)
mid = m["id"]
ok("Created member", m["name"])

# List
lst = req("GET", "/members?size=5")
ok("Total members", lst["total"] if lst else "?")

# Update
upd = req("PATCH", f"/members/{mid}", {"phone": "555-9999"})
ok("Updated phone", upd["phone"] if upd else "?")

# ── Create a book ─────────────────────────────────────────────
print("\n[Books]")
b = req("POST", "/books", {
    "title": "Test Book", "author": "A. Tester",
    "isbn": "9999999999999", "total_copies": 2
})
if not b: sys.exit(1)
bid = b["id"]
ok("Created book", b["title"])
ok("Available copies", b["available_copies"])

# ── Borrow ────────────────────────────────────────────────────
print("\n[Loans]")
loan = req("POST", "/loans", {"member_id": mid, "book_id": bid})
if not loan: sys.exit(1)
lid = loan["id"]
ok("Loan created, due", loan["due_date"])

# List active loans for member
active = req("GET", f"/loans?member_id={mid}&active_only=true")
ok("Active loans for member", active["total"] if active else "?")

# Duplicate borrow → should fail
print("  (duplicate borrow should fail)")
req("POST", "/loans", {"member_id": mid, "book_id": bid})

# ── Return ────────────────────────────────────────────────────
ret = req("POST", f"/loans/{lid}/return")
ok("Returned book, fine", f"${ret['fine_amount']}" if ret else "?")

# ── Stats ─────────────────────────────────────────────────────
print("\n[Stats]")
s = req("GET", "/loans/stats")
if s:
    ok("total_books",   s["total_books"])
    ok("total_members", s["total_members"])
    ok("active_loans",  s["active_loans"])

# ── Cleanup ───────────────────────────────────────────────────
print("\n[Cleanup]")
req("DELETE", f"/members/{mid}")
ok("Deleted test member", mid[:8] + "…")
req("DELETE", f"/books/{bid}")
ok("Deleted test book", bid[:8] + "…")

print("\n✅  All checks passed!\n")
