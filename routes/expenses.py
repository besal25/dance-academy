from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db, Expense
from routes.auth import admin_required, permission_required
import nepali_datetime
from datetime import datetime

expenses_bp = Blueprint('expenses', __name__)

@expenses_bp.route('/expenses')
@login_required
@permission_required('can_manage_expenses')
def index():
    from database import Instructor
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    instructors = Instructor.query.all()
    date_str = nepali_datetime.date.today().strftime('%Y-%m-%d')
    return render_template('expenses/index.html', expenses=expenses, instructors=instructors, date_str=date_str)

@expenses_bp.route('/expenses/add', methods=['POST'])
@login_required
@admin_required
def add():
    date_str = request.form['date']
    amount = float(request.form['amount'])
    if amount <= 0:
        flash("Error: Expense amount must be greater than zero.", "danger")
        return redirect(url_for('expenses.index'))
        
    category = request.form['category']
    description = request.form['description']
    
    instructor_id = request.form.get('instructor_id')
    
    date = date_str
    
    new_expense = Expense(
        date=date, 
        amount=amount, 
        category=category, 
        description=description,
        instructor_id=int(instructor_id) if category == 'Salary' and instructor_id else None
    )
    db.session.add(new_expense)
    db.session.commit()
    
    flash('Expense added successfully')
    return redirect(url_for('expenses.index'))

@expenses_bp.route('/expenses/void/<int:id>')
@login_required
@permission_required('can_manage_expenses')
def void_expense(id):
    """
    Standard Accounting: Void instead of Delete.
    """
    expense = Expense.query.get_or_404(id)
    expense.is_void = True
    db.session.commit()
    flash('Expense has been VOIDED (Audit record preserved).')
    return redirect(url_for('expenses.index'))

@expenses_bp.route('/expenses/delete/<int:id>')
@login_required
@admin_required
def delete_expense(id):
    """
    Permanent Deletion (Admin Only)
    """
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense has been PERMANENTLY DELETED.')
    return redirect(url_for('expenses.index'))
