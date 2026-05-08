# API Testing Framework with Agentic Auto-Fix

An automated API testing framework that generates pytest tests from a Swagger/OpenAPI spec, runs them with detailed reporting, and **automatically fixes failing tests using [Devin AI](https://devin.ai)**.

## How It Works

```
┌──────────┐     ┌───────────┐     ┌────────────┐     ┌───────────┐
│ Swagger  │────>│ Generate  │────>│ Run pytest │────>│ Devin AI  │
│ spec     │     │ tests     │     │ + JSON     │     │ auto-fix  │
│          │     │           │     │ report     │     │ failures  │
└──────────┘     └───────────┘     └────────────┘     └───────────┘
                                         │                  │
                                         └──────────────────┘
                                          re-run until pass
```

1. **Generate** — `generate_api_tests.py` reads `swagger.json` and creates pytest test files in `tests/api/generated/`.
2. **Run** — pytest executes the tests and produces HTML, Allure, and JSON reports in `api-artifacts/`.
3. **Fix** — `run_and_fix.py` reads the JSON report, identifies failures, and creates a Devin session with full context (swagger spec + failing test code + error details). Devin analyzes the failures and creates a PR with fixes.
4. **Repeat** — With `--wait`, the pipeline re-runs tests after Devin finishes, up to N retries.

## Quick Start

### 1. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API credentials and Devin API key
```

**Required `.env` variables:**

| Variable       | Description                                          |
|----------------|------------------------------------------------------|
| `API_BASE_URL` | Base URL of the API under test                       |
| `BASE_URL`     | App login URL (for token capture)                    |
| `USER_NAME`    | Login email                                          |
| `PASSWORD`     | Login password                                       |
| `DEVIN_API_KEY`| Devin API key (from https://app.devin.ai/settings)   |

### 3. Generate Tests

```bash
python generate_api_tests.py
```

This reads `swagger.json` and creates test files in `tests/api/generated/`.

### 4. Run Tests

```bash
pytest tests/api/generated/ -v
```

Reports are saved to `api-artifacts/<date>/<run>/`:
- `api-pytest-report.html` — HTML report
- `api-pytest-report.json` — JSON report (used by the agent)
- `api-allure-results/` — Allure results

### 5. Auto-Fix Failing Tests with Devin

```bash
# Run tests and send failures to Devin:
python run_and_fix.py

# Use an existing report:
python run_and_fix.py --report api-artifacts/2024-01-15/run-143000/api-pytest-report.json

# Wait for Devin to finish, then re-run (up to 3 retries):
python run_and_fix.py --wait --max-retries 3

# Just view the latest report summary:
python run_and_fix.py --report-only
```

## Project Structure

```
api-testing/
├── agent/                      # Devin AI auto-fix agent
│   ├── report_parser.py        #   Parse pytest JSON reports
│   └── devin_fixer.py          #   Create Devin sessions to fix tests
├── core/                       # Test framework
│   ├── api_client.py           #   HTTP client with auth
│   ├── auth_manager.py         #   JWT token management
│   ├── data_factory.py         #   Faker-based test data
│   └── token_capture.py        #   Playwright token capture
├── tests/api/generated/        # Auto-generated pytest test files
├── conftest.py                 # Pytest config + reporting hooks
├── generate_api_tests.py       # Swagger → test generator
├── run_and_fix.py              # Orchestrator: run + auto-fix
├── swagger.json                # OpenAPI specification
├── pytest.ini                  # Pytest configuration
└── requirements.txt            # Python dependencies
```

## Getting Your Devin API Key

1. Go to [Devin Settings](https://app.devin.ai/settings)
2. Navigate to **Service Users**
3. Create a new Service User (or use an existing one)
4. Generate an **API key**
5. Add it to your `.env` file as `DEVIN_API_KEY`

## How the Agent Works

When tests fail, the agent (`agent/devin_fixer.py`) constructs a detailed prompt containing:

- The **Swagger/OpenAPI specification** so Devin understands the expected API behavior
- The **source code of all failing test files**
- **Detailed error messages and tracebacks** for each failure
- The **framework code** (APIClient, conftest, data_factory) so Devin understands how tests are structured

This prompt is sent to the [Devin API](https://docs.devin.ai/api-reference/overview), which creates a session where Devin:
1. Analyzes why each test is failing
2. Compares test expectations against the spec
3. Fixes the test code
4. Commits changes and creates a PR
