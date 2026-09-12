"""Data models used by TaskTrail."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PRIORITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}
VALID_PRIORITIES = tuple(PRIORITY_ORDER.keys())


@dataclass(frozen=True)
class ProjectInfo:
    """Basic detected repository information."""

    root: Path
    name: str
    project_types: tuple[str, ...]
    package_files: tuple[str, ...]

    def display_types(self) -> str:
        return ", ".join(self.project_types) if self.project_types else "general"


@dataclass(frozen=True)
class Task:
    """One actionable task discovered by TaskTrail."""

    title: str
    description: str
    category: str
    priority: str
    labels: tuple[str, ...]
    source: str
    path: str | None = None
    line: int | None = None
    marker: str | None = None
    suggested_steps: tuple[str, ...] = field(default_factory=tuple)
    evidence: str | None = None
    fingerprint: str | None = None
    occurrences: tuple[str, ...] = field(default_factory=tuple)

    @property
    def stable_id(self) -> str:
        """Return a deterministic readable id for the task."""
        base = self.title.lower()
        safe = "".join(ch if ch.isalnum() else "-" for ch in base).strip("-")
        while "--" in safe:
            safe = safe.replace("--", "-")
        prefix = self.category.lower().replace(" ", "-")
        return f"{prefix}-{safe[:48]}"

    @property
    def location(self) -> str:
        if self.occurrences:
            if len(self.occurrences) == 1:
                return self.occurrences[0]
            return f"{self.occurrences[0]} (+{len(self.occurrences) - 1} more)"
        if self.path and self.line:
            return f"{self.path}:{self.line}"
        if self.path:
            return self.path
        return "repository"

    @property
    def all_locations(self) -> tuple[str, ...]:
        if self.occurrences:
            return self.occurrences
        return (self.location,)

    @property
    def occurrence_count(self) -> int:
        return max(1, len(self.all_locations))

    @property
    def dedupe_key(self) -> str:
        if self.fingerprint:
            return self.fingerprint
        return f"{self.source}:{self.category}:{self.title.lower()}"

    def with_occurrences(self, occurrences: tuple[str, ...]) -> "Task":
        return replace(self, occurrences=occurrences)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.stable_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "labels": list(self.labels),
            "source": self.source,
            "path": self.path,
            "line": self.line,
            "marker": self.marker,
            "location": self.location,
            "locations": list(self.all_locations),
            "occurrence_count": self.occurrence_count,
            "evidence": self.evidence,
            "suggested_steps": list(self.suggested_steps),
        }


@dataclass(frozen=True)
class ScanResult:
    """Full output of a TaskTrail scan."""

    project: ProjectInfo
    tasks: tuple[Task, ...]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total(self) -> int:
        return len(self.tasks)

    @property
    def total_occurrences(self) -> int:
        return sum(task.occurrence_count for task in self.tasks)

    def by_priority(self) -> dict[str, int]:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for task in self.tasks:
            counts[task.priority] = counts.get(task.priority, 0) + 1
        return counts

    def by_category(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for task in self.tasks:
            counts[task.category] = counts.get(task.category, 0) + 1
        return dict(sorted(counts.items()))

    def top_priority(self) -> str:
        if not self.tasks:
            return "none"
        return max(self.tasks, key=lambda task: PRIORITY_ORDER.get(task.priority, 0)).priority

    def filtered(self, min_priority: str | None = None, category: str | None = None) -> "ScanResult":
        tasks = list(self.tasks)
        if min_priority:
            minimum = PRIORITY_ORDER[min_priority]
            tasks = [task for task in tasks if PRIORITY_ORDER[task.priority] >= minimum]
        if category:
            tasks = [task for task in tasks if task.category == category]
        return ScanResult(project=self.project, tasks=tuple(tasks), generated_at=self.generated_at)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": {
                "name": self.project.name,
                "root": str(self.project.root),
                "types": list(self.project.project_types),
                "package_files": list(self.project.package_files),
            },
            "generated_at": self.generated_at.isoformat(),
            "summary": {
                "total_tasks": self.total,
                "total_occurrences": self.total_occurrences,
                "top_priority": self.top_priority(),
                "by_priority": self.by_priority(),
                "by_category": self.by_category(),
            },
            "tasks": [task.to_dict() for task in self.tasks],
        }
