"""Command-line interface for TaskTrail."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from tasktrail import __version__
from tasktrail.config import load_config, write_default_config
from tasktrail.console import print_scan_result, print_task_details
from tasktrail.detector import detect_project
from tasktrail.issue_writer import render_issue_collection, write_issue_files, write_single_issue_file
from tasktrail.models import PRIORITY_ORDER
from tasktrail.reports import (
    render_board,
    render_checklist,
    render_html_report,
    render_json_report,
    render_markdown_report,
)
from tasktrail.scanner import scan_project
from tasktrail.utils import ensure_parent, resolve_root

app = typer.Typer(
    name="tasktrail",
    help="Turn repository TODOs, gaps, and cleanup work into GitHub-ready tasks.",
    add_completion=False,
    invoke_without_command=True,
)
console = Console()


class OutputFormat(str, Enum):
    table = "table"
    markdown = "markdown"
    json = "json"
    html = "html"


class ExportFormat(str, Enum):
    markdown = "markdown"
    json = "json"
    html = "html"


class Priority(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", help="Show the installed TaskTrail version."),
) -> None:
    if version:
        console.print(f"TaskTrail {__version__}")
        raise typer.Exit()


def _render(result_format: OutputFormat | ExportFormat, result: object) -> str:
    if result_format.value == "markdown":
        return render_markdown_report(result)  # type: ignore[arg-type]
    if result_format.value == "json":
        return render_json_report(result)  # type: ignore[arg-type]
    if result_format.value == "html":
        return render_html_report(result)  # type: ignore[arg-type]
    raise ValueError(f"Unsupported output format: {result_format}")


@app.command()
def scan(
    path: Path = typer.Argument(Path("."), help="Repository path to scan."),
    output_format: OutputFormat = typer.Option(OutputFormat.table, "--format", "-f", help="Output format."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write report to a file."),
    markers_only: bool = typer.Option(False, "--markers-only", help="Only scan TODO-style code markers."),
    repo_only: bool = typer.Option(False, "--repo-only", help="Only run repository-level checks."),
    changed: bool = typer.Option(False, "--changed", help="Only scan files changed according to Git for marker checks."),
    dedupe: bool = typer.Option(True, "--dedupe/--no-dedupe", help="Group duplicate tasks into one task."),
    min_priority: Optional[Priority] = typer.Option(None, "--min-priority", help="Only show tasks at or above this priority."),
    category: Optional[str] = typer.Option(None, "--category", help="Only show tasks from one category."),
) -> None:
    """Scan a repository and show discovered tasks."""
    result = scan_project(path, markers_only=markers_only, repo_only=repo_only, changed_only=changed, dedupe=dedupe)
    if min_priority or category:
        result = result.filtered(min_priority.value if min_priority else None, category)

    if output_format == OutputFormat.table:
        if output:
            raise typer.BadParameter("Use --format markdown, json, or html when writing to --output.")
        print_scan_result(console, result)
        return

    rendered = _render(output_format, result)
    if output:
        ensure_parent(output)
        output.write_text(rendered, encoding="utf-8")
        console.print(f"[green]Report written to[/green] {output}")
    else:
        console.print(rendered)


@app.command()
def todos(
    path: Path = typer.Argument(Path("."), help="Repository path to scan."),
    min_priority: Optional[Priority] = typer.Option(None, "--min-priority", help="Only show tasks at or above this priority."),
    changed: bool = typer.Option(False, "--changed", help="Only scan changed files according to Git."),
    dedupe: bool = typer.Option(True, "--dedupe/--no-dedupe", help="Group duplicate markers."),
) -> None:
    """Scan only TODO, FIXME, BUG, HACK, NOTE, and XXX markers."""
    result = scan_project(path, markers_only=True, changed_only=changed, dedupe=dedupe)
    if min_priority:
        result = result.filtered(min_priority.value)
    print_scan_result(console, result)


@app.command()
def gaps(
    path: Path = typer.Argument(Path("."), help="Repository path to scan."),
) -> None:
    """Scan only missing repository essentials."""
    result = scan_project(path, repo_only=True)
    print_scan_result(console, result)


@app.command()
def issues(
    path: Path = typer.Argument(Path("."), help="Repository path to scan."),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", help="Write one Markdown issue per task."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write all issues into one Markdown file."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing generated issue files."),
    changed: bool = typer.Option(False, "--changed", help="Only scan changed files for marker checks."),
    dedupe: bool = typer.Option(True, "--dedupe/--no-dedupe", help="Group duplicate tasks."),
    min_priority: Optional[Priority] = typer.Option(None, "--min-priority", help="Only export tasks at or above this priority."),
) -> None:
    """Generate GitHub-ready issue descriptions."""
    result = scan_project(path, changed_only=changed, dedupe=dedupe)
    if min_priority:
        result = result.filtered(min_priority.value)

    if output_dir and output:
        raise typer.BadParameter("Use either --output-dir or --output, not both.")

    if output_dir:
        written = write_issue_files(result, output_dir, force=force)
        console.print(f"[green]Wrote {len(written)} issue files to[/green] {output_dir}")
        return

    if output:
        write_single_issue_file(result, output, force=force)
        console.print(f"[green]Issue collection written to[/green] {output}")
        return

    console.print(render_issue_collection(result))


@app.command()
def checklist(
    path: Path = typer.Argument(Path("."), help="Repository path to scan."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write checklist to a file."),
    min_priority: Optional[Priority] = typer.Option(None, "--min-priority", help="Only include tasks at or above this priority."),
    changed: bool = typer.Option(False, "--changed", help="Only scan changed files for marker checks."),
) -> None:
    """Generate a Markdown checklist from discovered tasks."""
    result = scan_project(path, changed_only=changed)
    if min_priority:
        result = result.filtered(min_priority.value)
    rendered = render_checklist(result)
    if output:
        ensure_parent(output)
        output.write_text(rendered, encoding="utf-8")
        console.print(f"[green]Checklist written to[/green] {output}")
    else:
        console.print(rendered)


@app.command()
def board(
    path: Path = typer.Argument(Path("."), help="Repository path to scan."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write board to a Markdown file."),
    changed: bool = typer.Option(False, "--changed", help="Only scan changed files for marker checks."),
) -> None:
    """Generate a Markdown kanban board from discovered tasks."""
    result = scan_project(path, changed_only=changed)
    rendered = render_board(result)
    if output:
        ensure_parent(output)
        output.write_text(rendered, encoding="utf-8")
        console.print(f"[green]Board written to[/green] {output}")
    else:
        console.print(rendered)


@app.command()
def export(
    path: Path = typer.Argument(Path("."), help="Repository path to scan."),
    output_format: ExportFormat = typer.Option(ExportFormat.markdown, "--format", "-f", help="Export format."),
    output: Path = typer.Option(..., "--output", "-o", help="Output file path."),
    min_priority: Optional[Priority] = typer.Option(None, "--min-priority", help="Only export tasks at or above this priority."),
    changed: bool = typer.Option(False, "--changed", help="Only scan changed files for marker checks."),
) -> None:
    """Export a full report as Markdown, JSON, or HTML."""
    result = scan_project(path, changed_only=changed)
    if min_priority:
        result = result.filtered(min_priority.value)
    rendered = _render(output_format, result)
    ensure_parent(output)
    output.write_text(rendered, encoding="utf-8")
    console.print(f"[green]Export written to[/green] {output}")


@app.command()
def show(
    path: Path = typer.Argument(Path("."), help="Repository path to scan."),
    task_id: str = typer.Argument(..., help="Task id shown in reports."),
) -> None:
    """Show details for a single generated task."""
    result = scan_project(path)
    for task in result.tasks:
        if task.stable_id == task_id:
            print_task_details(console, task)
            return
    console.print(f"[red]Task not found:[/red] {task_id}")
    raise typer.Exit(code=1)


@app.command()
def detect(
    path: Path = typer.Argument(Path("."), help="Repository path to inspect."),
) -> None:
    """Detect repository type and package files."""
    root = resolve_root(path)
    project = detect_project(root)
    table = Table(title="Detected project")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Name", project.name)
    table.add_row("Types", project.display_types())
    table.add_row("Package files", ", ".join(project.package_files) or "none")
    console.print(table)


@app.command(name="init")
def init_config(
    path: Path = typer.Argument(Path("."), help="Repository path."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing config."),
) -> None:
    """Create a .tasktrail.yaml config file."""
    root = resolve_root(path)
    try:
        target = write_default_config(root, force=force)
    except FileExistsError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Config written to[/green] {target}")


@app.command()
def config(
    path: Path = typer.Argument(Path("."), help="Repository path."),
) -> None:
    """Print the active TaskTrail config."""
    root = resolve_root(path)
    try:
        active = load_config(root)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(active.to_yaml())


@app.command()
def priorities() -> None:
    """List supported priority levels."""
    table = Table(title="Priority levels")
    table.add_column("Priority")
    table.add_column("Weight")
    for name, value in sorted(PRIORITY_ORDER.items(), key=lambda item: -item[1]):
        table.add_row(name, str(value))
    console.print(table)


if __name__ == "__main__":
    app()
