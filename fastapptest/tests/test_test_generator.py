from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from core.test_generator import run_endpoint_tests
from core.payload_generator import generate_payloads_for_endpoints
from core.schema_extractor import PydanticModel, PydanticField
from core.endpoint_extractor import Endpoint  # frozen dataclass

# -----------------------------
# Fixtures
# -----------------------------

@pytest.fixture
def sample_endpoints():
    return [
        Endpoint(
            file=Path("dummy"),
            function_name="create_user",
            path="/users",
            methods={"POST"}
        ),
        Endpoint(
            file=Path("dummy"),
            function_name="get_users",
            path="/users/list",
            methods={"GET"}
        ),
    ]

@pytest.fixture
def sample_models():
    return [
        PydanticModel(
            name="UserCreate",
            fields=[
                PydanticField(name="username", type_annotation="str", default=None),
                PydanticField(name="password", type_annotation="str", default=None)
            ],
            file=Path("dummy")
        )
    ]

# -----------------------------
# Tests
# -----------------------------

@patch("core.test_generator.requests.post")
@patch("core.test_generator.requests.get")
def test_run_endpoint_tests(mock_get, mock_post, sample_endpoints, sample_models):
    """
    Test run_endpoint_tests function by mocking requests.
    Works with frozen Endpoint class.
    """

    # Dynamically assign body_model_name for POST endpoint (frozen workaround)
    for ep in sample_endpoints:
        if any(m.upper() in ["POST", "PUT", "PATCH"] for m in ep.methods):
            object.__setattr__(ep, "body_model_name", "UserCreate")

    # Mock POST response
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 201
    mock_post_resp.json.return_value = {"id": 1, "username": "test"}
    mock_post.return_value = mock_post_resp

    # Mock GET response
    mock_get_resp = MagicMock()
    mock_get_resp.status_code = 200
    mock_get_resp.json.return_value = [{"id": 1, "username": "test"}]
    mock_get.return_value = mock_get_resp

    # Run test generator
    results = run_endpoint_tests(sample_endpoints, sample_models)

    # Assert results for POST endpoint
    post_result = results["/users"]
    assert post_result["method"] == "POST"
    assert "username" in post_result["body"]
    assert "password" in post_result["body"]

    # Assert results for GET endpoint
    get_result = results["/users/list"]
    assert get_result["method"] == "GET"
    assert get_result["body"] is None


def test_generate_payloads_with_sample_data(sample_endpoints, sample_models):
    """
    Test payload generation for endpoints using sample models.
    """

    # Dynamically assign body_model_name for POST endpoint (frozen workaround)
    for ep in sample_endpoints:
        if any(m.upper() in ["POST", "PUT", "PATCH"] for m in ep.methods):
            object.__setattr__(ep, "body_model_name", "UserCreate")

    payloads = generate_payloads_for_endpoints(sample_endpoints, sample_models)

    # Check POST payload
    post_payload = payloads["/users"]
    assert post_payload["method"] == "POST"
    assert "username" in post_payload["body"]
    assert "password" in post_payload["body"]

    # Check GET payload
    get_payload = payloads["/users/list"]
    assert get_payload["method"] == "GET"
    assert get_payload["body"] is None
