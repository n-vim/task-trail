"""GitHub issue Markdown generation."""

from __future__ import annotations

from pathlib import Path

from tasktrail.models import ScanResult, Task
from tasktrail.utils import ensure_parent, slugify


def render_issue(task: Task) -> str:
    """Render one Task as a GitHub-ready issue description."""
    labels = ", ".join(task.labels)
    steps = "\n".join(f"- {step}" for step in task.suggested_steps) or "- Review and complete this task."
    evidence = f"\n## Evidence\n\n```text\n{task.evidence}\n```\n" if task.evidence else ""
    locations = "\n".join(f"- `{location}`" for location in task.all_locations)

    return f"""## Description

{task.description}

## Locations

{locations}
{evidence}
## Suggested work

{steps}

## Priority

{task.priority.title()}

## Labels

{labels}
""".strip() + "\n"


def issue_filename(task: Task, index: int | None = None) -> str:
    prefix = f"{index:03d}-" if index is not None else ""
    return f"{prefix}{slugify(task.title)}.md"


def render_issue_collection(result: ScanResult) -> str:
    """Render all tasks into a single Markdown issue list."""
    lines = [
        f"# TaskTrail Issues for {result.project.name}",
        "",
        f"Generated tasks: **{result.total}**",
        f"Total locations: **{result.total_occurrences}**",
        "",
    ]
    for index, task in enumerate(result.tasks, start=1):
        lines.extend(
            [
                f"## {index}. {task.title}",
                "",
                f"- Priority: **{task.priority.title()}**",
                f"- Category: `{task.category}`",
                f"- Location: `{task.location}`",
                f"- Occurrences: **{task.occurrence_count}**",
                f"- Labels: {', '.join(task.labels)}",
                "",
                task.description,
                "",
            ]
        )
        if task.occurrence_count > 1:
            lines.extend(["### Locations", ""])
            lines.extend(f"- `{location}`" for location in task.all_locations)
            lines.append("")
        lines.extend(["### Suggested work", ""])
        lines.extend(f"- {step}" for step in task.suggested_steps)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_issue_files(result: ScanResult, output_dir: Path, force: bool = False) -> list[Path]:
    """Write each task as an individual Markdown issue file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for index, task in enumerate(result.tasks, start=1):
        target = output_dir / issue_filename(task, index)
        if target.exists() and not force:
            continue
        target.write_text(render_issue(task), encoding="utf-8")
        written.append(target)
    return written


def write_single_issue_file(result: ScanResult, output: Path, force: bool = False) -> Path:
    if output.exists() and not force:
        raise FileExistsError(f"Output already exists: {output}")
    ensure_parent(output)
    output.write_text(render_issue_collection(result), encoding="utf-8")
    return output
