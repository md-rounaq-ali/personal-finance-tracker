"""
Dashboard Route — High-performance queries, summary cards, charts, recent transactions
"""
from flask import Blueprint, render_template, redirect, url_for, Response
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from datetime import datetime, date
from decimal import Decimal
from app import db
from app.models import Transaction, Category, Account, Budget

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def home():
    """
    Public SEO-optimized Landing Page.
    Logged-in users are automatically routed to their active dashboard.
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('landing.html')


@dashboard_bp.route('/robots.txt')
def robots_txt():
    """Search Engine Crawling Directives for Googlebot & Bingbot"""
    content = """User-agent: *
Allow: /
Allow: /static/
Disallow: /admin
Disallow: /transactions
Disallow: /accounts
Disallow: /budgets
Disallow: /reports
Disallow: /profile

Sitemap: https://personal-finance-tracker-l1n2.onrender.com/sitemap.xml
"""
    return Response(content, mimetype="text/plain")


@dashboard_bp.route('/sitemap.xml')
def sitemap_xml():
    """XML Sitemap for Search Engine Indexing & PageRank Discovery"""
    return render_template('sitemap.xml'), 200, {'Content-Type': 'application/xml'}


@dashboard_bp.route('/dashboard')
@login_required
def index():
    today = date.today()
    current_month = today.month
    current_year = today.year

    # --- Summary Cards ---
    totals_query = db.session.query(
        Transaction.type,
        func.coalesce(func.sum(Transaction.amount), 0).label('total')
    ).filter(
        Transaction.user_id == current_user.id,
        extract('month', Transaction.transaction_date) == current_month,
        extract('year', Transaction.transaction_date) == current_year
    ).group_by(Transaction.type).all()

    month_totals = {row.type: Decimal(str(row.total)) for row in totals_query}
    total_income = month_totals.get('income', Decimal('0'))
    total_expense = month_totals.get('expense', Decimal('0'))
    balance = total_income - total_expense

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
    ).join(Transaction, Transaction.category_id == Category.id).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        extract('month', Transaction.transaction_date) == current_month,
        extract('year', Transaction.transaction_date) == current_year
    ).group_by(Category.id, Category.name, Category.color, Category.icon).order_by(func.sum(Transaction.amount).desc()).all()

    category_labels = [c.name for c in category_spending]
    category_amounts = [float(c.total) for c in category_spending]
    category_colors = [c.color for c in category_spending]

    # --- Monthly Trend (last 6 months) — OPTIMIZED Single Query ---
    # Calculate starting month/year 5 months ago
    m_start = current_month - 5
    y_start = current_year
    if m_start <= 0:
        m_start += 12
        y_start -= 1
    start_date = date(y_start, m_start, 1)

    trend_rows = db.session.query(
        extract('year', Transaction.transaction_date).label('yr'),
        extract('month', Transaction.transaction_date).label('mo'),
        Transaction.type,
        func.coalesce(func.sum(Transaction.amount), 0).label('total')
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_date >= start_date
    ).group_by(
        extract('year', Transaction.transaction_date),
        extract('month', Transaction.transaction_date),
        Transaction.type
    ).all()

    trend_map = {}
    for row in trend_rows:
        key = (int(row.yr), int(row.mo), row.type)
        trend_map[key] = float(row.total)

    month_labels = []
    month_incomes = []
    month_expenses = []

    for i in range(5, -1, -1):
        m = current_month - i
        y = current_year
        if m <= 0:
            m += 12
            y -= 1
        month_label = datetime(y, m, 1).strftime('%b %Y')
        month_labels.append(month_label)
        month_incomes.append(trend_map.get((y, m, 'income'), 0.0))
        month_expenses.append(trend_map.get((y, m, 'expense'), 0.0))

    # --- Accounts ---
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    total_balance_all_accounts = sum((float(a.balance or 0) for a in accounts), 0.0)

    # --- Budget Alerts — OPTIMIZED Single Query (eliminates N+1 loop) ---
    budgets = Budget.query.filter_by(
        user_id=current_user.id,
        month=current_month,
        year=current_year
    ).all()

    budget_alerts = []
    if budgets:
        # Pre-fetch monthly spending for all budgeted categories in ONE query
        cat_ids = [b.category_id for b in budgets]
        spending_lookup = dict(db.session.query(
            Transaction.category_id,
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.category_id.in_(cat_ids),
            Transaction.type == 'expense',
            extract('month', Transaction.transaction_date) == current_month,
            extract('year', Transaction.transaction_date) == current_year
        ).group_by(Transaction.category_id).all())

        for budget in budgets:
            spent = float(spending_lookup.get(budget.category_id, 0))
            budget_amt = float(budget.amount)
            percentage = (spent / budget_amt * 100) if budget_amt > 0 else 0
            if percentage >= 80:
                budget_alerts.append({
                    'category': budget.category.name,
                    'icon': budget.category.icon,
                    'budget': budget_amt,
                    'spent': spent,
                    'percentage': min(percentage, 100),
                    'exceeded': percentage >= 100
                })

    # --- Transaction count ---
    transaction_count = Transaction.query.filter_by(user_id=current_user.id).count()

    return render_template('dashboard.html',
                           total_income=float(total_income),
                           total_expense=float(total_expense),
                           balance=float(balance),
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
