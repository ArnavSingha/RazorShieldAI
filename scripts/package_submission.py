#!/usr/bin/env python3
import os
import zipfile


def should_exclude(filepath):
    # Normalize path separator
    filepath = filepath.replace("\\", "/")
    basename = os.path.basename(filepath)
    parts = [p.lower() for p in filepath.split("/") if p and p != "."]

    # 1. Always exclude ZIP files to prevent self-packaging or archiving stale zips
    if filepath.lower().endswith(".zip"):
        return True

    # 2. Exclude environment files (except .env.example)
    if basename.startswith(".env") and basename != ".env.example":
        return True

    # 3. Exclude local databases
    if (
        filepath.lower().endswith(".db")
        or filepath.lower().endswith(".sqlite")
        or filepath.lower().endswith(".sqlite3")
    ):
        return True

    # 4. Exclude test extraction / audit / verification directories
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
    for p in parts:
        if (
            p in forbidden_dirs
            or p.startswith("fresh_")
            or (p.startswith("extracted_") and p != "extracted")
            or (p.endswith("_audit") and p != "audit")
        ):
            return True

    # 5. Build, cache, and VCS directories to exclude
    exclude_dirs = {
        "node_modules",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".venv",
        "venv",
        "env",
        ".git",
        ".github",
        ".vscode",
        ".idea",
        "build",
    }

    if any(d in exclude_dirs for d in parts):
        return True

    return False


def package():
    zip_name = "RazorShield_AI_Final.zip"
    if os.path.exists(zip_name):
        os.remove(zip_name)

    print(f"Creating {zip_name} from clean repository root...")

    added_files = []
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("."):
            # Prune excluded directories in-place during walk
            dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]

            for file in files:
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, ".")
                if not should_exclude(rel_path) and rel_path != zip_name:
                    zipf.write(filepath, arcname=rel_path)
                    added_files.append(rel_path)

    print(
        f"[SUCCESS] Packaging complete: {zip_name} ({len(added_files)} total files archived)"
    )
    return len(added_files)


if __name__ == "__main__":
    package()
