from pathlib import Path

from tasktrail.config import TaskTrailConfig
from tasktrail.repo_checks import scan_repository_gaps


def test_repo_checks_create_missing_tasks(tmp_path: Path) -> None:
    tasks = scan_repository_gaps(tmp_path, TaskTrailConfig())
    titles = {task.title for task in tasks}

    assert "Add a project README" in titles
    assert "Add a license file" in titles
    assert "Add a test suite" in titles


def test_repo_checks_respect_existing_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(".venv\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text("name: CI\n", encoding="utf-8")

    tasks = scan_repository_gaps(tmp_path, TaskTrailConfig())
    titles = {task.title for task in tasks}

    assert "Add a project README" not in titles
    assert "Add a license file" not in titles
    assert "Add a test suite" not in titles
    assert "Add continuous integration workflow" not in titles
