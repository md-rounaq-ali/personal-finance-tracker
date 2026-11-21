"""
Tests for Transactions, Transfers, Precision, and IDOR validation
"""
from decimal import Decimal
from app import db
from app.models import User, Account, Category, Transaction


def test_add_expense_updates_balance(auth_client, app, test_user):
    with app.app_context():
        account = Account.query.filter_by(user_id=test_user).first()
        category = Category.query.filter_by(user_id=test_user, type='expense').first()
        acc_id = account.id
        cat_id = category.id

    response = auth_client.post('/transactions/add', data={
        'type': 'expense',
        'amount': '150.50',
        'account_id': acc_id,
        'category_id': cat_id,
        'description': 'Weekly vegetables',
        'transaction_date': '2026-05-18'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Expense of' in response.data

    with app.app_context():
        updated_acc = db.session.get(Account, acc_id)
        # 1000.00 - 150.50 = 849.50
        assert Decimal(str(updated_acc.balance)) == Decimal('849.50')


def test_idor_protection_on_foreign_account(auth_client, app, test_user):
    """Ensure a user cannot charge or add transactions to an account owned by another user"""
    with app.app_context():
        victim = User(username='victim', email='victim@test.com')
        victim.set_password('VictimPass1!')
        db.session.add(victim)
        db.session.commit()

        victim_acc = Account(user_id=victim.id, name='Victim Vault', type='bank', balance=50000.00)
        db.session.add(victim_acc)
        db.session.commit()
        victim_acc_id = victim_acc.id

    # Try to add transaction against victim's account
    response = auth_client.post('/transactions/add', data={
        'type': 'expense',
        'amount': '500.00',
        'account_id': victim_acc_id,
        'description': 'Malicious transaction',
    }, follow_redirects=True)

    assert b'Invalid account selected' in response.data

    # Verify victim's balance remains untouched
    with app.app_context():
        victim_check = db.session.get(Account, victim_acc_id)
        assert Decimal(str(victim_check.balance)) == Decimal('50000.00')


def test_account_to_account_transfer(auth_client, app, test_user):
    with app.app_context():
        acc1 = Account.query.filter_by(user_id=test_user).first()
        acc2 = Account(user_id=test_user, name='Savings Stash', type='bank', balance=200.00)
        db.session.add(acc2)
        db.session.commit()
        acc1_id = acc1.id
        acc2_id = acc2.id

    response = auth_client.post('/transactions/transfer', data={
        'from_account_id': acc1_id,
        'to_account_id': acc2_id,
        'amount': '250.00',
        'description': 'Monthly savings allocation',
        'transaction_date': '2026-05-18'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Successfully transferred' in response.data

    with app.app_context():
        # acc1: 1000 - 250 = 750
        # acc2: 200 + 250 = 450
        a1 = db.session.get(Account, acc1_id)
        a2 = db.session.get(Account, acc2_id)
        assert Decimal(str(a1.balance)) == Decimal('750.00')
        assert Decimal(str(a2.balance)) == Decimal('450.00')
