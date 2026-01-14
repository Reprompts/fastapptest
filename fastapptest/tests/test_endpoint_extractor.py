from pathlib import Path
from core.endpoint_extractor import extract_endpoints

def test_extract_endpoints_from_fastapi_app():
    project_root = Path(__file__).resolve().parents[1]
    app_file = project_root / "new_app" / "src" / "new_app" / "main.py"

    endpoints = extract_endpoints(app_file)

    assert endpoints, "No endpoints detected"
