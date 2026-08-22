# API Reference

Base URL (local): `http://localhost:8000`  
Interactive docs: `/api/docs` · ReDoc: `/api/redoc` · OpenAPI: `/api/openapi.json`

Unless noted, authenticated routes expect:

```http
Authorization: Bearer <access_token>
```

**Tagline:** Issue. Own. Verify.  
**Architecture:** proof on-chain, data off-chain.  
**Disclaimer:** Open-source reference API — not government-endorsed.

---

## Health & meta

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | No | Service name, tagline, disclaimer |
| `GET` | `/health` | No | Liveness `{ status, service, version }` |

---

## Auth — `/api/auth`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/auth/register` | No | Create user; returns token pair |
| `POST` | `/api/auth/login` | No | Email/password → tokens |
| `POST` | `/api/auth/refresh` | No | Refresh token → new pair |
| `GET` | `/api/auth/me` | Yes | Current user profile |

### Register body (shape)

```json
{
  "email": "you@example.com",
  "password": "…",
  "full_name": "Your Name",
  "username": "optional",
  "account_type": "individual"
}
```

`account_type`: `individual` | `organization`.

### Token response

```json
{
  "access_token": "…",
  "refresh_token": "…",
  "token_type": "bearer"
}
```

---

## Organizations — `/api/organizations`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/organizations` | Yes | Create org + Ed25519 identity + owner membership |
| `GET` | `/api/organizations` | No | List orgs (`status_filter`, `limit`, `offset`) |
| `GET` | `/api/organizations/mine` | Yes | Orgs for current user |
| `GET` | `/api/organizations/{org_id}` | No | Org details |
| `POST` | `/api/organizations/{org_id}/identity` | Member/Admin | Ensure cryptographic identity |
| `GET` | `/api/organizations/{org_id}/identity` | No | Public key metadata |
| `POST` | `/api/organizations/{org_id}/status` | Admin | Set `OrgStatus` |

`OrgStatus`: `PENDING_VERIFICATION` · `VERIFIED` · `SUSPENDED` · `REVOKED`.

---

## Credentials — `/api/credentials`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/credentials` | Issuer | Issue credential + ledger anchor |
| `GET` | `/api/credentials/{credential_id}` | Holder/Issuer/Admin | Fetch credential summary |
| `POST` | `/api/credentials/{credential_id}/revoke` | Issuer | Revoke + ledger event |
| `GET` | `/api/credentials/issued/{organization_id}` | Issuer | List credentials issued by org |
| `POST` | `/api/credentials/demo/tamper-check` | Yes | Integrity failure demonstration |

### Issue body (shape)

```json
{
  "organization_id": "uuid",
  "holder_did": "ptn:user:…",
  "holder_email": "student@demo.ptn",
  "type_code": "UniversityDegree",
  "title": "BS Computer Science",
  "credential_subject": { "degree": "BS Computer Science", "graduation_year": 2026 },
  "public_fields": ["title", "type", "issuer_name", "issued_at", "status"]
}
```

Provide `holder_did` and/or `holder_email`. Sensitive subject keys are stripped server-side.

### Revoke body

```json
{
  "reason": "Issued in error",
  "public_reason": true
}
```

---

## Public verification

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/verify/{credential_id}` | No | Full cryptographic + ledger verification |

Typical `overall` values: `VERIFIED` · `FAILED` · `REVOKED` · `NOT_FOUND`.

Checks object includes issuer, signature, integrity, ledger proof, chain integrity, and active status flags.

---

## Ledger — `/api/ledger`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/ledger/blocks` | No | Paginated blocks + height |
| `GET` | `/api/ledger/blocks/{height}` | No | Block detail + transactions |
| `GET` | `/api/ledger/transactions/{tx_id}` | No | Transaction summary |
| `GET` | `/api/ledger/search?q=` | No | Search blocks/txs/credentials |
| `GET` | `/api/ledger/verify-chain` | No | Full chain integrity report |
| `POST` | `/api/ledger/dev/tamper-block/{height}` | Admin | **Dev only** — corrupt hash for demo |

---

## Wallet — `/api/wallet`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/wallet/me` | Yes | Grouped credentials for current user |
| `GET` | `/api/wallet/users/{user_id}` | Self/Admin | Wallet for a user id |

Categories: `education`, `professional`, `skills`, `achievement`.

---

## CV — `/api/cv`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/cv/me` | Yes | Sync + return own CV profile |
| `POST` | `/api/cv/publish` | Yes | Set visibility + summary |
| `POST` | `/api/cv/unpublish` | Yes | Make private |
| `GET` | `/api/cv/{username}` | No* | Public CV (`?token=` for `LINK_ONLY`) |

\* Availability depends on visibility settings.

Publish body:

```json
{
  "visibility": "PUBLIC",
  "summary": "Short bio"
}
```

`visibility`: `PRIVATE` · `PUBLIC` · `LINK_ONLY`.

---

## Stats & admin

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/stats` | No | Network counters |
| `GET` | `/api/admin/overview` | Admin | Stats, chain status, recent orgs/audit |

Admin overview notes that operators **cannot modify ledger history**; the ledger is append-only.

---

## Error shapes

Typical FastAPI errors:

```json
{ "detail": "Invalid credentials" }
```

Rate limits and auth failures use standard HTTP status codes (`401`, `403`, `404`, `429`, `500`).

---

## Demo accounts (local seed)

| Email | Password |
|-------|----------|
| `student@demo.ptn` | `DemoPass123!` |
| `university@demo.ptn` | `DemoPass123!` |
| `employer@demo.ptn` | `DemoPass123!` |
| `training@demo.ptn` | `DemoPass123!` |
| `admin@ptn.demo` | `AdminPass123!` |

---

## Related docs

- [Architecture](architecture.md)  
- [Credentials](credentials.md)  
- [Security](security.md)
