# Self-hosting PTN with Docker

Pakistan Trust Network is designed so **anyone can run the same stack**. There are two separate goals:

1. **Contributors** run PTN on their own machines and send pull requests.
2. **A public demo** stays online 24/7 so people can try it without installing anything.

Docker Compose covers both. It is **not** a cryptocurrency network — each deployment has its own database and ledger.

---

## 1. Run it on any machine (contributors)

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/macOS) or Docker Engine + Compose (Linux).

```bash
git clone https://github.com/YOUR_ORG/ptn.git
cd ptn
docker compose up --build
```

No `.env` file is required for a demo. Then open:

| What | URL |
|------|-----|
| Website | http://localhost:3000 |
| API docs | http://localhost:3000/api/docs |
| Direct API | http://localhost:8000/api/docs |

The UI talks to **`/api` on the same host**. That means a phone on your Wi‑Fi can use `http://YOUR_LAN_IP:3000` without extra CORS setup.

Stop with `Ctrl+C`, or run detached:

```bash
docker compose up --build -d
docker compose logs -f
docker compose down
```

Demo logins: `student@demo.ptn` / `DemoPass123!` (see the root README).

---

## 2. Share it on your LAN

1. Start Compose as above.
2. Find your LAN IP (`ipconfig` on Windows, `ip a` on Linux).
3. On another device open `http://YOUR_LAN_IP:3000`.

If QR codes and CV share links still point at `localhost`, set this in a `.env` next to `docker-compose.yml` and recreate:

```bash
PTN_FRONTEND_URL=http://YOUR_LAN_IP:3000
PTN_API_URL=http://YOUR_LAN_IP:3000
PTN_CORS_ORIGINS=http://YOUR_LAN_IP:3000
```

```bash
docker compose up --build -d
```

Windows may block inbound port 3000 in the firewall — allow it if other devices cannot connect.

---

## 3. Put a public copy on the internet (24/7)

Use a small always-on VPS (Hetzner, DigitalOcean, Linode, Oracle free tier, etc.), not a laptop.

```bash
# on the VPS
git clone https://github.com/YOUR_ORG/ptn.git
cd ptn
docker compose --profile public up --build -d
```

That starts Caddy on **port 80**. Visitors use `http://YOUR_SERVER_IP`.

For HTTPS with a domain, edit `deploy/Caddyfile` to your hostname (Caddy obtains a certificate automatically), point DNS A records at the VPS, open ports 80 and 443, then:

```bash
docker compose --profile public up --build -d
```

Set production secrets before this is a real public demo:

```bash
PTN_ENV=production
PTN_DEBUG=false
JWT_SECRET=...          # long random
ENCRYPTION_KEY=...      # long random
POSTGRES_PASSWORD=...
ADMIN_PASSWORD=...
PTN_FRONTEND_URL=https://ptn.example.com
PTN_API_URL=https://ptn.example.com
PTN_CORS_ORIGINS=https://ptn.example.com
```

Keep `SEED_DEMO_DATA=true` only if you want the labelled demo university/student.

---

## 4. Open source: what actually gets people contributing

Docker lets people **run** PTN. GitHub lets them **change** it.

1. Create a public GitHub repository and push this project.
2. Keep the root README clone + `docker compose up --build` as the first path.
3. Run CI (already in `.github/workflows/ci.yml`) on pull requests.
4. Optionally host one public demo from section 3 and link it in the README as “Live demo (reference implementation, not a government service)”.

Contributors should not need your laptop, your SQLite file, or Docker Desktop on *your* PC. They clone, compose up, patch, and open a PR.

---

## What not to do

- Do not expose this from a sleeping laptop and call it 24/7.
- Do not commit real `.env` secrets.
- Do not claim the public demo is an official Pakistani government system.
- Do not confuse “people can run their own node” with a global shared blockchain. The MVP ledger is per deployment unless you later operate a shared network.

More: [deployment.md](deployment.md) · [contributing.md](contributing.md)
