"""
Reports Route — Financial reports with optimized queries & chart data
"""
from decimal import Decimal
from flask import Blueprint, render_template, request, flash, redirect, url_for
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

    # Validate month/year bounds
    if sel_month < 1 or sel_month > 12:
        sel_month = today.month
    if sel_year < 2000 or sel_year > 2100:
        sel_year = today.year

    # 1. Income vs Expense for selected month (Single query)
    totals_query = db.session.query(
        Transaction.type,
        func.coalesce(func.sum(Transaction.amount), 0).label('total')
    ).filter(
        Transaction.user_id == current_user.id,
        extract('month', Transaction.transaction_date) == sel_month,
        extract('year', Transaction.transaction_date) == sel_year
    ).group_by(Transaction.type).all()

    month_totals = {row.type: Decimal(str(row.total)) for row in totals_query}
    income = month_totals.get('income', Decimal('0'))
    expense = month_totals.get('expense', Decimal('0'))
    savings = income - expense
    savings_rate = (float(savings) / float(income) * 100) if income > 0 else 0

    # 2. Category breakdown
    cat_data = db.session.query(
        Category.name, Category.color, Category.icon,
        func.sum(Transaction.amount).label('total')
    ).join(Transaction, Transaction.category_id == Category.id).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        extract('month', Transaction.transaction_date) == sel_month,
        extract('year', Transaction.transaction_date) == sel_year
    ).group_by(Category.id, Category.name, Category.color, Category.icon).order_by(func.sum(Transaction.amount).desc()).all()

    cat_labels = [c.name for c in cat_data]
    cat_amounts = [float(c.total) for c in cat_data]
    cat_colors = [c.color for c in cat_data]

    # 3. 6 Months Comparison — OPTIMIZED Single Query
    m_start = sel_month - 5
    y_start = sel_year
    if m_start <= 0:
        m_start += 12
        y_start -= 1
    start_date = date(y_start, m_start, 1)

    # Cap end date to selected month's end
    end_m = sel_month + 1
    end_y = sel_year
    if end_m > 12:
        end_m = 1
        end_y += 1
    end_date = date(end_y, end_m, 1)

    trend_rows = db.session.query(
        extract('year', Transaction.transaction_date).label('yr'),
        extract('month', Transaction.transaction_date).label('mo'),
        Transaction.type,
        func.coalesce(func.sum(Transaction.amount), 0).label('total')
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date < end_date
    ).group_by(
        extract('year', Transaction.transaction_date),
        extract('month', Transaction.transaction_date),
        Transaction.type
    ).all()

    trend_map = {(int(r.yr), int(r.mo), r.type): float(r.total) for r in trend_rows}

    comp_labels = []
    comp_incomes = []
    comp_expenses = []
    for i in range(5, -1, -1):
        m = sel_month - i
        y = sel_year
        if m <= 0:
            m += 12
            y -= 1
        comp_labels.append(datetime(y, m, 1).strftime('%b %Y'))
        comp_incomes.append(trend_map.get((y, m, 'income'), 0.0))
        comp_expenses.append(trend_map.get((y, m, 'expense'), 0.0))

    # 4. Budget vs Actual — OPTIMIZED Single Query
    budgets = Budget.query.filter_by(user_id=current_user.id, month=sel_month, year=sel_year).all()
    budget_data = []
    if budgets:
        cat_ids = [b.category_id for b in budgets]
        spending_lookup = dict(db.session.query(
            Transaction.category_id,
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.category_id.in_(cat_ids),
            Transaction.type == 'expense',
            extract('month', Transaction.transaction_date) == sel_month,
            extract('year', Transaction.transaction_date) == sel_year
        ).group_by(Transaction.category_id).all())

        for b in budgets:
            spent = float(spending_lookup.get(b.category_id, 0))
            budget_amt = float(b.amount)
            pct = (spent / budget_amt * 100) if budget_amt > 0 else 0
            budget_data.append({
                'category': b.category.name,
                'icon': b.category.icon,
                'budget': budget_amt,
                'spent': spent,
                'remaining': budget_amt - spent,
                'percentage': min(pct, 100),
                'exceeded': pct >= 100
            })

    # Top 5 expenses
    top_expenses = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        extract('month', Transaction.transaction_date) == sel_month,
        extract('year', Transaction.transaction_date) == sel_year
    ).order_by(Transaction.amount.desc()).limit(5).all()

    txn_count = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        extract('month', Transaction.transaction_date) == sel_month,
        extract('year', Transaction.transaction_date) == sel_year
    ).count()

    month_name = datetime(sel_year, sel_month, 1).strftime('%B %Y')
    years = list(range(today.year - 2, today.year + 2))
    expense_categories = Category.query.filter_by(user_id=current_user.id, type='expense').order_by(Category.name).all()

    return render_template('reports/monthly.html',
                           income=float(income),
                           expense=float(expense),
                           savings=float(savings),
                           savings_rate=round(savings_rate, 1),
                           cat_labels=cat_labels,
                           cat_amounts=cat_amounts,
                           cat_colors=cat_colors,
                           comp_labels=comp_labels,
                           comp_incomes=comp_incomes,
                           comp_expenses=comp_expenses,
                           budget_data=budget_data,
                           top_expenses=top_expenses,
                           txn_count=txn_count,
                           month_name=month_name,
                           sel_month=sel_month,
                           sel_year=sel_year,
                           years=years,
                           expense_categories=expense_categories)


@reports_bp.route('/budgets/set', methods=['POST'])
@login_required
def set_budget():
    category_id = request.form.get('category_id', type=int)
    amount_raw = request.form.get('amount', '0').strip()
    month = request.form.get('month', date.today().month, type=int)
    year = request.form.get('year', date.today().year, type=int)

    try:
        amount = Decimal(amount_raw)
        if amount <= Decimal('0'):
            raise ValueError()
    except (Exception):
        flash('Budget amount must be a positive number.', 'error')
        return redirect(request.referrer or url_for('reports.monthly'))

    # IDOR check: Verify category belongs to user
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first()
    if not category:
        flash('Invalid category selected.', 'error')
        return redirect(request.referrer or url_for('reports.monthly'))

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
    flash(f'Budget for "{category.name}" set to ₹{amount:,.2f}! 📊', 'success')
    return redirect(request.referrer or url_for('reports.monthly'))
