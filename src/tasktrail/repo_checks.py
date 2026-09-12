"""Repository-level task generation."""

from __future__ import annotations

from pathlib import Path

from tasktrail.config import TaskTrailConfig
from tasktrail.models import Task

SENSITIVE_FILE_NAMES = (
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_dsa",
    "credentials.json",
    "secrets.json",
)
SENSITIVE_SUFFIXES = (".pem", ".key", ".p12", ".pfx")


def exists_any(root: Path, names: tuple[str, ...]) -> bool:
    return any((root / name).exists() for name in names)


def has_tests(root: Path) -> bool:
    if (root / "tests").exists() or (root / "test").exists() or (root / "__tests__").exists():
        return True
    patterns = ("test_*.py", "*_test.py", "*.test.js", "*.spec.js", "*.test.ts", "*.spec.ts")
    return any(any(root.rglob(pattern)) for pattern in patterns)


def has_ci(root: Path) -> bool:
    workflows = root / ".github" / "workflows"
    if not workflows.exists():
        return False
    return any(workflows.glob("*.yml")) or any(workflows.glob("*.yaml"))


def has_issue_templates(root: Path) -> bool:
    folder = root / ".github" / "ISSUE_TEMPLATE"
    return folder.exists() and any(folder.glob("*.md"))


def has_pr_template(root: Path) -> bool:
    return exists_any(root, (".github/pull_request_template.md", "pull_request_template.md", "PULL_REQUEST_TEMPLATE.md"))


def find_sensitive_files(root: Path) -> tuple[str, ...]:
    found: list[str] = []
    for name in SENSITIVE_FILE_NAMES:
        if (root / name).exists():
            found.append(name)
    for path in root.glob("**/*"):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.suffix.lower() in SENSITIVE_SUFFIXES:
            try:
                found.append(path.relative_to(root).as_posix())
            except ValueError:
                found.append(path.as_posix())
    return tuple(dict.fromkeys(found))


def missing_task(
    title: str,
    description: str,
    category: str,
    priority: str,
    labels: tuple[str, ...],
    steps: tuple[str, ...],
    path: str | None = None,
) -> Task:
    return Task(
        title=title,
        description=description,
        category=category,
        priority=priority,
        labels=labels,
        source="repository-check",
        path=path,
        fingerprint=f"repo:{category}:{title.lower()}",
        occurrences=(path or "repository",),
        suggested_steps=steps,
    )


