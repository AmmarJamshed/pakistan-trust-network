from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def find_git_bash() -> str | None:
    env = os.environ.get("PTN_GIT_BASH")
    if env and Path(env).exists():
        return env
    candidates = [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
    ]
    for path in candidates:
        if Path(path).exists():
            return path
    which = shutil.which("bash")
    if which:
        return which
    return None


def find_repo_root(start: Path | None = None) -> Path | None:
    here = start or Path.cwd()
    search = [here, *here.resolve().parents, *Path(__file__).resolve().parents]
    seen: set[Path] = set()
    for p in search:
        if p in seen:
            continue
        seen.add(p)
        if (p / ".git").exists() and (p / "backend").is_dir():
            return p
    return None


def run_git_bash(
    command: str,
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    bash = find_git_bash()
    git = shutil.which("git")
    merged = os.environ.copy()
    if env:
        merged.update(env)
    merged["GIT_TERMINAL_PROMPT"] = "0"
    if bash:
        return subprocess.run(
            [bash, "-lc", command],
            cwd=str(cwd),
            env=merged,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    if not git:
        raise RuntimeError("Git Bash / git not found. Install Git for Windows.")
    return subprocess.run(
        command,
        cwd=str(cwd),
        env=merged,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=True,
    )
