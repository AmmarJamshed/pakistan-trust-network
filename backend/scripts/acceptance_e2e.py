"""End-to-end acceptance script for PTN MVP workflow."""

from __future__ import annotations

import json
import sys
import uuid

import httpx

BASE = "http://127.0.0.1:8000"


def main() -> int:
    c = httpx.Client(base_url=BASE, timeout=30.0)
    steps = []

    def ok(name: str, cond: bool, detail: str = ""):
        steps.append((name, cond, detail))
        status = "PASS" if cond else "FAIL"
        print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
        if not cond:
            raise SystemExit(1)

    # 1 health / website API
    r = c.get("/health")
    ok("1. API health", r.status_code == 200, r.text)

    # 2 Register university org user
    email = f"uni-{uuid.uuid4().hex[:8]}@test.ptn"
    r = c.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "TestPass123!",
            "full_name": "Acceptance University",
            "username": f"uni{uuid.uuid4().hex[:6]}",
            "account_type": "organization",
        },
    )
    ok("2. Register institution user", r.status_code == 200)
    uni_token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {uni_token}"}

    # 3 Create org + identity
    r = c.post(
        "/api/organizations",
        headers=headers,
        json={
            "name": f"Acceptance Demo University {uuid.uuid4().hex[:4]}",
            "org_type": "UNIVERSITY",
            "country": "Pakistan",
            "email": email,
            "description": "DEMO acceptance org",
        },
    )
    ok("3. Create organization + identity", r.status_code == 200, r.text[:200])
    org = r.json()
    ok("3b. Identity created", org.get("has_identity") is True)

    # 4 Register student
    student_email = f"stu-{uuid.uuid4().hex[:8]}@test.ptn"
    r = c.post(
        "/api/auth/register",
        json={
            "email": student_email,
            "password": "TestPass123!",
            "full_name": "Acceptance Student",
            "username": f"stu{uuid.uuid4().hex[:6]}",
        },
    )
    ok("4. Register student", r.status_code == 200)
    student_token = r.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}
    me = c.get("/api/auth/me", headers=student_headers).json()

    # 5-8 Issue credential
    r = c.post(
        "/api/credentials",
        headers=headers,
        json={
            "organization_id": org["id"],
            "holder_email": student_email,
            "type_code": "UniversityDegree",
            "title": "BS Computer Science",
            "credential_subject": {"degree": "BS Computer Science", "graduation_year": 2026},
        },
    )
    ok("5-8. Issue signed credential + ledger anchor", r.status_code == 200, r.text[:300])
    cred = r.json()
    cred_id = cred["credential_id"]
    ok("8b. Has ledger tx", bool(cred.get("ledger_tx_id")))

    # 9-10 Wallet
    wallet = c.get("/api/wallet/me", headers=student_headers).json()
    titles = [x["title"] for cat in wallet["categories"].values() for x in cat]
    ok("9-10. Credential in wallet", "BS Computer Science" in titles)

    # 11-13 CV publish
    r = c.post(
        "/api/cv/publish",
        headers=student_headers,
        json={"visibility": "PUBLIC", "summary": "Acceptance CV"},
    )
    ok("11-13. Publish CV", r.status_code == 200)
    cv_url = r.json()["public_url"]
    username = r.json()["username"]
    pub = c.get(f"/api/cv/{username}")
    ok("13b. Public CV reachable", pub.status_code == 200)

    # 15-16 Verify
    v = c.get(f"/api/verify/{cred_id}").json()
    ok("15-16. Verification VERIFIED", v.get("overall") == "VERIFIED", json.dumps(v.get("checks")))

    # 17-18 Tamper demo
    r = c.post(
        "/api/credentials/demo/tamper-check",
        headers=headers,
        json={"credential_id": cred_id, "modified_subject": {"degree": "FAKE PhD"}},
    )
    ok("17-18. Tamper shows integrity failure", r.status_code == 200)
    body = r.json()
    ok(
        "18b. Modified integrity false",
        body["modified"]["checks"]["credential_integrity_verified"] is False,
    )

    # 19-20 Revoke
    r = c.post(
        f"/api/credentials/{cred_id}/revoke",
        headers=headers,
        json={"reason": "Acceptance test revocation", "public_reason": True},
    )
    ok("19. Revoke credential", r.status_code == 200)
    v2 = c.get(f"/api/verify/{cred_id}").json()
    ok("20. Verification shows REVOKED", v2.get("overall") == "REVOKED", v2.get("status"))

    # 21-22 Explorer
    blocks = c.get("/api/ledger/blocks").json()
    ok("21. Explorer blocks", "blocks" in blocks and blocks.get("height", 0) >= 1)
    search = c.get("/api/ledger/search", params={"q": cred_id}).json()
    ok("22. Locate credential transaction", len(search.get("transactions", [])) >= 1)

    # 23 Chain integrity
    chain = c.get("/api/ledger/verify-chain").json()
    ok("23. Chain integrity valid", chain.get("valid") is True, chain.get("message"))

    # 24-25 Tamper block (admin)
    login_admin = c.post(
        "/api/auth/login",
        json={"email": "admin@ptn.demo", "password": "AdminPass123!"},
    )
    ok("24a. Admin login", login_admin.status_code == 200)
    admin_h = {"Authorization": f"Bearer {login_admin.json()['access_token']}"}
    # Use a non-genesis block
    height = blocks["height"]
    if height < 1:
        ok("24-25. Tamper demo", False, "no blocks to tamper")
    else:
        r = c.post(f"/api/ledger/dev/tamper-block/{height}", headers=admin_h)
        ok("24. Tamper block (dev)", r.status_code == 200, r.text[:200])
        result = r.json()["chain_verification"]
        ok("25. Chain detects tampering", result.get("valid") is False, str(result.get("errors"))[:200])

    # Demo student verify still works for other creds
    stats = c.get("/api/stats").json()
    ok("Bonus. Network stats", stats.get("credentials_issued", 0) >= 1)

    print("\nAll acceptance steps passed.")
    print(f"Sample CV: {cv_url}")
    print(f"Sample verify: {BASE}/api/verify/{cred_id}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
