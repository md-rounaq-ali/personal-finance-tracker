"""
Category Management Routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Category, Transaction

categories_bp = Blueprint('categories', __name__)


@categories_bp.route('/categories')
@login_required
def manage():
    income_categories = Category.query.filter_by(
        user_id=current_user.id, type='income'
    ).order_by(Category.name).all()

    expense_categories = Category.query.filter_by(
        user_id=current_user.id, type='expense'
    ).order_by(Category.name).all()

    return render_template('categories/manage.html',
                           income_categories=income_categories,
                           expense_categories=expense_categories)


@categories_bp.route('/categories/add', methods=['POST'])
@login_required
def add():
    name = request.form.get('name', '').strip()
    cat_type = request.form.get('type', 'expense')
    icon = request.form.get('icon', '📦').strip()
    color = request.form.get('color', '#14b8a6')

    if not name:
        flash('Category name is required.', 'error')
    elif len(name) > 50:
        flash('Category name must be 50 characters or less.', 'error')
    else:
        existing = Category.query.filter_by(
            user_id=current_user.id, name=name, type=cat_type
        ).first()
        if existing:
            flash(f'Category "{name}" already exists.', 'error')
        else:
            category = Category(
                user_id=current_user.id,
                name=name,
                type=cat_type,
                icon=icon,
                color=color
            )
            db.session.add(category)
            db.session.commit()
            flash(f'Category "{name}" added! ✅', 'success')

    return redirect(url_for('categories.manage'))


@categories_bp.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    category = Category.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    # Check if category has transactions
    txn_count = Transaction.query.filter_by(category_id=id).count()
    if txn_count > 0:
        flash(f'Cannot delete "{category.name}" — it has {txn_count} transaction(s). Reassign them first.', 'error')
    else:
        db.session.delete(category)
        db.session.commit()
        flash(f'Category "{category.name}" deleted. 🗑️', 'success')

    return redirect(url_for('categories.manage'))
