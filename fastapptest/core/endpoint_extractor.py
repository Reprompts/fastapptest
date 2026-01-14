from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set, Optional, Dict

from fastapptest.core.ast_parser import ASTParser, ParsedFile

HTTP_METHODS = {
    "get", "post", "put", "delete", "patch", "options", "head"
}


@dataclass(frozen=False)
class Endpoint:
    file: Path
    function_name: str
    path: str
    methods: Set[str]
    body_model_name: Optional[str] = None


class EndpointExtractor(ast.NodeVisitor):
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.endpoints: List[Endpoint] = []

        # Track fastapi imports
        self.fastapi_modules: Set[str] = set()
        self.router_names: Set[str] = set()

    # ---------- Import tracking ----------

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "fastapi":
                self.fastapi_modules.add(alias.asname or "fastapi")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "fastapi":
            for alias in node.names:
                if alias.name in {"APIRouter", "FastAPI"}:
                    self.router_names.add(alias.asname or alias.name)
        self.generic_visit(node)

    # ---------- Function handling ----------

    def visit_FunctionDef(self, node: ast.FunctionDef):
        for decorator in node.decorator_list:
            endpoint = self._parse_decorator(decorator, node.name)
            if endpoint:
                self.endpoints.append(endpoint)

        self.generic_visit(node)

    # ---------- Decorator parsing ----------

    def _parse_decorator(
        self,
        decorator: ast.expr,
        function_name: str,
    ) -> Optional[Endpoint]:
        if not isinstance(decorator, ast.Call):
            return None

        func = decorator.func
        methods: Set[str] = set()

        # router.get(...)
        if isinstance(func, ast.Attribute):
            if not isinstance(func.value, ast.Name):
                return None

            router_name = func.value.id
            method = func.attr.lower()

            if method in HTTP_METHODS:
                methods.add(method.upper())
            elif method == "route":
                methods |= self._extract_methods_kw(decorator)
            else:
                return None

            # Validate router origin
            if (
                router_name not in self.router_names
                and router_name not in self.fastapi_modules
            ):
                return None

        else:
            return None

        path = self._extract_path(decorator)
        if path is None:
            return None

        body_model = self._extract_body_model(decorator)

        return Endpoint(
            file=self.file_path,
            function_name=function_name,
            path=path,
            methods=methods,
            body_model_name=body_model,
        )

    # ---------- Helpers ----------

    def _extract_path(self, decorator: ast.Call) -> Optional[str]:
        if not decorator.args:
            return None

        node = decorator.args[0]

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value

        if isinstance(node, ast.JoinedStr):
            # f-string → keep readable form
            return "".join(
                part.value if isinstance(part, ast.Constant) else "{...}"
                for part in node.values
            )

        return None

    def _extract_methods_kw(self, decorator: ast.Call) -> Set[str]:
        for kw in decorator.keywords:
            if kw.arg == "methods" and isinstance(kw.value, ast.List):
                methods = set()
                for elt in kw.value.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        methods.add(elt.value.upper())
                return methods
        return set()

    def _extract_body_model(self, decorator: ast.Call) -> Optional[str]:
        for kw in decorator.keywords:
            if kw.arg in {"response_model", "body"}:
                if isinstance(kw.value, ast.Name):
                    return kw.value.id
        return None


def extract_endpoints(py_file: Path) -> List[Endpoint]:
    """
    Extract endpoints from a single Python file using ASTParser.
    """
    parser = ASTParser()

    try:
        parsed_file: ParsedFile = parser.parse_file(py_file)
    except Exception:
        # Fail safe: invalid files produce no endpoints
        return []

    extractor = EndpointExtractor(parsed_file.path)
    extractor.visit(parsed_file.tree)
    return extractor.endpoints
