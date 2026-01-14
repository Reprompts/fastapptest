# core/request_executor.py

from typing import Dict, Any, Optional
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

def execute_request(
    base_url: str,
    path: str,
    method: str,
    body: Dict[str, Any] | None = None,
    headers: Dict[str, str] | None = None,
    params: Dict[str, Any] | None = None,
    timeout: int = 10,
    retries: int = 2,
) -> Dict[str, Any]:
    """
    Execute HTTP request and return response info.

    Returns a dict compatible with current modules:
    {
        "status_code": int | None,
        "response": dict | list | str | None,
        "error": str | None
    }
    """

    url = base_url.rstrip("/") + path
    method = method.upper()
    headers = headers or {}
    last_error: str | None = None

    for attempt in range(retries + 1):
        try:
            resp: requests.Response

            if method == "GET":
                resp = requests.get(url, headers=headers, params=params, timeout=timeout)
            elif method == "POST":
                resp = requests.post(url, json=body, headers=headers, params=params, timeout=timeout)
            elif method == "PUT":
                resp = requests.put(url, json=body, headers=headers, params=params, timeout=timeout)
            elif method == "PATCH":
                resp = requests.patch(url, json=body, headers=headers, params=params, timeout=timeout)
            elif method == "DELETE":
                resp = requests.delete(url, headers=headers, params=params, timeout=timeout)
            else:
                return {"status_code": None, "response": None, "error": f"Unsupported method: {method}"}

            # Attempt to parse JSON, fallback to text
            try:
                content = resp.json() if resp.content else None
            except ValueError:
                content = resp.text if resp.content else None

            return {
                "status_code": resp.status_code,
                "response": content,
                "error": None,
            }

        except (Timeout, ConnectionError) as e:
            last_error = str(e)
            if attempt < retries:
                continue  # retry
            return {"status_code": None, "response": None, "error": last_error}

        except RequestException as e:
            # For other requests exceptions
            return {"status_code": None, "response": None, "error": str(e)}

    # fallback in case all retries fail
    return {"status_code": None, "response": None, "error": last_error}
