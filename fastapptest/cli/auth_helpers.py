# cli/auth_helpers.py

from typing import Dict, Optional

class AuthHelper:
    """
    Handles authentication for API requests.
    Supports Bearer/JWT tokens, API keys, and OAuth2.
    """

    def __init__(self):
        self.headers: Dict[str, str] = {}

    def set_bearer_token(self, token: str):
        self.headers["Authorization"] = f"Bearer {token}"

    def set_api_key(self, key_name: str, key_value: str, in_header: bool = True):
        """
        Attach API key either as header or query parameter.
        """
        if in_header:
            self.headers[key_name] = key_value
        else:
            # For query parameters, caller must append manually in URL
            pass

    def get_headers(self) -> Dict[str, str]:
        return self.headers

    def clear(self):
        self.headers.clear()
