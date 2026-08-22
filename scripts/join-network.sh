#!/usr/bin/env bash
# Pull the shared PTN Git hub (public proofs). Does not start the app.
set -euo pipefail

HUB="${PTN_NETWORK_GIT_URL:-https://github.com/AmmarJamshed/pakistan-trust-network.git}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ ! -d "$ROOT/.git" ]; then
  echo "Not a git clone. Cloning $HUB"
  git clone "$HUB" "$ROOT"
fi

cd "$ROOT"
echo "Syncing from GitHub hub..."
git pull --rebase origin main || git pull origin main
echo "Hub updated. Start a node with join-network.bat (Windows) or start-local.bat / docker compose."
