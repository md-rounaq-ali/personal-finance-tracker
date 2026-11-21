"""
Tests for User Authentication flows
"""
from app import db
from app.models import User


def test_register_success(client, app):
    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'newuser@domain.com',
        'password': 'Password123',
        'confirm_password': 'Password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Account created successfully' in response.data

    with app.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.categories.count() >= 14
        assert user.accounts.count() >= 1


def test_register_duplicate_username(client, test_user):
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'another@domain.com',
        'password': 'Password123',
        'confirm_password': 'Password123'
    }, follow_redirects=True)

    assert b'Username already taken' in response.data


def test_login_and_logout(client, test_user):
    # Valid login
    login_resp = client.post('/login', data={
        'username': 'testuser',
        'password': 'Secret123!'
    }, follow_redirects=True)
    assert login_resp.status_code == 200
    assert b'Welcome back' in login_resp.data

    # Logout
    logout_resp = client.get('/logout', follow_redirects=True)
    assert logout_resp.status_code == 200
    assert b'You have been logged out' in logout_resp.data


def test_unauthorized_access(client):
    response = client.get('/transactions', follow_redirects=True)
    assert b'Please log in to access this page' in response.data
