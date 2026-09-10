"""Configuration loading for TaskTrail."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_MARKERS = ("TODO", "FIXME", "BUG", "HACK", "NOTE", "XXX")
DEFAULT_IGNORE_DIRS = (
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    "dist",
    "build",
    "coverage",
    "htmlcov",
    ".next",
    ".nuxt",
    "target",
)
DEFAULT_IGNORE_FILES = (
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "uv.lock",
    "Cargo.lock",
)
DEFAULT_TEXT_EXTENSIONS = (
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".php",
    ".rb",
    ".sh",
    ".bash",
    ".zsh",
    ".md",
    ".rst",
    ".txt",
    ".yml",
    ".yaml",
    ".toml",
    ".json",
    ".ini",
    ".cfg",
    ".html",
    ".css",
    ".scss",
)


def _tuple(value: Any, default: tuple[str, ...]) -> tuple[str, ...]:
    if value is None:
        return default
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list | tuple):
        return tuple(str(item) for item in value)
    return default


def _mapping(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key).lower(): str(item).lower() for key, item in value.items()}


@dataclass(frozen=True)
class TaskTrailConfig:
    """User-configurable TaskTrail behavior."""

    markers: tuple[str, ...] = DEFAULT_MARKERS
    ignored_markers: tuple[str, ...] = ()
    ignore_dirs: tuple[str, ...] = DEFAULT_IGNORE_DIRS
    ignore_files: tuple[str, ...] = DEFAULT_IGNORE_FILES
    text_extensions: tuple[str, ...] = DEFAULT_TEXT_EXTENSIONS
    max_file_size_kb: int = 512
    include_repo_checks: bool = True
    include_todo_checks: bool = True
    default_priority: str = "medium"
    github_labels: bool = True
    dedupe: bool = True
    priority_overrides: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "TaskTrailConfig":
        ignore_data = data.get("ignore", {}) if isinstance(data.get("ignore", {}), dict) else {}
        check_data = data.get("checks", {}) if isinstance(data.get("checks", {}), dict) else {}

        ignored_markers = _tuple(
            data.get("ignored_markers", ignore_data.get("comments")),
            (),
        )
        markers = tuple(
            marker.upper()
            for marker in _tuple(data.get("markers"), DEFAULT_MARKERS)
            if marker.upper() not in {item.upper() for item in ignored_markers}
        )

        priority_overrides: dict[str, str] = {}
        priority_overrides.update(_mapping(data.get("priority_overrides")))
        priority_overrides.update(_mapping(data.get("priorities")))

        return cls(
            markers=markers,
            ignored_markers=tuple(item.upper() for item in ignored_markers),
            ignore_dirs=_tuple(data.get("ignore_dirs", ignore_data.get("paths")), DEFAULT_IGNORE_DIRS),
            ignore_files=_tuple(data.get("ignore_files", ignore_data.get("files")), DEFAULT_IGNORE_FILES),
            text_extensions=_tuple(data.get("text_extensions"), DEFAULT_TEXT_EXTENSIONS),
            max_file_size_kb=int(data.get("max_file_size_kb", 512)),
            include_repo_checks=bool(check_data.get("repo", data.get("include_repo_checks", True))),
            include_todo_checks=bool(check_data.get("markers", data.get("include_todo_checks", True))),
            default_priority=str(data.get("default_priority", "medium")).lower(),
            github_labels=bool(data.get("github_labels", True)),
            dedupe=bool(data.get("dedupe", True)),
            priority_overrides=priority_overrides,
        )

    def priority_for(self, key: str, fallback: str) -> str:
        return self.priority_overrides.get(key.lower(), fallback)

    def to_yaml(self) -> str:
        data = {
            "markers": list(self.markers),
            "ignore": {
                "paths": list(self.ignore_dirs),
                "files": list(self.ignore_files),
                "comments": list(self.ignored_markers),
            },
            "text_extensions": list(self.text_extensions),
            "max_file_size_kb": self.max_file_size_kb,
            "checks": {
                "repo": self.include_repo_checks,
                "markers": self.include_todo_checks,
            },
            "dedupe": self.dedupe,
            "default_priority": self.default_priority,
            "github_labels": self.github_labels,
            "priorities": self.priority_overrides,
        }
        return yaml.safe_dump(data, sort_keys=False)


def load_config(root: Path) -> TaskTrailConfig:
    """Load .tasktrail.yaml from a repository root when available."""
    config_path = root / ".tasktrail.yaml"
    if not config_path.exists():
        return TaskTrailConfig()

    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError(".tasktrail.yaml must contain a YAML mapping")
    return TaskTrailConfig.from_mapping(loaded)


def write_default_config(root: Path, force: bool = False) -> Path:
    """Create a default TaskTrail config file."""
    target = root / ".tasktrail.yaml"
    if target.exists() and not force:
        raise FileExistsError(".tasktrail.yaml already exists. Use --force to overwrite it.")
    target.write_text(TaskTrailConfig().to_yaml(), encoding="utf-8")
    return target
