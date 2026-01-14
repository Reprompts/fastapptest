from pathlib import Path

from core.project_scanner import ProjectScanner
from core.ast_parser import ASTParser, ParsedFile


def test_ast_parser_on_real_fastapi_project():
    """
    This test parses ASTs from the real FastAPI project directory: new_app/
    """

    project_root = Path(__file__).resolve().parent.parent
    target_project = project_root / "new_app"

    assert target_project.exists(), "new_app directory does not exist"

    # Step 1: Scan project files
    scanner = ProjectScanner(target_project)
    scan_result = scanner.scan()

    assert len(scan_result.python_files) > 0, "No Python files found to parse"

    # Step 2: Parse ASTs
    parser = ASTParser()
    parsed_files = parser.parse_files(scan_result.python_files)

    assert len(parsed_files) > 0, "No ASTs were parsed"

    # Step 3: Validate parsed structure
    for parsed in parsed_files:
        assert isinstance(parsed, ParsedFile)
        assert parsed.tree is not None
        assert parsed.source.strip() != ""
        assert parsed.path.exists()
