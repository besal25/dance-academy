from flask import Flask, render_template
from database import db, User
from flask_login import LoginManager, login_required
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dance_academy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'dev_key_very_secret' # Change for production

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from routes.students import student_bp
from routes.classes import class_bp
from routes.finance import finance_bp
from routes.attendance import attendance_bp
from routes.reports import reports_bp
from routes.auth import auth_bp, create_admin_user
from routes.expenses import expenses_bp
from routes.settings import settings_bp, get_settings
from routes.api import api_bp
from routes.workshops import workshops_bp
from routes.packages import packages_bp
from routes.inventory import inventory_bp

app.register_blueprint(student_bp)
app.register_blueprint(class_bp)
app.register_blueprint(finance_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(api_bp)
app.register_blueprint(workshops_bp)
app.register_blueprint(packages_bp)
app.register_blueprint(inventory_bp)

# Global Context Processor for Academy Settings
@app.context_processor
def inject_settings():
    return dict(site_settings=get_settings())

@app.route('/')
@login_required
def dashboard():
    from database import Student, Class
    from datetime import datetime
    
    student_count = Student.query.filter_by(status='Active').count()
    class_count = Class.query.count()
    
    # --- Upcoming Birthdays (Next 30 days) ---
    import nepali_datetime
    today_bs = nepali_datetime.date.today()
    active_students = Student.query.filter_by(status='Active').all()
    birthdays = []
    
    for s in active_students:
        dob_str = s.dob # String YYYY-MM-DD
        if dob_str and dob_str != 'None':
            try:
                # Parse YYYY-MM-DD
                parts = dob_str.split('-')
                dob_year = int(parts[0])
                dob_month = int(parts[1])
                dob_day = int(parts[2])
                
                # Create birthday for *this year*
                # Handle month/day overflow? 
                # Nepali months vary. We'll try to create it.
                # If day is 32 and this year month has 31, it might error.
                # We can skip complex validation or try/except
                
                bday_this_year = nepali_datetime.date(today_bs.year, dob_month, dob_day)
            except ValueError:
                # E.g. Date doesn't exist this year
                continue

            if bday_this_year < today_bs:
                try:
                    bday_this_year = nepali_datetime.date(today_bs.year + 1, dob_month, dob_day)
                except ValueError:
                    continue
            
            days_until = (bday_this_year - today_bs).days
            if 0 <= days_until <= 30:
                 birthdays.append(s)

    # Sort manually or just pass list. Let's pass list.
    
    # --- Today's Schedule ---
    today = datetime.now()
    day_name = today.strftime("%a") # Mon, Tue...
    all_classes = Class.query.all()
    todays_classes = [c for c in all_classes if c.schedule and day_name in c.schedule]

    # --- Analytics & Alerts (High Dues) ---
    from database import LedgerTransaction, Expense
    import nepali_datetime
    
    # High Due Students (> 5000)
    high_due_students = [s for s in active_students if s.get_balance() > 5000]
    
    # 6-Month Income vs Expenses
    analytics_labels = []
    income_data = []
    expense_data = []
    
    # We'll use the last 6 Nepali months
    curr_month = today_bs.month
    curr_year = today_bs.year
    
    for i in range(5, -1, -1):
        m = curr_month - i
        y = curr_year
        if m <= 0:
            m += 12
            y -= 1
        
        month_label = f"{y}-{m:02d}"
        analytics_labels.append(month_label)
        
        # Income from Ledger (Credits)
        # Note: LedgerTransaction.date is "YYYY-MM-DD" BS string
        month_prefix = f"{y}-{m:02d}"
        month_income = db.session.query(db.func.sum(LedgerTransaction.credit)).filter(LedgerTransaction.date.like(f"{month_prefix}%")).scalar() or 0.0
        income_data.append(month_income)
        
        # Expenses
        month_expense = db.session.query(db.func.sum(Expense.amount)).filter(Expense.date.like(f"{month_prefix}%")).scalar() or 0.0
        expense_data.append(month_expense)

    # --- Absence Alerts (3+ consecutive Absents) ---
    from database import Attendance
    absence_alerts = []
    for s in active_students:
        # Get last 3 attendance records for this student sorted by date desc
        last_3 = Attendance.query.filter_by(student_id=s.id).order_by(Attendance.date.desc()).limit(3).all()
        if len(last_3) >= 3:
            # Check if all 3 are 'Absent'
            if all(a.status == 'Absent' for a in last_3):
                absence_alerts.append(s)

    return render_template('dashboard.html', 
                           student_count=student_count, 
                           class_count=class_count,
                           birthdays=birthdays,
                           todays_classes=todays_classes,
                           high_due_students=high_due_students,
                           analytics_labels=analytics_labels,
                           income_data=income_data,
                           expense_data=expense_data,
                           absence_alerts=absence_alerts)

if __name__ == '__main__':
    if not os.path.exists('dance_academy.db') or not os.path.exists('instance/dance_academy.db'):
        # Just in case it's in instance, but let's stick to root for this simple setup or let SQLAlchemy handle it
        with app.app_context():
            db.create_all()
            create_admin_user() # Ensure admin exists
            print("Database initialized.")
    else:
        # Also check on restart if admin exists (e.g. if db existed but table didn't or user deleted)
        with app.app_context():
            # db.create_all() # safe to call even if exists
            create_admin_user()
            
    app.run(debug=True)
