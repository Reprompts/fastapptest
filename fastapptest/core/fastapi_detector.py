from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set

from fastapptest.core.ast_parser import BaseVisitor, ParsedFile


@dataclass(frozen=True)
class FastAPIDetectionResult:
    is_fastapi_project: bool
    app_files: List[Path]
    router_files: List[Path]


class FastAPIDetector(BaseVisitor):
    """
    AST visitor that detects FastAPI and APIRouter usage
    with import-aware resolution.
    """

    def __init__(self, parsed_file: ParsedFile) -> None:
        super().__init__(parsed_file)

        self.found_fastapi_app = False
        self.found_router = False

        # Maps local name -> original symbol
        # e.g. {"App": "FastAPI"}
        self.imported_symbols: Dict[str, str] = {}

        # e.g. {"fa"} for `import fastapi as fa`
        self.fastapi_modules: Set[str] = set()

    # ---------- Import Tracking ----------

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "fastapi":
                self.fastapi_modules.add(alias.asname or "fastapi")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "fastapi":
            for alias in node.names:
                self.imported_symbols[alias.asname or alias.name] = alias.name
        self.generic_visit(node)

    # ---------- Call Detection ----------

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func

        # Case: FastAPI() or alias like App()
        if isinstance(func, ast.Name):
            original = self.imported_symbols.get(func.id)

            if original == "FastAPI":
                self.found_fastapi_app = True
            elif original == "APIRouter":
                self.found_router = True

        # Case: fastapi.FastAPI() or fa.APIRouter()
        elif isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name):
                if func.value.id in self.fastapi_modules:
                    if func.attr == "FastAPI":
                        self.found_fastapi_app = True
                    elif func.attr == "APIRouter":
                        self.found_router = True

        self.generic_visit(node)


def detect_fastapi_project(parsed_files: List[ParsedFile]) -> FastAPIDetectionResult:
    """
    Run FastAPI detection across all parsed files.
    """

    app_files: List[Path] = []
    router_files: List[Path] = []

    for parsed in parsed_files:
        detector = FastAPIDetector(parsed)
        detector.visit(parsed.tree)

        if detector.found_fastapi_app:
            app_files.append(parsed.path)

        if detector.found_router:
            router_files.append(parsed.path)

    return FastAPIDetectionResult(
        is_fastapi_project=bool(app_files),
        app_files=sorted(app_files),
        router_files=sorted(router_files),
    )
