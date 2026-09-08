from pathlib import Path

from typer.testing import CliRunner

from tasktrail.cli import app

runner = CliRunner()


def test_cli_scan_runs(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("# TODO: add feature\n", encoding="utf-8")

    result = runner.invoke(app, ["scan", str(tmp_path)])

    assert result.exit_code == 0
    assert "TaskTrail" in result.output


def test_cli_markdown_output(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("# TODO: add feature\n", encoding="utf-8")
    output = tmp_path / "report.md"

    result = runner.invoke(app, ["scan", str(tmp_path), "--format", "markdown", "--output", str(output)])

    assert result.exit_code == 0
    assert output.exists()
    assert "TaskTrail Report" in output.read_text(encoding="utf-8")


def test_cli_init_config(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 0
    assert (tmp_path / ".tasktrail.yaml").exists()


def test_cli_detect(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"name":"demo"}', encoding="utf-8")

    result = runner.invoke(app, ["detect", str(tmp_path)])

    assert result.exit_code == 0
    assert "node" in result.output
