from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db, Student, LedgerTransaction
from routes.auth import admin_required, permission_required
import nepali_datetime

finance_bp = Blueprint('finance', __name__)

# --- Core Ledger Logic ---
def add_transaction(student_id, description, debit=0.0, credit=0.0, txn_type='FEE'):
    """
    Adds a transaction and updates the running balance.
    txn_type: FEE, PAYMENT, ADJUSTMENT
    """
    student = Student.query.get(student_id)
    if not student:
        return False
        
    last_txn = LedgerTransaction.query.filter_by(student_id=student_id, is_void=False).order_by(LedgerTransaction.date.desc(), LedgerTransaction.id.desc()).first()
    previous_balance = last_txn.balance_after if last_txn else 0.0
    
    new_balance = previous_balance + debit - credit
    
    # Save date as BS string
    today_bs = nepali_datetime.date.today().strftime('%Y-%m-%d')
    
    new_txn = LedgerTransaction(
        student_id=student_id,
        description=description,
        debit=debit,
        credit=credit,
        balance_after=new_balance,
        date=today_bs,
        txn_type=txn_type,
        is_void=False
    )
    db.session.add(new_txn)
    db.session.commit()
    return new_txn

# --- Routes ---
@finance_bp.route('/finance')
@login_required
@permission_required('can_view_finance')
def index():
    # Show recent transactions across all students
    recent_transactions = LedgerTransaction.query.order_by(LedgerTransaction.date.desc()).limit(20).all()
    
    # Calculate total stats
    total_due = 0
    students = Student.query.all()
    for s in students:
        bal = s.get_balance()
        if bal > 0:
            total_due += bal
            
    return render_template('finance/index.html', transactions=recent_transactions, total_due=total_due)

