from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from routes.auth import admin_required, permission_required
from database import db, Student
from datetime import datetime
import os
from werkzeug.utils import secure_filename

student_bp = Blueprint('students', __name__)

@student_bp.route('/students')
@login_required
@permission_required('can_manage_students')
def index():
    search = request.args.get('search', '')
    if search:
        students = Student.query.filter(
            (Student.name.contains(search)) | (Student.phone.contains(search))
        ).all()
    else:
        students = Student.query.all()
    return render_template('students/index.html', students=students, search=search)

@student_bp.route('/students/add', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_students')
def add():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        dob = request.form.get('dob') # Optional
        guardian = request.form.get('guardian_name')
        emergency = request.form.get('emergency_contact')
        fee = float(request.form.get('custom_monthly_fee', 5000))
        
        admission_type = request.form.get('admission_fee_type', 'Normal')
        admission_discount = float(request.form.get('admission_discount_percent', 0))
        admission_custom = float(request.form.get('custom_admission_fee', 0))
        
        # dob is now a string (BS date)
        if dob == 'None': dob = None
        
        # Handle photo upload
        photo = request.files.get('photo')
        photo_path = None
        if photo and photo.filename:
            filename = secure_filename(f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{photo.filename}")
            photo.save(os.path.join('static/uploads/students', filename))
            photo_path = f'uploads/students/{filename}'
        
        import nepali_datetime
        today_bs = nepali_datetime.date.today().strftime('%Y-%m-%d')

        new_student = Student(
            name=name,
            phone=phone,
            dob=dob,
            guardian_name=guardian,
            emergency_contact=emergency,
            custom_monthly_fee=fee,
            base_monthly_fee=float(request.form.get('base_monthly_fee', 5000)),
            status='Active',
            photo_path=photo_path,
            admission_fee_type=admission_type,
            admission_discount_percent=admission_discount,
            custom_admission_fee=admission_custom,

            last_admission_date=today_bs
        )
        db.session.add(new_student)
        db.session.commit()
        
        # Auto-charge admission fee and first month fee
        from database import Settings
        from routes.finance import add_transaction, calculate_prorata_fee
        
        settings = Settings.query.first()
        # Default to 1000 if not provided in form (though form has value="1000")
        admission_to_charge = float(request.form.get('custom_admission_fee', 1000))
        
        if admission_to_charge > 0:
            add_transaction(new_student.id, description="Admission Fee", debit=admission_to_charge, credit=0, txn_type='FEE')

        if fee < 0:
            flash("Error: Monthly fee cannot be negative.", "danger")
            return redirect(url_for('students.add'))
            
        if phone:
            # Remove any spaces or dashes
            clean_phone = ''.join(filter(str.isdigit, phone))
            if len(clean_phone) != 10:
                flash("Error: Phone number must be exactly 10 digits.", "warning")
                return redirect(url_for('students.add'))
            phone = clean_phone # Save cleaned version
            
        today_bs = nepali_datetime.date.today()
        month_name = today_bs.strftime('%B')
        description = f"Monthly Fee (Enrollment) - {month_name} {today_bs.year}"
        
        # Calculate Pro-Rata for initial enrollment
        # We pass fees and today_bs (which is admission date here)
        fee_to_charge, suffix = calculate_prorata_fee(fee, today_bs.strftime('%Y-%m-%d'))
        description += suffix
        
        add_transaction(new_student.id, description=description, debit=fee_to_charge, credit=0, txn_type='FEE')
        
        flash('Student added and first month fee charged!')
        return redirect(url_for('students.index'))
    return render_template('students/form.html', student=None)

@student_bp.route('/students/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_students')
def edit(id):
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        phone = request.form['phone']
        new_admission_date = request.form.get('last_admission_date')
        if new_admission_date == 'None' or not new_admission_date:
            new_admission_date = None
        
        # 10-digit validation
        clean_phone = ''.join(filter(str.isdigit, phone))
        if len(clean_phone) != 10:
            flash("Error: Phone number must be exactly 10 digits.", "warning")
            return redirect(url_for('students.edit', id=id))
        
        student.name = request.form['name']
        student.phone = clean_phone
        student.last_admission_date = new_admission_date
        student.guardian_name = request.form.get('guardian_name')
        student.emergency_contact = request.form.get('emergency_contact')
        student.custom_monthly_fee = float(request.form.get('custom_monthly_fee', 5000))
        student.base_monthly_fee = float(request.form.get('base_monthly_fee', 5000))
        old_status = student.status
        student.status = request.form.get('status', 'Active')
        
        admission_type = request.form.get('admission_fee_type', 'Normal')
        admission_discount = float(request.form.get('admission_discount_percent', 0))
        admission_custom = float(request.form.get('custom_admission_fee', 0))
        student.admission_fee_type = admission_type
        student.admission_discount_percent = admission_discount
        student.custom_admission_fee = admission_custom

        if student.custom_monthly_fee < 0:
            flash("Error: Monthly fee cannot be negative.", "danger")
            return redirect(url_for('students.edit', id=id))



        # Handle Re-activation (Re-admission) logic if Status changed Inactive -> Active
        if old_status == 'Inactive' and student.status == 'Active':
            import nepali_datetime
            today_bs = nepali_datetime.date.today()
            
            # If they didn't manually set a date in this same edit, update to Today for re-admission
            # But since we now have the field on the form, the 'new_admission_date' above likely captured 
            # whatever was in the input. If the input was the OLD date, and we want to reset it on activation?
            # Actually, usually on Re-activation, the user SHOULD update the date manually or we auto-set it if empty.
            # Let's trust the form value first. If form value was empty (unlikely with required), fallback to today.
            
            if not new_admission_date:
                student.last_admission_date = today_bs.strftime('%Y-%m-%d')
            
            if request.form.get('charge_readmission') == 'yes':
                from database import Settings
                from routes.finance import add_transaction
                settings = Settings.query.first()
                base_admission = settings.default_admission_fee if settings else 2000.0
                
                # Re-admission is 50% of what they would normally pay for admission
                fee_to_charge = 0.0
                if admission_type == 'Normal':
                    fee_to_charge = base_admission * 0.5
                elif admission_type == 'Percentage':
                    fee_to_charge = (base_admission * (1 - admission_discount / 100)) * 0.5
                elif admission_type == 'Fixed':
                    fee_to_charge = admission_custom * 0.5
                
                if fee_to_charge > 0:
                    add_transaction(student.id, description="Re-admission Fee (50%)", debit=fee_to_charge, credit=0, txn_type='FEE')
                    flash(f"Re-admission fee of Rs {fee_to_charge} charged.")

        dob = request.form.get('dob')
        if dob == 'None': dob = None
        student.dob = dob

        # Handle photo upload
        photo = request.files.get('photo')
        if photo and photo.filename:
            # Delete old photo if exists
            if student.photo_path:
                old_path = os.path.join('static', student.photo_path)
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            filename = secure_filename(f"{student.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{photo.filename}")
            photo.save(os.path.join('static/uploads/students', filename))
            student.photo_path = f'uploads/students/{filename}'
        
        db.session.commit()
        
        db.session.commit()
        flash('Student updated successfully!')
        return redirect(url_for('students.index'))
    return render_template('students/form.html', student=student)
@student_bp.route('/students/delete/<int:id>')
@login_required
@admin_required
def delete(id):
    from database import Enrollment, Attendance, LedgerTransaction, WorkshopEnrollment, PackageEnrollment, ProductSale, ProgressReport
    student = Student.query.get_or_404(id)
    
    # Cascade delete related records manually
    Enrollment.query.filter_by(student_id=id).delete()
    Attendance.query.filter_by(student_id=id).delete()
    LedgerTransaction.query.filter_by(student_id=id).delete()
    WorkshopEnrollment.query.filter_by(student_id=id).delete()
    PackageEnrollment.query.filter_by(student_id=id).delete()
    ProductSale.query.filter_by(student_id=id).delete()
    ProgressReport.query.filter_by(student_id=id).delete()
    
    db.session.delete(student)
    db.session.commit()
    flash(f'Student {student.name} and all related records deleted.')
    return redirect(url_for('students.index'))

@student_bp.route('/students/progress/<int:id>', methods=['GET', 'POST'])
@login_required
def progress(id):
    from database import ProgressReport
    student = Student.query.get_or_404(id)
    
    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        note = request.form.get('note')
        date = request.form.get('date') # Should be BS string
        instructor = request.form.get('instructor_name')
        
        new_report = ProgressReport(
            student_id=id,
            rating=rating,
            note=note,
            date=date,
            instructor_name=instructor
        )
        db.session.add(new_report)
        db.session.commit()
        flash('Progress report added!')
        return redirect(url_for('students.progress', id=id))
        
    reports = ProgressReport.query.filter_by(student_id=id).order_by(ProgressReport.date.desc()).all()
    import nepali_datetime
    today_bs = nepali_datetime.date.today().strftime('%Y-%m-%d')
    return render_template('students/progress.html', student=student, reports=reports, today_bs=today_bs)

@student_bp.route('/students/delete-all', methods=['POST'])
@login_required
@admin_required
def delete_all():
    from database import Enrollment, Attendance, LedgerTransaction, WorkshopEnrollment, PackageEnrollment, ProductSale, ProgressReport
    
    # Get count for confirmation message
    student_count = Student.query.count()
    
    # Delete all related records first
    Enrollment.query.delete()
    Attendance.query.delete()
    LedgerTransaction.query.delete()
    WorkshopEnrollment.query.delete()
    PackageEnrollment.query.delete()
    ProductSale.query.delete()
    ProgressReport.query.delete()
    
    # Delete all students
    Student.query.delete()
    
    db.session.commit()
    flash(f'Successfully deleted all {student_count} students and their related records.', 'success')
    return redirect(url_for('students.index'))
