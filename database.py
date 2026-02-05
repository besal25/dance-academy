from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.String(20), nullable=True)
    guardian_name = db.Column(db.String(100), nullable=True)
    emergency_contact = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), default='Active') # Active, Inactive
    custom_monthly_fee = db.Column(db.Float, default=5000.0) # Final fee
    base_monthly_fee = db.Column(db.Float, default=5000.0) # Baseline fee
    photo_path = db.Column(db.String(200), nullable=True)
    
    # Admission Tracking
    last_admission_date = db.Column(db.String(20), nullable=True)
    admission_fee_type = db.Column(db.String(50), default='Normal') # Normal, Scholarship, Percentage, Fixed
    admission_discount_percent = db.Column(db.Float, default=0.0)
    custom_admission_fee = db.Column(db.Float, default=0.0)

    # Relationships
    enrollments = db.relationship('Enrollment', backref='student', lazy=True, cascade="all, delete-orphan")
    attendance_records = db.relationship('Attendance', backref='student', lazy=True, cascade="all, delete-orphan")
    ledger_entries = db.relationship('LedgerTransaction', backref='student', lazy=True, order_by="LedgerTransaction.date", cascade="all, delete-orphan")
    workshop_enrollments = db.relationship('WorkshopEnrollment', backref='student', lazy=True, cascade="all, delete-orphan")
    package_enrollments = db.relationship('PackageEnrollment', backref='student', lazy=True, cascade="all, delete-orphan")
    product_sales = db.relationship('ProductSale', backref='student', lazy=True, cascade="all, delete-orphan")

    def get_balance(self):
        # Calculate balance dynamically or use the last transaction's balance_after
        last_txn = LedgerTransaction.query.filter_by(student_id=self.id, is_void=False).order_by(LedgerTransaction.date.desc(), LedgerTransaction.id.desc()).first()
        return last_txn.balance_after if last_txn else 0.0

class Instructor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    specialty = db.Column(db.String(50), nullable=True)
    
    classes = db.relationship('Class', backref='instructor', lazy=True)
    
    # New Fields
    photo_path = db.Column(db.String(200), nullable=True)
    citizenship_no = db.Column(db.String(50), nullable=True)
    document_path = db.Column(db.String(200), nullable=True)

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # e.g., Jazz Batch A
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructor.id'), nullable=True)
    schedule = db.Column(db.String(200), nullable=True) # e.g., "Mon, Wed, Fri 6PM"
    capacity = db.Column(db.Integer, nullable=True)
    
    enrollments = db.relationship('Enrollment', backref='class_info', lazy=True)

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    enrolled_date = db.Column(db.String(20), default=lambda: datetime.now().strftime('%Y-%m-%d'))

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False, default=lambda: datetime.now().strftime('%Y-%m-%d'))
    status = db.Column(db.String(20), nullable=False) # Present, Absent, Late
    remarks = db.Column(db.Text, nullable=True)

class LedgerTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.String(20), default=lambda: datetime.now().strftime('%Y-%m-%d'))
    description = db.Column(db.String(200), nullable=False)
    debit = db.Column(db.Float, default=0.0) # Charge (Increases what they owe)
    credit = db.Column(db.Float, default=0.0) # Payment (Decreases what they owe)
    balance_after = db.Column(db.Float, nullable=False) # Snapshot of balance
    txn_type = db.Column(db.String(20), default='FEE') # FEE, PAYMENT, ADJUSTMENT
    is_void = db.Column(db.Boolean, default=False)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='Staff') # Admin, Staff
    
    # Granular Permissions
    can_manage_students = db.Column(db.Boolean, default=True)
    can_manage_classes = db.Column(db.Boolean, default=True)
    can_view_attendance = db.Column(db.Boolean, default=True)
    can_view_finance = db.Column(db.Boolean, default=False)
    can_manage_expenses = db.Column(db.Boolean, default=False)
    can_view_reports = db.Column(db.Boolean, default=False)
    can_manage_settings = db.Column(db.Boolean, default=False)
    can_manage_workshops = db.Column(db.Boolean, default=False)
    can_manage_packages = db.Column(db.Boolean, default=False)
    can_manage_inventory = db.Column(db.Boolean, default=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), default=lambda: datetime.now().strftime('%Y-%m-%d'))
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False) # Rent, Utility, Salary, Misc
    description = db.Column(db.String(200), nullable=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructor.id'), nullable=True)
    is_void = db.Column(db.Boolean, default=False)
    
    instructor = db.relationship('Instructor', backref='salaries', lazy=True)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    academy_name = db.Column(db.String(100), default='Dance Academy')
    logo_path = db.Column(db.String(200), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    contact = db.Column(db.String(50), nullable=True)
    currency = db.Column(db.String(10), default='Rs')
    default_admission_fee = db.Column(db.Float, default=1000.0)
    default_monthly_fee = db.Column(db.Float, default=5000.0)

class ProgressReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.String(20), default=lambda: datetime.now().strftime('%Y-%m-%d'))
    rating = db.Column(db.Integer) # 1-5 stars
    note = db.Column(db.Text, nullable=True)
    instructor_name = db.Column(db.String(100), nullable=True)
    
    student_rel = db.relationship('Student', backref='progress_reports', lazy=True)

class Workshop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.String(20), nullable=False) # BS Date
    end_date = db.Column(db.String(20), nullable=False) # BS Date
    fee = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    enrollments = db.relationship('WorkshopEnrollment', backref='workshop', lazy=True)

class WorkshopEnrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workshop_id = db.Column(db.Integer, db.ForeignKey('workshop.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True) # Null for outside students
    guest_name = db.Column(db.String(100), nullable=True) # For outside students
    guest_phone = db.Column(db.String(20), nullable=True) # For outside students
    amount_paid = db.Column(db.Float, default=0.0)
    date = db.Column(db.String(20), default=lambda: datetime.now().strftime('%Y-%m-%d'))

class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    duration_months = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)

class PackageEnrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    start_date = db.Column(db.String(20), nullable=False) # BS Date
    end_date = db.Column(db.String(20), nullable=False) # BS Date
    total_price = db.Column(db.Float, nullable=False)
    amount_paid = db.Column(db.Float, default=0.0)
    payment_deadline = db.Column(db.String(20), nullable=True) # BS Date
    
    package = db.relationship('Package', backref='enrollments', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)

class ProductSale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.String(20), default=lambda: datetime.now().strftime('%Y-%m-%d'))
    quantity = db.Column(db.Integer, default=1)
    price_sold = db.Column(db.Float, nullable=False) # Can be discounted
    
    product = db.relationship('Product', backref='sales', lazy=True)

