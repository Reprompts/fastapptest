from pathlib import Path
from core.schema_extractor import extract_pydantic_models
from core.endpoint_extractor import extract_endpoints
from core.payload_generator import generate_payloads_for_endpoints

def test_generate_payloads():
    project_root = Path(__file__).resolve().parents[1]

    # Path to schema file
    schema_file = project_root / "new_app" / "src" / "new_app" / "schemas" / "user.py"
    # Path to routers file with endpoints
    routers_file = project_root / "new_app" / "src" / "new_app" / "routers" / "users.py"

    # Extract models and endpoints
    models = extract_pydantic_models(schema_file)
    endpoints = extract_endpoints(routers_file)

    # Manually assign body_model_name for testing POST/PUT/PATCH
    for ep in endpoints:
        # Adjust attribute name here based on your Endpoint class
        http_method_attr = getattr(ep, "method", getattr(ep, "http_method", None))
        if http_method_attr and http_method_attr.upper() in ["POST", "PUT", "PATCH"]:
            ep.body_model_name = "UserCreate"  # For testing only

    payloads = generate_payloads_for_endpoints(endpoints, models)

    assert payloads, "No payloads generated"
    for url, data in payloads.items():
        # Adjust according to your Endpoint attribute names
        method = data.get("method")
        body = data.get("body")
        assert method, f"No method for endpoint {url}"
        assert "body" in data
        if method.upper() in ["POST", "PUT", "PATCH"]:
            assert isinstance(body, dict)
            if body:
                assert "username" in body
                assert "email" in body
