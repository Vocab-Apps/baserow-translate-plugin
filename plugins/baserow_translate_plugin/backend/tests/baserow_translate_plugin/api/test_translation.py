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

    url = f'/api/database/tables/database/{database.id}/'
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

    # enter some text in the English field
    # ====================================

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table_id}),
        {f"field_{english_text_field_id}": "Hello"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_row = response.json()
    table_row_id = response_row['id']
    assert response.status_code == HTTP_200_OK

    # retrieve the row, make sure it contains the french translation
    # ==============================================================

    response = api_client.get(
        reverse("api:database:rows:item", kwargs={"table_id": table_id, 'row_id': table_row_id}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_row = response.json()
    assert response.status_code == HTTP_200_OK

    assert response_row[f'field_{french_translation_field_id}'] == 'translation (en to fr): Hello'


@pytest.mark.django_db(transaction=True)
def test_update_all_rows(api_client, data_fixture):
    # first, create a test user so we can interact with the API
    user, token = data_fixture.create_user_and_token()

    # create a baserow database
    # =========================
    database = data_fixture.create_database_application(user=user)
    # create table
    url = f'/api/database/tables/database/{database.id}/'
    response = api_client.post(
        url, {"name": "test_table_1"}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_200_OK
    json_response = response.json()
    table_id = json_response['id']

    # create english text field
    # =========================

    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table_id}),
        {"name": "English", "type": "text"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    english_text_field_id = response_json['id']
    assert response.status_code == HTTP_200_OK


    # enter two rows of english text
    # ==============================

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table_id}),
        {f"field_{english_text_field_id}": "Hello"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_row = response.json()
    table_row_id_1 = response_row['id']
    assert response.status_code == HTTP_200_OK


    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table_id}),
        {f"field_{english_text_field_id}": "Bye bye"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_row = response.json()
    table_row_id_2 = response_row['id']
    assert response.status_code == HTTP_200_OK

    # add spanish translation field
    # ===============================================================

    field_data = {
        'name': 'Spanish', 
        'type': 'translation', 
        'source_field_id': english_text_field_id, 
        'source_language': 'en', 
        'target_language': 'es'}
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
    spanish_translation_field_id = response_json['id']


    # retrieve rows 1 and 2, make sure they contain the translated text
    # =================================================================

    response = api_client.get(
        reverse("api:database:rows:item", kwargs={"table_id": table_id, 'row_id': table_row_id_1}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_row = response.json()
    assert response.status_code == HTTP_200_OK

    assert response_row[f'field_{spanish_translation_field_id}'] == 'translation (en to es): Hello'

    response = api_client.get(
        reverse("api:database:rows:item", kwargs={"table_id": table_id, 'row_id': table_row_id_2}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_row = response.json()
    assert response.status_code == HTTP_200_OK

    assert response_row[f'field_{spanish_translation_field_id}'] == 'translation (en to es): Bye bye'


@pytest.mark.django_db(transaction=True)
def test_create_multiple_rows(api_client, data_fixture):
    """create multiple rows at once, which simulates the pasting multiple rows of data action"""

    # first, create a test user so we can interact with the API
    user, token = data_fixture.create_user_and_token()

    # create a baserow database
    # =========================
    database = data_fixture.create_database_application(user=user)
    # create table
    url = f'/api/database/tables/database/{database.id}/'
    response = api_client.post(
        url, {"name": "test_table_1"}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_200_OK
    json_response = response.json()
    table_id = json_response['id']

    # create english text field
    # =========================

    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table_id}),
        {"name": "English", "type": "text"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    english_text_field_id = response_json['id']
    assert response.status_code == HTTP_200_OK

    # add spanish translation field
    # =============================

    field_data = {
        'name': 'Spanish', 
        'type': 'translation', 
        'source_field_id': english_text_field_id, 
        'source_language': 'en', 
        'target_language': 'es'}
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
    spanish_translation_field_id = response_json['id']

    # create new rows which contain english text
    # ==========================================

    url = f'/api/database/rows/table/{table_id}/batch/'
    rows = [
        {f"field_{english_text_field_id}": "Hello"},
        {f"field_{english_text_field_id}": "Bye bye"},
    ]
    response = api_client.post(
        url,
        {'items': rows},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_row = response.json()
    assert response.status_code == HTTP_200_OK, response.content

    # retrieve all rows, make sure they contain the translated text
    # =============================================================

    url = f'/api/database/rows/table/{table_id}/'
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_data = response.json()
    assert response.status_code == HTTP_200_OK

    assert response_data['results'][0][f'field_{spanish_translation_field_id}'] == 'translation (en to es): Hello'
    assert response_data['results'][1][f'field_{spanish_translation_field_id}'] == 'translation (en to es): Bye bye'
