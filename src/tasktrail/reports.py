"""Report rendering for TaskTrail."""

from __future__ import annotations

import html
import json

from tasktrail.models import ScanResult, Task


def render_markdown_report(result: ScanResult) -> str:
    """Render a full Markdown report."""
    priority = result.by_priority()
    category = result.by_category()
    lines = [
        f"# TaskTrail Report: {result.project.name}",
        "",
        f"Generated at: `{result.generated_at.isoformat()}`",
        f"Project types: `{result.project.display_types()}`",
        "",
        "## Summary",
        "",
        f"Total tasks: **{result.total}**",
        f"Total locations: **{result.total_occurrences}**",
        f"Top priority: **{result.top_priority().title()}**",
        "",
        "### By priority",
        "",
        "| Priority | Count |",
        "| --- | ---: |",
    ]
    for key in ("critical", "high", "medium", "low"):
        lines.append(f"| {key.title()} | {priority.get(key, 0)} |")

    lines.extend(["", "### By category", "", "| Category | Count |", "| --- | ---: |"])
    for name, count in category.items():
        lines.append(f"| {name} | {count} |")

    next_steps = build_next_steps(result)
    if next_steps:
        lines.extend(["", "## Suggested next steps", ""])
        lines.extend(f"- {step}" for step in next_steps)

    lines.extend(["", "## Tasks", ""])
    if not result.tasks:
        lines.append("No tasks were found. The repository looks clean based on the enabled checks.")
    else:
        for index, task in enumerate(result.tasks, start=1):
            lines.extend(render_task_summary(index, task))
    return "\n".join(lines).rstrip() + "\n"


def render_task_summary(index: int, task: Task) -> list[str]:
    lines = [
        f"### {index}. {task.title}",
        "",
        f"- Priority: **{task.priority.title()}**",
        f"- Category: `{task.category}`",
        f"- Source: `{task.source}`",
        f"- Location: `{task.location}`",
        f"- Occurrences: **{task.occurrence_count}**",
        f"- Labels: {', '.join(task.labels)}",
        "",
        task.description,
        "",
    ]
    if task.occurrence_count > 1:
        lines.extend(["Locations:", ""])
        lines.extend(f"- `{location}`" for location in task.all_locations)
        lines.append("")
    if task.evidence:
        lines.extend(["Evidence:", "", "```text", task.evidence, "```", ""])
    if task.suggested_steps:
        lines.extend(["Suggested work:", ""])
        lines.extend(f"- {step}" for step in task.suggested_steps)
        lines.append("")
    return lines


def render_checklist(result: ScanResult) -> str:
    """Render tasks as a project checklist."""
    lines = [f"# TaskTrail Checklist: {result.project.name}", ""]
    if not result.tasks:
        lines.append("- [x] No tasks found by TaskTrail")
        return "\n".join(lines) + "\n"

    current_category = None
    for task in result.tasks:
        if task.category != current_category:
            current_category = task.category
            lines.extend(["", f"## {current_category.title()}", ""])
        lines.append(f"- [ ] **[{task.priority.title()}]** {task.title} (`{task.location}`)")
    return "\n".join(lines).strip() + "\n"


