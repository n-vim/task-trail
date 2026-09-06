# Contributing to TaskTrail

Thank you for your interest in contributing to TaskTrail.

TaskTrail is a Python CLI that scans repositories and turns TODO markers, missing project essentials, and cleanup work into GitHub-ready tasks and issue descriptions.

The project should stay simple, practical, and easy to understand.

---

## Ways to Contribute

You can contribute by:

- Fixing bugs
- Improving task detection
- Adding new repository checks
- Improving Markdown or JSON reports
- Improving CLI output
- Adding tests
- Improving documentation
- Suggesting useful features

---

## Development Setup

Clone the repository:

```bash
git clone https://github.com/n-vim/task-trail.git
cd task-trail
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

---

## Run Tests

```bash
pytest
```

Run linting:

```bash
ruff check .
```

Run type checking:

```bash
mypy src
```

---

## Pull Request Guidelines

Before opening a pull request:

- Keep the change focused
- Add tests for new behavior
- Update documentation if needed
- Make sure tests pass
- Avoid committing cache or build files
- Keep CLI messages clear and useful

---

## Adding New Checks

A good TaskTrail check should:

- Produce a clear task title
- Explain why the task matters
- Include useful suggested steps
- Avoid noisy or overly opinionated warnings
- Include tests

---

## License

By contributing, you agree that your contribution will be licensed under the MIT License.
