"""
Pytest Fixtures for FinTrack test suite
"""
import pytest
from app import create_app, db
from app.config import TestConfig
from app.models import User, Account, Category, Transaction


@pytest.fixture
def app():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('Secret123!')
        db.session.add(user)
        db.session.commit()

        # Seed an account and category
        account = Account(user_id=user.id, name='Test Bank', type='bank', balance=1000.00)
        category = Category(user_id=user.id, name='Groceries', type='expense', icon='🛒', color='#f43f5e')
        db.session.add(account)
        db.session.add(category)
        db.session.commit()

        return user.id


@pytest.fixture
def auth_client(client, test_user):
    client.post('/login', data={'username': 'testuser', 'password': 'Secret123!'}, follow_redirects=True)
    return client
