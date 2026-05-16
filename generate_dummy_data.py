from app import create_app, db
from app.models import User, Category, Account, Transaction, Budget
from datetime import date, timedelta
import random

app = create_app()

with app.app_context():
    # Get the first user
    user = User.query.first()
    if not user:
        print("❌ Please register an account in the web app first!")
        exit()

    print(f"Generating data for user: {user.username}...")

    # 1. Ensure Accounts exist
    if Account.query.filter_by(user_id=user.id).count() == 0:
        db.session.add(Account(user_id=user.id, name='HDFC Bank', type='bank', balance=185000))
        db.session.add(Account(user_id=user.id, name='Credit Card', type='credit_card', balance=-12000))
        db.session.commit()
    
    account = Account.query.filter_by(user_id=user.id).first()

    # 2. Get Categories
    salary_cat = Category.query.filter_by(user_id=user.id, name='Salary').first()
    rent_cat = Category.query.filter_by(user_id=user.id, name='Rent').first()
    groceries_cat = Category.query.filter_by(user_id=user.id, name='Groceries').first()
    food_cat = Category.query.filter_by(user_id=user.id, name='Food & Dining').first()
    transport_cat = Category.query.filter_by(user_id=user.id, name='Transport').first()
    utilities_cat = Category.query.filter_by(user_id=user.id, name='Utilities').first()

    categories = [rent_cat, groceries_cat, food_cat, transport_cat, utilities_cat]
    
    if not all(categories) or not salary_cat:
        print("❌ Categories not found. Did you register an account properly?")
        exit()

    # 3. Clear existing transactions to start fresh
    Transaction.query.filter_by(user_id=user.id).delete()
    Budget.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    # 4. Generate Transactions for the last 3 months
    today = date.today()
    transactions = []

    for month_offset in range(3):
        target_date = today - timedelta(days=30 * month_offset)
        
        # Add Salary
        transactions.append(Transaction(
            user_id=user.id, account_id=account.id, category_id=salary_cat.id,
            amount=85000, type='income', description='Monthly Salary',
            transaction_date=target_date.replace(day=1)
        ))

        # Add Rent
        transactions.append(Transaction(
            user_id=user.id, account_id=account.id, category_id=rent_cat.id,
            amount=25000, type='expense', description='Monthly Rent',
            transaction_date=target_date.replace(day=5)
        ))

        # Add random expenses throughout the month
        for _ in range(15):
            cat = random.choice([groceries_cat, food_cat, transport_cat, utilities_cat])
            amt = random.randint(500, 4500)
            rand_day = random.randint(1, 28)
            
            transactions.append(Transaction(
                user_id=user.id, account_id=account.id, category_id=cat.id,
                amount=amt, type='expense', description=f'{cat.name} expense',
                transaction_date=target_date.replace(day=rand_day)
            ))

    db.session.add_all(transactions)

    # 5. Set some budgets for the current month
    db.session.add(Budget(user_id=user.id, category_id=groceries_cat.id, amount=15000, month=today.month, year=today.year))
    db.session.add(Budget(user_id=user.id, category_id=food_cat.id, amount=8000, month=today.month, year=today.year))

    db.session.commit()
    print("✅ Dummy data successfully generated! Refresh your browser to see beautiful charts.")
