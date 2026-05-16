"""
Transaction Routes — Full CRUD + CSV Export
"""
import csv
import io
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from app.models import Transaction, Category, Account

transactions_bp = Blueprint('transactions', __name__)


@transactions_bp.route('/transactions')
@login_required
def list_transactions():
    page = request.args.get('page', 1, type=int)
    per_page = 15

    # Filters
    filter_type = request.args.get('type', '')
    filter_category = request.args.get('category', '', type=str)
    filter_account = request.args.get('account', '', type=str)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search = request.args.get('search', '').strip()

    query = Transaction.query.filter_by(user_id=current_user.id)

    if filter_type in ('income', 'expense'):
        query = query.filter(Transaction.type == filter_type)
    if filter_category:
        query = query.filter(Transaction.category_id == int(filter_category))
    if filter_account:
        query = query.filter(Transaction.account_id == int(filter_account))
    if date_from:
        query = query.filter(Transaction.transaction_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        query = query.filter(Transaction.transaction_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    if search:
        query = query.filter(Transaction.description.ilike(f'%{search}%'))

    pagination = query.order_by(
        Transaction.transaction_date.desc(),
        Transaction.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    accounts = Account.query.filter_by(user_id=current_user.id).order_by(Account.name).all()

    return render_template('transactions/list.html',
                           transactions=pagination.items,
                           pagination=pagination,
                           categories=categories,
                           accounts=accounts,
                           filter_type=filter_type,
                           filter_category=filter_category,
                           filter_account=filter_account,
                           date_from=date_from,
                           date_to=date_to,
                           search=search)


@transactions_bp.route('/transactions/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        txn_type = request.form.get('type', 'expense')
        amount = request.form.get('amount', 0, type=float)
        category_id = request.form.get('category_id', type=int)
        account_id = request.form.get('account_id', type=int)
        description = request.form.get('description', '').strip()
        txn_date = request.form.get('transaction_date', '')

        if amount <= 0:
            flash('Amount must be greater than zero.', 'error')
        elif not account_id:
            flash('Please select an account.', 'error')
        else:
            transaction = Transaction(
                user_id=current_user.id,
                account_id=account_id,
                category_id=category_id if category_id else None,
                amount=amount,
                type=txn_type,
                description=description,
                transaction_date=datetime.strptime(txn_date, '%Y-%m-%d').date() if txn_date else date.today()
            )
            db.session.add(transaction)

            # Update account balance
            account = Account.query.get(account_id)
            if txn_type == 'income':
                account.balance = float(account.balance) + amount
            else:
                account.balance = float(account.balance) - amount

            db.session.commit()
            flash(f'{"Income" if txn_type == "income" else "Expense"} of ₹{amount:,.2f} added! ✅', 'success')
            return redirect(url_for('transactions.list_transactions'))

    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.type, Category.name).all()
    accounts = Account.query.filter_by(user_id=current_user.id).order_by(Account.name).all()

    return render_template('transactions/add.html',
                           categories=categories,
                           accounts=accounts,
                           today=date.today().isoformat())


@transactions_bp.route('/transactions/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        old_type = transaction.type
        old_amount = float(transaction.amount)
        old_account_id = transaction.account_id

        new_type = request.form.get('type', 'expense')
        new_amount = request.form.get('amount', 0, type=float)
        new_category_id = request.form.get('category_id', type=int)
        new_account_id = request.form.get('account_id', type=int)
        description = request.form.get('description', '').strip()
        txn_date = request.form.get('transaction_date', '')

        if new_amount <= 0:
            flash('Amount must be greater than zero.', 'error')
        else:
            # Reverse old balance effect
            old_account = Account.query.get(old_account_id)
            if old_type == 'income':
                old_account.balance = float(old_account.balance) - old_amount
            else:
                old_account.balance = float(old_account.balance) + old_amount

            # Apply new balance effect
            new_account = Account.query.get(new_account_id)
            if new_type == 'income':
                new_account.balance = float(new_account.balance) + new_amount
            else:
                new_account.balance = float(new_account.balance) - new_amount

            # Update transaction
            transaction.type = new_type
            transaction.amount = new_amount
            transaction.category_id = new_category_id if new_category_id else None
            transaction.account_id = new_account_id
            transaction.description = description
            transaction.transaction_date = datetime.strptime(txn_date, '%Y-%m-%d').date() if txn_date else transaction.transaction_date

            db.session.commit()
            flash('Transaction updated! ✏️', 'success')
            return redirect(url_for('transactions.list_transactions'))

    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.type, Category.name).all()
    accounts = Account.query.filter_by(user_id=current_user.id).order_by(Account.name).all()

    return render_template('transactions/edit.html',
                           transaction=transaction,
                           categories=categories,
                           accounts=accounts)


@transactions_bp.route('/transactions/<int:id>/delete', methods=['POST'])
@login_required
def delete_transaction(id):
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    # Reverse balance effect
    account = Account.query.get(transaction.account_id)
    if transaction.type == 'income':
        account.balance = float(account.balance) - float(transaction.amount)
    else:
        account.balance = float(account.balance) + float(transaction.amount)

    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted. 🗑️', 'success')
    return redirect(url_for('transactions.list_transactions'))


@transactions_bp.route('/transactions/export')
@login_required
def export_csv():
    """Export all transactions as CSV"""
    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.transaction_date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Type', 'Category', 'Account', 'Amount (₹)', 'Description'])

    for t in transactions:
        writer.writerow([
            t.transaction_date.isoformat(),
            t.type.capitalize(),
            t.category.name if t.category else 'Uncategorized',
            t.account.name if t.account else 'N/A',
            float(t.amount),
            t.description
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=transactions_{date.today().isoformat()}.csv'}
    )
