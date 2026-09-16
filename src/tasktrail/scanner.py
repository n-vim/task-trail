"""High-level scan orchestration."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from tasktrail.config import TaskTrailConfig, load_config
from tasktrail.detector import detect_project
from tasktrail.models import PRIORITY_ORDER, ScanResult, Task
from tasktrail.repo_checks import scan_repository_gaps
from tasktrail.todo_scanner import scan_markers
from tasktrail.utils import resolve_root


def sort_tasks(tasks: list[Task]) -> tuple[Task, ...]:
    """Sort tasks by priority, category, and location."""
    return tuple(
        sorted(
            tasks,
            key=lambda task: (
                -PRIORITY_ORDER.get(task.priority, 0),
                task.category,
                task.path or "",
                task.line or 0,
                task.title,
            ),
        )
    )


def deduplicate_tasks(tasks: list[Task]) -> list[Task]:
    """Merge repeated tasks while preserving all locations."""
    grouped: dict[str, Task] = {}
    locations: dict[str, list[str]] = {}

    for task in tasks:
        key = task.dedupe_key
        if key not in grouped:
            grouped[key] = task
            locations[key] = []
        for location in task.all_locations:
            if location not in locations[key]:
                locations[key].append(location)

        current = grouped[key]
        if PRIORITY_ORDER.get(task.priority, 0) > PRIORITY_ORDER.get(current.priority, 0):
            grouped[key] = task

    merged: list[Task] = []
    for key, task in grouped.items():
        all_locations = tuple(locations[key])
        if len(all_locations) <= 1:
            merged.append(task.with_occurrences(all_locations))
            continue
        description = task.description
        if task.source == "code-marker":
            description += f" It appears in {len(all_locations)} locations, so it has been grouped into one task."
        labels = tuple(dict.fromkeys((*task.labels, "deduplicated")))
        merged.append(replace(task, description=description, labels=labels, occurrences=all_locations))
    return merged


def scan_project(
    path: str | Path,
    config: TaskTrailConfig | None = None,
    markers_only: bool = False,
    repo_only: bool = False,
    changed_only: bool = False,
    dedupe: bool | None = None,
) -> ScanResult:
    """Scan a repository and return actionable tasks."""
    root = resolve_root(path)
    final_config = config or load_config(root)
    project = detect_project(root)

    tasks: list[Task] = []
    if not repo_only:
        tasks.extend(scan_markers(root, final_config, changed_only=changed_only))
    if not markers_only:
        tasks.extend(scan_repository_gaps(root, final_config))

    should_dedupe = final_config.dedupe if dedupe is None else dedupe
    if should_dedupe:
        tasks = deduplicate_tasks(tasks)

    return ScanResult(project=project, tasks=sort_tasks(tasks))
