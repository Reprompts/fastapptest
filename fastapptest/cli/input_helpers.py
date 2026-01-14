# cli/input_helpers.py

from typing import Dict, Any, List

from fastapptest.core.endpoint_extractor import Endpoint
from fastapptest.core.schema_extractor import PydanticModel


def prompt_path_params(endpoint: Endpoint) -> Dict[str, Any]:
    """
    Prompt user to enter values for path parameters like /users/{id}
    """
    params: Dict[str, Any] = {}

    if "{" not in endpoint.path:
        return params

    print("\nPath Parameters Required:")
    for part in endpoint.path.split("/"):
        if part.startswith("{") and part.endswith("}"):
            key = part.strip("{}")
            value = input(f"  Enter value for '{key}': ").strip()
            params[key] = value

    return params


def prompt_body_fields(endpoint, models):
    """
    Prompt the user to fill in the body fields for POST/PUT/PATCH endpoints.
    """
    if not endpoint.body_model_name:
        print("[INFO] No request body required.")
        return {}

    # Find the model by name
    model = next((m for m in models if m.name == endpoint.body_model_name), None)
    if not model:
        print(f"[WARN] Model {endpoint.body_model_name} not found.")
        return {}

    data = {}
    for field in model.fields:
        # Pydantic v1 -> use outer_type_
        # Pydantic v2 -> use annotation
        type_hint = getattr(field, "annotation", None) or getattr(field, "outer_type_", None)
        prompt = f"Enter value for {field.name} ({type_hint}): "
        value = input(prompt)
        data[field.name] = value
    return data


def _cast_value(value: str, type_hint: str) -> Any:
    """
    Convert string input to appropriate Python type.
    """
    try:
        if type_hint in {"int", "Optional[int]"}:
            return int(value)
        if type_hint in {"float", "Optional[float]"}:
            return float(value)
        if type_hint in {"bool", "Optional[bool]"}:
            return value.lower() in {"true", "1", "yes"}
    except Exception:
        pass

    return value
