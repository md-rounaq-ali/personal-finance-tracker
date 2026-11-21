"""
Budget Management Routes — Dedicated Budgeting Dashboard & CRUD
"""
from decimal import Decimal, InvalidOperation
from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from app import db
from app.models import Budget, Category, Transaction

budgets_bp = Blueprint('budgets', __name__)


@budgets_bp.route('/budgets')
@login_required
def manage():
    today = date.today()
    sel_month = request.args.get('month', today.month, type=int)
    sel_year = request.args.get('year', today.year, type=int)

    if sel_month < 1 or sel_month > 12:
        sel_month = today.month
    if sel_year < 2000 or sel_year > 2100:
        sel_year = today.year

    budgets = Budget.query.filter_by(
        user_id=current_user.id,
        month=sel_month,
        year=sel_year
    ).all()

    # Pre-fetch monthly spending for all budgeted categories
    budget_items = []
    total_budgeted = Decimal('0')
    total_spent = Decimal('0')

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
            spent = Decimal(str(spending_lookup.get(b.category_id, 0)))
            b_amt = Decimal(str(b.amount))
            total_budgeted += b_amt
            total_spent += spent
            pct = (float(spent) / float(b_amt) * 100) if b_amt > 0 else 0

            budget_items.append({
                'id': b.id,
                'category': b.category,
                'amount': float(b_amt),
                'spent': float(spent),
                'remaining': float(b_amt - spent),
                'percentage': min(round(pct, 1), 100),
                'raw_percentage': round(pct, 1),
                'is_over': spent > b_amt
            })

    expense_categories = Category.query.filter_by(
        user_id=current_user.id, type='expense'
    ).order_by(Category.name).all()

    years = list(range(today.year - 2, today.year + 2))

    return render_template('budgets/manage.html',
                           budget_items=budget_items,
                           total_budgeted=float(total_budgeted),
                           total_spent=float(total_spent),
                           total_remaining=float(total_budgeted - total_spent),
                           expense_categories=expense_categories,
                           sel_month=sel_month,
                           sel_year=sel_year,
                           years=years)


@budgets_bp.route('/budgets/add', methods=['POST'])
@login_required
def add():
    category_id = request.form.get('category_id', type=int)
    amount_raw = request.form.get('amount', '0').strip()
    month = request.form.get('month', date.today().month, type=int)
    year = request.form.get('year', date.today().year, type=int)

    try:
        amount = Decimal(amount_raw)
        if amount <= Decimal('0'):
            raise ValueError()
    except (InvalidOperation, ValueError):
        flash('Budget amount must be a positive number.', 'error')
        return redirect(url_for('budgets.manage', month=month, year=year))

    # IDOR check: Verify category belongs to user
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first()
    if not category:
        flash('Invalid category selected.', 'error')
        return redirect(url_for('budgets.manage', month=month, year=year))

    existing = Budget.query.filter_by(
        user_id=current_user.id, category_id=category_id, month=month, year=year
    ).first()

    if existing:
        existing.amount = amount
        flash(f'Updated budget for "{category.name}" to ₹{amount:,.2f}!', 'success')
    else:
        budget = Budget(user_id=current_user.id, category_id=category_id,
                        amount=amount, month=month, year=year)
        db.session.add(budget)
        flash(f'Budget for "{category.name}" set to ₹{amount:,.2f}! 🎯', 'success')

    db.session.commit()
    return redirect(url_for('budgets.manage', month=month, year=year))


@budgets_bp.route('/budgets/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    budget = Budget.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    month = budget.month
    year = budget.year
    cat_name = budget.category.name

    db.session.delete(budget)
    db.session.commit()
    flash(f'Budget for "{cat_name}" deleted.', 'info')
    return redirect(url_for('budgets.manage', month=month, year=year))
