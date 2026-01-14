# cli/main.py

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Dict

from fastapptest.cli.manual_runner import run_cli_tester
from fastapptest.cli.ci_runner import run_ci_cd_tests
from fastapptest.cli.batch_runner import run_batch_tests


# ---------------------------------------------------------
# Utilities
# ---------------------------------------------------------

def resolve_project_root(path: Optional[str]) -> Path:
    """
    Resolve project root.
    - If path is provided → resolve it
    - If empty → use current working directory
    """
    if path:
        root = Path(path).expanduser().resolve()
    else:
        root = Path.cwd().resolve()

    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")

    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root}")

    return root


def parse_auth(auth: Optional[str]) -> Optional[Dict[str, str]]:
    """
    Parse auth JSON safely.
    """
    if not auth:
        return None

    try:
        value = json.loads(auth)
        if not isinstance(value, dict):
            raise ValueError("Auth must be a JSON object")
        return value
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid auth JSON: {exc}") from exc


# ---------------------------------------------------------
# Command handlers
# ---------------------------------------------------------

def manual_test_cli() -> None:
    parser = argparse.ArgumentParser(
        prog="manual_test",
        description="Interactive FastAPI API tester"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="FastAPI project root (defaults to current directory)"
    )
    parser.add_argument(
        "--auth",
        type=str,
        help='Optional auth JSON. Example: \'{"Authorization": "Bearer <token>"}\''
    )

    args = parser.parse_args()
    project_root = resolve_project_root(args.path)
    auth = parse_auth(args.auth)

    run_cli_tester(
        project_root=str(project_root),
        auth=auth
    )


def ci_test_cli() -> None:
    parser = argparse.ArgumentParser(
        prog="ci_test",
        description="CI-mode FastAPI test runner (non-interactive)"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="FastAPI project root (defaults to current directory)"
    )
    parser.add_argument(
        "--auth",
        type=str,
        help='Optional auth JSON'
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure"
    )

    args = parser.parse_args()
    project_root = resolve_project_root(args.path)
    auth = parse_auth(args.auth)

    run_ci_cd_tests(
        project_root=str(project_root),
        auth=auth,
        fail_fast=args.fail_fast
    )


def batch_test_cli() -> None:
    parser = argparse.ArgumentParser(
        prog="batch_test",
        description="Batch FastAPI endpoint tester"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="FastAPI project root (defaults to current directory)"
    )
    parser.add_argument(
        "--auth",
        type=str,
        help='Optional auth JSON'
    )
    parser.add_argument(
        "--output",
        type=str,
        default="batch_report.json",
        help="Output report file"
    )

    args = parser.parse_args()
    project_root = resolve_project_root(args.path)
    auth = parse_auth(args.auth)

    run_batch_tests(
        project_root=str(project_root),
        auth=auth,
        output_file=args.output
    )


# ---------------------------------------------------------
# Entry-point safety
# ---------------------------------------------------------

def _safe_entry(fn):
    try:
        fn()
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
