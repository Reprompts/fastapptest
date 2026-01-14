from pathlib import Path

from core.project_scanner import ProjectScanner
from core.ast_parser import ASTParser
from core.fastapi_detector import detect_fastapi_project


def test_fastapi_detection_on_real_project():
    """
    Detect FastAPI usage in the real new_app/ directory.
    """

    project_root = Path(__file__).resolve().parent.parent
    target_project = project_root / "new_app"

    assert target_project.exists(), "new_app directory does not exist"

    # Step 1: Scan project files
    scanner = ProjectScanner(target_project)
    scan_result = scanner.scan()

    assert scan_result.python_files, "No Python files found in new_app"

    # Step 2: Parse ASTs
    parser = ASTParser()
    parsed_files = parser.parse_files(scan_result.python_files)

    assert parsed_files, "No Python files were parsed into ASTs"

    # Step 3: Detect FastAPI
    detection_result = detect_fastapi_project(parsed_files)

    # Assertions
    assert detection_result.is_fastapi_project is True, "FastAPI not detected"

    assert len(detection_result.app_files) >= 1, "No FastAPI app files detected"

    for app_file in detection_result.app_files:
        assert target_project in app_file.parents

    for router_file in detection_result.router_files:
        assert target_project in router_file.parents
