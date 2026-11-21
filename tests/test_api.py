"""
Tests for RESTful API endpoints
"""


def test_api_health(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'online'
    assert data['service'] == 'FinTrack API'


def test_api_summary_requires_auth(client):
    response = client.get('/api/v1/summary')
    assert response.status_code == 302  # Redirected to login


def test_api_summary_authenticated(auth_client):
    response = auth_client.get('/api/v1/summary')
    assert response.status_code == 200
    data = response.get_json()
    assert 'net_savings' in data
    assert 'accounts' in data
    assert len(data['accounts']) >= 1
