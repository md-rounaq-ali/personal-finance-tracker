"""
Dashboard Route — Summary cards, charts, recent transactions
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from datetime import datetime, date
from app import db
from app.models import Transaction, Category, Account, Budget

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    today = date.today()
    current_month = today.month
    current_year = today.year

    # --- Summary Cards ---
    total_income = db.session.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'income',
        extract('month', Transaction.transaction_date) == current_month,
        extract('year', Transaction.transaction_date) == current_year
    ).scalar()

    total_expense = db.session.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        extract('month', Transaction.transaction_date) == current_month,
        extract('year', Transaction.transaction_date) == current_year
    ).scalar()

    balance = float(total_income) - float(total_expense)

    # --- Recent Transactions ---
    recent_transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Transaction.transaction_date.desc(),
        Transaction.created_at.desc()
    ).limit(7).all()

    # --- Spending by Category (current month) ---
    category_spending = db.session.query(
        Category.name,
        Category.color,
        Category.icon,
        func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        extract('month', Transaction.transaction_date) == current_month,
        extract('year', Transaction.transaction_date) == current_year
    ).group_by(Category.id).order_by(func.sum(Transaction.amount).desc()).all()

    category_labels = [c.name for c in category_spending]
    category_amounts = [float(c.total) for c in category_spending]
    category_colors = [c.color for c in category_spending]

    # --- Monthly Trend (last 6 months) ---
    monthly_data = []
    for i in range(5, -1, -1):
        m = current_month - i
        y = current_year
        if m <= 0:
            m += 12
            y -= 1

        month_income = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'income',
            extract('month', Transaction.transaction_date) == m,
            extract('year', Transaction.transaction_date) == y
        ).scalar()

        month_expense = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'expense',
            extract('month', Transaction.transaction_date) == m,
            extract('year', Transaction.transaction_date) == y
        ).scalar()

        month_name = datetime(y, m, 1).strftime('%b %Y')
        monthly_data.append({
            'month': month_name,
            'income': float(month_income),
            'expense': float(month_expense)
        })

    month_labels = [d['month'] for d in monthly_data]
    month_incomes = [d['income'] for d in monthly_data]
    month_expenses = [d['expense'] for d in monthly_data]

    # --- Accounts ---
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    total_balance_all_accounts = sum(float(a.balance) for a in accounts)

    # --- Budget Alerts ---
    budget_alerts = []
    budgets = Budget.query.filter_by(
        user_id=current_user.id,
        month=current_month,
        year=current_year
    ).all()

    for budget in budgets:
        spent = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.category_id == budget.category_id,
            Transaction.type == 'expense',
            extract('month', Transaction.transaction_date) == current_month,
            extract('year', Transaction.transaction_date) == current_year
        ).scalar()

        percentage = (float(spent) / float(budget.amount) * 100) if budget.amount > 0 else 0
        if percentage >= 80:
            budget_alerts.append({
                'category': budget.category.name,
                'icon': budget.category.icon,
                'budget': float(budget.amount),
                'spent': float(spent),
                'percentage': min(percentage, 100),
                'exceeded': percentage >= 100
            })

    # --- Transaction count ---
    transaction_count = Transaction.query.filter_by(user_id=current_user.id).count()

    return render_template('dashboard.html',
                           total_income=float(total_income),
                           total_expense=float(total_expense),
                           balance=balance,
                           total_balance_all_accounts=total_balance_all_accounts,
                           recent_transactions=recent_transactions,
                           category_labels=category_labels,
                           category_amounts=category_amounts,
                           category_colors=category_colors,
                           month_labels=month_labels,
                           month_incomes=month_incomes,
                           month_expenses=month_expenses,
                           accounts=accounts,
                           budget_alerts=budget_alerts,
                           transaction_count=transaction_count,
                           current_month_name=today.strftime('%B %Y'))
