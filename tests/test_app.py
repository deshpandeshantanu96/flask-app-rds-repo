# tests/test_app.py
from app import create_app
import pytest

@pytest.fixture
def client():
    app = create_app()
    with app.test_client() as client:
        yield client

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert b'OK' in response.data

def test_invalid_route(client):
    response = client.get('/nonexistent')
    assert response.status_code == 404