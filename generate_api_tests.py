import json
import os
import re

SWAGGER_FILE = "swagger.json"
OUTPUT_DIR = "tests/api/generated"


# Load swagger
def load_swagger():
    with open(SWAGGER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# Convert endpoint to function name
def sanitize_name(method, endpoint):
    name = endpoint.strip("/")
    name = re.sub(r"[{}]", "", name)
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    return f"test_{method.lower()}_{name.lower()}"


# Extract collection endpoint
def get_collection_endpoint(endpoint):
    parts = endpoint.split("/")
    if parts[-1].startswith("{"):
        return "/".join(parts[:-1])
    return None


# Extract request body schema
def extract_body_schema(details, components):
    request_body = details.get("requestBody")

    if not request_body:
        return None

    content = request_body.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema")

    if not schema:
        return None

    if "$ref" in schema:
        ref = schema["$ref"].split("/")[-1]
        schema = components.get(ref, {})

    return schema


# Extract query params
def extract_query_params(details):
    params = details.get("parameters", [])
    query_params = {}

    for param in params:
        if param.get("in") == "query":
            name = param["name"]
            param_type = param.get("schema", {}).get("type", "string")

            if param_type == "integer":
                query_params[name] = 1
            else:
                query_params[name] = "test"

    return query_params


# Create test file
def create_test_file(endpoint, method, details, components):

    function_name = sanitize_name(method, endpoint)

    filename = f"{function_name}.py"
    filepath = os.path.join(OUTPUT_DIR, filename)

    collection_endpoint = get_collection_endpoint(endpoint)
    query_params = extract_query_params(details)
    body = extract_body_schema(details, components)

    content = f'''
import pytest
import allure
from core.api_client import APIClient
from core.data_factory import generate_object


@allure.feature("API Testing")
@allure.story("{method.upper()} {endpoint}")
@allure.severity(allure.severity_level.CRITICAL)
def {function_name}(request):

    client = APIClient()
'''

    # Handle endpoints with ID
    if collection_endpoint:
        content += f'''

    # Get real ID
    list_response = client.get("{collection_endpoint}")
    assert list_response.status_code == 200

    data = list_response.json()
    assert len(data) > 0

    sample_id = data[0]["id"]
    endpoint = "{endpoint}".replace("{{id}}", str(sample_id))
'''
    else:
        content += f'''
    endpoint = "{endpoint}"
'''

    # Build API call
    if method.lower() == "get":

        if query_params:
            content += f'''
    response = client.get(endpoint, params={query_params})
'''
        else:
            content += '''
    response = client.get(endpoint)
'''

    elif method.lower() in ["post", "put"]:

        if body:
            schema_str = json.dumps(body, indent=4)

            schema_str = schema_str.replace("true", "True")
            schema_str = schema_str.replace("false", "False")
            schema_str = schema_str.replace("null", "None")

            content += (
                f"\n"
                f"    schema = {schema_str}\n\n"
                f"    payload = generate_object(schema)\n\n"
                f"    response = client.{method.lower()}(endpoint, json=payload)\n"
            )
        else:
            content += (
                f"\n"
                f"    response = client.{method.lower()}(endpoint)\n"
            )

    elif method.lower() == "delete":
        content += '''
    response = client.delete(endpoint)
'''

    # 🔥 IMPORTANT: Attach response for Allure (conftest will use this)
    content += '''

    # Attach response to request node for reporting
    request.node.response = response
'''

    # Assertion
    content += '''

    assert response.status_code in [200, 201, 204], \
        f"Failed: {response.status_code} - {response.text}"
'''

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print("Created:", filepath)


# Generate all tests
def generate_tests():

    swagger = load_swagger()

    paths = swagger.get("paths", {})
    components = swagger.get("components", {}).get("schemas", {})

    count = 0

    for endpoint, methods in paths.items():
        for method, details in methods.items():

            if method.lower() in ["get", "post", "put", "delete"]:
                create_test_file(endpoint, method, details, components)
                count += 1

    print(f"\nTotal tests generated: {count}")


# Main
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    generate_tests()