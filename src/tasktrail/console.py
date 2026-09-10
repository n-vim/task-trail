"""Rich terminal rendering."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from tasktrail.models import ScanResult, Task
from tasktrail.reports import build_next_steps

PRIORITY_STYLE = {
    "critical": "bold red",
    "high": "red",
    "medium": "yellow",
    "low": "green",
}


def print_scan_result(console: Console, result: ScanResult) -> None:
    """Print a polished scan summary and task table."""
    priority_counts = result.by_priority()
    category_counts = result.by_category()
    title = Text("TaskTrail", style="bold cyan")
    subtitle = (
        f"Project: {result.project.name}\n"
        f"Type: {result.project.display_types()}\n"
        f"Tasks found: {result.total}\n"
        f"Locations found: {result.total_occurrences}\n"
        f"Top priority: {result.top_priority().title()}"
    )
    border = "green" if result.total == 0 else "cyan"
    if priority_counts.get("critical", 0):
        border = "red"
    console.print(Panel(subtitle, title=title, border_style=border))

    summary = Table(title="Priority summary", show_header=True, header_style="bold")
    summary.add_column("Priority")
    summary.add_column("Count", justify="right")
    for priority in ("critical", "high", "medium", "low"):
        style = PRIORITY_STYLE[priority]
        summary.add_row(f"[{style}]{priority.title()}[/{style}]", str(priority_counts.get(priority, 0)))
    console.print(summary)

    if category_counts:
        category = Table(title="Category summary", show_header=True, header_style="bold")
        category.add_column("Category")
        category.add_column("Count", justify="right")
        for name, count in category_counts.items():
            category.add_row(name, str(count))
        console.print(category)

    next_steps = build_next_steps(result)
    if next_steps:
        console.print(Panel("\n".join(f"- {step}" for step in next_steps), title="Next steps", border_style="blue"))

    if not result.tasks:
        console.print(Panel("No tasks found. The repository looks clean for the enabled checks.", border_style="green"))
        return

    table = Table(title="Tasks", show_lines=False, header_style="bold magenta")
    table.add_column("Priority", no_wrap=True)
    table.add_column("Category", no_wrap=True)
    table.add_column("Title")
    table.add_column("Location")
    table.add_column("Count", justify="right")

    for task in result.tasks:
        style = PRIORITY_STYLE.get(task.priority, "white")
        table.add_row(
            f"[{style}]{task.priority.title()}[/{style}]",
            task.category,
            task.title,
            task.location,
            str(task.occurrence_count),
        )
    console.print(table)


def print_task_details(console: Console, task: Task) -> None:
    """Print one task in a readable panel."""
    steps = "\n".join(f"- {step}" for step in task.suggested_steps)
    locations = "\n".join(f"- {location}" for location in task.all_locations)
    body = (
        f"[bold]Priority:[/bold] {task.priority.title()}\n"
        f"[bold]Category:[/bold] {task.category}\n"
        f"[bold]Occurrences:[/bold] {task.occurrence_count}\n"
        f"[bold]Labels:[/bold] {', '.join(task.labels)}\n\n"
        f"[bold]Locations[/bold]\n{locations}\n\n"
        f"{task.description}\n\n"
        f"[bold]Suggested work[/bold]\n{steps}"
    )
    console.print(Panel(body, title=task.title, border_style="cyan"))
