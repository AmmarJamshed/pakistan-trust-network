# Architecture

Pakistan Trust Network (PTN) is designed around one principle:

> **Proof on-chain. Data off-chain.**

Credentials are issued, owned, and verified without putting personal payloads on the ledger. The ledger records integrity proofs; the application database stores credential content under access control.

**Tagline:** Issue. Own. Verify.

**Disclaimer:** PTN is an open-source reference implementation. It is not affiliated with or endorsed by any government.

---

## System overview

```mermaid
flowchart TB
  subgraph Clients
    Web[Next.js Frontend]
    SDK[TS / Python SDKs]
    Public[Anonymous Verifier]
  end

  subgraph API["FastAPI · /api"]
    Auth[Auth + JWT]
    Orgs[Organizations]
    Creds[Credentials]
    Wallet[Wallet]
    CV[CV]
    LedgerAPI[Ledger Explorer]
    Verify[Public Verify]
    Admin[Admin]
  end

  subgraph Persistence
    PG[(PostgreSQL)]
    Blocks[Ledger Blocks + Txs]
    Audit[Append-only Audit Log]
  end

  Web --> Auth
  Web --> Creds
  Web --> Wallet
  Web --> CV
  Web --> LedgerAPI
  SDK --> Auth
  Public --> Verify
  Auth --> PG
  Orgs --> PG
  Creds --> PG
  Creds --> Blocks
  Wallet --> PG
  CV --> PG
  LedgerAPI --> Blocks
  Verify --> PG
  Verify --> Blocks
  Admin --> PG
  Admin --> Blocks
  Admin --> Audit
```

| Layer | Responsibility |
|-------|----------------|
| Frontend | Dashboards, wallet, issue UI, explorer, public verify/CV pages |
| API | Auth, RBAC, issuance, revocation, verification, stats |
| Off-chain DB | Users, orgs, credential subjects, encrypted org keys, CV profiles |
| Permissioned ledger | Append-only blocks of hashes, signatures, status events |
| Audit log | Hash-chained operational events for operators |

---

## Spec-aligned high-level flow

```mermaid
flowchart LR
  A[Register org / user] --> B[Create Ed25519 identity]
  B --> C[Issue credential]
  C --> D[Hash + sign payload]
  D --> E[Store data off-chain]
  E --> F[Append ledger proof]
  F --> G[Holder wallet]
  G --> H[Public verify / CV share]
  H --> I{Checks pass?}
  I -->|Yes| J[VERIFIED]
  I -->|Revoked| K[REVOKED]
  I -->|No| L[FAILED]
```

---

## Issuance

Only members with issuer-capable roles (`OWNER`, `ISSUER`, `ADMIN`) — or platform admins — may issue for an organization.

```mermaid
sequenceDiagram
  participant Issuer as Issuer user
  participant API as PTN API
  participant DB as Off-chain DB
  participant Key as Org identity
  participant Ledger as Permissioned ledger

  Issuer->>API: POST /api/credentials
  API->>DB: Load org + holder + type
  API->>DB: Strip prohibited subject fields
  API->>API: SHA-256 credential hash
  API->>Key: Decrypt private key · Ed25519 sign
  API->>DB: Persist credential + signature
  API->>Ledger: CREDENTIAL_ISSUED tx → mine block
  API-->>Issuer: credential_id + verification_url
```

On-chain (in the transaction / block):

- `credential_id`, `credential_hash`, `issuer_id` (DID)
- `digital_signature`, `metadata_hash`, `transaction_type`

Off-chain:

- Full `credential_subject` (after sensitive-field stripping)
- Titles, membership, encrypted private keys

---

## Verification

`GET /api/verify/{credential_id}` is public (no auth).

```mermaid
flowchart TD
  Start[Verify request] --> Found{Credential found?}
  Found -->|No| NF[NOT_FOUND]
  Found -->|Yes| C1[Issuer identity ACTIVE?]
  C1 --> C2[Ed25519 signature valid?]
  C2 --> C3[Recomputed hash matches?]
  C3 --> C4[Ledger proof matches hash?]
  C4 --> C5[Chain integrity OK?]
  C5 --> C6{Status REVOKED?}
  C6 -->|Yes| R[REVOKED]
  C6 -->|No| All{All critical checks pass?}
  All -->|Yes| V[VERIFIED]
  All -->|No| F[FAILED]
```

