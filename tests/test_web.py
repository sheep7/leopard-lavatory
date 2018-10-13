"""Testing the web package."""

import pytest
from leopard_lavatory import web


@pytest.fixture
def client():
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

def test_index_post_invalid_input(client):
    rv = client.post('/', data=dict(
        email='invalidemail',
        address='testaddress'
    ), follow_redirects=True)
    assert b'fel' in rv.data
    assert b'Aktivera' not in rv.data