def scan_repository_gaps(root: Path, config: TaskTrailConfig) -> tuple[Task, ...]:
    """Create tasks for missing repository essentials."""
    if not config.include_repo_checks:
        return ()

    tasks: list[Task] = []

    sensitive_files = find_sensitive_files(root)
    if sensitive_files:
        tasks.append(
            Task(
                title="Review sensitive files before publishing",
                description=(
                    "Potentially sensitive files were found in the repository. TaskTrail does not read or print "
                    "their contents, but these files should be reviewed before pushing or releasing the project."
                ),
                category="security",
                priority=config.priority_for("security", "critical"),
                labels=("security", "critical"),
                source="repository-check",
                path=sensitive_files[0],
                fingerprint="repo:security:sensitive-files",
                occurrences=sensitive_files,
                evidence="Potentially sensitive file names detected only. File contents were not included.",
                suggested_steps=(
                    "Confirm whether each file should be tracked in Git.",
                    "Move real secrets to local environment variables or a secret manager.",
                    "Add safe examples such as .env.example instead of committing real values.",
                    "Rotate any secret that may have been committed by mistake.",
                ),
            )
        )

    if not exists_any(root, ("README.md", "README.rst", "README.txt")):
        tasks.append(
            missing_task(
                "Add a project README",
                "The repository does not include a README file. A README helps visitors understand what the project does, how to install it, and how to use it.",
                "documentation",
                config.priority_for("documentation", "high"),
                ("documentation", "high"),
                (
                    "Create a README.md file at the repository root.",
                    "Explain the project purpose, installation, usage, commands, development setup, and license.",
                    "Keep the content clear, specific, and useful for GitHub visitors.",
                ),
                "README.md",
            )
        )

    if not exists_any(root, ("LICENSE", "LICENSE.md", "COPYING")):
        tasks.append(
            missing_task(
                "Add a license file",
                "The repository does not include a license file. A license tells users how they are allowed to use, modify, and distribute the project.",
                "legal",
                "high",
                ("license", "high"),
                (
                    "Choose an appropriate open-source license.",
                    "Add the license text to a LICENSE file.",
                    "Mention the license in the README.",
                ),
                "LICENSE",
            )
        )

    if not exists_any(root, (".gitignore",)):
        tasks.append(
            missing_task(
                "Add a .gitignore file",
                "The repository does not include a .gitignore file. This can cause cache files, local environments, and build output to be committed accidentally.",
                "cleanup",
                "medium",
                ("cleanup", "medium"),
                (
                    "Create a .gitignore file for the project language.",
                    "Ignore virtual environments, caches, build output, editor files, and local secrets.",
                    "Review the current repository for files that should not be tracked.",
                ),
                ".gitignore",
            )
        )

    if not has_tests(root):
        tasks.append(
            missing_task(
                "Add a test suite",
                "No test folder or common test files were found. Tests make the project safer to change and easier to maintain.",
                "testing",
                config.priority_for("testing", "high"),
                ("testing", "high"),
                (
                    "Create a tests folder or use the standard test layout for the project language.",
                    "Add tests for core behavior and important edge cases.",
                    "Document how to run the tests locally.",
                ),
                "tests/",
            )
        )

    if not has_ci(root):
        tasks.append(
            missing_task(
                "Add continuous integration workflow",
                "No GitHub Actions workflow was found. CI helps verify tests, linting, and project health on every push or pull request.",
                "automation",
                "medium",
                ("ci", "automation", "medium"),
                (
                    "Create a workflow under .github/workflows/.",
                    "Run tests and basic checks in the workflow.",
                    "Make sure the workflow runs on pull requests and pushes.",
                ),
                ".github/workflows/ci.yml",
            )
        )

    if not has_issue_templates(root):
        tasks.append(
            missing_task(
                "Add GitHub issue templates",
                "No GitHub issue templates were found. Issue templates help users report bugs and request features with enough detail.",
                "workflow",
                "medium",
                ("github", "workflow", "medium"),
                (
                    "Create .github/ISSUE_TEMPLATE/bug_report.md.",
                    "Create .github/ISSUE_TEMPLATE/feature_request.md.",
                    "Keep prompts short and useful.",
                ),
                ".github/ISSUE_TEMPLATE/",
            )
        )

    if not has_pr_template(root):
        tasks.append(
            missing_task(
                "Add a pull request template",
                "No pull request template was found. A PR template helps contributors explain changes, testing, and related issues consistently.",
                "workflow",
                "low",
                ("github", "workflow", "low"),
                (
                    "Create .github/pull_request_template.md.",
                    "Ask for summary, testing, and checklist details.",
                    "Keep the template lightweight so contributors actually use it.",
                ),
                ".github/pull_request_template.md",
            )
        )

    if not exists_any(root, ("CONTRIBUTING.md", ".github/CONTRIBUTING.md")):
        tasks.append(
            missing_task(
                "Add contribution guidelines",
                "The repository does not include contribution guidelines. A CONTRIBUTING file helps people understand how to report issues, set up the project, and submit changes.",
                "documentation",
                "medium",
                ("documentation", "good first issue"),
                (
                    "Create CONTRIBUTING.md.",
                    "Include development setup, test commands, pull request guidance, and issue reporting rules.",
                    "Keep the guide simple and friendly for new contributors.",
                ),
                "CONTRIBUTING.md",
            )
        )

    if not exists_any(root, ("SECURITY.md", ".github/SECURITY.md")):
        tasks.append(
            missing_task(
                "Add a security policy",
                "The repository does not include a SECURITY.md file. A security policy tells users how to report vulnerabilities responsibly.",
                "security",
                "medium",
                ("security", "documentation"),
                (
                    "Create SECURITY.md.",
                    "Explain how vulnerabilities should be reported.",
                    "Ask users not to publish sensitive details in public issues.",
                ),
                "SECURITY.md",
            )
        )

    if not exists_any(root, ("CHANGELOG.md", "HISTORY.md", "RELEASES.md")):
        tasks.append(
            missing_task(
                "Add a changelog",
                "The repository does not include a changelog. A changelog helps users understand what changed between releases.",
                "release",
                "low",
                ("release", "documentation"),
                (
                    "Create CHANGELOG.md.",
                    "Group changes by version and date.",
                    "Include added, changed, fixed, and removed sections when useful.",
                ),
                "CHANGELOG.md",
            )
        )

    if not exists_any(root, ("docs", "documentation")):
        tasks.append(
            missing_task(
                "Add a docs folder for extended documentation",
                "No docs folder was found. Larger projects are easier to maintain when detailed usage, command, or architecture notes are separated from the README.",
                "documentation",
                "low",
                ("documentation", "low"),
                (
                    "Create a docs folder if the project needs extended documentation.",
                    "Add command references, examples, architecture notes, or usage guides.",
                    "Link the docs from the README.",
                ),
                "docs/",
            )
        )

    if (root / ".env").exists() and not exists_any(root, (".env.example", ".env.sample")):
        tasks.append(
            missing_task(
                "Add an environment example file",
                "A .env file exists but no .env.example file was found. Projects should document required environment variables without exposing real secrets.",
                "security",
                "high",
                ("security", "configuration"),
                (
                    "Create .env.example with safe placeholder values.",
                    "Make sure real .env files are ignored by Git.",
                    "Rotate any secret that was accidentally committed.",
                ),
                ".env.example",
            )
        )

    return tuple(tasks)
