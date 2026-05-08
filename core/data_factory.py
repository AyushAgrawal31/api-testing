from faker import Faker
import random

fake = Faker()


def generate_value(field_name, field_type="string"):

    name = field_name.lower()

    if "email" in name:
        return fake.email()

    if "name" in name:
        return fake.name()

    if "title" in name:
        return fake.job()

    if "description" in name:
        return fake.text(max_nb_chars=50)

    if "phone" in name:
        return fake.phone_number()

    if "address" in name:
        return fake.address()

    if "city" in name:
        return fake.city()

    if "country" in name:
        return fake.country()

    if "company" in name:
        return fake.company()

    if "date" in name:
        return fake.iso8601()

    if "status" in name:
        return random.choice(["Active", "Inactive"])

    # fallback based on type
    if field_type == "integer":
        return random.randint(1, 100)

    if field_type == "number":
        return random.uniform(1, 100)

    if field_type == "boolean":
        return random.choice([True, False])

    return fake.word()


def generate_object(schema):

    obj = {}

    properties = schema.get("properties", {})

    for field, details in properties.items():

        field_type = details.get("type", "string")

        obj[field] = generate_value(field, field_type)

    return obj