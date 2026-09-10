# TaskTrail Commands

This document lists the main TaskTrail commands and common examples.

## Scan

```bash
tasktrail scan .
```

Options:

```bash
tasktrail scan . --markers-only
tasktrail scan . --repo-only
tasktrail scan . --changed
tasktrail scan . --no-dedupe
tasktrail scan . --min-priority high
tasktrail scan . --category documentation
```

## TODO Marker Scan

```bash
tasktrail todos .
```

## Repository Gap Scan

```bash
tasktrail gaps .
```

## Issue Export

Print issue descriptions:

```bash
tasktrail issues .
```

Write one file per issue:

```bash
tasktrail issues . --output-dir issues
```

Write one combined Markdown file:

```bash
tasktrail issues . --output TASKTRAIL_ISSUES.md
```

## Checklist

```bash
tasktrail checklist . --output TASKS.md
```

## Board

```bash
tasktrail board . --output BOARD.md
```

## Export

```bash
tasktrail export . --format markdown --output report.md
tasktrail export . --format json --output report.json
tasktrail export . --format html --output report.html
```

## Show Task

```bash
tasktrail show . documentation-add-a-project-readme
```

## Detect Project

```bash
tasktrail detect .
```

## Config

```bash
tasktrail init
tasktrail config .
```

## Priorities

```bash
tasktrail priorities
```
