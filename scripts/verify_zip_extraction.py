#!/usr/bin/env python3
"""
RazorShield AI — Extracted Submission ZIP Verification Script
Validates structural cleanliness of RazorShield_AI_Final.zip and tests extraction
in a strictly external temporary directory outside the workspace tree.
"""

import os
import sys
import zipfile
import shutil
import tempfile
import subprocess


def verify_zip_structure(zip_path="RazorShield_AI_Final.zip"):
    if not os.path.exists(zip_path):
        print(f"[FAIL] Submission zip '{zip_path}' does not exist!")
        sys.exit(1)

    print(f"[*] Inspecting ZIP archive structure: {zip_path}...")
    with zipfile.ZipFile(zip_path, "r") as z:
        namelist = z.namelist()
        total_files = len(namelist)
        print(f"[*] Total archived files count: {total_files}")

        forbidden_dirs = {
            "extracted_submission_audit",
            "final_extracted_audit",
            "fresh_extraction_audit",
            "fresh_test",
            "fresh_test2",
            "extracted_audit_final",
            "scratch",
            "temp",
            "tmp",
        }
        forbidden_exact = ["frontend/app.js", ".env"]

        for name in namelist:
            parts = [p.lower() for p in name.split("/") if p]

            # Check for nested audit/verification directories
            for p in parts:
                if (
                    p in forbidden_dirs
                    or p.startswith("fresh_")
                    or (p.startswith("extracted_") and p != "extracted")
                    or (p.endswith("_audit") and p != "audit")
                ):
                    print(
                        f"[FAIL] Nested verification item '{name}' found in ZIP archive!"
                    )
                    sys.exit(1)
                if p in [
                    "node_modules",
                    "__pycache__",
                    ".mypy_cache",
                    ".ruff_cache",
                    ".pytest_cache",
                ]:
                    print(
                        f"[FAIL] Forbidden directory item '{name}' found in ZIP archive!"
                    )
                    sys.exit(1)

            if name in forbidden_exact:
                print(f"[FAIL] Forbidden file '{name}' found in ZIP archive!")
                sys.exit(1)

            if name.lower().endswith(".db"):
                print(f"[FAIL] Forbidden database file '{name}' found in ZIP archive!")
                sys.exit(1)

        # Mandatory positive assertions
        required = [
            "frontend/dist/index.html",
            "frontend/dist/assets",
            "frontend/src/App.tsx",
            "frontend/src/main.tsx",
            "frontend/package.json",
            "frontend/package-lock.json",
            "backend/app/main.py",
            "backend/app/policy/rbac.py",
            "backend/app/agent/llm_provider.py",
            "scripts/package_submission.py",
        ]

        for req in required:
            if not any(n == req or n.startswith(req + "/") for n in namelist):
                print(f"[FAIL] Mandatory item '{req}' missing from ZIP archive!")
                sys.exit(1)

    print(
        f"[*] ZIP archive structure verified: PASS ({total_files} clean files, 0 nested audit dirs)"
    )
    return total_files


def verify_external_extraction(zip_path="RazorShield_AI_Final.zip"):
    abs_zip = os.path.abspath(zip_path)
    temp_dir = tempfile.mkdtemp(prefix="razorshield_audit_ext_")
    print(f"[*] Extracting {zip_path} into external temp directory: {temp_dir}...")

    env = {**os.environ, "PYTHONPATH": temp_dir}

    try:
        with zipfile.ZipFile(abs_zip, "r") as z:
            z.extractall(temp_dir)

        print("[*] Running verification gate from external temp directory...")

        # 1. Environment check
        res = subprocess.run(
            [sys.executable, "scripts/check_environment.py"],
            cwd=temp_dir,
            env=env,
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            print(
                f"[FAIL] check_environment.py failed in extracted archive:\n{res.stderr}\n{res.stdout}"
            )
            sys.exit(1)
        print("  [PASS] check_environment.py")

        # 2. Submission integrity check
        res = subprocess.run(
            [sys.executable, "scripts/submission_integrity_check.py"],
            cwd=temp_dir,
            env=env,
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            print(
                f"[FAIL] submission_integrity_check.py failed in extracted archive:\n{res.stderr}\n{res.stdout}"
            )
            sys.exit(1)
        print("  [PASS] submission_integrity_check.py")

        # 3. Negative regression test suite
        res = subprocess.run(
            [sys.executable, "scripts/submission_integrity_check.py", "--test"],
            cwd=temp_dir,
            env=env,
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            print(
                f"[FAIL] submission_integrity_check.py --test failed in extracted archive:\n{res.stderr}\n{res.stdout}"
            )
            sys.exit(1)
        print("  [PASS] submission_integrity_check.py --test")

        # 4. Quality check
        res = subprocess.run(
            [sys.executable, "scripts/quality_check.py"],
            cwd=temp_dir,
            env=env,
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            print(
                f"[FAIL] quality_check.py failed in extracted archive:\n{res.stderr}\n{res.stdout}"
            )
            sys.exit(1)
        print("  [PASS] quality_check.py")

        print("[*] External extraction verification 100% PASS!")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"[*] Cleaned up external temp directory: {temp_dir}")


if __name__ == "__main__":
    zip_path = "RazorShield_AI_Final.zip"
    if os.path.exists(zip_path):
        verify_zip_structure(zip_path)
        verify_external_extraction(zip_path)
    elif os.path.exists("backend/app/main.py"):
        print(
            "[*] 'RazorShield_AI_Final.zip' not found in root, running in ALREADY-EXTRACTED REPOSITORY mode..."
        )
        env = {**os.environ, "PYTHONPATH": "."}
        checks = [
            ("scripts/check_environment.py", []),
            ("scripts/submission_integrity_check.py", []),
            ("scripts/submission_integrity_check.py", ["--test"]),
            ("scripts/quality_check.py", []),
        ]
        for script, args in checks:
            cmd = [sys.executable, script] + args
            res = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if res.returncode != 0:
                print(
                    f"[FAIL] {script} {' '.join(args)} failed in extracted workspace:\n{res.stderr}\n{res.stdout}"
                )
                sys.exit(1)
            print(f"  [PASS] {script} {' '.join(args)}")
        print("[*] Already-extracted repository verification 100% PASS!")
    else:
        print(
            "[FAIL] Neither 'RazorShield_AI_Final.zip' nor valid extracted workspace root found!"
        )
        sys.exit(1)
