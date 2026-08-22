# Contributing

Thank you for helping improve Pakistan Trust Network — open-source trust infrastructure for **Issue. Own. Verify.**

By contributing, you agree that your work is licensed under the MIT License (see root `LICENSE`) and that you will not misrepresent PTN as government-endorsed.

---

## Getting started

1. Fork and clone the repository.  
2. Run the stack with Docker (no `.env` required for the demo):

```bash
docker compose up --build
```

Open http://localhost:3000 — details in [self-host.md](self-host.md).

3. Or run backend/frontend separately with local Postgres (see [deployment.md](deployment.md)).

---

## Development tips

| Area | Path | Checks |
|------|------|--------|
| API | `backend/` | `pytest`, `ruff` |
| UI | `frontend/` | `npm test`, `npm run lint`, `npm run build` |
| Docs | `docs/` | Clarity, Mermaid where useful, no gov endorsement claims |
| SDKs | `sdk/` | Keep thin and aligned with `/api` |

Please preserve the architecture rule: **proof on-chain / data off-chain**. Do not add CNIC (or similar) fields to ledger payloads or credential subjects.

---

## Conventional commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use for |
|--------|---------|
| `feat:` | New user-facing capability |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `refactor:` | Internal restructuring |
| `test:` | Tests only |
| `chore:` | Tooling, deps, CI |
| `security:` | Security hardening (optional scope) |

Examples:

```text
feat: add ledger search by credential id
fix: reject revoked orgs from issuing
docs: clarify on-chain vs off-chain table
```

Reference issues as `#123` when applicable.

---

## Pull request checklist

Before opening a PR:

- [ ] Scope is focused (prefer small MRs/PRs)  
- [ ] Tests added or updated when behavior changes  
- [ ] No secrets committed (`.env`, keys, production passwords)  
- [ ] Demo data remains clearly labelled when touched  
- [ ] Docs updated if APIs or architecture change  
- [ ] Commit messages follow conventional commits  

### CI expectations

GitHub Actions (`.github/workflows/ci.yml`) runs:

1. **Backend** — install deps, lint (non-blocking currently), `pytest` with coverage  
2. **Frontend** — `npm ci`, test, lint (non-blocking currently), production build  
3. **Docker** — build backend and frontend images  

PRs should stay green on required checks as the project tightens gates.

---

## Code of conduct (basics)

We are committed to a respectful, inclusive project.

**Expected**

- Assume good faith; disagree on ideas, not people  
- Prefer precise technical feedback  
- Protect users’ privacy; never request real CNICs or production secrets in issues  
- Credit others’ work  

**Unacceptable**

- Harassment, hate speech, or personal attacks  
- Publishing others’ private data  
- Social-engineering maintainers for credentials  
- Presenting PTN as an official government product  
- Introducing malware, token scams, or undisclosed mining/crypto schemes  

Report concerns privately to the maintainers listed in the repository (or the hosting platform’s abuse channel). Maintainers may moderate, revert, or ban to protect the community and users.

---

## Security disclosures

If you find a vulnerability:

1. **Do not** open a public issue with exploit details.  
2. Contact maintainers privately with reproduction steps and impact.  
3. Allow reasonable time for a fix before disclosure.  

Demo tamper endpoints are intentional teaching tools — report only if they are reachable or unsafe in production configurations.

---

## Documentation contributions

Docs live under `/docs` and the root `README.md`. Keep the tone professional, accessible, and honest about MVP limits. Mermaid diagrams are welcome when they clarify flows.

---

## Related docs

- [Architecture](architecture.md)  
- [API](api.md)  
- [Governance](governance.md)
