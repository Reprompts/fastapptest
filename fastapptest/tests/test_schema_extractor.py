from pathlib import Path
from core.schema_extractor import extract_pydantic_models

def test_extract_user_models():
    # Change the path ONLY in test file for the actual FastAPI app
    project_root = Path(__file__).resolve().parents[1]
    schema_file = project_root / "new_app" / "src" / "new_app" / "schemas" / "user.py"

    models = extract_pydantic_models(schema_file)

    assert models, "No Pydantic models detected"

    model_names = [m.name for m in models]
    expected_models = ["UserBase", "UserCreate", "User", "Token"]
    for name in expected_models:
        assert name in model_names
