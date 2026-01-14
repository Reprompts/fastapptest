from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Type


@dataclass(frozen=True)
class ParsedFile:
    """
    Represents a successfully parsed Python file.
    """
    path: Path
    tree: ast.AST
    source: str


class ASTParseError(Exception):
    """Raised when a Python file cannot be parsed into an AST."""


class ASTParser:
    """
    Responsible for parsing Python files into ASTs.
    """

    def parse_file(self, path: Path) -> ParsedFile:
        """
        Parse a single Python file into an AST.
        """
        try:
            # UTF-8 first (correct default for Python source)
            try:
                source = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Fallback for non-UTF8 files (enterprise repos reality)
                source = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise ASTParseError(f"Failed to read file: {path}") from exc

        try:
            tree = ast.parse(
                source,
                filename=str(path),
                type_comments=True,
            )
        except SyntaxError as exc:
            raise ASTParseError(f"Syntax error in file: {path}") from exc

        return ParsedFile(
            path=path,
            tree=tree,
            source=source,
        )

    def parse_files(self, paths: Iterable[Path]) -> List[ParsedFile]:
        """
        Parse multiple Python files, skipping invalid ones.
        """
        parsed_files: List[ParsedFile] = []

        for path in paths:
            try:
                parsed_files.append(self.parse_file(path))
            except ASTParseError:
                # Invalid files are ignored by design
                continue

        return parsed_files


class BaseVisitor(ast.NodeVisitor):
    """
    Base class for all AST visitors used in this project.
    """

    def __init__(self, parsed_file: ParsedFile) -> None:
        self.parsed_file = parsed_file

    @property
    def tree(self) -> ast.AST:
        return self.parsed_file.tree

    @property
    def source(self) -> str:
        return self.parsed_file.source

    @property
    def path(self) -> Path:
        return self.parsed_file.path


def run_visitor(
    visitor_cls: Type[BaseVisitor],
    parsed_files: Iterable[ParsedFile],
) -> List[BaseVisitor]:
    """
    Run a visitor against all parsed files.
    """
    if not issubclass(visitor_cls, BaseVisitor):
        raise TypeError("visitor_cls must be a subclass of BaseVisitor")

    visitors: List[BaseVisitor] = []

    for parsed in parsed_files:
        try:
            visitor = visitor_cls(parsed)
            visitor.visit(parsed.tree)
            visitors.append(visitor)
        except Exception:
            # Visitor failures are isolated per file
            continue

    return visitors