def render_board(result: ScanResult) -> str:
    """Render a lightweight Markdown kanban board."""
    critical_or_high = [task for task in result.tasks if task.priority in {"critical", "high"}]
    medium = [task for task in result.tasks if task.priority == "medium"]
    low = [task for task in result.tasks if task.priority == "low"]

    lines = [f"# TaskTrail Board: {result.project.name}", ""]
    columns = (
        ("Backlog", low),
        ("To Do", medium),
        ("Needs Attention", critical_or_high),
        ("Done", []),
    )
    for heading, tasks in columns:
        lines.extend([f"## {heading}", ""])
        if not tasks:
            lines.append("- No tasks")
        else:
            for task in tasks:
                lines.append(f"- **[{task.priority.title()}]** {task.title} (`{task.category}`)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_json_report(result: ScanResult) -> str:
    """Render a JSON report."""
    return json.dumps(result.to_dict(), indent=2, sort_keys=False) + "\n"


def build_next_steps(result: ScanResult) -> tuple[str, ...]:
    if not result.tasks:
        return ("Keep the repository clean and run TaskTrail again before major changes.",)
    steps: list[str] = []
    priorities = result.by_priority()
    categories = result.by_category()
    if priorities.get("critical", 0):
        steps.append("Start with critical security or release-blocking tasks.")
    if categories.get("testing", 0):
        steps.append("Add or improve tests before large refactors.")
    if categories.get("documentation", 0):
        steps.append("Improve documentation so visitors can understand and use the project.")
    if categories.get("automation", 0) or categories.get("workflow", 0):
        steps.append("Add workflow automation to keep future changes safer.")
    return tuple(steps[:4])


def render_html_report(result: ScanResult) -> str:
    """Render a standalone HTML report."""
    priority = result.by_priority()
    category = result.by_category()
    task_cards = []
    for task in result.tasks:
        locations = "".join(f"<li><code>{html.escape(location)}</code></li>" for location in task.all_locations)
        steps = "".join(f"<li>{html.escape(step)}</li>" for step in task.suggested_steps)
        evidence = f"<pre>{html.escape(task.evidence)}</pre>" if task.evidence else ""
        task_cards.append(
            f"""
            <article class="task {html.escape(task.priority)}">
              <h3>{html.escape(task.title)}</h3>
              <p>{html.escape(task.description)}</p>
              <div class="meta">
                <span>{html.escape(task.priority.title())}</span>
                <span>{html.escape(task.category)}</span>
                <span>{task.occurrence_count} location(s)</span>
              </div>
              <h4>Locations</h4>
              <ul>{locations}</ul>
              {evidence}
              <h4>Suggested work</h4>
              <ul>{steps}</ul>
            </article>
            """
        )

    priority_rows = "".join(f"<tr><td>{key.title()}</td><td>{priority.get(key, 0)}</td></tr>" for key in ("critical", "high", "medium", "low"))
    category_rows = "".join(f"<tr><td>{html.escape(name)}</td><td>{count}</td></tr>" for name, count in category.items())
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TaskTrail Report - {html.escape(result.project.name)}</title>
  <style>
    body {{ font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f7f8fb; color: #172033; }}
    header {{ background: #101827; color: white; padding: 48px 24px; }}
    main {{ max-width: 1040px; margin: 0 auto; padding: 28px 20px 64px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }}
    .card, .task {{ background: white; border: 1px solid #e6e8ef; border-radius: 16px; padding: 20px; box-shadow: 0 10px 24px rgba(16,24,39,0.06); }}
    .score {{ font-size: 42px; font-weight: 800; margin: 0; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 10px; border-bottom: 1px solid #edf0f5; text-align: left; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }}
    .meta span {{ background: #edf2ff; color: #1d3b8b; border-radius: 999px; padding: 5px 10px; font-size: 13px; }}
    .critical {{ border-left: 6px solid #dc2626; }}
    .high {{ border-left: 6px solid #f97316; }}
    .medium {{ border-left: 6px solid #eab308; }}
    .low {{ border-left: 6px solid #16a34a; }}
    pre {{ background: #101827; color: #f8fafc; padding: 14px; border-radius: 12px; overflow: auto; }}
    code {{ background: #eef2f7; padding: 2px 5px; border-radius: 6px; }}
  </style>
</head>
<body>
  <header>
    <h1>TaskTrail Report</h1>
    <p>Project: {html.escape(result.project.name)} | Types: {html.escape(result.project.display_types())}</p>
  </header>
  <main>
    <section class="grid">
      <div class="card"><p>Total tasks</p><p class="score">{result.total}</p></div>
      <div class="card"><p>Total locations</p><p class="score">{result.total_occurrences}</p></div>
      <div class="card"><p>Top priority</p><p class="score">{html.escape(result.top_priority().title())}</p></div>
    </section>
    <section class="grid" style="margin-top: 20px;">
      <div class="card"><h2>By priority</h2><table>{priority_rows}</table></div>
      <div class="card"><h2>By category</h2><table>{category_rows}</table></div>
    </section>
    <section style="margin-top: 24px;">
      <h2>Tasks</h2>
      {''.join(task_cards) if task_cards else '<div class="card">No tasks found.</div>'}
    </section>
  </main>
</body>
</html>
"""
