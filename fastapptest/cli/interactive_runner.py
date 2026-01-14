# cli/interactive_runner.py

from typing import List
import requests

from fastapptest.core.endpoint_extractor import Endpoint
from fastapptest.core.schema_extractor import PydanticModel
from fastapptest.cli.input_helpers import (
    prompt_path_params,
    prompt_body_fields,
)

BASE_URL = "http://127.0.0.1:8000"


def run_interactive_cli(endpoints: List[Endpoint], models: List[PydanticModel]) -> None:
    """
    Interactive loop to manually test FastAPI endpoints.
    """

    while True:
        print("\nAvailable Endpoints")
        print("=" * 60)

        indexed = []
        idx = 1

        # Index all endpoints with their methods
        for ep in endpoints:
            for method in ep.methods:
                indexed.append((ep, method))
                print(f"[{idx}] {method:<6} {ep.path}")
                idx += 1

        # Prompt user for selection
        choice = input("\nSelect endpoint number (or 'exit'): ").strip()
        if choice.lower() in {"exit", "q"}:
            print("[INFO] Exiting interactive tester.")
            return

        if not choice.isdigit():
            print("[ERROR] Please enter a valid number.")
            continue

        choice = int(choice)
        if choice < 1 or choice > len(indexed):
            print("[ERROR] Invalid selection.")
            continue

        ep, method = indexed[choice - 1]

        print("\nSelected Endpoint")
        print("-" * 50)
        print(f"Method : {method}")
        print(f"Path   : {ep.path}")

        # -----------------------------
        # Handle path parameters
        # -----------------------------
        path = ep.path
        path_params = prompt_path_params(ep)
        for key, value in path_params.items():
            path = path.replace(f"{{{key}}}", str(value))

        # -----------------------------
        # Handle request body
        # -----------------------------
        body = None
        if method in {"POST", "PUT", "PATCH"}:
            print("\nRequest Body Schema:", ep.body_model_name or "Unknown")
            print("-" * 50)
            body = prompt_body_fields(ep, models)

        # -----------------------------
        # Build final URL
        # -----------------------------
        url = BASE_URL.rstrip("/") + path

        print("\nRequest Preview")
        print("-" * 50)
        print("URL    :", url)
        print("Method :", method)
        print("Body   :", body if body else "None")

        confirm = input("\nSend request? (y/n): ").strip().lower()
        if confirm not in {"y", "yes"}:
            print("[INFO] Request cancelled.")
            continue

        # -----------------------------
        # Send HTTP request
        # -----------------------------
        try:
            response = requests.request(
                method=method,
                url=url,
                json=body if body else None,
                timeout=10,
            )

            print("\nResponse")
            print("-" * 50)
            print("Status Code:", response.status_code)

            try:
                print("JSON Response:")
                print(response.json())
            except Exception:
                print("Text Response:")
                print(response.text)

        except requests.exceptions.ConnectionError:
            print("[ERROR] Could not connect to FastAPI server. Make sure it is running!")
        except requests.RequestException as exc:
            print("[ERROR] Request failed:", exc)
