from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db, Package, PackageEnrollment, Student, LedgerTransaction
from routes.auth import admin_required, permission_required
from routes.finance import add_transaction
import nepali_datetime

packages_bp = Blueprint('packages', __name__)

@packages_bp.route('/packages')
@login_required
@permission_required('can_manage_packages')
def index():
    packages = Package.query.all()
    # Pass students for the Enrollment Modal
    students = Student.query.filter_by(status='Active').all()
    return render_template('packages/index.html', packages=packages, students=students)

@packages_bp.route('/api/packages/<int:id>/members')
@login_required
def get_package_members(id):
    enrollments = PackageEnrollment.query.filter_by(package_id=id).all()
    data = []
    for e in enrollments:
        data.append({
            'student_name': e.student.name,
            'student_phone': e.student.phone,
            'start_date': e.start_date,
            'end_date': e.end_date,
            'payment_status': 'Paid' if e.amount_paid >= e.total_price else 'Due', # Simple logic
            'enrollment_id': e.id
        })
    return {'members': data}

@packages_bp.route('/packages/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    if request.method == 'POST':
        name = request.form['name']
        duration = int(request.form['duration_months'])
        price = float(request.form['price'])
        description = request.form.get('description')
        
        new_package = Package(
            name=name,
            duration_months=duration,
            price=price,
            description=description
        )
        db.session.add(new_package)
        db.session.commit()
        flash('Package created successfully!')
        return redirect(url_for('packages.index'))
    return render_template('packages/form.html', package=None)

@packages_bp.route('/packages/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(id):
    package = Package.query.get_or_404(id)
    if request.method == 'POST':
        package.name = request.form['name']
        package.duration_months = int(request.form['duration_months'])
        package.price = float(request.form['price'])
        package.description = request.form.get('description')
        
        db.session.commit()
        flash('Package updated successfully!')
        return redirect(url_for('packages.index'))
    return render_template('packages/form.html', package=package)

@packages_bp.route('/packages/enroll/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_packages')
def enroll(id):
    package = Package.query.get_or_404(id)
    students = Student.query.filter_by(status='Active').all()
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        start_date_str = request.form.get('start_date')
        amount_paid = float(request.form.get('amount_paid', 0))
        deadline = request.form.get('payment_deadline')
        
        student = Student.query.get(student_id)
        if not student:
            flash('Student not found.', 'danger')
            return redirect(url_for('packages.enroll', id=id))

        # Check if student has paid admission fee (last_admission_date)
        if not student.last_admission_date:
            flash(f'Student {student.name} must pay admission fee before enrolling in a package.', 'warning')
            return redirect(url_for('students.edit', id=student.id))

        # Calculate end date (crude approximation for BS months)
        try:
            parts = [int(p) for p in start_date_str.split('-')]
            start_date = nepali_datetime.date(parts[0], parts[1], parts[2])
            # Add duration_months
            new_month = start_date.month + package.duration_months
            new_year = start_date.year + (new_month - 1) // 12
            new_month = (new_month - 1) % 12 + 1
            # Adjust day if needed (e.g. if day 32 and target month has 31)
            try:
                end_date = nepali_datetime.date(new_year, new_month, start_date.day)
            except ValueError:
                end_date = nepali_datetime.date(new_year, new_month, 30) # Safe bet for BS
            
            end_date_str = end_date.strftime('%Y-%m-%d')
        except Exception:
            end_date_str = start_date_str # Fallback

        enrollment = PackageEnrollment(
            package_id=id,
            student_id=student_id,
            start_date=start_date_str,
            end_date=end_date_str,
            total_price=package.price,
            amount_paid=amount_paid,
            payment_deadline=deadline
        )
        db.session.add(enrollment)
        
        add_transaction(student_id, description=f"Package: {package.name} ({package.duration_months} Months)", debit=package.price, credit=0, txn_type='FEE')
        if amount_paid > 0:
            add_transaction(student_id, description=f"Payment for Package: {package.name}", debit=0, credit=amount_paid, txn_type='PAYMENT')
            
        # --- Package Fee Adjustment ---
        if request.form.get('skip_monthly') == 'yes':
            void_count = 0
            # Loop through each month of the package duration
            for i in range(package.duration_months):
                # Calculate target month/year
                # Add i months to start_date
                target_month_idx = start_date.month + i
                target_year = start_date.year + (target_month_idx - 1) // 12
                target_month_num = (target_month_idx - 1) % 12 + 1
                
                # Get Month Name from nepali_datetime might be tricky if not built-in for number->name
                # Let's rely on constructing a date and getting strftime
                # We need a valid day (1 is safe)
                target_date = nepali_datetime.date(target_year, target_month_num, 1)
                search_month = target_date.strftime('%B')
                search_year = target_date.year
                
                search_pattern = f"%Monthly Fee% - {search_month} {search_year}"
                
                overlapping_fees = LedgerTransaction.query.filter(
                    LedgerTransaction.student_id == student_id,
                    LedgerTransaction.description.like(search_pattern),
                    LedgerTransaction.is_void == False,
                    LedgerTransaction.txn_type == 'FEE'
                ).all()
                
                for fee in overlapping_fees:
                    fee.is_void = True
                    void_count += 1
            
            if void_count > 0:
                from routes.finance import recalculate_balances
                recalculate_balances(student_id)
                flash(f"Automatically waived {void_count} overlapping monthly fees for package duration.")

        db.session.commit()
        flash('Package enrollment successful!')
        return redirect(url_for('packages.index'))
        
    return render_template('packages/enroll.html', package=package, students=students)

@packages_bp.route('/packages/view/<int:id>')
@login_required
@permission_required('can_manage_packages')
def view(id):
    package = Package.query.get_or_404(id)
    enrollments = PackageEnrollment.query.filter_by(package_id=id).all()
    return render_template('packages/view.html', package=package, enrollments=enrollments)

@packages_bp.route('/packages/enrollment/delete/<int:id>')
@login_required
@admin_required
def delete_enrollment(id):
    enrollment = PackageEnrollment.query.get_or_404(id)
    package_id = enrollment.package_id
    
    # Void ledger transactions
    from database import LedgerTransaction
    search_term = f"%Package: {enrollment.package.name}%"
    txns = LedgerTransaction.query.filter(
        LedgerTransaction.student_id == enrollment.student_id,
        LedgerTransaction.description.like(search_term),
        LedgerTransaction.is_void == False
    ).all()
    
    for txn in txns:
        txn.is_void = True
        
    db.session.delete(enrollment)
    db.session.commit()
    flash('Student removed from package.')
    return redirect(url_for('packages.view', id=package_id))

@packages_bp.route('/packages/delete/<int:id>')
@login_required
@admin_required
def delete(id):
    package = Package.query.get_or_404(id)
    if PackageEnrollment.query.filter_by(package_id=id).first():
        flash('Cannot delete package with active enrollments.', 'danger')
        return redirect(url_for('packages.index'))
        
    db.session.delete(package)
    db.session.commit()
    flash('Package deleted.')
    return redirect(url_for('packages.index'))

@packages_bp.route('/packages/delete-all', methods=['POST'])
@login_required
@admin_required
def delete_all():
    count = Package.query.count()
    
    # Cascade delete all package enrollments
    # Similar to classes/workshops, we just delete the records.
    # Ideally should void transactions, but for mass delete, we prioritize cleanup.
    
    PackageEnrollment.query.delete()
    Package.query.delete()
    
    db.session.commit()
    flash(f'All {count} packages and their enrollments have been deleted.', 'success')
    return redirect(url_for('packages.index'))
