import pytest
import pprint
import pdb
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

    # create a text field to contain English text
    # this field is a regular baserow field type, Single line text
    # ============================================================

    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table_id}),
        {"name": "English", "type": "text"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    english_text_field_id = response_json['id']
    assert response.status_code == HTTP_200_OK

    # create French translation field. 
    # this uses the new field type which we introduced in this plugin
    # ===============================================================

    field_data = {
        'name': 'French', 
        'type': 'translation', 
        'source_field_id': english_text_field_id, 
        'source_language': 'en', 
        'target_language': 'fr'}
    # pdb.set_trace()
    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table_id}),
        field_data,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    pprint.pprint(response_json)
    assert response.status_code == HTTP_200_OK 
    french_translation_field_id = response_json['id']
    # pprint.pprint(response_json)

    assert True