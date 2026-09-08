from pathlib import Path

from typer.testing import CliRunner

from tasktrail.cli import app
from tasktrail.issue_writer import write_issue_files
from tasktrail.reports import render_board, render_html_report
from tasktrail.scanner import scan_project

runner = CliRunner()


def test_duplicate_markers_are_grouped(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("# TODO: add tests\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("# TODO: add tests\n", encoding="utf-8")

    result = scan_project(tmp_path, markers_only=True)

    assert result.total == 1
    assert result.tasks[0].occurrence_count == 2
    assert "deduplicated" in result.tasks[0].labels


def test_issue_files_are_numbered(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("# FIXME: handle error\n", encoding="utf-8")
    result = scan_project(tmp_path, markers_only=True)

    out = tmp_path / "issues"
    written = write_issue_files(result, out)

    assert written[0].name.startswith("001-")
    assert "## Locations" in written[0].read_text(encoding="utf-8")


def test_html_report_renders(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("# BUG: wrong output\n", encoding="utf-8")
    result = scan_project(tmp_path, markers_only=True)

    html = render_html_report(result)

    assert "<!doctype html>" in html
    assert "TaskTrail Report" in html
    assert "wrong output" in html


def test_board_command_writes_markdown(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("# TODO: improve docs\n", encoding="utf-8")
    output = tmp_path / "BOARD.md"

    result = runner.invoke(app, ["board", str(tmp_path), "--output", str(output)])

    assert result.exit_code == 0
    assert output.exists()
    assert "TaskTrail Board" in output.read_text(encoding="utf-8")


def test_config_can_ignore_note_markers(tmp_path: Path) -> None:
    (tmp_path / ".tasktrail.yaml").write_text(
        "ignore:\n  comments:\n    - NOTE\n",
        encoding="utf-8",
    )
    (tmp_path / "app.py").write_text("# NOTE: document later\n# TODO: add docs\n", encoding="utf-8")

    result = scan_project(tmp_path, markers_only=True)

    assert result.total == 1
    assert result.tasks[0].marker == "TODO"
