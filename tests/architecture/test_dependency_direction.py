"""
[PURPOSE]: AST-based static analysis dependency direction guard tests.
[DEPENDENCIES]: unittest, ast, os, pathlib.
"""

import ast
import os
from pathlib import Path
import unittest


ALLOWED_DEPENDENCIES = {
    "src.core": ["src.core"],
    "src.data": ["src.core", "src.data"],
    "src.config": ["src.core", "src.config", "src.data"],
    "src.features": ["src.core", "src.data", "src.features"],
    "src.strategies": ["src.core", "src.strategies"],
    "src.environment": [
        "src.core",
        "src.config",
        "src.data",
        "src.environment",
        "src.engine",
    ],
    "src.engine": [
        "src.core",
        "src.config",
        "src.data",
        "src.environment",
        "src.strategies",
        "src.engine",
    ],
    "src.experiments": ["src.core", "src.experiments"],
    "src.evaluation": ["src.core", "src.engine", "src.evaluation"],
}


class TestDependencyDirection(unittest.TestCase):
    """
    [PURPOSE]: Enforce strict architectural dependency directions using AST static analysis.
    """

    def setUp(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.src_dir = self.project_root / "src"

    def _get_package_prefix(self, mod_name: str) -> str:
        parts = mod_name.split(".")
        if len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"
        return mod_name

    def _parse_imports(self, file_path: Path) -> set:
        with open(file_path, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=str(file_path))

        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module)
        return imported_modules

    def test_dependency_direction_invariants(self):
        """[Architecture Guard]: Verify all internal package imports satisfy ALLOWED_DEPENDENCIES matrix."""
        violations = []

        for root, _, files in os.walk(self.src_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(self.project_root)
                    mod_name = rel_path.with_suffix("").as_posix().replace("/", ".")

                    source_pkg = self._get_package_prefix(mod_name)
                    if source_pkg not in ALLOWED_DEPENDENCIES:
                        continue

                    allowed_target_pkgs = ALLOWED_DEPENDENCIES[source_pkg]
                    imports = self._parse_imports(file_path)

                    for imp in imports:
                        if imp.startswith("src.") or imp == "src":
                            target_pkg = self._get_package_prefix(imp)
                            if target_pkg not in allowed_target_pkgs:
                                msg = (
                                    f"\nARCHITECTURE VIOLATION\n\n"
                                    f"Module:\n    {mod_name}\n\n"
                                    f"Forbidden dependency:\n    {imp} ({target_pkg})\n\n"
                                    f"Rule:\n    {source_pkg} must not depend on {target_pkg}\n\n"
                                    f"Reason:\n    Enforcing strict architectural layer dependency direction.\n"
                                )
                                violations.append(msg)

        if violations:
            self.fail("\n".join(violations))


if __name__ == "__main__":
    unittest.main()
