# ci_runner.py

from pathlib import Path
from typing import List, Optional, Dict

from fastapptest.core.project_scanner import ProjectScanner
from fastapptest.core.fastapi_detector import detect_fastapi_project
from fastapptest.core.endpoint_extractor import extract_endpoints
from fastapptest.core.schema_extractor import extract_pydantic_models
from fastapptest.core.payload_generator import generate_payloads_for_endpoints
from fastapptest.core.test_runner import TestRunner
from fastapptest.core.reporting import Reporting
from fastapptest.core.ast_parser import ASTParser
from fastapptest.core.validators import Validator
from fastapptest.cli.schema_validator import SchemaValidator

BASE_URL = "http://127.0.0.1:8000"


def run_ci_cd_tests(
    project_root: str,
    output_dir: str = "ci_reports",
    auth: Optional[Dict[str, str]] = None,
    fail_fast: bool = False,
) -> None:
    """
    CI/CD runner for FastAPI projects with automatic validation.
    """

    root_path = Path(project_root).resolve()
    print(f"[INFO] Scanning project root: {root_path}")

    # -----------------------------
    # Scan project
    # -----------------------------
    scanner = ProjectScanner(root_path)
    python_files = scanner.scan().python_files
    if not python_files:
        print("[ERROR] No Python files found.")
        return

    # -----------------------------
    # Detect FastAPI project
    # -----------------------------
    parser = ASTParser()
    parsed_files = parser.parse_files(python_files)
    detection = detect_fastapi_project(parsed_files)
    if not detection.is_fastapi_project:
        print("[ERROR] No FastAPI app detected.")
        return

    # -----------------------------
    # Extract endpoints
    # -----------------------------
    all_endpoints = []
    for file_path in detection.app_files + detection.router_files:
        try:
            all_endpoints.extend(extract_endpoints(file_path))
        except Exception as exc:
            print(f"[WARN] Failed extracting endpoints from {file_path}: {exc}")

    if not all_endpoints:
        print("[ERROR] No endpoints found.")
        return

    # -----------------------------
    # Extract Pydantic models
    # -----------------------------
    all_models = []
    for file_path in python_files:
        try:
            all_models.extend(extract_pydantic_models(file_path))
        except Exception:
            continue

    # -----------------------------
    # Generate payloads
    # -----------------------------
    generate_payloads_for_endpoints(all_endpoints, all_models)
    print(f"[INFO] Generated payload templates for {len(all_endpoints)} endpoints.")

    # -----------------------------
    # Run tests with validation
    # -----------------------------
    print("[INFO] Running CI/CD automated tests with validation...")

    # ✅ Create TestRunner with supported args ONLY
    runner = TestRunner(base_url=BASE_URL)

    # ✅ Attach optional attributes safely (future-ready)
    if auth is not None:
        runner.auth = auth
    runner.fail_fast = fail_fast

    raw_results = runner.run_tests(all_endpoints, all_models)

    validators = Validator()
    validated_results = {}

    for test_key, result in raw_results.items():
        response = result.get("response")
        error = result.get("error", "")

        status_valid = validators.validate_status(result)

        schema_valid = False
        schema_error = None
        if response:
            try:
                SchemaValidator.validate_response(
                    response=response,
                    expected_status=result.get("status_code") or 200
                )
                schema_valid = True
            except Exception as exc:
                schema_error = str(exc)

        validated_results[test_key] = {
            "status_code": result.get("status_code"),
            "status_valid": status_valid,
            "schema_valid": schema_valid,
            "response": response,
            "error": error or schema_error,
        }

        # Optional fail-fast behavior
        if fail_fast and (not status_valid or not schema_valid):
            print("[ERROR] Fail-fast enabled. Stopping execution.")
            break

    # -----------------------------
    # Save report
    # -----------------------------
    report_path = Path(output_dir)
    report_path.mkdir(exist_ok=True)
    report_file = report_path / "ci_test_report.json"
    Reporting.save_json(validated_results, report_file)
    print(f"[INFO] CI/CD tests complete. Report saved to {report_file}\n")

    # -----------------------------
    # Print summary to terminal
    # -----------------------------
    print("========== CI/CD Test Summary ==========")
    for test_key, result in validated_results.items():
        status_str = str(result.get("status_code") or "N/A")
        status_valid = "✅" if result.get("status_valid") else "❌"
        schema_valid = "✅" if result.get("schema_valid") else "❌"
        error_str = str(result.get("error") or "-")
        print(
            f"{test_key:<30} | Status: {status_str:<3} ({status_valid}) | "
            f"Schema: {schema_valid} | Error: {error_str}"
        )
        print("-" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CI/CD FastAPI Test Runner")
    parser.add_argument("project_root", type=str, help="Root directory of FastAPI project")
    parser.add_argument(
        "--output",
        type=str,
        default="ci_reports",
        help="Directory to save CI/CD reports",
    )
    args = parser.parse_args()

    run_ci_cd_tests(args.project_root, args.output)
