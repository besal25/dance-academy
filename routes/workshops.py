from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db, Workshop, WorkshopEnrollment, Student, LedgerTransaction
from routes.auth import admin_required, permission_required
from routes.finance import add_transaction
import nepali_datetime

workshops_bp = Blueprint('workshops', __name__)

@workshops_bp.route('/workshops')
@login_required
def index():
    workshops = Workshop.query.order_by(Workshop.start_date.desc()).all()
    return render_template('workshops/index.html', workshops=workshops)

@workshops_bp.route('/workshops/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    if request.method == 'POST':
        name = request.form['name']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        fee = float(request.form['fee'])
        description = request.form.get('description')
        
        new_workshop = Workshop(
            name=name,
            start_date=start_date,
            end_date=end_date,
            fee=fee,
            description=description
        )
        db.session.add(new_workshop)
        db.session.commit()
        flash('Workshop created successfully!')
        return redirect(url_for('workshops.index'))
    return render_template('workshops/form.html', workshop=None)

@workshops_bp.route('/workshops/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(id):
    workshop = Workshop.query.get_or_404(id)
    if request.method == 'POST':
        workshop.name = request.form['name']
        workshop.start_date = request.form['start_date']
        workshop.end_date = request.form['end_date']
        workshop.fee = float(request.form['fee'])
        workshop.description = request.form.get('description')
        
        db.session.commit()
        flash('Workshop updated successfully!')
        return redirect(url_for('workshops.index'))
    return render_template('workshops/form.html', workshop=workshop)

@workshops_bp.route('/workshops/enroll/<int:id>', methods=['GET', 'POST'])
@login_required
def enroll(id):
    workshop = Workshop.query.get_or_404(id)
    students = Student.query.filter_by(status='Active').all()
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        guest_name = request.form.get('guest_name')
        guest_phone = request.form.get('guest_phone')
        amount_paid = float(request.form.get('amount_paid', 0))
        
        today_bs = nepali_datetime.date.today().strftime('%Y-%m-%d')
        
        enrollment = WorkshopEnrollment(
            workshop_id=id,
            student_id=student_id if student_id else None,
            guest_name=guest_name if not student_id else None,
            guest_phone=guest_phone if not student_id else None,
            amount_paid=amount_paid,
            date=today_bs
        )
        db.session.add(enrollment)
        
        # If it's a student, charge their ledger and record payment
        if student_id:
            # Charge full workshop fee
            add_transaction(student_id, description=f"Workshop: {workshop.name}", debit=workshop.fee, credit=0, txn_type='FEE')
            # If they paid something, record as payment
            if amount_paid > 0:
                add_transaction(student_id, description=f"Payment for Workshop: {workshop.name}", debit=0, credit=amount_paid, txn_type='PAYMENT')
            
            # --- Monthly Fee Waiver Logic ---
            if request.form.get('skip_monthly') == 'yes':
                # Determine current Nepali Month/Year
                today_bs_date = nepali_datetime.date.today()
                month_name = today_bs_date.strftime("%B")
                year = today_bs_date.year
                
                search_pattern = f"%Monthly Fee% - {month_name} {year}"
                
                overlapping_fees = LedgerTransaction.query.filter(
                    LedgerTransaction.student_id == student_id,
                    LedgerTransaction.description.like(search_pattern),
                    LedgerTransaction.is_void == False,
                    LedgerTransaction.txn_type == 'FEE'
                ).all()
                
                void_count = 0
                for fee in overlapping_fees:
                    fee.is_void = True
                    void_count += 1
                
                if void_count > 0:
                    from routes.finance import recalculate_balances
                    recalculate_balances(student_id)
                    flash(f"Automatically waived {void_count} regular monthly fees for {month_name}.")
        
        db.session.commit()
        flash('Enrollment successful!')
        return redirect(url_for('workshops.view', id=id))
        
    return render_template('workshops/enroll.html', workshop=workshop, students=students)

@workshops_bp.route('/workshops/view/<int:id>')
@login_required
def view(id):
    workshop = Workshop.query.get_or_404(id)
    enrollments = WorkshopEnrollment.query.filter_by(workshop_id=id).all()
    return render_template('workshops/view.html', workshop=workshop, enrollments=enrollments)

@workshops_bp.route('/workshops/delete/<int:id>')
@login_required
@admin_required
def delete(id):
    workshop = Workshop.query.get_or_404(id)
    # Check if there are enrollments
    if WorkshopEnrollment.query.filter_by(workshop_id=id).first():
        flash('Cannot delete workshop with active enrollments.', 'danger')
        return redirect(url_for('workshops.index'))
        
    db.session.delete(workshop)
    db.session.commit()
    flash('Workshop deleted.')
    return redirect(url_for('workshops.index'))
@workshops_bp.route('/workshops/enrollment/delete/<int:id>')
@login_required
@admin_required
def delete_enrollment(id):
    enrollment = WorkshopEnrollment.query.get_or_404(id)
    workshop_id = enrollment.workshop_id
    
    # If it was a student, we should void the ledger transactions
    if enrollment.student_id:
        from database import LedgerTransaction
        # Find transactions related to this workshop for this student
        # Looking for descriptions like "Workshop: [Name]" or "Payment for Workshop: [Name]"
        search_term = f"%Workshop: {enrollment.workshop.name}%"
        txns = LedgerTransaction.query.filter(
            LedgerTransaction.student_id == enrollment.student_id,
            LedgerTransaction.description.like(search_term),
            LedgerTransaction.is_void == False
        ).all()
        
        for txn in txns:
            txn.is_void = True
        
    db.session.delete(enrollment)
    db.session.commit()
    flash('Participant removed from workshop.')
    db.session.commit()
    flash('Participant removed from workshop.')
    return redirect(url_for('workshops.view', id=workshop_id))

@workshops_bp.route('/workshops/delete-all', methods=['POST'])
@login_required
@admin_required
def delete_all():
    count = Workshop.query.count()
    
    # Cascade delete all workshop enrollments
    # We should also void ledger transactions for students, but that's complex for bulk delete.
    # For now, we'll just delete the enrollment records. Ledger history remains (as "Workshop X") 
    # but the workshop object is gone. Ideally we should keep ledger integrity.
    
    WorkshopEnrollment.query.delete()
    Workshop.query.delete()
    
    db.session.commit()
    flash(f'All {count} workshops and their enrollments have been deleted.', 'success')
    return redirect(url_for('workshops.index'))
