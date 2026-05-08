
import pytest
import allure
from core.api_client import APIClient
from core.data_factory import generate_object


@allure.feature("API Testing")
@allure.story("DELETE /api/v1/RoleXResourcePermission/{id}")
@allure.severity(allure.severity_level.CRITICAL)
def test_delete_api_v1_rolexresourcepermission_id(request):

    client = APIClient()


    # Get real ID
    list_response = client.get("/api/v1/RoleXResourcePermission")
    assert list_response.status_code == 200

    data = list_response.json()
    assert len(data) > 0

    sample_id = data[0]["id"]
    endpoint = "/api/v1/RoleXResourcePermission/{id}".replace("{id}", str(sample_id))

    response = client.delete(endpoint)


    # Attach response to request node for reporting
    request.node.response = response


    assert response.status_code in [200, 201, 204],         f"Failed: {response.status_code} - {response.text}"
