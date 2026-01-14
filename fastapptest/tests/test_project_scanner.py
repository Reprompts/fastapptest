from pathlib import Path

from core.project_scanner import ProjectScanner


def test_project_scanner_on_real_fastapi_project():
    """
    This test scans the real FastAPI project directory: new_app/
    """

    project_root = Path(__file__).resolve().parent.parent
    target_project = project_root / "new_app"

    assert target_project.exists(), "new_app directory does not exist"
    assert target_project.is_dir(), "new_app is not a directory"

    scanner = ProjectScanner(target_project)
    result = scanner.scan()

    # Basic sanity checks
    assert result.root == target_project
    assert len(result.python_files) > 0, "No Python files detected in new_app"

    # Ensure all detected files are inside new_app
    for py_file in result.python_files:
        assert target_project in py_file.parents
        assert py_file.suffix == ".py"

    # Ensure excluded directories are NOT scanned
    for skipped in result.skipped_dirs:
        assert skipped.exists()
