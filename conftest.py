from logging import config
import os
import pytest
import allure
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

IS_API_RUN = "tests/api" in " ".join(os.sys.argv)

# -------------------------------
# 📁 VERSIONED REPORT STRUCTURE
# -------------------------------
DATE_STR = datetime.now().strftime("%Y-%m-%d")
RUN_STR = datetime.now().strftime("run-%H%M%S")

ARTIFACT_ROOT = Path(os.getenv("ARTIFACT_ROOT", "api-artifacts"))

if IS_API_RUN:
    BASE_DIR = ARTIFACT_ROOT / DATE_STR / RUN_STR
    BASE_DIR.mkdir(parents=True, exist_ok=True)
else:
    BASE_DIR = None

PYTEST_HTML_REPORT = BASE_DIR / "api-pytest-report.html"
ALLURE_RESULTS_DIR = BASE_DIR / "api-allure-results"
PYTEST_JSON_REPORT = BASE_DIR / "api-pytest-report.json"

LATEST_FILE = ARTIFACT_ROOT / "LATEST_RUN.txt"
LATEST_FILE.parent.mkdir(parents=True, exist_ok=True)

if IS_API_RUN:
    with open(LATEST_FILE, "w") as f:
        f.write(str(BASE_DIR))
    
def is_api_run(config, items=None):
    if items:
        return any("api" in item.keywords for item in items)
    return True

def pytest_collection_modifyitems(config, items):
    for item in items:
        if "tests/api" in str(item.fspath):
            item.add_marker("api")

# -------------------------------
# 🔧 AUTO-INJECT REPORT PATHS
# -------------------------------
def pytest_load_initial_conftests(args):
    args.append(f"--html={PYTEST_HTML_REPORT}")
    args.append("--self-contained-html")
    args.append(f"--alluredir={ALLURE_RESULTS_DIR}")

    # ✅ ADD THIS
    args.append(f"--json-report")
    args.append(f"--json-report-file={PYTEST_JSON_REPORT}")


# -------------------------------
# 📊 PYTEST CONFIG
# -------------------------------
def pytest_configure(config):
    if not IS_API_RUN:
        return

    os.makedirs(ALLURE_RESULTS_DIR, exist_ok=True)

    config.option.htmlpath = str(PYTEST_HTML_REPORT)
    config.option.self_contained_html = True
    config.option.allure_report_dir = str(ALLURE_RESULTS_DIR)

    config.option.json_report = True
    config.option.json_report_file = str(PYTEST_JSON_REPORT)    

    config._metadata = {
        "Project": "API Automation Framework",
        "Module": "API Testing",
        "Environment": "QA",
        "Execution Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# -------------------------------
# 📌 CAPTURE TEST RESULT + ALLURE ATTACHMENTS
# -------------------------------
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):

    if "api" not in item.keywords:
        yield
        return

    outcome = yield
    report = outcome.get_result()

    setattr(item, "rep_" + report.when, report)

    if report.when == "call":

        response = getattr(item, "response", None)

        if response:
            try:
                allure.attach(
                    f"{response.request.method} {response.url}",
                    name="API Endpoint",
                    attachment_type=allure.attachment_type.TEXT
                )

                allure.attach(
                    str(response.request.headers),
                    name="Request Headers",
                    attachment_type=allure.attachment_type.TEXT
                )

                if response.request.body:
                    allure.attach(
                        str(response.request.body),
                        name="Request Body",
                        attachment_type=allure.attachment_type.TEXT
                    )

                allure.attach(
                    str(response.status_code),
                    name="Status Code",
                    attachment_type=allure.attachment_type.TEXT
                )

                allure.attach(
                    response.text,
                    name="Response Body",
                    attachment_type=allure.attachment_type.JSON
                )

            except Exception as e:
                print("Allure attach failed:", e)


# -------------------------------
# 📊 TERMINAL SUMMARY + PDF GENERATION
# -------------------------------
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not IS_API_RUN:
        return

    print("\n📁 Reports Generated At:")
    print(f"👉 HTML Report: {PYTEST_HTML_REPORT}")
    print(f"👉 Allure Results: {ALLURE_RESULTS_DIR}")

    # -------- PDF GENERATION --------
    try:
        from playwright.sync_api import sync_playwright

        html = config.option.htmlpath

        if not html or not os.path.exists(html):
            print("[PDF] HTML report not found")
            return

        pdf = html.replace(".html", ".pdf")

        print("\n📄 Generating expanded PDF report...")

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(f"file:///{html.replace(os.sep, '/')}")

            # safer wait
            page.wait_for_timeout(2000)

            # try show all details
            try:
                show_button = page.locator("#show_all_details")
                if show_button.is_visible():
                    show_button.click()
            except:
                pass

            # expand logs safely
            expanders = page.locator(".logexpander")
            count = expanders.count()

            if count > 0:
                for i in range(count):
                    try:
                        expanders.nth(i).click()
                    except:
                        pass

            page.wait_for_timeout(1500)

            page.pdf(
                path=pdf,
                format="A4",
                print_background=True
            )

            browser.close()

        print(f"✅ PDF Report Generated: {pdf}")

    except Exception as e:
        print(f"❌ PDF generation failed: {e}")


# -------------------------------
# 🏁 SESSION FINISH → ALLURE AUTO GENERATE
# -------------------------------
def pytest_sessionfinish(session, exitstatus):
    if not IS_API_RUN:
        return

    print("\n📊 Generating Allure Report...")

    try:
        allure_results = str(ALLURE_RESULTS_DIR)
        allure_report_dir = str(BASE_DIR / "allure-report")

        subprocess.run(
            f"allure generate {allure_results} -o {allure_report_dir} --clean",
            shell=True,
            check=True
        )

        print(f"✅ Allure report generated at: {allure_report_dir}")

    except Exception as e:
        print(f"❌ Failed to generate Allure report: {e}")

    print("\n✅ Test Execution Completed")
    print(f"📁 Artifacts stored in: {BASE_DIR}")


# -------------------------------
# 📊 HTML REPORT HEADER
# -------------------------------
def pytest_html_results_summary(prefix, summary, postfix):
    if not IS_API_RUN:
        return

    summary.extend([
        "<h2>API Test Execution Summary</h2>",
        f"<p><strong>Execution Folder:</strong> {BASE_DIR}</p>",
        f"<p><strong>Date:</strong> {DATE_STR}</p>",
        f"<p><strong>Run:</strong> {RUN_STR}</p>"
    ])