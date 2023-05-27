import pytest

@pytest.mark.django_db(transaction=True)
def test_add_language_field(api_client, data_fixture):
    # first, create a test user so we can interact with the API
    user, token = data_fixture.create_user_and_token()

    assert True