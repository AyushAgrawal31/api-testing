
import pytest
import allure
from core.api_client import APIClient
from core.data_factory import generate_object


@allure.feature("API Testing")
@allure.story("GET /api/v1/FlowBuilder/{flowBuilderId}/FlowTasks")
@allure.severity(allure.severity_level.CRITICAL)
def test_get_api_v1_flowbuilder_flowbuilderid_flowtasks(request):

    client = APIClient()

    endpoint = "/api/v1/FlowBuilder/{flowBuilderId}/FlowTasks"

    response = client.get(endpoint, params={'SortColumn': 'test', 'SortOrder': 'test', 'Title': 'test', 'FlowTaskTypes': 'test', 'PhaseId': 'test', 'MilestoneId': 'test', 'SubMilestoneId': 'test', 'PageNumber': 1, 'PageSize': 1})


    # Attach response to request node for reporting
    request.node.response = response


    assert response.status_code in [200, 201, 204],         f"Failed: {response.status_code} - {response.text}"
