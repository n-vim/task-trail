from pathlib import Path

from tasktrail.detector import detect_project


def test_detect_python_project(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    project = detect_project(tmp_path)
    assert "python" in project.project_types
    assert "pyproject.toml" in project.package_files


def test_detect_general_project(tmp_path: Path) -> None:
    project = detect_project(tmp_path)
    assert project.project_types == ("general",)
