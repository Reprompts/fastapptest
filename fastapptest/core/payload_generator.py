from __future__ import annotations

from typing import Any, Dict, List
from random import Random
import string

from fastapptest.core.schema_extractor import PydanticModel
from fastapptest.core.endpoint_extractor import Endpoint


# Deterministic RNG for reproducible payloads
_RNG = Random(42)


def generate_dummy_value(field_type: str | None) -> Any:
    """
    Generate a dummy value for a field based on its type.
    Backward compatible, but more robust and deterministic.
    """
    if not field_type:
        return "string"

    t = field_type.lower()

    if "optional" in t:
        t = t.replace("optional", "").strip("[] ")

    if "str" in t:
        return "".join(_RNG.choice(string.ascii_letters) for _ in range(8))

    if "int" in t:
        return _RNG.randint(1, 100)

    if "float" in t:
        return round(_RNG.uniform(1.0, 100.0), 2)

    if "bool" in t:
        return _RNG.choice([True, False])

    if "list" in t:
        return []

    if "dict" in t:
        return {}

    # Unknown or custom type
    return f"sample_{t}"


def generate_payload_from_model(model: PydanticModel) -> Dict[str, Any]:
    """
    Generate a JSON-compatible dict from a PydanticModel.
    """
    payload: Dict[str, Any] = {}

    for field in model.fields:
        if field.default is not None:
            payload[field.name] = field.default
        else:
            payload[field.name] = generate_dummy_value(field.type_annotation)

    return payload


def generate_payloads_for_endpoints(
    endpoints: List[Endpoint],
    models: List[PydanticModel],
) -> Dict[str, Dict[str, Any]]:
    """
    Generate payloads for endpoints.

    Return format (unchanged):
    {
        endpoint_path: {"method": "POST", "body": {...}}
    }
    """
    payloads: Dict[str, Dict[str, Any]] = {}
    model_map = {model.name: model for model in models}

    for ep in endpoints:
        methods = sorted(m.upper() for m in ep.methods)
        primary_method = methods[0] if methods else "GET"

        requires_body = any(m in {"POST", "PUT", "PATCH"} for m in methods)

        body_payload: Dict[str, Any] | None

        if requires_body:
            body_model_name = getattr(ep, "body_model_name", None)

            if body_model_name and body_model_name in model_map:
                body_payload = generate_payload_from_model(model_map[body_model_name])
            else:
                body_payload = {}
        else:
            body_payload = None

        payloads[ep.path] = {
            "method": primary_method,
            "body": body_payload,
        }

    return payloads
