"""Testing the web package."""

import pytest

from leopard_lavatory import web


@pytest.fixture
def client():
    """Create testing client for other tests."""
    app = web.create_app()
    app.config['TESTING'] = True
    app.secret_key = 'testing'
    yield app.test_client()


def test_index_get(client):
    """Check that first word of title is in get request to landing page."""
    rv = client.get('/')
    assert b'Bevaka' in rv.data


def test_index_post(client):
    rv = client.post('/', data=dict(
        email='test@example.com',
        address='testaddress'
    ), follow_redirects=True)
    assert b'fel' not in rv.data
    assert b'Aktivera' in rv.data
    # TODO cleanup


def test_index_post_invalid_input(client):
    rv = client.post('/', data=dict(
        email='invalidemail',
        address='testaddress'
    ), follow_redirects=True)
    assert b'fel' in rv.data
    assert b'Aktivera' not in rv.data


def test_delete_get_with_token(client):
    token = 'sometoken'
    rv = client.get('/delete', query_string=dict(t=token))
    assert b'<label for="token">' not in rv.data
    token_value = 'value="%s"' % token
    assert bytearray(token_value, 'utf-8') in rv.data


def test_delete_get_without_token(client):
    token = 'sometoken'
    rv = client.get('/delete')
    assert b'<label for="token">' in rv.data
    token_value = 'value="%s"' % token
    assert bytearray(token_value, 'utf-8') not in rv.data


# TODO how to test with existing data, ie deleting an account?