Critical checks for `VERIFIED`:

1. Issuer identity present and active  
2. Signature verified against org public key  
3. Credential integrity (hash)  
4. Ledger proof present and consistent  
5. Not revoked  

Chain integrity is also reported (`chain_integrity_verified`) for explorer / ops visibility.

---

## Revocation

Issuers append a new ledger event; history is never rewritten.

```mermaid
sequenceDiagram
  participant Issuer as Issuer
  participant API as PTN API
  participant DB as Off-chain DB
  participant Ledger as Ledger

  Issuer->>API: POST /api/credentials/{id}/revoke
  API->>DB: status = REVOKED · store Revocation row
  API->>Ledger: CREDENTIAL_REVOKED tx → new block
  Note over Ledger: Prior ISSUED block remains immutable
  API-->>Issuer: Updated credential status
```

Public verification thereafter returns overall `REVOKED` and optional public reason.

---

## Wallet

Holders see credentials grouped by category (education, professional, skills, achievement).

```mermaid
flowchart LR
  User[Authenticated holder] --> W[GET /api/wallet/me]
  W --> G[Group by type_code]
  G --> UI[Wallet UI]
  UI --> Link[Per-credential verify URL]
```

Admins (or the user themselves) may also call `GET /api/wallet/users/{user_id}`.

---

## Verifiable CV

CV profiles sync from wallet credentials and can be published:

| Visibility | Behavior |
|------------|----------|
| `PRIVATE` | Not publicly listed |
| `PUBLIC` | Available at `/cv/{username}` |
| `LINK_ONLY` | Requires share token query param |

```mermaid
flowchart TD
  Sync[Sync wallet → CV items] --> Publish[POST /api/cv/publish]
  Publish --> Vis{Visibility}
  Vis -->|PUBLIC| Open[Anyone with username]
  Vis -->|LINK_ONLY| Token[Username + token]
  Vis -->|PRIVATE| Hide[No public URL]
```

---

## Security architecture

```mermaid
flowchart TB
  subgraph Edge
    CORS[CORS allowlist]
    RL[Rate limit / IP]
    HDR[Security headers]
  end

  subgraph AuthZ
    JWT[JWT Bearer access/refresh]
    RBAC[User roles + org membership roles]
    Argon[argon2 password hashes]
  end

  subgraph Crypto
    Ed[Ed25519 issue/revoke signatures]
    Fernet[Fernet-encrypted org private keys]
    Hash[SHA-256 + Merkle]
  end

  Client --> CORS --> RL --> HDR --> JWT
  JWT --> RBAC
  RBAC --> Ed
  Ed --> Hash
  Argon -.-> JWT
  Fernet --> Ed
```

See [security.md](security.md) for details.

---

## Deployment topology

```mermaid
flowchart LR
  Browser --> FE[Frontend · :3000]
  Browser --> API[Backend · :8000]
  FE --> API
  API --> DB[(PostgreSQL · :5432)]

  subgraph Optional["docker compose --profile multi-node"]
    N1[ptn-node-university :8001]
    N2[ptn-node-employer :8002]
    N3[ptn-node-training :8003]
  end

  N1 --> DB
  N2 --> DB
  N3 --> DB
```

Today’s multi-node profile demonstrates **distinct validator identities** against a **shared ledger database**. Future work may add peer replication and consensus — see [blockchain.md](blockchain.md) and [deployment.md](deployment.md).

---

## Component map (repository)

| Path | Role |
|------|------|
| `backend/app` | FastAPI application, ledger, credentials, identity |
| `frontend/src` | Next.js UI |
| `sdk/typescript`, `sdk/python` | Thin API clients |
| `docker-compose.yml` | Local full stack |
| `docs/` | This documentation set |

---

## Design invariants

1. **No token economy** — ledger is integrity infrastructure, not a currency.  
2. **Append-only proofs** — revocation adds events; it does not delete history.  
3. **Minimal public surface** — verify endpoints expose display-safe fields only.  
4. **Demo honesty** — seeded orgs carry `is_demo` / `demo_label` flags.  
5. **No government claim** — PTN does not speak for any public authority.
