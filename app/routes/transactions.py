"""
Transaction Routes — Full CRUD, Secure IDOR Validation, Account Transfers & CSV Export
"""
import csv
import io
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
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
        try:
            query = query.filter(Transaction.transaction_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(Transaction.transaction_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        except ValueError:
            pass
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
        amount_raw = request.form.get('amount', '0').strip()
        category_id = request.form.get('category_id', type=int)
        account_id = request.form.get('account_id', type=int)
        description = request.form.get('description', '').strip()
        txn_date = request.form.get('transaction_date', '')

        # Decimal conversion
        try:
            amount = Decimal(amount_raw)
            if amount <= Decimal('0'):
                raise ValueError()
        except (InvalidOperation, ValueError):
            flash('Amount must be a valid positive number.', 'error')
            return redirect(url_for('transactions.add_transaction'))

        # IDOR check: Verify account belongs to current user
        account = Account.query.filter_by(id=account_id, user_id=current_user.id).first()
        if not account:
            flash('Invalid account selected.', 'error')
            return redirect(url_for('transactions.add_transaction'))

        # IDOR check: Verify category belongs to current user
        if category_id:
            category = Category.query.filter_by(id=category_id, user_id=current_user.id).first()
            if not category:
                flash('Invalid category selected.', 'error')
                return redirect(url_for('transactions.add_transaction'))

        try:
            parsed_date = datetime.strptime(txn_date, '%Y-%m-%d').date() if txn_date else date.today()
        except ValueError:
            parsed_date = date.today()

        transaction = Transaction(
            user_id=current_user.id,
            account_id=account.id,
            category_id=category_id if category_id else None,
            amount=amount,
            type=txn_type,
            description=description,
            transaction_date=parsed_date
        )
        db.session.add(transaction)

        # Update account balance using high precision Decimal
        current_bal = Decimal(str(account.balance or 0))
        if txn_type == 'income':
            account.balance = current_bal + amount
        else:
            account.balance = current_bal - amount

        db.session.commit()
        flash(f'{"Income" if txn_type == "income" else "Expense"} of ₹{amount:,.2f} added! ✅', 'success')
        return redirect(url_for('transactions.list_transactions'))

    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.type, Category.name).all()
    accounts = Account.query.filter_by(user_id=current_user.id).order_by(Account.name).all()

    return render_template('transactions/add.html',
                           categories=categories,
                           accounts=accounts,
                           today=date.today().isoformat())


@transactions_bp.route('/transactions/transfer', methods=['POST'])
@login_required
def transfer():
    """Transfer funds atomically between two accounts owned by current user"""
    from_account_id = request.form.get('from_account_id', type=int)
    to_account_id = request.form.get('to_account_id', type=int)
    amount_raw = request.form.get('amount', '0').strip()
    notes = request.form.get('description', '').strip()
    txn_date_raw = request.form.get('transaction_date', '')

    try:
        amount = Decimal(amount_raw)
        if amount <= Decimal('0'):
            raise ValueError()
    except (InvalidOperation, ValueError):
        flash('Transfer amount must be a positive number.', 'error')
        return redirect(url_for('accounts.manage'))

    if from_account_id == to_account_id:
        flash('Source and destination accounts must be different.', 'error')
        return redirect(url_for('accounts.manage'))

    # IDOR check: Verify both accounts belong to current user
    from_acc = Account.query.filter_by(id=from_account_id, user_id=current_user.id).first()
    to_acc = Account.query.filter_by(id=to_account_id, user_id=current_user.id).first()

    if not from_acc or not to_acc:
        flash('Invalid account selected for transfer.', 'error')
        return redirect(url_for('accounts.manage'))

    try:
        parsed_date = datetime.strptime(txn_date_raw, '%Y-%m-%d').date() if txn_date_raw else date.today()
    except ValueError:
        parsed_date = date.today()

    # Find or use Transfer category
    transfer_cat = Category.query.filter_by(user_id=current_user.id, name='Transfer').first()

    # Atomically adjust balances
    from_acc.balance = Decimal(str(from_acc.balance or 0)) - amount
    to_acc.balance = Decimal(str(to_acc.balance or 0)) + amount

    # Create debit transaction for source account
    debit_txn = Transaction(
        user_id=current_user.id,
        account_id=from_acc.id,
        category_id=transfer_cat.id if transfer_cat else None,
        amount=amount,
        type='expense',
        description=f"Transfer to {to_acc.name}" + (f": {notes}" if notes else ""),
        transaction_date=parsed_date
    )
    # Create credit transaction for destination account
    credit_txn = Transaction(
        user_id=current_user.id,
        account_id=to_acc.id,
        category_id=transfer_cat.id if transfer_cat else None,
        amount=amount,
        type='income',
        description=f"Transfer from {from_acc.name}" + (f": {notes}" if notes else ""),
        transaction_date=parsed_date
    )

    db.session.add(debit_txn)
    db.session.add(credit_txn)
    db.session.commit()

    flash(f'Successfully transferred ₹{amount:,.2f} from {from_acc.name} to {to_acc.name}! 🔄', 'success')
    return redirect(url_for('accounts.manage'))


@transactions_bp.route('/transactions/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        old_type = transaction.type
        old_amount = Decimal(str(transaction.amount))
        old_account_id = transaction.account_id

        new_type = request.form.get('type', 'expense')
        amount_raw = request.form.get('amount', '0').strip()
        new_category_id = request.form.get('category_id', type=int)
        new_account_id = request.form.get('account_id', type=int)
        description = request.form.get('description', '').strip()
        txn_date = request.form.get('transaction_date', '')

        try:
            new_amount = Decimal(amount_raw)
            if new_amount <= Decimal('0'):
                raise ValueError()
        except (InvalidOperation, ValueError):
            flash('Amount must be a valid positive number.', 'error')
            return redirect(url_for('transactions.edit_transaction', id=id))

        # IDOR check: Verify new_account belongs to user
        new_account = Account.query.filter_by(id=new_account_id, user_id=current_user.id).first()
        if not new_account:
            flash('Invalid account selected.', 'error')
            return redirect(url_for('transactions.edit_transaction', id=id))

        # IDOR check: Verify new_category belongs to user if specified
        if new_category_id:
            cat = Category.query.filter_by(id=new_category_id, user_id=current_user.id).first()
            if not cat:
                flash('Invalid category selected.', 'error')
                return redirect(url_for('transactions.edit_transaction', id=id))

        # Reverse old balance effect on old_account
        old_account = Account.query.filter_by(id=old_account_id, user_id=current_user.id).first()
        if old_account:
            old_bal = Decimal(str(old_account.balance or 0))
            if old_type == 'income':
                old_account.balance = old_bal - old_amount
            else:
                old_account.balance = old_bal + old_amount

        # Apply new balance effect on new_account
        new_bal = Decimal(str(new_account.balance or 0))
        if new_type == 'income':
            new_account.balance = new_bal + new_amount
        else:
            new_account.balance = new_bal - new_amount

        # Update transaction
        transaction.type = new_type
        transaction.amount = new_amount
        transaction.category_id = new_category_id if new_category_id else None
        transaction.account_id = new_account.id
        transaction.description = description
        if txn_date:
            try:
                transaction.transaction_date = datetime.strptime(txn_date, '%Y-%m-%d').date()
            except ValueError:
                pass

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
    account = Account.query.filter_by(id=transaction.account_id, user_id=current_user.id).first()
    if account:
        cur_bal = Decimal(str(account.balance or 0))
        txn_amt = Decimal(str(transaction.amount or 0))
        if transaction.type == 'income':
            account.balance = cur_bal - txn_amt
        else:
            account.balance = cur_bal + txn_amt

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
