from pathlib import Path

from tasktrail.issue_writer import render_issue, write_issue_files
from tasktrail.scanner import scan_project


def test_render_issue_is_github_ready(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("# TODO: improve docs\n", encoding="utf-8")
    result = scan_project(tmp_path, markers_only=True)

    issue = render_issue(result.tasks[0])

    assert "## Description" in issue
    assert "## Suggested work" in issue
    assert "## Labels" in issue


def test_write_issue_files(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text("# TODO: improve docs\n", encoding="utf-8")
    result = scan_project(project, markers_only=True)

    output = tmp_path / "issues"
    written = write_issue_files(result, output)

    assert len(written) == 1
    assert written[0].exists()
