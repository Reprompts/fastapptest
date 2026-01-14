# core/test_runner.py

from typing import List, Dict, Any, Optional
import time
import requests
from fastapptest.core.endpoint_extractor import Endpoint
from fastapptest.core.schema_extractor import PydanticModel
from fastapptest.core.payload_generator import generate_payloads_for_endpoints

DEFAULT_TIMEOUT = 10  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # Exponential backoff multiplier


class TestRunner:
    """
    Production-grade test runner for FastAPI endpoints.
    Supports:
        - Interactive/manual testing
        - Automated CI/CD testing
        - Batch testing
        - Optional headers and query params
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8000", headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}

    def run_test(
        self,
        endpoint: Endpoint,
        method: str,
        path_params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> Dict[str, Any]:
        """
        Run a single HTTP request to the endpoint.

        Returns:
            dict: {
                'status_code': int | None,
                'response': dict | str | None,
                'error': str | None
            }
        """
        # Fill path parameters
        path = endpoint.path
        if path_params:
            for k, v in path_params.items():
                path = path.replace(f"{{{k}}}", str(v))

        url = f"{self.base_url}{path}"
        result: Dict[str, Any] = {
            "status_code": None,
            "response": None,
            "error": None,
        }

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.request(
                    method=method.upper(),
                    url=url,
                    headers=self.headers,
                    params=query_params,
                    json=body if body else None,
                    timeout=timeout,
                )

                result["status_code"] = response.status_code
                try:
                    result["response"] = response.json()
                except Exception:
                    result["response"] = response.text
                break  # Success, exit retry loop

            except requests.RequestException as exc:
                result["error"] = f"Attempt {attempt}: {str(exc)}"
                if attempt < MAX_RETRIES:
                    wait_time = BACKOFF_FACTOR ** (attempt - 1)
                    time.sleep(wait_time)  # exponential backoff
                else:
                    break

        return result

    def run_tests(
        self,
        endpoints: List[Endpoint],
        models: List[PydanticModel],
        auto_generate_payloads: bool = True,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run all endpoints sequentially.
        Returns a dictionary keyed by METHOD and path.
        """
        results: Dict[str, Dict[str, Any]] = {}

        # Optionally generate payloads for POST/PUT/PATCH
        payloads: Dict[str, Dict[str, Any]] = {}
        if auto_generate_payloads:
            payloads = generate_payloads_for_endpoints(endpoints, models)

        for ep in endpoints:
            for method in ep.methods:
                body = None
                if method.upper() in {"POST", "PUT", "PATCH"}:
                    body = payloads.get(ep.path, {}).get("body", None)

                test_key = f"{method.upper()} {ep.path}"
                results[test_key] = self.run_test(
                    endpoint=ep,
                    method=method,
                    path_params=None,
                    body=body,
                )

        return results

    def run_batch(
        self,
        endpoints: List[Endpoint],
        batch_payloads: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run endpoints based on a batch payload list.

        batch_payloads example:
        [
            {"path": "/users", "method": "POST", "body": {"username": "abc"}},
            {"path": "/users/{id}", "method": "GET", "path_params": {"id": 1}}
        ]
        """
        results: Dict[str, Dict[str, Any]] = {}

        for entry in batch_payloads:
            path = entry.get("path")
            method = entry.get("method", "GET").upper()
            body = entry.get("body")
            path_params = entry.get("path_params")
            query_params = entry.get("query_params")

            # Find matching endpoint (supports path params dynamically)
            matching_eps = [
                ep for ep in endpoints
                if ep.path.split("{")[0] == path.split("{")[0] and method in map(str.upper, ep.methods)
            ]
            if not matching_eps:
                results[f"{method} {path}"] = {"error": "Endpoint not found"}
                continue

            ep = matching_eps[0]
            results[f"{method} {path}"] = self.run_test(
                endpoint=ep,
                method=method,
                path_params=path_params,
                body=body,
                query_params=query_params,
            )

        return results
