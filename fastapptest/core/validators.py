# core/validators.py

from typing import Any, Dict, Optional, Union, List
from pydantic import BaseModel, ValidationError


class Validator:
    """
    Core response validator for FastAPI endpoints.
    Ensures correctness, reliability, and production readiness.
    """

    @staticmethod
    def validate_status(
        response: Dict[str, Any],
        expected_status: Union[int, List[int]] = 200
    ) -> bool:
        """
        Validate HTTP status code.
        Supports single status or list of acceptable statuses.
        """
        status = response.get("status_code")
        if status is None:
            return False
        if isinstance(expected_status, list):
            return status in expected_status
        return status == expected_status

    @staticmethod
    def validate_schema(
        response: Dict[str, Any],
        model: Optional[BaseModel] = None
    ) -> bool:
        """
        Validate response JSON against a Pydantic model.
        Handles dict or list of dicts.
        """
        if not model:
            return True  # Nothing to validate
        data = response.get("response")
        if data is None:
            return False

        try:
            if isinstance(data, list):
                # Validate each item if response is a list
                for item in data:
                    if not isinstance(item, dict):
                        return False
                    model.parse_obj(item)
            else:
                # Single dict
                model.parse_obj(data)
            return True
        except ValidationError:
            return False

    @staticmethod
    def validate_content(
        response: Dict[str, Any],
        required_fields: Optional[List[str]] = None
    ) -> bool:
        """
        Ensure response contains required fields.
        Supports nested keys using dot notation, e.g., "user.id".
        """
        data = response.get("response", {})
        if not required_fields:
            return True
        if not isinstance(data, dict):
            return False

        def has_nested_key(d: dict, key_path: str) -> bool:
            keys = key_path.split(".")
            current = d
            for key in keys:
                if not isinstance(current, dict) or key not in current:
                    return False
                current = current[key]
            return True

        return all(has_nested_key(data, field) for field in required_fields)

    @classmethod
    def validate(
        cls,
        response: Dict[str, Any],
        expected_status: Union[int, List[int]] = 200,
        model: Optional[BaseModel] = None,
        required_fields: Optional[List[str]] = None
    ) -> Dict[str, Union[bool, str]]:
        """
        Full validation: status + schema + content.
        Returns dict with 'passed' and 'error' keys.
        """
        passed = True
        errors = []

        # Status validation
        if not cls.validate_status(response, expected_status):
            passed = False
            errors.append(f"Expected status {expected_status}, got {response.get('status_code')}")

        # Schema validation
        if model and not cls.validate_schema(response, model):
            passed = False
            errors.append("Response does not match schema")

        # Content validation
        if required_fields and not cls.validate_content(response, required_fields):
            passed = False
            errors.append(f"Missing required fields: {required_fields}")

        return {"passed": passed, "error": "; ".join(errors) if errors else ""}
