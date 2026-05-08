import os
import uuid
import requests
from core.auth_manager import AuthManager
from dotenv import load_dotenv

load_dotenv()


class APIClient:

    def __init__(self):

        self.base_url = os.getenv("API_BASE_URL")

        self.session = requests.Session()

    def _headers(self):

        token = AuthManager.get_token()
        saved_headers = AuthManager.get_headers()

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Correlation-Id": str(uuid.uuid4()),
            **saved_headers
        }

    def get(self, endpoint, params=None):

        return self.session.get(
            f"{self.base_url}{endpoint}",
            headers=self._headers(),
            params=params
        )

    def post(self, endpoint, json=None):

        return self.session.post(
            f"{self.base_url}{endpoint}",
            headers=self._headers(),
            json=json
        )

    def put(self, endpoint, json=None):

        return self.session.put(
            f"{self.base_url}{endpoint}",
            headers=self._headers(),
            json=json
        )

    def delete(self, endpoint):

        return self.session.delete(
            f"{self.base_url}{endpoint}",
            headers=self._headers()
        )