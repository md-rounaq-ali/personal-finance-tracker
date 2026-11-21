"""
Tests for User Authentication flows, OTP Email Verification, and Password Reset
"""
from unittest.mock import patch
from app import db
from app.models import User, OTPVerification


def test_register_and_verify_otp_flow(client, app):
    # Mock OTP generator so we know the exact code to test
    with patch('app.utils.email_service.generate_otp', return_value='123456'):
        # Step 1: Fill registration form
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@domain.com',
            'password': 'Password123',
            'confirm_password': 'Password123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Verify Your Email' in response.data

        # Verify user does not exist in DB yet before OTP confirmation
        with app.app_context():
            assert User.query.filter_by(username='newuser').first() is None

        # Step 2: Invalid OTP check
        invalid_resp = client.post('/verify-otp', data={'otp': '999999'}, follow_redirects=True)
        assert b'Invalid verification code' in invalid_resp.data

        # Step 3: Valid OTP confirmation
        valid_resp = client.post('/verify-otp', data={'otp': '123456'}, follow_redirects=True)
        assert valid_resp.status_code == 200
        assert b'Email verified and account created successfully' in valid_resp.data

        # Verify user is now created in DB with categories and account
        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            assert user is not None
            assert user.is_verified is True
            assert user.categories.count() >= 14
            assert user.accounts.count() >= 1


def test_register_duplicate_email(client, test_user):
    response = client.post('/register', data={
        'username': 'differentuser',
        'email': 'test@example.com',
        'password': 'Password123',
        'confirm_password': 'Password123'
    }, follow_redirects=True)

    assert b'Email is already registered' in response.data


def test_update_profile_username(auth_client, app, test_user):
    # Test user can edit their display name
    response = auth_client.post('/profile', data={
        'username': 'New Updated Name',
        'currency': '₹'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Profile updated successfully' in response.data

    with app.app_context():
        u = db.session.get(User, test_user)
        assert u.username == 'New Updated Name'


def test_forgot_and_reset_password_flow(client, app, test_user):
    with patch('app.utils.email_service.generate_otp', return_value='654321'):
        # Step 1: Request reset
        req_resp = client.post('/forgot-password', data={
            'email': 'test@example.com'
        }, follow_redirects=True)
        assert req_resp.status_code == 200
        assert b'Reset Password' in req_resp.data

        # Step 2: Submit OTP and new password
        reset_resp = client.post('/reset-password', data={
            'otp': '654321',
            'password': 'BrandNewPassword123!',
            'confirm_password': 'BrandNewPassword123!'
        }, follow_redirects=True)
        assert reset_resp.status_code == 200
        assert b'Password reset successfully' in reset_resp.data

        # Step 3: Verify login with new password works
        login_resp = client.post('/login', data={
            'username': 'testuser',
            'password': 'BrandNewPassword123!'
        }, follow_redirects=True)
        assert b'Welcome back' in login_resp.data


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
