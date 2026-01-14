# cli/batch_runner.py

import json
from pathlib import Path
from typing import Optional, Dict
from fastapptest.core.endpoint_extractor import extract_endpoints
from fastapptest.core.schema_extractor import extract_pydantic_models
from fastapptest.core.project_scanner import ProjectScanner
from fastapptest.core.fastapi_detector import detect_fastapi_project
from fastapptest.core.ast_parser import ASTParser  # <- required for AST parsing
from fastapptest.core.test_runner import TestRunner
from fastapptest.core.reporting import Reporting
from fastapptest.core.validators import Validator
from fastapptest.cli.schema_validator import SchemaValidator
from fastapptest.cli.auth_helpers import AuthHelper  # handles JWT/API keys

BASE_URL = "http://127.0.0.1:8000"


def run_batch_tests(
    project_root: str,
    batch_file: Optional[str] = None,
    output_file: str = "batch_reports/batch_test_report.json",
    auth: Optional[Dict[str, str]] = None,
) -> None:
    """
    Run batch tests on FastAPI endpoints using optional JSON payload file.
    If batch_file is not provided, only scans endpoints and validates empty payloads.

    Args:
        project_root: Root directory of the FastAPI project
        batch_file: Optional JSON file containing batch payloads
        output_file: Path to save the report
        auth: Optional dictionary for auth headers (JWT, API keys, etc.)
    """
    root_path = Path(project_root).resolve()
    batch_data = []

    if batch_file:
        batch_path = Path(batch_file).resolve()
        if not batch_path.exists():
            print(f"[ERROR] Batch file not found: {batch_path}")
            return

        print(f"[INFO] Loading batch file: {batch_path}")
        with batch_path.open("r", encoding="utf-8") as f:
            batch_data = json.load(f)

    # -----------------------------
    # Scan project & detect endpoints
    # -----------------------------
    scanner = ProjectScanner(root_path)
    python_files = scanner.scan().python_files
    if not python_files:
        print("[ERROR] No Python files found in project.")
        return

    # Parse Python files into ASTs first
    parser = ASTParser()
    parsed_files = parser.parse_files(python_files)

    # Detect FastAPI apps and routers
    detection = detect_fastapi_project(parsed_files)
    all_endpoints = []
    for file_path in detection.app_files + detection.router_files:
        try:
            all_endpoints.extend(extract_endpoints(file_path))
        except Exception as exc:
            print(f"[WARN] Failed extracting endpoints from {file_path}: {exc}")

    if not all_endpoints:
        print("[ERROR] No endpoints detected in project.")
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
    # Initialize TestRunner
    # -----------------------------
    runner = TestRunner(base_url=BASE_URL)

    # -----------------------------
    # Handle authentication
    # -----------------------------
    auth_helper = AuthHelper()
    if auth:
        for k, v in auth.items():
            if k.lower() == "authorization" and v.startswith("Bearer "):
                auth_helper.set_bearer_token(v.split(" ", 1)[1])
            else:
                auth_helper.set_api_key(k, v)

    # Attach auth headers to each batch request
    for item in batch_data:
        headers = item.get("headers", {})
        headers.update(auth_helper.get_headers())
        item["headers"] = headers

    # -----------------------------
    # Run batch tests
    # -----------------------------
    raw_results = runner.run_batch(all_endpoints, batch_data)

    # -----------------------------
    # Validate results
    # -----------------------------
    validators = Validator()
    validated_results = {}

    for test_key, result in raw_results.items():
        response = result.get("response")
        error = result.get("error", "")

        # Validate status code
        status_valid = validators.validate_status(result)

        # Validate response schema
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

    # -----------------------------
    # Save report
    # -----------------------------
    report_path = Path(output_file).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    Reporting.save_json(validated_results, report_path)

    print(f"[INFO] Batch testing complete. Report saved to {report_path}\n")

    # -----------------------------
    # Print summary to terminal
    # -----------------------------
    print("========== Batch Test Summary ==========")
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
