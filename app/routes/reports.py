"""
Reports Route — Monthly/yearly financial reports with chart data
"""
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from datetime import datetime, date
from app import db
from app.models import Transaction, Category, Budget

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/reports')
@login_required
def monthly():
    today = date.today()
    sel_month = request.args.get('month', today.month, type=int)
    sel_year = request.args.get('year', today.year, type=int)

    # Income vs Expense for selected month
    income = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == current_user.id, Transaction.type == 'income',
        extract('month', Transaction.transaction_date) == sel_month,
        extract('year', Transaction.transaction_date) == sel_year
    ).scalar()

    expense = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == current_user.id, Transaction.type == 'expense',
        extract('month', Transaction.transaction_date) == sel_month,
        extract('year', Transaction.transaction_date) == sel_year
    ).scalar()

    savings = float(income) - float(expense)
    savings_rate = (savings / float(income) * 100) if float(income) > 0 else 0

    # Category breakdown
    cat_data = db.session.query(
        Category.name, Category.color, Category.icon,
        func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.user_id == current_user.id, Transaction.type == 'expense',
        extract('month', Transaction.transaction_date) == sel_month,
        extract('year', Transaction.transaction_date) == sel_year
    ).group_by(Category.id).order_by(func.sum(Transaction.amount).desc()).all()

    cat_labels = [c.name for c in cat_data]
    cat_amounts = [float(c.total) for c in cat_data]
    cat_colors = [c.color for c in cat_data]

    # Last 6 months comparison
    monthly_comp = []
    for i in range(5, -1, -1):
        m = sel_month - i
        y = sel_year
        if m <= 0:
            m += 12
            y -= 1

        mi = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.user_id == current_user.id, Transaction.type == 'income',
            extract('month', Transaction.transaction_date) == m,
            extract('year', Transaction.transaction_date) == y
        ).scalar()

        me = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.user_id == current_user.id, Transaction.type == 'expense',
            extract('month', Transaction.transaction_date) == m,
            extract('year', Transaction.transaction_date) == y
        ).scalar()

        monthly_comp.append({
            'month': datetime(y, m, 1).strftime('%b %Y'),
            'income': float(mi), 'expense': float(me)
        })

    comp_labels = [d['month'] for d in monthly_comp]
    comp_incomes = [d['income'] for d in monthly_comp]
    comp_expenses = [d['expense'] for d in monthly_comp]

    # Budget vs Actual
    budget_data = []
    budgets = Budget.query.filter_by(user_id=current_user.id, month=sel_month, year=sel_year).all()
    for b in budgets:
        spent = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.user_id == current_user.id, Transaction.category_id == b.category_id,
            Transaction.type == 'expense',
            extract('month', Transaction.transaction_date) == sel_month,
            extract('year', Transaction.transaction_date) == sel_year
        ).scalar()
        pct = (float(spent) / float(b.amount) * 100) if b.amount > 0 else 0
        budget_data.append({
            'category': b.category.name, 'icon': b.category.icon,
            'budget': float(b.amount), 'spent': float(spent),
            'remaining': float(b.amount) - float(spent),
            'percentage': min(pct, 100), 'exceeded': pct >= 100
        })

    # Top 5 expenses
    top_expenses = Transaction.query.filter(
        Transaction.user_id == current_user.id, Transaction.type == 'expense',
        extract('month', Transaction.transaction_date) == sel_month,
        extract('year', Transaction.transaction_date) == sel_year
    ).order_by(Transaction.amount.desc()).limit(5).all()

    txn_count = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        extract('month', Transaction.transaction_date) == sel_month,
        extract('year', Transaction.transaction_date) == sel_year
    ).count()

    month_name = datetime(sel_year, sel_month, 1).strftime('%B %Y')

    # Available years for selector
    years = list(range(today.year - 2, today.year + 1))

    expense_categories = Category.query.filter_by(user_id=current_user.id, type='expense').order_by(Category.name).all()

    return render_template('reports/monthly.html',
        income=float(income), expense=float(expense),
        savings=savings, savings_rate=savings_rate,
        cat_labels=cat_labels, cat_amounts=cat_amounts, cat_colors=cat_colors,
        comp_labels=comp_labels, comp_incomes=comp_incomes, comp_expenses=comp_expenses,
        budget_data=budget_data, top_expenses=top_expenses,
        txn_count=txn_count, month_name=month_name,
        sel_month=sel_month, sel_year=sel_year, years=years,
        expense_categories=expense_categories)


@reports_bp.route('/budgets/set', methods=['POST'])
@login_required
def set_budget():
    from flask import flash, redirect
    category_id = request.form.get('category_id', type=int)
    amount = request.form.get('amount', 0, type=float)
    month = request.form.get('month', date.today().month, type=int)
    year = request.form.get('year', date.today().year, type=int)

    if not category_id or amount <= 0:
        flash('Invalid budget data.', 'error')
    else:
        existing = Budget.query.filter_by(
            user_id=current_user.id, category_id=category_id, month=month, year=year
        ).first()
        if existing:
            existing.amount = amount
        else:
            budget = Budget(user_id=current_user.id, category_id=category_id,
                          amount=amount, month=month, year=year)
            db.session.add(budget)
        db.session.commit()
        flash('Budget set! 📊', 'success')

    return redirect(request.referrer or '/reports')