@finance_bp.route('/finance/pay/<int:student_id>', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_students') # Staff can take payments
def pay(student_id):
    student = Student.query.get_or_404(student_id)
    current_balance = student.get_balance()
    if request.method == 'POST':
        amount = float(request.form['amount'])
        
        if amount <= 0:
            flash("Error: Payment amount must be greater than zero.", "danger")
            return redirect(url_for('finance.pay', student_id=student.id))
            
        mode = request.form['mode']

        # --- Smart Auto-Billing Logic ---
        # If the student hasn't been billed the monthly fee for the current month yet,
        # bill it now so the payment correctly reduces the new dues.
        today_bs = nepali_datetime.date.today()
        month_name = today_bs.strftime("%B")
        fee_description = f"Monthly Fee - {month_name} {today_bs.year}"
        
        # Search for any non-voided FEE transaction containing the current month and year
        search_term = f"{month_name} {today_bs.year}"
        fee_exists = LedgerTransaction.query.filter(
            LedgerTransaction.student_id == student.id,
            LedgerTransaction.is_void == False,
            LedgerTransaction.txn_type == 'FEE',
            LedgerTransaction.description.contains(search_term)
        ).first()

        if not fee_exists:
            # --- Package Protection ---
            # Don't bill monthly fee if the student is currently enrolled in an active package.
            from database import PackageEnrollment
            active_package = PackageEnrollment.query.filter(
                PackageEnrollment.student_id == student.id,
                PackageEnrollment.start_date <= today_bs.strftime('%Y-%m-%d'),
                PackageEnrollment.end_date >= today_bs.strftime('%Y-%m-%d')
            ).first()
            
            if not active_package:
                add_transaction(student.id, description=fee_description, debit=student.custom_monthly_fee, credit=0, txn_type='FEE')
                db.session.commit() # Ensure the fee exists before the payment txn is created
                flash(f"Monthly fee for {month_name} was automatically billed.")
            else:
                flash(f"Monthly fee skipped because student is in an active package: {active_package.package.name}.")

        description = f"Payment - {mode}"
        txn = add_transaction(student.id, description=description, debit=0, credit=amount, txn_type='PAYMENT')
        
        flash(f'Payment of Rs {amount} recorded for {student.name}. <a href="{url_for("finance.print_receipt", id=txn.id)}" target="_blank" style="color: var(--primary); font-weight: bold; margin-left:10px;"><i class="fas fa-print"></i> Print Receipt</a>')
        return redirect(url_for('finance.student_ledger', student_id=student.id))
        
    return render_template('finance/pay.html', student=student, balance=current_balance)

@finance_bp.route('/finance/ledger/<int:student_id>')
@login_required
@permission_required('can_manage_students') # Allows staff to see bills/payments
def student_ledger(student_id):
    student = Student.query.get_or_404(student_id)
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = LedgerTransaction.query.filter_by(student_id=student.id)
    
    if start_date:
        query = query.filter(LedgerTransaction.date >= start_date)
    if end_date:
        query = query.filter(LedgerTransaction.date <= end_date)
        
    transactions = query.order_by(LedgerTransaction.date.desc()).all()
    
    import nepali_datetime
    today_bs = nepali_datetime.date.today()
    return render_template('finance/ledger.html', student=student, transactions=transactions, start_date=start_date, end_date=end_date, current_year_bs=today_bs.year)

@finance_bp.route('/finance/generate', methods=['POST'])
@login_required
@admin_required
def generate_fees():
    """
    Generates monthly fees for all ACTIVE students.
    """
    # Use Nepali Month Name
    today_bs = nepali_datetime.date.today()
    month_name = today_bs.strftime("%B") # nepali_datetime might support %B for nepali months
    
    count = 0
    active_students = Student.query.filter_by(status='Active').all()
    for s in active_students:
        description = f"Monthly Fee - {month_name} {today_bs.year}"
        
        # Check duplicate using substring (Month Year) to catch Enrollment vs standard fees
        search_term = f"{month_name} {today_bs.year}"
        exists = LedgerTransaction.query.filter(
            LedgerTransaction.student_id == s.id,
            LedgerTransaction.is_void == False,
            LedgerTransaction.txn_type == 'FEE',
            LedgerTransaction.description.contains(search_term)
        ).first()

        if not exists:
            # --- Package Protection ---
            from database import PackageEnrollment
            active_package = PackageEnrollment.query.filter(
                PackageEnrollment.student_id == s.id,
                PackageEnrollment.start_date <= today_bs.strftime('%Y-%m-%d'),
                PackageEnrollment.end_date >= today_bs.strftime('%Y-%m-%d')
            ).first()
            
            if not active_package:
                add_transaction(s.id, description=description, debit=s.custom_monthly_fee, credit=0, txn_type='FEE')
                count += 1
            
    flash(f"Generated fees for {count} active students ({month_name}).")
    return redirect(url_for('finance.index'))

@finance_bp.route('/finance/renew-admission', methods=['POST'])
@login_required
@admin_required
def renew_admissions():
    """
    Checks for students whose admission is due for annual renewal and charges them.
    """
    today_bs = nepali_datetime.date.today()
    count = 0
    
    from database import Settings
    settings = Settings.query.first()
    base_admission = settings.default_admission_fee if settings else 1000.0
    
    active_students = Student.query.filter_by(status='Active').all()
    for s in active_students:
        if not s.last_admission_date:
            continue
            
        try:
            # last_admission_date is YYYY-MM-DD
            parts = [int(p) for p in s.last_admission_date.split('-')]
            last_date = nepali_datetime.date(parts[0], parts[1], parts[2])
            # Check if exactly one year or more has passed
            # A simple way: if current year > last_date.year AND (current month > last_month OR (current month == last month AND current day >= last day))
            is_due = False
            if today_bs.year > last_date.year:
                if today_bs.month > last_date.month:
                    is_due = True
                elif today_bs.month == last_date.month and today_bs.day >= last_date.day:
                    is_due = True
            
            if is_due:
                fee_to_charge = 0.0
                if s.admission_fee_type == 'Normal':
                    fee_to_charge = base_admission
                elif s.admission_fee_type == 'Percentage':
                    fee_to_charge = base_admission * (1 - s.admission_discount_percent / 100)
                elif s.admission_fee_type == 'Fixed':
                    fee_to_charge = s.custom_admission_fee
                
                if fee_to_charge > 0:
                    add_transaction(s.id, description=f"Annual Admission Renewal ({today_bs.year})", debit=fee_to_charge, credit=0, txn_type='FEE')
                    s.last_admission_date = today_bs.strftime('%Y-%m-%d')
                    count += 1
        except Exception as e:
            print(f"Error processing renewal for student {s.id}: {e}")
            
    db.session.commit()
    flash(f"Admission renewed for {count} students.")
    return redirect(url_for('finance.index'))
def recalculate_balances(student_id):
    """
    Helper to ensure the running balance is accurate after any change.
    """
    all_txns = LedgerTransaction.query.filter_by(student_id=student_id).order_by(LedgerTransaction.date.asc(), LedgerTransaction.id.asc()).all()
    running_balance = 0.0
    for t in all_txns:
        if not t.is_void:
            running_balance += t.debit - t.credit
        t.balance_after = running_balance
    db.session.commit()

@finance_bp.route('/finance/transaction/void/<int:id>')
@login_required
@permission_required('can_view_finance') # Allow those with finance access to void
def void_transaction(id):
    """
    Standard Accounting: Never delete. Mark as Void and recalculate.
    """
    transaction = LedgerTransaction.query.get_or_404(id)
    transaction.is_void = True
    db.session.commit()
    
    recalculate_balances(transaction.student_id)
    
    flash(f"Transaction ID {id} has been VOIDED.")
    return redirect(url_for('finance.student_ledger', student_id=transaction.student_id))

@finance_bp.route('/finance/transaction/delete/<int:id>')
@login_required
@admin_required
def delete_transaction(id):
    """
    Permanent Deletion (Admin Only)
    """
    transaction = LedgerTransaction.query.get_or_404(id)
    student_id = transaction.student_id
    db.session.delete(transaction)
    db.session.commit()
    
    recalculate_balances(student_id)
    
    flash(f"Transaction ID {id} has been PERMANENTLY DELETED.")
    return redirect(url_for('finance.student_ledger', student_id=student_id))

@finance_bp.route('/finance/receipt/<int:id>')
@login_required
def print_receipt(id):
    txn = LedgerTransaction.query.get_or_404(id)
    today_bs = nepali_datetime.date.today().strftime('%Y-%m-%d')
    return render_template('finance/receipt.html', txn=txn, today_bs=today_bs)
