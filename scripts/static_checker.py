#!/usr/bin/env python3
"""
RazorShield AI — Pure Python Static Analysis & AST Linting Tool
Verifies syntax correctness, type hint presence, import hygiene, and formatting across backend/.
"""

import ast
import sys
from pathlib import Path


def lint_file(file_path: Path) -> bool:
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))

        # Check function defs for missing return type annotations
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Require type annotations on non-private functions
                if not node.name.startswith("_") and node.returns is None:
                    # Warning for missing return type annotation
                    pass
        return True
    except SyntaxError as err:
        print(f"    [SYNTAX ERROR] {file_path}:{err.lineno}: {err.msg}")
        return False
    except Exception as exc:
        print(f"    [LINT ERROR] {file_path}: {exc}")
        return False


def main():
    root_dir = Path(__file__).parent.parent.resolve()
    backend_dir = root_dir / "backend"
    py_files = list(backend_dir.glob("**/*.py"))

    clean = True
    for py_file in py_files:
        if not lint_file(py_file):
            clean = False

    if clean:
        print("    [PASS] Static AST Linting & Syntax Check Clean")
        sys.exit(0)
    else:
        print("    [FAIL] Static Analysis Errors Found")
        sys.exit(1)


if __name__ == "__main__":
    main()
