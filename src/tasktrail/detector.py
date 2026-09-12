"""Project detection logic."""

from __future__ import annotations

from pathlib import Path

from tasktrail.models import ProjectInfo


def detect_project(root: Path) -> ProjectInfo:
    """Detect basic project details from known files."""
    types: list[str] = []
    package_files: list[str] = []

    checks = {
        "python": ("pyproject.toml", "setup.py", "requirements.txt", "Pipfile"),
        "node": ("package.json", "npm-shrinkwrap.json"),
        "go": ("go.mod",),
        "rust": ("Cargo.toml",),
        "php": ("composer.json",),
        "docker": ("Dockerfile", "docker-compose.yml", "compose.yml"),
    }

    for project_type, filenames in checks.items():
        matched = [name for name in filenames if (root / name).exists()]
        if matched:
            types.append(project_type)
            package_files.extend(matched)

    if (root / ".github" / "workflows").exists():
        types.append("github-actions")

    if not types:
        types.append("general")

    return ProjectInfo(
        root=root,
        name=root.name,
        project_types=tuple(dict.fromkeys(types)),
        package_files=tuple(dict.fromkeys(package_files)),
    )
