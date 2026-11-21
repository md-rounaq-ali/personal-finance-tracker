"""
Tests for Admin Panel access control and user management
"""
from app import db
from app.models import User


def test_admin_panel_forbidden_for_regular_user(auth_client):
    # Regular testuser tries to access /admin
    response = auth_client.get('/admin')
    assert response.status_code == 403


def test_admin_panel_accessible_for_tabrasali7(client, app):
    with app.app_context():
        admin = User(username='tabras', email='tabrasali7@gmail.com')
        admin.set_password('AdminPass123!')
        db.session.add(admin)
        db.session.commit()

    # Login as root administrator
    client.post('/login', data={'username': 'tabras', 'password': 'AdminPass123!'}, follow_redirects=True)

    # Access /admin
    response = client.get('/admin')
    assert response.status_code == 200
    assert b'System Administration' in response.data
    assert b'Registered Users' in response.data


def test_admin_can_delete_regular_user(client, app, test_user):
    with app.app_context():
        admin = User(username='tabras', email='tabrasali7@gmail.com')
        admin.set_password('AdminPass123!')
        db.session.add(admin)
        db.session.commit()

        # Regular user id
        target_id = test_user

    # Login as admin
    client.post('/login', data={'username': 'tabras', 'password': 'AdminPass123!'}, follow_redirects=True)

    # Delete test_user
    del_resp = client.post(f'/admin/users/{target_id}/delete', follow_redirects=True)
    assert del_resp.status_code == 200
    assert b'deleted successfully' in del_resp.data

    with app.app_context():
        assert db.session.get(User, target_id) is None
