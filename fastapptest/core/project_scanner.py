# core/project_scanner.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Set


DEFAULT_EXCLUDED_DIRS: Set[str] = {
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    ".git",
    ".hg",
    ".svn",
    ".pytest_cache",
    ".mypy_cache",
    "site-packages",
    "node_modules",
    "dist",
    "build",
}


@dataclass(frozen=True)
class ProjectScanResult:
    root: Path
    python_files: List[Path]
    skipped_dirs: Set[Path]


class ProjectScanner:
    """
    Scans a project directory and returns only project-owned Python files.
    """

    def __init__(
        self,
        root: Path,
        exclude_dirs: Iterable[str] | None = None,
    ) -> None:
        self.root = root.resolve()
        self.exclude_dirs = set(exclude_dirs or DEFAULT_EXCLUDED_DIRS)

        if not self.root.exists():
            raise FileNotFoundError(f"Project root does not exist: {self.root}")

        if not self.root.is_dir():
            raise NotADirectoryError(f"Project root is not a directory: {self.root}")

    def scan(self) -> ProjectScanResult:
        python_files: List[Path] = []
        skipped_dirs: Set[Path] = set()

        for path in self._walk(self.root, skipped_dirs):
            if path.suffix == ".py":
                python_files.append(path)

        return ProjectScanResult(
            root=self.root,
            python_files=sorted(python_files),
            skipped_dirs=skipped_dirs,
        )

    def _walk(self, root: Path, skipped_dirs: Set[Path]) -> Iterable[Path]:
        """
        Iterative directory walk with exclusion, symlink protection,
        and deep-recursion safety.
        """
        stack: List[Path] = [root]

        while stack:
            current_dir = stack.pop()

            try:
                for entry in current_dir.iterdir():
                    # Skip directory symlinks to prevent cycles
                    if entry.is_dir():
                        if entry.is_symlink():
                            continue

                        if entry.name in self.exclude_dirs:
                            skipped_dirs.add(entry)
                            continue

                        stack.append(entry)
                    else:
                        yield entry

            except PermissionError:
                # Ignore directories we cannot access
                continue
