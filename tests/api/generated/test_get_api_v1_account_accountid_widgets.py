
import pytest
import allure
from core.api_client import APIClient
from core.data_factory import generate_object


@allure.feature("API Testing")
@allure.story("GET /api/v1/Account/{accountId}/Widgets")
@allure.severity(allure.severity_level.CRITICAL)
def test_get_api_v1_account_accountid_widgets(request):

    client = APIClient()

    endpoint = "/api/v1/Account/{accountId}/Widgets"

    response = client.get(endpoint, params={'SortColumn': 'test', 'SortOrder': 'test', 'Title': 'test', 'PageNumber': 1, 'PageSize': 1})


    # Attach response to request node for reporting
    request.node.response = response


    assert response.status_code in [200, 201, 204],         f"Failed: {response.status_code} - {response.text}"
