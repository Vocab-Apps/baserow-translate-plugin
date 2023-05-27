import pytest
from django.shortcuts import reverse
from rest_framework.status import HTTP_200_OK

@pytest.mark.django_db(transaction=True)
def test_add_language_field(api_client, data_fixture):
    # first, create a test user so we can interact with the API
    user, token = data_fixture.create_user_and_token()

    # create a baserow database
    # =========================
    database = data_fixture.create_database_application(user=user)

    # now, create a baserow database table
    # ====================================

    url = reverse(
        "api:database:tables:async_create", kwargs={"database_id": database.id}
    )
    response = api_client.post(
        url, {"name": "test_table_1"}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_200_OK
    json_response = response.json()
    # we'll need the table_id for future API calls
    table_id = json_response['id']

    assert True