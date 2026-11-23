"""Offline checks for Phase 11 Streamlit dashboard and GitHub Actions CI config."""

import ast
from pathlib import Path

import yaml


def test_dashboard_has_valid_python_syntax():
    path = Path("app/dashboard.py")
    ast.parse([invalid URL]_text(encoding="utf-8"))


def test_github_actions_ci_runs_ruff_and_pytest():
    ci_path = Path(".github/workflows/ci.yml")
    cfg = [invalid URL]_load(ci_path.read_text(encoding="utf-8"))
    steps = cfg["jobs"]["lint-and-test"]["steps"]
    commands = " ".join(step.get("run", "") for step in steps)

    assert "ruff check" in commands
    assert "pytest" in commands