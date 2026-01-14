# core/schema_extractor.py
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Set

from fastapptest.core.ast_parser import ASTParser, ParsedFile, BaseVisitor


@dataclass(frozen=True)
class PydanticField:
    name: str
    type_annotation: str | None
    default: Any = None


@dataclass(frozen=True)
class PydanticModel:
    name: str
    fields: List[PydanticField]
    file: Path


class PydanticModelVisitor(BaseVisitor):
    """
    Visitor to extract Pydantic models from a parsed Python file.
    AST-only, safe, and side-effect free.
    """

    def __init__(self, parsed_file: ParsedFile):
        super().__init__(parsed_file)
        self.models: List[PydanticModel] = []
        self._model_names: Set[str] = set()

    def visit_ClassDef(self, node: ast.ClassDef):
        is_pydantic_model = self._is_pydantic_model(node)

        if is_pydantic_model:
            fields: List[PydanticField] = []

            for stmt in node.body:
                # Skip inner classes (Config, nested models, etc.)
                if isinstance(stmt, ast.ClassDef):
                    continue

                # Annotated fields: name: type = default
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    name = stmt.target.id

                    if self._should_ignore_field(name, stmt.annotation):
                        continue

                    fields.append(
                        PydanticField(
                            name=name,
                            type_annotation=self._get_annotation(stmt.annotation),
                            default=self._get_default(stmt.value),
                        )
                    )

                # Unannotated assignment: name = value
                elif isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name):
                            name = target.id
                            if self._should_ignore_field(name, None):
                                continue

                            fields.append(
                                PydanticField(
                                    name=name,
                                    type_annotation=None,
                                    default=self._get_default(stmt.value),
                                )
                            )

            self.models.append(
                PydanticModel(
                    name=node.name,
                    fields=fields,
                    file=self.path,
                )
            )
            self._model_names.add(node.name)

        self.generic_visit(node)

    # ----------------- helpers -----------------

    def _is_pydantic_model(self, node: ast.ClassDef) -> bool:
        # Direct BaseModel inheritance
        for base in node.bases:
            if self._is_pydantic_base(base):
                return True

        # Indirect inheritance (order independent, same file)
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in self._model_names:
                return True

        return False

    def _is_pydantic_base(self, base: ast.expr) -> bool:
        if isinstance(base, ast.Name):
            return base.id == "BaseModel"
        if isinstance(base, ast.Attribute):
            return base.attr == "BaseModel"
        return False

    def _should_ignore_field(self, name: str, annotation: ast.expr | None) -> bool:
        # Ignore private attributes
        if name.startswith("_"):
            return True

        # Ignore Config / model_config
        if name in {"Config", "model_config"}:
            return True

        # Ignore ClassVar fields
        if annotation and self._is_classvar(annotation):
            return True

        return False

    def _is_classvar(self, annotation: ast.expr) -> bool:
        if isinstance(annotation, ast.Subscript):
            if isinstance(annotation.value, ast.Name):
                return annotation.value.id == "ClassVar"
        return False

    def _get_annotation(self, annotation: ast.expr) -> str | None:
        if annotation is None:
            return None

        if isinstance(annotation, ast.Name):
            return annotation.id

        if isinstance(annotation, ast.Attribute):
            return annotation.attr

        if isinstance(annotation, ast.Constant):
            return str(annotation.value)

        # List[str], Optional[int], etc.
        if isinstance(annotation, ast.Subscript):
            value = self._get_annotation(annotation.value)
            slice_ = self._get_annotation(annotation.slice)
            if value and slice_:
                return f"{value}[{slice_}]"

        # Python 3.10+: A | B
        if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
            left = self._get_annotation(annotation.left)
            right = self._get_annotation(annotation.right)
            if left and right:
                return f"{left} | {right}"

        return None

    def _get_default(self, value: ast.expr | None) -> Any:
        if value is None:
            return None

        if isinstance(value, ast.Constant):
            return value.value

        if isinstance(value, ast.List):
            return []

        if isinstance(value, ast.Dict):
            return {}

        # Explicit None
        if isinstance(value, ast.Name) and value.id == "None":
            return None

        # Anything dynamic (Field(), function calls, etc.)
        return None


def extract_pydantic_models(py_file: Path) -> List[PydanticModel]:
    """
    Extract all Pydantic models from a single Python file.
    """
    parser = ASTParser()
    parsed_file: ParsedFile = parser.parse_file(py_file)
    visitor = PydanticModelVisitor(parsed_file)
    visitor.visit(parsed_file.tree)
    return visitor.models
