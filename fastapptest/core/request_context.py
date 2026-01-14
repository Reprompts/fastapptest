# core/request_context.py

from typing import Dict, Any, List
import re

from fastapptest.core.endpoint_extractor import Endpoint
from fastapptest.core.schema_extractor import PydanticModel, PydanticField


def extract_path_params(path: str) -> List[str]:
    """Extract {param} from path"""
    return re.findall(r"{(.*?)}", path)


def prompt_path_params(path: str, interactive: bool = True) -> str:
    """Ask user for path parameter values"""
    params = extract_path_params(path)
    final_path = path

    for param in params:
        if interactive:
            value = input(f"Enter value for path parameter '{param}': ").strip()
        else:
            value = "1"  # safe default for automation

        final_path = final_path.replace(f"{{{param}}}", value)

    return final_path


def _coerce_type(value: str, type_annotation: str | None) -> Any:
    """Best-effort type coercion"""
    if not type_annotation:
        return value

    t = type_annotation.lower()

    try:
        if "int" in t:
            return int(value)
        if "float" in t:
            return float(value)
        if "bool" in t:
            return value.lower() in {"true", "1", "yes"}
    except Exception:
        pass

    return value


def prompt_body(
    model: PydanticModel,
    interactive: bool = True,
) -> Dict[str, Any]:
    """Prompt user for request body fields"""
    print("\nRequest Body Schema:", model.name)
    print("-" * 40)

    body: Dict[str, Any] = {}

    for field in model.fields:
        field_name = field.name
        field_type = field.type_annotation or "Any"
        required = field.default is None

        if not interactive:
            body[field_name] = field.default
            continue

        prompt = f"{field_name} ({field_type})"
        prompt += " [required]: " if required else " [optional]: "

        while True:
            value = input(prompt).strip()

            if value == "":
                if required:
                    print(f"[ERROR] '{field_name}' is required")
                    continue
                body[field_name] = field.default
                break
            else:
                body[field_name] = _coerce_type(value, field.type_annotation)
                break

    return body


def build_request_context(
    endpoint: Endpoint,
    models: List[PydanticModel],
    interactive: bool = True,
) -> Dict[str, Any]:
    """
    Builds final request context.
    Interactive by default, automation-safe when interactive=False.
    """
    # Path params
    final_path = prompt_path_params(endpoint.path, interactive=interactive)

    # Body
    body = None
    if getattr(endpoint, "body_model_name", None):
        model = next(
            (m for m in models if m.name == endpoint.body_model_name),
            None,
        )
        if model:
            body = prompt_body(model, interactive=interactive)

    # Deterministic method selection
    method = sorted(endpoint.methods)[0]

    return {
        "path": final_path,
        "method": method,
        "body": body,
    }
