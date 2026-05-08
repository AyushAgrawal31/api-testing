"""Parse pytest JSON reports and extract actionable failure information."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_report(report_path: str) -> dict[str, Any]:
    """Load a pytest JSON report from disk."""
    path = Path(report_path)
    if not path.exists():
        raise FileNotFoundError(f"Report not found: {report_path}")
    return json.loads(path.read_text())


def find_latest_report(artifact_root: str = "api-artifacts") -> str:
    """Find the latest JSON report using the LATEST_RUN.txt pointer."""
    latest_file = Path(artifact_root) / "LATEST_RUN.txt"
    if not latest_file.exists():
        raise FileNotFoundError(
            f"No LATEST_RUN.txt found in {artifact_root}. "
            "Run the tests first: pytest tests/api/generated/"
        )

    run_dir = Path(latest_file.read_text().strip())
    report_path = run_dir / "api-pytest-report.json"
    if not report_path.exists():
        raise FileNotFoundError(f"JSON report not found at {report_path}")

    return str(report_path)


def parse_failures(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract structured failure info from a pytest JSON report."""
    failures: list[dict[str, Any]] = []
    for test in report.get("tests", []):
        if test.get("outcome") != "failed":
            continue
        call_info = test.get("call", {})
        failures.append({
            "nodeid": test["nodeid"],
            "outcome": test["outcome"],
            "duration": test.get("duration"),
            "longrepr": call_info.get("longrepr", ""),
            "crash": call_info.get("crash", {}),
            "stdout": call_info.get("stdout", ""),
            "stderr": call_info.get("stderr", ""),
        })
    return failures


def get_summary(report: dict[str, Any]) -> dict[str, Any]:
    """Return a concise summary dict from a pytest JSON report."""
    summary = report.get("summary", {})
    return {
        "total": summary.get("total", 0),
        "passed": summary.get("passed", 0),
        "failed": summary.get("failed", 0),
        "error": summary.get("error", 0),
        "skipped": summary.get("skipped", 0),
        "duration": report.get("duration"),
    }


def collect_failing_test_files(test_dir: str, failures: list[dict[str, Any]]) -> dict[str, str]:
    """Read the source code of test files that contain failures."""
    failing_files: set[str] = set()
    for f in failures:
        file_part = f["nodeid"].split("::")[0]
        failing_files.add(file_part)

    test_files: dict[str, str] = {}
    for fp in failing_files:
        path = Path(fp)
        if path.exists():
            test_files[fp] = path.read_text()

    return test_files
