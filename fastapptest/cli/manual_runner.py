# cli/manual_runner.py

from pathlib import Path
import argparse
from typing import List, Optional, Dict
import json

from fastapptest.core.project_scanner import ProjectScanner
from fastapptest.core.fastapi_detector import detect_fastapi_project
from fastapptest.core.endpoint_extractor import extract_endpoints
from fastapptest.core.schema_extractor import extract_pydantic_models
from fastapptest.core.payload_generator import generate_payloads_for_endpoints
from fastapptest.core.ast_parser import ASTParser, ParsedFile

from fastapptest.core.validators import Validator
from fastapptest.cli.schema_validator import SchemaValidator
from fastapptest.cli.auth_helpers import AuthHelper

# Interactive CLI runner
from fastapptest.cli.interactive_runner import run_interactive_cli


def run_cli_tester(
    project_root: str,
    auth: Optional[Dict[str, str]] = None  # Optional JWT/API key headers
) -> None:
    """
    CLI Flow:
    1. Scan project
    2. Parse Python files (AST)
    3. Detect FastAPI app & routers
    4. Extract endpoints & schemas
    5. (Optional) Generate payload templates
    6. Launch interactive endpoint tester (manual, loop-based)
    """

    root_path = Path(project_root).resolve()
    print(f"[INFO] Scanning project root: {root_path}")

    # -----------------------------
    # Scan project
    # -----------------------------
    scanner = ProjectScanner(root_path)
    scan_result = scanner.scan()
    python_files = scan_result.python_files
    print(f"[INFO] Found {len(python_files)} Python files.")

    if not python_files:
        print("[WARN] No Python files found.")
        return

    # -----------------------------
    # Parse Python files → AST
    # -----------------------------
    parser = ASTParser()
    parsed_files: List[ParsedFile] = parser.parse_files(python_files)
    print(f"[INFO] Parsed {len(parsed_files)} files successfully.")

    if not parsed_files:
        print("[ERROR] No valid Python files could be parsed.")
        return

    # -----------------------------
    # Detect FastAPI project
    # -----------------------------
    detection = detect_fastapi_project(parsed_files)
    if not detection.is_fastapi_project:
        print("[WARN] No FastAPI app detected.")
        return

    print(
        f"[INFO] FastAPI detected | "
        f"Apps: {len(detection.app_files)}, Routers: {len(detection.router_files)}"
    )

    # -----------------------------
    # Extract endpoints
    # -----------------------------
    all_endpoints = []
    for file_path in detection.app_files + detection.router_files:
        try:
            all_endpoints.extend(extract_endpoints(file_path))
        except Exception as exc:
            print(f"[WARN] Failed extracting endpoints from {file_path}: {exc}")

    print(f"[INFO] Extracted {len(all_endpoints)} endpoints.")
    if not all_endpoints:
        print("[WARN] No endpoints detected.")
        return

    # -----------------------------
    # Extract Pydantic schemas
    # -----------------------------
    all_models = []
    for file_path in python_files:
        try:
            all_models.extend(extract_pydantic_models(file_path))
        except Exception:
            continue

    print(f"[INFO] Extracted {len(all_models)} Pydantic models.")

    # -----------------------------
    # Generate payload templates
    # -----------------------------
    payloads = generate_payloads_for_endpoints(all_endpoints, all_models)
    print(f"[INFO] Generated payload templates for {len(payloads)} endpoints.")

    # -----------------------------
    # Initialize auth helper if needed
    # -----------------------------
    auth_helper = AuthHelper()
    if auth:
        for k, v in auth.items():
            if k.lower() == "authorization" and v.startswith("Bearer "):
                auth_helper.set_bearer_token(v.split(" ", 1)[1])
            else:
                auth_helper.set_api_key(k, v)

    # -----------------------------
    # Assign body models for POST/PUT/PATCH endpoints
    # -----------------------------
    for ep in all_endpoints:
        if any(m in ["POST", "PUT", "PATCH"] for m in ep.methods):
            if getattr(ep, "body_model_name", None) is None and all_models:
                ep.body_model_name = all_models[0].name  # heuristic: first model

        # Assign auth headers if provided
        ep.headers = getattr(ep, "headers", {})
        ep.headers.update(auth_helper.get_headers())

    # -----------------------------
    # Launch interactive CLI tester
    # -----------------------------
    print("\n[INFO] Launching interactive API tester...")
    print("[INFO] Make sure your FastAPI app is running (e.g. uvicorn main:app)\n")

    run_interactive_cli(
        endpoints=all_endpoints,
        models=all_models,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FastAPI Interactive CLI Tester")
    parser.add_argument(
        "project_root",
        type=str,
        help="Root directory of the FastAPI project",
    )
    parser.add_argument(
        "--auth",
        type=str,
        default=None,
        help='Optional auth JSON string, e.g. \'{"Authorization": "Bearer <token>"}\''
    )
    args = parser.parse_args()

    auth_dict = json.loads(args.auth) if args.auth else None
    run_cli_tester(args.project_root, auth=auth_dict)


