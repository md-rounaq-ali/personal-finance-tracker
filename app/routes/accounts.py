"""
Account Management Routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Account, Transaction

accounts_bp = Blueprint('accounts', __name__)


@accounts_bp.route('/accounts')
@login_required
def manage():
    accounts = Account.query.filter_by(user_id=current_user.id).order_by(Account.name).all()
    total_balance = sum(float(a.balance) for a in accounts)
    return render_template('accounts/manage.html', accounts=accounts, total_balance=total_balance)


@accounts_bp.route('/accounts/add', methods=['POST'])
@login_required
def add():
    name = request.form.get('name', '').strip()
    acc_type = request.form.get('type', 'bank')
    initial_balance = request.form.get('balance', 0, type=float)

    if not name:
        flash('Account name is required.', 'error')
    else:
        existing = Account.query.filter_by(user_id=current_user.id, name=name).first()
        if existing:
            flash(f'Account "{name}" already exists.', 'error')
        else:
            account = Account(user_id=current_user.id, name=name, type=acc_type, balance=initial_balance)
            db.session.add(account)
            db.session.commit()
            flash(f'Account "{name}" added! ✅', 'success')

    return redirect(url_for('accounts.manage'))


@accounts_bp.route('/accounts/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    account = Account.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    txn_count = Transaction.query.filter_by(account_id=id).count()
    if txn_count > 0:
        flash(f'Cannot delete "{account.name}" — it has {txn_count} transaction(s).', 'error')
    else:
        db.session.delete(account)
        db.session.commit()
        flash(f'Account "{account.name}" deleted. 🗑️', 'success')
    return redirect(url_for('accounts.manage'))
