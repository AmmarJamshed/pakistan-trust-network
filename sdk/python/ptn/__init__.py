"""PTN Python SDK — thin client for the Pakistan Trust Network API."""

from __future__ import annotations

from typing import Any

import httpx


class PTNError(Exception):
    def __init__(self, message: str, status_code: int | None = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class _CredentialsAPI:
    def __init__(self, client: "PTN"):
        self._client = client

    def issue(
        self,
        *,
        organization_id: str,
        holder_email: str | None = None,
        holder_did: str | None = None,
        credential_type: str,
        title: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "organization_id": organization_id,
            "holder_email": holder_email,
            "holder_did": holder_did,
            "type_code": credential_type,
            "title": title,
            "credential_subject": data or {},
        }
        return self._client.request("POST", "/api/credentials", json=payload)

    def get(self, credential_id: str) -> dict[str, Any]:
        return self._client.request("GET", f"/api/credentials/{credential_id}")

    def revoke(self, credential_id: str, reason: str | None = None) -> dict[str, Any]:
        return self._client.request(
            "POST",
            f"/api/credentials/{credential_id}/revoke",
            json={"reason": reason, "public_reason": True},
        )


class _VerifyAPI:
    def __init__(self, client: "PTN"):
        self._client = client

    def credential(self, credential_id: str) -> dict[str, Any]:
        return self._client.request("GET", f"/api/verify/{credential_id}", auth=False)


class _LedgerAPI:
    def __init__(self, client: "PTN"):
        self._client = client

    def blocks(self, limit: int = 20) -> dict[str, Any]:
        return self._client.request("GET", f"/api/ledger/blocks?limit={limit}", auth=False)

    def verify_chain(self) -> dict[str, Any]:
        return self._client.request("GET", "/api/ledger/verify-chain", auth=False)


class PTN:
    """
    Example:
        from ptn import PTN
        ptn = PTN(api_url="https://api.ptn.example")
        ptn.login("university@demo.ptn", "DemoPass123!")
        credential = ptn.credentials.issue(
            organization_id="...",
            holder="ptn:user:123",  # use holder_did=
            credential_type="UniversityDegree",
            title="BS Computer Science",
            data={"degree": "BS Computer Science", "graduation_year": 2026},
        )
        print(credential["credential_id"])
    """

    def __init__(self, api_url: str = "http://localhost:8000", token: str | None = None):
        self.api_url = api_url.rstrip("/")
        self.token = token
        self.credentials = _CredentialsAPI(self)
        self.verify = _VerifyAPI(self)
        self.ledger = _LedgerAPI(self)

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        auth: bool = True,
    ) -> dict[str, Any]:
        headers = {"Accept": "application/json"}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        with httpx.Client(base_url=self.api_url, timeout=30.0) as client:
            resp = client.request(method, path, json=json, headers=headers)
        if resp.status_code >= 400:
            try:
                body = resp.json()
            except Exception:
                body = resp.text
            raise PTNError(f"PTN API error {resp.status_code}", resp.status_code, body)
        if resp.status_code == 204:
            return {}
        return resp.json()

    def login(self, email: str, password: str) -> dict[str, Any]:
        data = self.request(
            "POST",
            "/api/auth/login",
            json={"email": email, "password": password},
            auth=False,
        )
        self.token = data["access_token"]
        return data

    def register(self, email: str, password: str, full_name: str, **kwargs: Any) -> dict[str, Any]:
        payload = {"email": email, "password": password, "full_name": full_name, **kwargs}
        data = self.request("POST", "/api/auth/register", json=payload, auth=False)
        self.token = data["access_token"]
        return data
