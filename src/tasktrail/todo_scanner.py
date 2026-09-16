"""Scan source files for TODO-style markers."""

from __future__ import annotations

import re
from pathlib import Path

from tasktrail.config import TaskTrailConfig
from tasktrail.models import Task
from tasktrail.utils import (
    get_changed_files,
    is_probably_binary,
    iter_project_files,
    normalize_space,
    safe_relative,
    slugify,
)


def priority_for_marker(marker: str, text: str, config: TaskTrailConfig) -> str:
    lowered = text.lower()
    if "security" in lowered or "vulnerability" in lowered or "secret" in lowered or "token" in lowered:
        return config.priority_for("security", "critical")
    if marker in {"BUG", "FIXME", "XXX"}:
        return config.priority_for(marker, "high")
    if marker == "HACK":
        return config.priority_for(marker, "medium")
    if marker == "NOTE":
        return config.priority_for(marker, "low")
    return config.priority_for(marker, config.default_priority)


def category_for_marker(marker: str, text: str) -> str:
    lowered = text.lower()
    if "test" in lowered or "coverage" in lowered:
        return "testing"
    if "doc" in lowered or "readme" in lowered:
        return "documentation"
    if "security" in lowered or "secret" in lowered or "auth" in lowered or "token" in lowered:
        return "security"
    if "release" in lowered or "changelog" in lowered or "version" in lowered:
        return "release"
    if "ci" in lowered or "workflow" in lowered or "deploy" in lowered:
        return "automation"
    if marker == "BUG":
        return "bug"
    if marker == "FIXME":
        return "maintenance"
    if marker == "HACK":
        return "cleanup"
    if marker == "NOTE":
        return "documentation"
    return "task"


def title_for_marker(marker: str, body: str) -> str:
    body = normalize_space(body).strip(" .")
    readable = body[:68] if body else "review marker"
    title_prefix = {
        "TODO": "Complete TODO",
        "FIXME": "Fix marked issue",
        "BUG": "Investigate bug marker",
        "HACK": "Clean up workaround",
        "NOTE": "Review note",
        "XXX": "Resolve flagged code",
    }.get(marker, "Review marker")
    return f"{title_prefix}: {readable}"


def build_task_from_marker(root: Path, path: Path, line_number: int, marker: str, body: str, line: str, config: TaskTrailConfig) -> Task:
    relative = safe_relative(path, root)
    cleaned_body = normalize_space(body.strip(" :-\t")) or f"Resolve {marker.lower()} marker"
    category = category_for_marker(marker, cleaned_body)
    priority = priority_for_marker(marker, cleaned_body, config)
    location = f"{relative}:{line_number}"
    labels = tuple(dict.fromkeys((category, priority, marker.lower())))

    return Task(
        title=title_for_marker(marker, cleaned_body),
        description=(
            f"A `{marker}` marker was found in the repository. The note says: "
            f"`{cleaned_body}`. This should be reviewed and converted into completed work, "
            "a documented decision, or a tracked follow-up task."
        ),
        category=category,
        priority=priority,
        labels=labels,
        source="code-marker",
        path=relative,
        line=line_number,
        marker=marker,
        evidence=line.strip(),
        fingerprint=f"marker:{marker.lower()}:{slugify(cleaned_body, 96)}",
        occurrences=(location,),
        suggested_steps=(
            "Review the marked line and understand why it was left in the code.",
            "Decide whether the work should be completed, documented, tested, or removed.",
            "Update the code and remove the marker once the work is finished.",
        ),
    )


def scan_markers(root: Path, config: TaskTrailConfig, changed_only: bool = False) -> tuple[Task, ...]:
    """Scan text files for configured markers."""
    if not config.include_todo_checks or not config.markers:
        return ()

    marker_pattern = "|".join(re.escape(marker) for marker in config.markers)
    comment_prefix = r"^\s*(?:(?:#|//|/\*+|\*|<!--|;|--|REM|::)\s*)?"
    pattern = re.compile(rf"{comment_prefix}({marker_pattern})\b\s*(?::|-)?\s*(.+)$", re.IGNORECASE)
    max_bytes = config.max_file_size_kb * 1024
    tasks: list[Task] = []
    changed_files = get_changed_files(root) if changed_only else None

    for path in iter_project_files(root, config.ignore_dirs, config.ignore_files, changed_files):
        if path.suffix and path.suffix.lower() not in config.text_extensions:
            continue
        try:
            if path.stat().st_size > max_bytes:
                continue
        except OSError:
            continue
        if is_probably_binary(path):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        in_fenced_block = False
        for index, line in enumerate(lines, start=1):
            stripped = line.strip()
            if path.suffix.lower() in {".md", ".rst"} and (stripped.startswith("```") or stripped.startswith("~~~")):
                in_fenced_block = not in_fenced_block
                continue
            if in_fenced_block:
                continue
            match = pattern.search(line)
            if not match:
                continue
            marker = match.group(1).upper()
            if marker in config.ignored_markers:
                continue
            body = match.group(2)
            tasks.append(build_task_from_marker(root, path, index, marker, body, line, config))

    return tuple(tasks)
