import json
import time
import base64
from pathlib import Path

from core.token_capture import capture_token


AUTH_FILE = Path("auth_tokens.json")


class AuthManager:

    _token = None
    _headers = None
    _expiry = 0

    @classmethod
    def _decode_expiry(cls, token: str) -> int:

        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)

        decoded = json.loads(base64.b64decode(payload))

        return decoded["exp"]

    @classmethod
    def _load_tokens(cls):

        if not AUTH_FILE.exists():
            print("No token file found. Capturing new token...")
            capture_token()

        with open(AUTH_FILE) as f:
            data = json.load(f)

        cls._token = data["bearer_token"]

        cls._headers = {
            "X-Account-Id": data["headers"]["X-Account-Id"],
            "X-Tenant-Id": data["headers"]["X-Tenant-Id"],
            "X-Workspace-Id": data["headers"]["X-Workspace-Id"]
        }

        cls._expiry = cls._decode_expiry(cls._token)

    @classmethod
    def _ensure_valid_token(cls):

        if cls._token is None:
            cls._load_tokens()

        now = int(time.time())

        if now >= cls._expiry - 60:
            print("Token expired or expiring soon. Capturing new token...")
            capture_token()
            cls._load_tokens()

    @classmethod
    def get_headers(cls):

        cls._ensure_valid_token()
        return cls._headers

    @classmethod
    def get_token(cls):

        cls._ensure_valid_token()
        return cls._token