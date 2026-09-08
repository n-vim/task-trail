from pathlib import Path

from tasktrail.config import TaskTrailConfig
from tasktrail.todo_scanner import scan_markers


def test_scan_markers_finds_todo(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text("# TODO: add validation\nprint('ok')\n", encoding="utf-8")

    tasks = scan_markers(tmp_path, TaskTrailConfig())

    assert len(tasks) == 1
    assert tasks[0].marker == "TODO"
    assert tasks[0].path == "app.py"
    assert tasks[0].line == 1


def test_scan_markers_skips_binary(tmp_path: Path) -> None:
    binary = tmp_path / "bad.py"
    binary.write_bytes(b"\x00TODO secret")

    tasks = scan_markers(tmp_path, TaskTrailConfig())

    assert tasks == ()


def test_security_marker_becomes_critical(tmp_path: Path) -> None:
    source = tmp_path / "settings.py"
    source.write_text("# TODO: remove secret token handling\n", encoding="utf-8")

    tasks = scan_markers(tmp_path, TaskTrailConfig())

    assert tasks[0].priority == "critical"
    assert tasks[0].category == "security"


def test_markdown_code_fences_are_ignored(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text("```python\n# TODO: example only\n```\n", encoding="utf-8")

    tasks = scan_markers(tmp_path, TaskTrailConfig())

    assert tasks == ()
