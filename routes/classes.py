from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from routes.auth import admin_required, permission_required
from database import Class, Instructor, Student, Enrollment, db

class_bp = Blueprint('classes', __name__)

@class_bp.route('/classes')
@login_required
@permission_required('can_manage_classes')
def index():
    classes = Class.query.all()
    instructors = Instructor.query.all()
    # Fetch active students for enrollment dropdown
    students = Student.query.filter_by(status='Active').order_by(Student.name).all()
    return render_template('classes/index.html', classes=classes, instructors=instructors, students=students)

# --- Instructor Management ---
@class_bp.route('/instructors/add', methods=['POST'])
@login_required
def add_instructor():
    name = request.form['name']
    phone = request.form['phone']
    
    # 10-digit validation
    clean_phone = ''.join(filter(str.isdigit, phone))
    if len(clean_phone) != 10:
        flash("Error: Instructor phone must be exactly 10 digits.", "warning")
        return redirect(url_for('classes.index'))
    
    specialty = request.form['specialty']
    citizenship_no = request.form.get('citizenship_no')
    
    # Handle File Uploads
    from werkzeug.utils import secure_filename
    import os
    from datetime import datetime
    
    photo_path = None
    document_path = None
    
    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename != '':
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = secure_filename(f"{name}_{timestamp}_{file.filename}")
            # Ensure directory exists
            upload_folder = os.path.join('static', 'uploads', 'instructors')
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, filename))
            photo_path = f"uploads/instructors/{filename}"

    if 'document' in request.files:
        file = request.files['document']
        if file and file.filename != '':
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = secure_filename(f"{name}_doc_{timestamp}_{file.filename}")
            upload_folder = os.path.join('static', 'uploads', 'instructors')
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, filename))
            document_path = f"uploads/instructors/{filename}"

    new_instructor = Instructor(
        name=name, 
        phone=clean_phone, 
        specialty=specialty,
        citizenship_no=citizenship_no,
        photo_path=photo_path,
        document_path=document_path
    )
    db.session.add(new_instructor)
    db.session.commit()
    flash('Instructor added successfully!')
    return redirect(url_for('classes.index'))

# --- Class Management ---
@class_bp.route('/classes/add', methods=['POST'])
@login_required
def add_class():
    name = request.form['name']
    instructor_id = request.form.get('instructor_id')
    schedule = request.form['schedule']
    capacity = request.form.get('capacity')
    
    new_class = Class(
        name=name,
        instructor_id=instructor_id,
        schedule=schedule,
        capacity=int(capacity) if capacity else None
    )
    db.session.add(new_class)
    db.session.commit()
    flash('Class created successfully!')
    return redirect(url_for('classes.index'))

@class_bp.route('/classes/edit/<int:id>', methods=['POST'])
@login_required
@permission_required('can_manage_classes')
def edit_class(id):
    cls = Class.query.get_or_404(id)
    cls.name = request.form['name']
    
    # Handle optional fields
    instructor_id = request.form.get('instructor_id')
    cls.instructor_id = instructor_id if instructor_id else None
    
    cls.schedule = request.form['schedule']
    
    capacity = request.form.get('capacity')
    cls.capacity = int(capacity) if capacity else None
    
    db.session.commit()
    flash('Class updated successfully!')
    return redirect(url_for('classes.index'))

@class_bp.route('/classes/delete/<int:id>')
@login_required
def delete_class(id):
    cls = Class.query.get_or_404(id)
    if cls.enrollments:
        flash('Cannot delete class, first delete students', 'danger')
        return redirect(url_for('classes.index'))
    db.session.delete(cls)
    db.session.commit()
    flash('Class deleted.')
    return redirect(url_for('classes.index'))
@class_bp.route('/instructors/delete/<int:id>')
@login_required
def delete_instructor(id):
    inst = Instructor.query.get_or_404(id)
    # Classes will have instructor_id set to NULL due to FK behavior or manual unset
    # In our models, it's nullable=True, so we can just delete and let SQLAlchemy handle or do it manually
    for cls in inst.classes:
        cls.instructor_id = None
    
    db.session.delete(inst)
    db.session.commit()
    flash(f'Instructor {inst.name} deleted.')
    return redirect(url_for('classes.index'))
@class_bp.route('/classes/enroll', methods=['POST'])
@login_required
def enroll_student():
    student_id = request.form.get('student_id')
    class_id = request.form.get('class_id')
    
    if student_id and class_id:
        # Check if already enrolled
        exists = Enrollment.query.filter_by(student_id=student_id, class_id=class_id).first()
        if not exists:
            new_enrollment = Enrollment(student_id=student_id, class_id=class_id)
            db.session.add(new_enrollment)
            db.session.commit()
            flash('Student enrolled successfully!')
        else:
            flash('Student is already enrolled in this class.')
    
    return redirect(url_for('classes.index'))

@class_bp.route('/classes/unenroll/<int:enrollment_id>')
@login_required
def unenroll_student(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    db.session.delete(enrollment)
    db.session.commit()
    flash('Student unenrolled.')
    db.session.commit()
    flash('Student unenrolled.')
    return redirect(url_for('classes.index'))

@class_bp.route('/classes/delete-all', methods=['POST'])
@login_required
@admin_required
def delete_all():
    from database import Enrollment, Attendance
    
    count = Class.query.count()
    
    # Cascade delete enrollments and attendance for all classes
    Enrollment.query.delete()
    Attendance.query.delete()
    Class.query.delete()
    
    db.session.commit()
    flash(f'All {count} classes and related records (Enrollments, Attendance) have been deleted.', 'success')
    return redirect(url_for('classes.index'))
