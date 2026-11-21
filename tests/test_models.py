"""
Unit Tests for Database Models
"""
from decimal import Decimal
from app import db
from app.models import User, Account, Category, Transaction, Budget


def test_password_hashing():
    user = User(username='hashman', email='hash@test.com')
    user.set_password('mysecretpass')

    assert user.password_hash != 'mysecretpass'
    assert user.check_password('mysecretpass') is True
    assert user.check_password('wrongpass') is False


def test_user_creation(app):
    with app.app_context():
        user = User(username='johndoe', email='john@example.com')
        user.set_password('Pass1234')
        db.session.add(user)
        db.session.commit()

        fetched = User.query.filter_by(username='johndoe').first()
        assert fetched is not None
        assert fetched.email == 'john@example.com'
        assert str(fetched) == '<User johndoe>'


def test_account_and_balance_precision(app, test_user):
    with app.app_context():
        account = Account.query.filter_by(user_id=test_user, name='Test Bank').first()
        assert account is not None
        assert Decimal(str(account.balance)) == Decimal('1000.00')
