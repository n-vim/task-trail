from pathlib import Path

from tasktrail.reports import render_checklist, render_json_report, render_markdown_report
from tasktrail.scanner import scan_project


def test_markdown_report_contains_summary(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("# FIXME: handle error\n", encoding="utf-8")
    result = scan_project(tmp_path, markers_only=True)

    report = render_markdown_report(result)

    assert "# TaskTrail Report" in report
    assert "Fix marked issue" in report


def test_json_report_contains_tasks(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("# BUG: wrong output\n", encoding="utf-8")
    result = scan_project(tmp_path, markers_only=True)

    report = render_json_report(result)

    assert '"tasks"' in report
    assert '"BUG"' in report


def test_checklist_contains_checkbox(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("# TODO: write tests\n", encoding="utf-8")
    result = scan_project(tmp_path, markers_only=True)

    checklist = render_checklist(result)

    assert "- [ ]" in checklist
