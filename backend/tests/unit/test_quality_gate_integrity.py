"""
RazorShield AI — Unit Tests: Quality Gate Integrity
Verifies that missing mandatory quality gate tools fail explicitly rather than producing a false PASS.
"""

from scripts.quality_check import run_mandatory_tool


def test_mandatory_tool_missing_fails():
    success = run_mandatory_tool(
        "Fake Missing Tool", "non_existent_tool_binary_xyz_123 --version"
    )
    assert success is False
