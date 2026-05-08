"""Create a Devin session to auto-fix failing API tests.

Reads the pytest JSON report, constructs a detailed prompt with the swagger
spec, failing test source code, and error details, then triggers a Devin
session via the REST API to analyze and fix the tests.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import requests

DEVIN_API_BASE = "https://api.devin.ai"


def _get_api_key() -> str:
    key = os.environ.get("DEVIN_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "DEVIN_API_KEY is not set.\n"
            "1. Go to https://app.devin.ai/settings\n"
            "2. Create a Service User and generate an API key\n"
            "3. Add DEVIN_API_KEY=<key> to your .env file"
        )
    return key


def _build_fix_prompt(
    failures: list[dict[str, Any]],
    test_files: dict[str, str],
    swagger_path: str,
    supporting_files: dict[str, str],
) -> str:
    """Construct the prompt that Devin will receive to fix failing tests."""

    # Read a trimmed version of the swagger spec (keep under 30k chars)
    swagger_content = Path(swagger_path).read_text()
    if len(swagger_content) > 30000:
        swagger_content = swagger_content[:30000] + "\n... (truncated)"

    parts = [
        "# Auto-Fix Failing API Tests\n",
        "You are working on the repo `AyushAgrawal31/api-testing`.",
        "This repo contains auto-generated pytest API tests created from a Swagger/OpenAPI spec.",
        "Some tests are failing. Your job is to fix them.\n",
        "## Instructions",
        "1. Analyze each failing test and its error message carefully.",
        "2. Compare the test expectations against the Swagger spec.",
        "3. Look at the supporting framework code (APIClient, conftest, data_factory) to understand how tests work.",
        "4. Fix the test files so they correctly test the API.",
        "5. Common issues include:",
        "   - Wrong expected status codes (the API may return 200 or 404 depending on data)",
        "   - Missing or incorrect query parameters",
        "   - Incorrect request body schemas",
        "   - Endpoints that need a valid ID from a prior listing call",
        "   - Authentication or header issues",
        "6. After fixing, commit your changes and create a PR.\n",
    ]

    # Failing tests
    parts.append("## Failing Tests\n")
    for i, failure in enumerate(failures, 1):
        parts.append(f"### Failure {i}: `{failure['nodeid']}`")
        parts.append("```")
        parts.append(str(failure.get("longrepr", "No details available")))
        parts.append("```\n")

    # Test source files
    parts.append("## Failing Test Source Files\n")
    for filepath, content in test_files.items():
        parts.append(f"### `{filepath}`")
        parts.append("```python")
        parts.append(content)
        parts.append("```\n")

    # Supporting framework files
    parts.append("## Supporting Framework Code\n")
    for filepath, content in supporting_files.items():
        parts.append(f"### `{filepath}`")
        parts.append("```python")
        parts.append(content)
        parts.append("```\n")

    # Swagger spec (trimmed)
    parts.append("## Swagger Specification (trimmed)\n")
    parts.append(f"File: `{swagger_path}`")
    parts.append("```json")
    parts.append(swagger_content)
    parts.append("```\n")

    return "\n".join(parts)


def _load_supporting_files() -> dict[str, str]:
    """Read framework files that give context about how tests work."""
    supporting: dict[str, str] = {}
    files_to_read = [
        "core/api_client.py",
        "core/data_factory.py",
        "core/auth_manager.py",
        "conftest.py",
        "generate_api_tests.py",
    ]
    for fp in files_to_read:
        path = Path(fp)
        if path.exists():
            supporting[fp] = path.read_text()
    return supporting


def create_fix_session(
    failures: list[dict[str, Any]],
    test_files: dict[str, str],
    swagger_path: str = "swagger.json",
) -> dict[str, Any]:
    """Create a Devin session to fix the failing tests.

    Returns the session info dict with session_id and url.
    """
    api_key = _get_api_key()
    supporting_files = _load_supporting_files()

    prompt = _build_fix_prompt(failures, test_files, swagger_path, supporting_files)

    print(f"\n🤖 Creating Devin session to fix {len(failures)} failing test(s)...")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "prompt": prompt,
        "title": f"Auto-fix {len(failures)} failing API test(s)",
    }

    response = requests.post(
        f"{DEVIN_API_BASE}/v1/sessions",
        headers=headers,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    session_info = response.json()

    print(f"✅ Devin session created!")
    print(f"   Session ID: {session_info['session_id']}")
    print(f"   URL:        {session_info['url']}")

    return session_info


def poll_session(session_id: str, timeout_minutes: int = 30) -> dict[str, Any]:
    """Poll a Devin session until it completes or times out."""
    api_key = _get_api_key()
    headers = {"Authorization": f"Bearer {api_key}"}
    deadline = time.time() + timeout_minutes * 60

    print(f"\n⏳ Waiting for Devin to finish (timeout: {timeout_minutes}min)...")

    while time.time() < deadline:
        resp = requests.get(
            f"{DEVIN_API_BASE}/v1/session/{session_id}",
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        status = data.get("status_enum", data.get("status", "unknown"))
        print(f"   Status: {status}")

        if status in {"finished", "stopped", "blocked", "failed"}:
            return data

        time.sleep(30)

    print("⚠️  Polling timed out.")
    return {"status_enum": "timeout", "session_id": session_id}


def trigger_fix(
    failures: list[dict[str, Any]],
    test_files: dict[str, str],
    swagger_path: str = "swagger.json",
    wait: bool = False,
    timeout_minutes: int = 30,
) -> dict[str, Any]:
    """High-level entry point: create a Devin fix session and optionally wait."""
    session = create_fix_session(failures, test_files, swagger_path)
    result: dict[str, Any] = {"session": session}

    if wait:
        final_state = poll_session(session["session_id"], timeout_minutes=timeout_minutes)
        result["final_state"] = final_state

    return result
