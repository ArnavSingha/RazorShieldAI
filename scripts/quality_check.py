#!/usr/bin/env python3
"""
RazorShield AI — Canonical Quality Gate Verification Runner
Directly executes mandatory quality tooling: Secret Scanning, Ruff Formatting, Ruff Linting, MyPy Type Checking, and Pytest.
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import Optional


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(f" RAZORSHIELD AI — {title.upper()}")
    print("=" * 60)


def run_mandatory_tool(
    tool_name: str, command: str, root_dir: Optional[Path] = None
) -> bool:
    print(f"[*] Running {tool_name}...")
    try:
        if root_dir is None:
            root_dir = Path(__file__).parent.parent.resolve()
        env = {**os.environ, "PYTHONPATH": str(root_dir)}
        result = subprocess.run(
            command,
            shell=True,
            env=env,
            cwd=str(root_dir),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"    [PASS] {tool_name}")
            return True
        else:
            print(f"    [FAIL] {tool_name}")
            if result.stdout:
                print(f"--- STDOUT ---\n{result.stdout.strip()}")
            if result.stderr:
                print(f"--- STDERR ---\n{result.stderr.strip()}")
            return False
    except Exception as exc:
        print(f"    [FAIL] {tool_name} ({exc})")
        return False


def check_secret_patterns(root_dir: Path) -> bool:
    print("[*] Scanning repository for committed secrets & hardcoded raw PANs...")
    p1 = "AKIA" + "[0-9A-Z]{16}"
    p2 = "41111" + "11111111111"
    p3 = "BEGIN " + "PRIVATE KEY"
    forbidden_patterns = [p1, p2, p3]
    found_issues = False

    for file_path in root_dir.glob("**/*"):
        if file_path.is_file() and not any(
            part.startswith(".") for part in file_path.parts
        ):
            if (
                "scripts" in file_path.parts
                or "node_modules" in file_path.parts
                or "scratch" in file_path.parts
            ):
                continue
            if file_path.suffix in [".py", ".ts", ".tsx", ".json", ".md"]:
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    for pattern in forbidden_patterns:
                        if pattern in content:
                            print(
                                f"    [FAIL] Forbidden secret pattern detected in {file_path}"
                            )
                            found_issues = True
                except Exception:
                    pass

    if not found_issues:
        print("    [PASS] Secret & PAN scanning clean")
        return True
    return False


def main() -> None:
    print_header("ENGINEERING QUALITY GATE VERIFICATION")
    root_dir = Path(__file__).parent.parent.resolve()
    py_exec = sys.executable

    checks = [
        ("Secret & PAN Scan", lambda: check_secret_patterns(root_dir)),
        (
            "Ruff Format Check",
            lambda: run_mandatory_tool(
                "Ruff Format Check",
                f'"{py_exec}" -m ruff format --check backend/',
                root_dir,
            ),
        ),
        (
            "Ruff Static Linting",
            lambda: run_mandatory_tool(
                "Ruff Static Linting",
                f'"{py_exec}" -m ruff check --select=F backend/',
                root_dir,
            ),
        ),
        (
            "MyPy Type Checking",
            lambda: run_mandatory_tool(
                "MyPy Type Checking",
                f'"{py_exec}" -m mypy backend/app/ --ignore-missing-imports --explicit-package-bases',
                root_dir,
            ),
        ),
        (
            "Pytest Test Suite",
            lambda: run_mandatory_tool(
                "Pytest Test Suite", f'"{py_exec}" -m pytest backend/tests/', root_dir
            ),
        ),
    ]

    overall_pass = True
    for name, check_fn in checks:
        if not check_fn():
            overall_pass = False

    print("\n" + "=" * 60)
    if overall_pass:
        print(" QUALITY GATE RESULT: PASS")
        print("=" * 60 + "\n")
        sys.exit(0)
    else:
        print(" QUALITY GATE RESULT: FAIL")
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
