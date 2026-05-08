import json
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

AUTH_FILE = "auth_tokens.json"

BASE_URL = os.getenv("BASE_URL")

USER_NAME = os.getenv("USER_NAME")
PASSWORD = os.getenv("PASSWORD")


def capture_token():

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)

        context = browser.new_context()

        page = context.new_page()

        token_saved = False

        collected = {
            "bearer_token": None,
            "X-Account-Id": None,
            "X-Tenant-Id": None,
            "X-Workspace-Id": None
        }

        # SAME interception logic as your TS version
        def handle_request(request):

            headers = request.headers

            # Capture token
            auth = headers.get("authorization")
            if auth and auth.startswith("Bearer"):
                collected["bearer_token"] = auth.replace("Bearer ", "")

            # Capture other headers if present
            if headers.get("x-account-id"):
                collected["X-Account-Id"] = headers.get("x-account-id")

            if headers.get("x-tenant-id"):
                collected["X-Tenant-Id"] = headers.get("x-tenant-id")

            if headers.get("x-workspace-id"):
                collected["X-Workspace-Id"] = headers.get("x-workspace-id")

            # Save only when token is found (headers may come later, but save anyway)
            if collected["bearer_token"]:

                data = {
                    "bearer_token": collected["bearer_token"],
                    "headers": {
                        "X-Account-Id": collected["X-Account-Id"],
                        "X-Tenant-Id": collected["X-Tenant-Id"],
                        "X-Workspace-Id": collected["X-Workspace-Id"]
                    }
                }

                with open(AUTH_FILE, "w") as f:
                    json.dump(data, f, indent=2)

                print("Token and headers captured.")

        page.on("request", handle_request)

        # Your exact login logic
        page.goto(BASE_URL)

        page.get_by_role("textbox", name="Email Address").fill(USER_NAME)
        page.get_by_role("textbox", name="Password").fill(PASSWORD)
        page.get_by_role("button", name="Sign in").click()

        # wait for API calls to happen
        page.wait_for_timeout(30000)

        browser.close()


if __name__ == "__main__":
    capture_token()