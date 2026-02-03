from flask import Blueprint, jsonify, request, url_for
from flask_login import login_required, current_user
from database import db, Student, Class, LedgerTransaction, Attendance
import nepali_datetime
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/search')
@login_required
def search():
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'results': []})

    results = []

    # 1. Search Students (Name or Phone)
    students = Student.query.filter(
        (Student.name.ilike(f'%{query}%')) | 
        (Student.phone.ilike(f'%{query}%'))
    ).limit(5).all()
    for s in students:
        results.append({
            'type': 'Student',
            'title': s.name,
            'subtitle': f'Phone: {s.phone}',
            'url': url_for('finance.student_ledger', student_id=s.id),
            'icon': 'fas fa-user-graduate'
        })

    # 2. Search Classes
    classes = Class.query.filter(Class.name.ilike(f'%{query}%')).limit(3).all()
    for c in classes:
        results.append({
            'type': 'Class',
            'title': c.name,
            'subtitle': c.schedule or 'No schedule',
            'url': url_for('classes.index'), # Could link to specific class view if existed
            'icon': 'fas fa-chalkboard-teacher'
        })

    # 3. Search Transactions (by ID or Description)
    # Check if query is numeric for ID search
    if query.isdigit():
        txns = LedgerTransaction.query.filter(LedgerTransaction.id == int(query)).limit(3).all()
    else:
        txns = LedgerTransaction.query.filter(LedgerTransaction.description.ilike(f'%{query}%')).limit(3).all()
    
    for t in txns:
        results.append({
            'type': 'Transaction',
            'title': f'Txn #{t.id}: {t.description}',
            'subtitle': f'Student: {t.student.name} | Rs {t.credit if t.credit > 0 else t.debit}',
            'url': url_for('finance.student_ledger', student_id=t.student_id),
            'icon': 'fas fa-receipt'
        })

    return jsonify({'results': results})

@api_bp.route('/alerts')
@login_required
def alerts():
    # Similar logic to dashboard but returns JSON
    today_bs = nepali_datetime.date.today()
    active_students = Student.query.filter_by(status='Active').all()
    
    notifications = []

    # 1. Birthdays
    for s in active_students:
        dob_str = s.dob
        if dob_str and dob_str != 'None':
            try:
                parts = dob_str.split('-')
                dob_month = int(parts[1])
                dob_day = int(parts[2])
                if dob_month == today_bs.month and dob_day == today_bs.day:
                    notifications.append({
                        'id': f'bday-{s.id}',
                        'type': 'birthday',
                        'title': f"Today is {s.name}'s Birthday! 🎂",
                        'message': "Don't forget to wish them!",
                        'url': url_for('finance.student_ledger', student_id=s.id),
                        'icon': 'fas fa-birthday-cake',
                        'color': '#f43f5e'
                    })
            except: continue

    # 2. Absence Alerts
    for s in active_students:
        last_3 = Attendance.query.filter_by(student_id=s.id).order_by(Attendance.date.desc()).limit(3).all()
        if len(last_3) >= 3 and all(a.status == 'Absent' for a in last_3):
            notifications.append({
                'id': f'absense-{s.id}',
                'type': 'caution',
                'title': 'Attendance Caution',
                'message': f'{s.name} missed 3 classes.',
                'url': url_for('attendance.index', class_id=last_3[0].class_id),
                'icon': 'fas fa-user-clock',
                'color': '#ef4444'
            })

    # 3. High Dues
    if current_user.role == 'Admin' or current_user.can_view_finance:
        for s in active_students:
            bal = s.get_balance()
            if bal > 5000:
                notifications.append({
                    'id': f'due-{s.id}',
                    'type': 'payment',
                    'title': 'High Balance Alert',
                    'message': f'{s.name} owes Rs {bal:,.0f}',
                    'url': url_for('finance.student_ledger', student_id=s.id),
                    'icon': 'fas fa-exclamation-triangle',
                    'color': '#f59e0b'
                })

    return jsonify({
        'count': len(notifications),
        'alerts': notifications
    })
