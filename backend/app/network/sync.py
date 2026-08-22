from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import SessionLocal
from app.ledger.service import LedgerService
from app.network.constants import GITHUB_GIT
from app.network.gitbash import find_git_bash, find_repo_root, run_git_bash
from app.network.snapshot import export_snapshot, import_snapshot

logger = logging.getLogger("ptn.network")

_lock = threading.Lock()
_state: dict[str, Any] = {
    "last_sync": None,
    "last_error": None,
    "last_result": None,
    "running": False,
}


def network_dir(repo: Path) -> Path:
    path = repo / "network" / "ledger"
    path.mkdir(parents=True, exist_ok=True)
    return path


def snapshot_path(repo: Path) -> Path:
    return network_dir(repo) / "snapshot.json"


def status() -> dict[str, Any]:
    repo = find_repo_root()
    return {
        "enabled": settings.ptn_network_enabled,
        "repo_root": str(repo) if repo else None,
        "git_bash": find_git_bash(),
        "remote": settings.ptn_network_git_url,
        "branch": settings.ptn_network_git_branch,
        "can_push": bool(settings.ptn_network_git_token),
        "interval_seconds": settings.ptn_network_sync_seconds,
        **_state,
    }


def write_snapshot_file(db: Session, repo: Path) -> Path:
    data = export_snapshot(db)
    path = snapshot_path(repo)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (path.parent / "README.md").write_text(
        "# PTN public ledger snapshot\n\n"
        "This folder is the shared access point for localhost nodes.\n\n"
        "Contains cryptographic proofs only: hashes, signatures, issuer DIDs, "
        "public credential titles. No private keys, passwords, CNICs, or private documents.\n",
        encoding="utf-8",
    )
    return path


def read_snapshot_file(repo: Path) -> dict[str, Any] | None:
    path = snapshot_path(repo)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _git_remote_url() -> str:
    token = settings.ptn_network_git_token.strip()
    base = settings.ptn_network_git_url.strip() or GITHUB_GIT
    if token and base.startswith("https://github.com/"):
        rest = base.removeprefix("https://")
        return f"https://x-access-token:{token}@{rest}"
    return base


def sync_once() -> dict[str, Any]:
    if not settings.ptn_network_enabled:
        return {"ok": False, "message": "Network sync disabled"}
    repo = find_repo_root()
    if repo is None:
        return {"ok": False, "message": "Not a git clone. Use join-network to clone the hub repo."}

    with _lock:
        _state["running"] = True
        _state["last_error"] = None
        try:
            result = _sync_locked(repo)
            _state["last_result"] = result
            _state["last_sync"] = datetime.now(timezone.utc).isoformat()
            return result
        except Exception as exc:
            _state["last_error"] = str(exc)
            logger.exception("PTN git network sync failed")
            return {"ok": False, "message": str(exc)}
        finally:
            _state["running"] = False


def _sync_locked(repo: Path) -> dict[str, Any]:
    branch = settings.ptn_network_git_branch
    token = settings.ptn_network_git_token.strip()
    if token:
        remote = _git_remote_url()
        pull_cmd = f'git pull --rebase "{remote}" {branch}'
        push_cmd = f'git push "{remote}" {branch}'
    else:
        pull_cmd = f"git pull --rebase origin {branch}"
        push_cmd = f"git push origin {branch}"

    pull = run_git_bash(pull_cmd, repo)
    pulled = pull.returncode == 0
    pull_msg = (pull.stderr or pull.stdout or "").strip()[-500:]

    db = SessionLocal()
    try:
        imported = {"identities": 0, "credentials": 0, "blocks": 0, "forks_resolved": 0}
        snap = read_snapshot_file(repo)
        if snap:
            imported = import_snapshot(db, snap)
        write_snapshot_file(db, repo)
        height = 0
        latest = LedgerService(db).get_latest_block()
        if latest:
            height = latest.index
        db.commit()
    finally:
        db.close()

    run_git_bash("git add network", repo)
    diff = run_git_bash("git diff --cached --quiet", repo)
    pushed = False
    commit_msg = ""
    if diff.returncode != 0:
        node = settings.ledger_node_name
        commit = run_git_bash(
            "git -c user.email=ptn-node@localhost -c user.name='PTN Node' "
            f"commit -m \"chore(network): sync ledger from {node}\"",
            repo,
        )
        commit_msg = (commit.stderr or commit.stdout or "").strip()[-400:]
        if commit.returncode == 0:
            push = run_git_bash(push_cmd, repo)
            pushed = push.returncode == 0
            if not pushed:
                commit_msg = (push.stderr or push.stdout or commit_msg)[-400:]
    return {
        "ok": True,
        "pulled": pulled,
        "pulled_detail": pull_msg,
        "imported": imported,
        "pushed": pushed,
        "commit": commit_msg,
        "height": height,
        "hub": settings.ptn_network_git_url,
    }


_stop = threading.Event()
_thread: threading.Thread | None = None


def start_background_sync() -> None:
    global _thread
    if not settings.ptn_network_enabled:
        return
    if _thread and _thread.is_alive():
        return

    def loop() -> None:
        sync_once()
        while not _stop.wait(settings.ptn_network_sync_seconds):
            sync_once()

    _thread = threading.Thread(target=loop, name="ptn-git-network", daemon=True)
    _thread.start()


def stop_background_sync() -> None:
    _stop.set()
