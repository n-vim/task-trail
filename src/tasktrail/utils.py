"""Small utility helpers."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def resolve_root(path: str | Path) -> Path:
    """Resolve and validate a repository path."""
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root}")
    return root


def safe_relative(path: Path, root: Path) -> str:
    """Return a POSIX relative path for display."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def is_probably_binary(path: Path) -> bool:
    """Detect binary files using a small byte sample."""
    try:
        sample = path.read_bytes()[:2048]
    except OSError:
        return True
    return b"\0" in sample


def should_skip_dir(name: str, ignored: tuple[str, ...]) -> bool:
    return name in ignored or (name.startswith(".") and name in ignored)


def iter_project_files(
    root: Path,
    ignore_dirs: tuple[str, ...],
    ignore_files: tuple[str, ...],
    only_paths: tuple[str, ...] | None = None,
) -> list[Path]:
    """Return project files while skipping common generated folders."""
    wanted = set(only_paths or ())
    found: list[Path] = []
    for current, dirnames, filenames in os.walk(root):
        current_path = Path(current)
        dirnames[:] = [name for name in dirnames if not should_skip_dir(name, ignore_dirs)]
        for filename in filenames:
            if filename in ignore_files:
                continue
            path = current_path / filename
            relative = safe_relative(path, root)
            if wanted and relative not in wanted:
                continue
            found.append(path)
    return found


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def slugify(value: str, max_length: int = 72) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    while "--" in safe:
        safe = safe.replace("--", "-")
    return (safe or "task")[:max_length].strip("-") or "task"


def normalize_space(value: str) -> str:
    return " ".join(value.strip().split())


def get_changed_files(root: Path) -> tuple[str, ...]:
    """Return files changed according to Git, if the path is inside a Git repo."""
    command = ["git", "-C", str(root), "status", "--short", "--untracked-files=all"]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return ()
    if completed.returncode != 0:
        return ()

    files: list[str] = []
    for raw_line in completed.stdout.splitlines():
        line = raw_line.rstrip()
        if not line or len(line) < 4:
            continue
        path_text = line[3:]
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1]
        path_text = path_text.strip().strip('"')
        if path_text:
            files.append(path_text)
    return tuple(dict.fromkeys(files))
