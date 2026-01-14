# test_generator.py

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
import requests
import random
import string

from fastapptest.core.payload_generator import generate_payloads_for_endpoints
from fastapptest.core.schema_extractor import PydanticModel
from fastapptest.core.endpoint_extractor import Endpoint

BASE_URL = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT = 5.0  # seconds


def _safe_json(response: requests.Response) -> Any:
    """
    Safely parse JSON responses.
    """
    try:
        return response.json()
    except Exception:
        return response.text


def _fill_path_params(path: str) -> str:
    """
    Automatically fill path parameters for testing.
    Example: /users/{id} -> /users/123
    """
    import re

    def random_value():
        return str(random.randint(1, 100))

    return re.sub(r"{(.*?)}", lambda _: random_value(), path)


def run_endpoint_tests(
    endpoints: List[Endpoint],
    models: List[PydanticModel],
    base_url: str = BASE_URL
) -> Dict[str, Dict[str, Any]]:
    """
    Automatically execute HTTP requests for all endpoints using generated payloads.
    """
    results: Dict[str, Dict[str, Any]] = {}
    payloads = generate_payloads_for_endpoints(endpoints, models)
    session = requests.Session()
    base_url = base_url.rstrip("/")

    for ep in endpoints:
        filled_path = _fill_path_params(ep.path)

        for method in sorted(m.upper() for m in ep.methods):
            key = f"{filled_path}::{method}"
            full_url = f"{base_url}{filled_path}"

            body = payloads.get(ep.path, {}).get("body") if method in {"POST", "PUT", "PATCH"} else None

            try:
                resp: requests.Response
                if method == "GET":
                    resp = session.get(full_url, timeout=DEFAULT_TIMEOUT)
                elif method == "POST":
                    resp = session.post(full_url, json=body, timeout=DEFAULT_TIMEOUT)
                elif method == "PUT":
                    resp = session.put(full_url, json=body, timeout=DEFAULT_TIMEOUT)
                elif method == "PATCH":
                    resp = session.patch(full_url, json=body, timeout=DEFAULT_TIMEOUT)
                elif method == "DELETE":
                    resp = session.delete(full_url, timeout=DEFAULT_TIMEOUT)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                results[key] = {
                    "method": method,
                    "body": body,
                    "status_code": resp.status_code,
                    "response": _safe_json(resp),
                }

            except Exception as e:
                results[key] = {
                    "method": method,
                    "body": body,
                    "status_code": None,
                    "response": str(e),
                }

    return results


def save_results_to_file(results: Dict[str, Dict[str, Any]], file_path: Path) -> None:
    """
    Save the results dict to a JSON file for review.
    """
    import json
    file_path.write_text(json.dumps(results, indent=4, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    """
    Example usage:
    python -m core.test_generator
    """
    from core.schema_extractor import extract_pydantic_models
    from core.endpoint_extractor import extract_endpoints

    project_root = Path(__file__).resolve().parents[1]

    routers_file = project_root / "new_app" / "src" / "new_app" / "routers" / "users.py"
    schema_file = project_root / "new_app" / "src" / "new_app" / "schemas" / "user.py"

    models = extract_pydantic_models(schema_file)
    endpoints = extract_endpoints(routers_file)

    # Assign body_model_name for POST/PUT/PATCH endpoints
    for ep in endpoints:
        if any(m.upper() in {"POST", "PUT", "PATCH"} for m in ep.methods):
            ep.body_model_name = "UserCreate"

    results = run_endpoint_tests(endpoints, models, BASE_URL)
    save_results_to_file(results, project_root / "fastapi_test_results.json")

    print("Test execution complete. Results saved to fastapi_test_results.json")
