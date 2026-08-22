# PTN Git network (localhost mesh)

Pakistan Trust Network does **not** need a public VPS. Each participant:

1. Downloads / clones this repository.
2. Runs the app on **localhost**.
3. Lets the backend talk to **one GitHub repo** (this one) via Git Bash.

That repo is the shared access point. Nodes do not open ports to each other.

```text
Your PC (localhost)          Their PC (localhost)
   PTN API + website            PTN API + website
            \                      /
             \                    /
              Git pull / Git push
                      |
              GitHub hub repo
              network/ledger/snapshot.json
```

## What is synced

Public proofs only:

- ledger blocks and transactions (hashes, signatures, issuer DIDs, credential IDs)
- issuer public keys and organization names
- public credential titles and verification material

Never synced:

- private keys
- passwords
- JWT secrets
- emails used for login
- CNIC / private credential subjects

## Windows (Git Bash)

1. Install [Git for Windows](https://git-scm.com/download/win) (includes Git Bash).
2. Double-click `join-network.bat` in the repo root.
3. Open http://localhost:3001 and http://localhost:3001/run

`join-network.bat` runs `scripts/join-network.sh` inside Git Bash, then `start-local.bat`.

## Publish proofs from your node

`git push` needs permission on https://github.com/AmmarJamshed/pakistan-trust-network

Either:

- The repo owner adds you as a collaborator, and Git Credential Manager signs in, or
- You set `PTN_NETWORK_GIT_TOKEN` in `backend/.env` to a fine-grained PAT with **Contents: Read and write**.

Without push access you can still **pull** the shared ledger and verify credentials locally.

## Environment

```
PTN_NETWORK_ENABLED=true
PTN_NETWORK_GIT_URL=https://github.com/AmmarJamshed/pakistan-trust-network.git
PTN_NETWORK_GIT_BRANCH=main
PTN_NETWORK_GIT_TOKEN=
PTN_NETWORK_SYNC_SECONDS=60
```

The API exposes `GET /api/network/status` and `POST /api/network/sync`.
