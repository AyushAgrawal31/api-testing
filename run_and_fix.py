#!/usr/bin/env python3
"""Orchestrator: run API tests and auto-fix failures with Devin.

Usage:
    # Run tests, then send failures to Devin:
    python run_and_fix.py

    # Use a specific report instead of running tests:
    python run_and_fix.py --report reports/api-pytest-report.json

    # Wait for Devin to finish and re-run tests:
    python run_and_fix.py --wait --max-retries 3

    # Just view the latest report:
    python run_and_fix.py --report-only
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from agent.report_parser import (
    collect_failing_test_files,
    find_latest_report,
    get_summary,
    load_report,
    parse_failures,
)
from agent.devin_fixer import trigger_fix


TEST_DIR = "tests/api/generated"
SWAGGER_PATH = "swagger.json"


def run_tests() -> str:
    """Run pytest and return the path to the JSON report."""
    print("\n🧪 Running API tests...")
    cmd = [sys.executable, "-m", "pytest", TEST_DIR, "-v"]
    subprocess.run(cmd)

    # Find the report that was just generated
    return find_latest_report()


def print_summary(report: dict) -> None:
    """Print a concise test summary."""
    summary = get_summary(report)
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"   Total:   {summary['total']}")
    print(f"   Passed:  {summary['passed']}")
    print(f"   Failed:  {summary['failed']}")
    print(f"   Errors:  {summary['error']}")
    print(f"   Skipped: {summary['skipped']}")
    if summary.get("duration"):
        print(f"   Duration: {summary['duration']:.2f}s")
    print("=" * 50)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run API tests and auto-fix failures with Devin."
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Path to an existing JSON report (skip running tests).",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Just print the latest report summary; don't trigger Devin.",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for Devin to finish before exiting.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=1,
        help="Max run-fix cycles (only used with --wait). Default: 1.",
    )
    parser.add_argument(
        "--swagger",
        default=SWAGGER_PATH,
        help=f"Path to swagger spec. Default: {SWAGGER_PATH}",
    )
    args = parser.parse_args()

    for attempt in range(1, args.max_retries + 1):
        # Step 1: Get the report
        if args.report:
            report_path = args.report
        elif args.report_only:
            report_path = find_latest_report()
        else:
            report_path = run_tests()

        print(f"\n📄 Using report: {report_path}")
        report = load_report(report_path)
        print_summary(report)

        # Step 2: Check for failures
        failures = parse_failures(report)

        if not failures:
            print("\n✅ All tests passed! Nothing to fix.")
            sys.exit(0)

        if args.report_only:
            print(f"\n❌ {len(failures)} test(s) failed:")
            for f in failures:
                print(f"   - {f['nodeid']}")
            sys.exit(1)

        # Step 3: Collect failing test source code
        test_files = collect_failing_test_files(TEST_DIR, failures)

        print(f"\n❌ {len(failures)} test(s) failed. Sending to Devin for fixing...")

        # Step 4: Trigger Devin
        result = trigger_fix(
            failures=failures,
            test_files=test_files,
            swagger_path=args.swagger,
            wait=args.wait,
        )

        if not args.wait:
            print(f"\n🔗 Devin is working on fixes: {result['session']['url']}")
            print("   Run again after Devin completes to verify, or use --wait.")
            sys.exit(0)

        # If waiting, check Devin's status
        final_state = result.get("final_state", {})
        status = final_state.get("status_enum", "unknown")

        if status == "finished":
            print(f"\n✅ Devin finished (attempt {attempt}/{args.max_retries}). Re-running tests...")
            args.report = None  # Force re-run of tests
            continue
        else:
            print(f"\n⚠️  Devin session ended with status: {status}")
            print(f"   Check the session: {result['session']['url']}")
            sys.exit(1)

    print(f"\n⚠️  Reached max retries ({args.max_retries}).")
    sys.exit(1)


if __name__ == "__main__":
    main()
