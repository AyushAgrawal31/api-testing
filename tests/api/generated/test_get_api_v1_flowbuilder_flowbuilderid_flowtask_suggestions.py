
import pytest
import allure
from core.api_client import APIClient
from core.data_factory import generate_object


@allure.feature("API Testing")
@allure.story("GET /api/v1/FlowBuilder/{flowBuilderId}/FlowTask/Suggestions")
@allure.severity(allure.severity_level.CRITICAL)
def test_get_api_v1_flowbuilder_flowbuilderid_flowtask_suggestions(request):

    client = APIClient()

    endpoint = "/api/v1/FlowBuilder/{flowBuilderId}/FlowTask/Suggestions"

    response = client.get(endpoint, params={'title': 'test'})


    # Attach response to request node for reporting
    request.node.response = response


    assert response.status_code in [200, 201, 204],         f"Failed: {response.status_code} - {response.text}"
