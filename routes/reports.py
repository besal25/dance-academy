from flask import Blueprint, render_template, request, Response, redirect, url_for, flash
from flask_login import login_required
from routes.auth import permission_required
from database import db, Student, LedgerTransaction, Enrollment, Attendance, Class
import csv
import io
import nepali_datetime
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
@permission_required('can_view_reports')
def index():
    # --- Defaulters List Logic ---
    # Students with Positive Balance (> 0)
    all_students = Student.query.filter_by(status='Active').all()
    defaulters = [s for s in all_students if s.get_balance() > 0]
    
    # --- Income Report Logic ---
    # Default to current month (BS)
    today_bs = nepali_datetime.date.today()
    first_day_bs = nepali_datetime.date(today_bs.year, today_bs.month, 1)
    
    start_date_str = request.args.get('start_date', first_day_bs.strftime('%Y-%m-%d'))
    end_date_str = request.args.get('end_date', today_bs.strftime('%Y-%m-%d'))
    
    start_date = start_date_str
    end_date = end_date_str
    
    # Fetch CREDIT transactions (Payments) within range
    income_txns = LedgerTransaction.query.filter(
        LedgerTransaction.date >= start_date,
        LedgerTransaction.date <= end_date,
        LedgerTransaction.credit > 0
    ).order_by(LedgerTransaction.date.desc()).all()
    
    total_income_ledger = sum(t.credit for t in income_txns)
    
    # Fetch Guest Workshop Payments (not in ledger)
    from database import WorkshopEnrollment
    guest_payments = WorkshopEnrollment.query.filter(
        WorkshopEnrollment.student_id == None,
        WorkshopEnrollment.date >= start_date,
        WorkshopEnrollment.date <= end_date,
        WorkshopEnrollment.amount_paid > 0
    ).all()
    
    total_guest_income = sum(p.amount_paid for p in guest_payments)
    total_income = total_income_ledger + total_guest_income

    # Unify for template
    unified_income = []
    for t in income_txns:
        unified_income.append({
            'date': t.date,
            'name': t.student.name if t.student else "Unknown",
            'description': t.description,
            'amount': t.credit,
            'id': t.id,
            'is_void': t.is_void,
            'type': 'Ledger'
        })
    for p in guest_payments:
        unified_income.append({
            'date': p.date,
            'name': f"{p.guest_name} (Guest)",
            'description': f"Workshop: {p.workshop.name}",
            'amount': p.amount_paid,
            'id': p.id,
            'is_void': False,
            'type': 'Workshop'
        })
    
    # Sort by date
    unified_income.sort(key=lambda x: x['date'], reverse=True)

    # --- Expense Logic ---
    from database import Expense
    expenses = Expense.query.filter(
        Expense.date >= start_date,
        Expense.date <= end_date
    ).order_by(Expense.date.desc()).all()
    
    total_expense = sum(e.amount for e in expenses)
    net_profit = total_income - total_expense
    
    return render_template('reports/index.html', 
                           defaulters=defaulters,
                           income_txns=unified_income,
                           total_income=total_income,
                           expenses=expenses,
                           total_expense=total_expense,
                           net_profit=net_profit,
                           start_date=start_date_str,
                           end_date=end_date_str)

@reports_bp.route('/reports/export/income')
@login_required
def export_income():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    start_date = start_date_str
    end_date = end_date_str
    
    # Unify for CSV
    unified_entries = []
    for txn in income_txns:
        unified_entries.append([txn.date, txn.student.name if txn.student else "Unknown", txn.description, txn.credit])
        
    # Guest Workshop Payments
    from database import WorkshopEnrollment
    guest_payments = WorkshopEnrollment.query.filter(
        WorkshopEnrollment.student_id == None,
        WorkshopEnrollment.date >= start_date,
        WorkshopEnrollment.date <= end_date,
        WorkshopEnrollment.amount_paid > 0
    ).all()
    
    for p in guest_payments:
        unified_entries.append([p.date, f"{p.guest_name} (Guest)", f"Workshop: {p.workshop.name}", p.amount_paid])
    
    # Sort by date
    unified_entries.sort(key=lambda x: x[0], reverse=True)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Name', 'Description', 'Amount'])
    
    for row in unified_entries:
        writer.writerow(row)
        
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=income_report_{start_date_str}_to_{end_date_str}.csv"}
    )

@reports_bp.route('/reports/export/attendance')
@login_required
def export_attendance():
    # Export attendance for all classes for a specific month? Or all time?
    # Let's do a simple dump for now, or maybe filter by class/date if params provided.
    # Request said "Implement CSV Export for Attendance".
    
    class_id = request.args.get('class_id')
    date_str = request.args.get('date')
    
    query = Attendance.query
    filename = "attendance_report.csv"
    
    if class_id:
        query = query.filter_by(class_id=class_id)
        filename = f"attendance_class_{class_id}.csv"
        
    if date_str:
        date = date_str
        query = query.filter_by(date=date)
        filename = f"attendance_{date_str}.csv"
        
    records = query.order_by(Attendance.date.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Class', 'Student Name', 'Status'])
    
    for r in records:
        # Resolve class name and student name lazily if not joined, but basic is fine
         if r.student and r.student.name: # checking relationships
            class_name = Class.query.get(r.class_id).name if r.class_id else "Unknown"
            writer.writerow([r.date, class_name, r.student.name, r.status])
            
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
