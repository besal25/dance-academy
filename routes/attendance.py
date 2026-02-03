from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db, Class, Attendance, Enrollment
from routes.auth import admin_required, permission_required
import nepali_datetime
from datetime import datetime

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
@permission_required('can_view_attendance')
def index():
    classes = Class.query.all()
    selected_class = None
    students = []
    today_bs = nepali_datetime.date.today()
    date_str = today_bs.strftime('%Y-%m-%d')
    is_future = False
    
    if request.method == 'POST' or request.args.get('class_id'):
        class_id = request.form.get('class_id') or request.args.get('class_id')
        date_str = request.form.get('date') or request.args.get('date') or date_str
        date = date_str
        
        # Validation: Check if future date
        try:
            y, m, d = map(int, date_str.split('-'))
            selected_date = nepali_datetime.date(y, m, d)
            if selected_date > today_bs:
                is_future = True
                flash(f"Error: Cannot take attendance for future date ({date_str}).", "warning")
        except:
            pass
            
        if class_id and not is_future:
            selected_class = Class.query.get(class_id)
            if selected_class:
                # Get enrolled students
                enrollments = Enrollment.query.filter_by(class_id=selected_class.id).all()
                student_ids = [e.student_id for e in enrollments]
                
                # Fetch existing attendance for this date
                existing_records = Attendance.query.filter_by(class_id=selected_class.id, date=date).all()
                attendance_map = {r.student_id: r.status for r in existing_records}
                
                # Build list of student objects with their status
                for enroll in enrollments:
                    s = enroll.student
                    s.attendance_status = attendance_map.get(s.id, 'Absent')
                    students.append(s)

    return render_template('attendance/index.html', classes=classes, selected_class=selected_class, students=students, date=date_str, is_future=is_future)

@attendance_bp.route('/attendance/mark', methods=['POST'])
@login_required
def mark():
    class_id = request.form['class_id']
    date_str = request.form['date']
    date = date_str
    
    # Server-side validation again just in case
    today_bs = nepali_datetime.date.today()
    try:
        y, m, d = map(int, date_str.split('-'))
        selected_date = nepali_datetime.date(y, m, d)
        if selected_date > today_bs:
            flash("Error: Cannot save attendance for future dates.", "danger")
            return redirect(url_for('attendance.index', class_id=class_id, date=date_str))
    except:
        pass

    selected_class = Class.query.get(class_id)
    enrollments = Enrollment.query.filter_by(class_id=selected_class.id).all()
    
    for enroll in enrollments:
        student_id = enroll.student.id
        status = request.form.get(f'status_{student_id}')
        
        if status:
            # Check if exists
            record = Attendance.query.filter_by(class_id=class_id, student_id=student_id, date=date).first()
            if record:
                record.status = status
            else:
                new_record = Attendance(class_id=class_id, student_id=student_id, date=date, status=status)
                db.session.add(new_record)
    
    db.session.commit()
    flash('Attendance updated successfully.')
    return redirect(url_for('attendance.index', class_id=class_id, date=date_str))
