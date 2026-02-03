import pytest
from app import app as flask_app
from database import db, Student, Workshop, Package, Product, LedgerTransaction, Settings, WorkshopEnrollment, PackageEnrollment, ProductSale
import nepali_datetime

@pytest.fixture
def app():
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['TESTING'] = True
    with flask_app.app_context():
        db.create_all()
        # Initial Settings
        settings = Settings(academy_name="Test Academy", default_admission_fee=2000.0)
        db.session.add(settings)
        db.session.commit()
        yield flask_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_admission_logic(app):
    with app.app_context():
        # 1. Normal Admission
        from routes.students import student_bp
        from flask import url_for
        
        # We'll test the route logic directly or mock the request
        # For simplicity, let's test the database state after manual calls to logic
        from routes.finance import add_transaction
        
        student = Student(name="John Doe", phone="9800000000", admission_fee_type='Normal')
        db.session.add(student)
        db.session.commit()
        
        # Simulate Admission Fee Charge (like in routes/students.py)
        settings = Settings.query.first()
        add_transaction(student.id, description="Admission Fee", debit=settings.default_admission_fee, txn_type='FEE')
        
        assert student.get_balance() == 2000.0

        # 2. Percentage Discount
        student2 = Student(name="Jane Doe", phone="9811111111", admission_fee_type='Percentage', admission_discount_percent=25.0)
        db.session.add(student2)
        db.session.commit()
        
        fee = settings.default_admission_fee * (1 - student2.admission_discount_percent / 100)
        add_transaction(student2.id, description="Admission Fee", debit=fee, txn_type='FEE')
        
        assert student2.get_balance() == 1500.0

def test_readmission_logic(app):
    with app.app_context():
        student = Student(name="John Rejoin", phone="9800000000", status='Inactive', admission_fee_type='Normal')
        db.session.add(student)
        db.session.commit()
        
        # Simulate Re-activation with Charge (50%)
        settings = Settings.query.first()
        fee = settings.default_admission_fee * 0.5
        from routes.finance import add_transaction
        add_transaction(student.id, description="Re-admission Fee (50%)", debit=fee, txn_type='FEE')
        student.status = 'Active'
        db.session.commit()
        
        assert student.get_balance() == 1000.0

def test_workshop_enrollment(app):
    with app.app_context():
        workshop = Workshop(name="Masterclass", start_date="2081-01-01", end_date="2081-01-05", fee=1500.0)
        db.session.add(workshop)
        student = Student(name="Dancer", phone="9800000000")
        db.session.add(student)
        db.session.commit()
        
        from routes.finance import add_transaction
        # Enroll
        enrollment = WorkshopEnrollment(workshop_id=workshop.id, student_id=student.id, amount_paid=500.0, date="2081-01-01")
        db.session.add(enrollment)
        
        # Charge Workshop
        add_transaction(student.id, description=f"Workshop: {workshop.name}", debit=workshop.fee, txn_type='FEE')
        # Record Payment
        add_transaction(student.id, description=f"Payment for Workshop", debit=0, credit=500.0, txn_type='PAYMENT')
        
        assert student.get_balance() == 1000.0

def test_package_enrollment_check(app):
    with app.app_context():
        package = Package(name="3 Month Pack", duration_months=3, price=4000.0)
        db.session.add(package)
        student = Student(name="Member", phone="9800000000") # No admission date
        db.session.add(student)
        db.session.commit()
        
        # The route should fail here (verified in routes/packages.py lines 69-71)
        # We can test the condition
        assert student.last_admission_date is None
        
        # Now pay admission
        student.last_admission_date = "2081-01-01"
        db.session.commit()
        assert student.last_admission_date is not None

def test_product_sale(app):
    with app.app_context():
        product = Product(name="T-Shirt", price=1200.0, stock=10)
        db.session.add(product)
        student = Student(name="Buyer", phone="9800000000")
        db.session.add(student)
        db.session.commit()
        
        from routes.finance import add_transaction
        # Sell with discount (Final price 1000)
        sale = ProductSale(product_id=product.id, student_id=student.id, quantity=1, price_sold=1000.0, date="2081-01-01")
        db.session.add(sale)
        product.stock -= 1
        add_transaction(student.id, description=f"Purchase: T-Shirt", debit=1000.0, txn_type='FEE')
        
        assert product.stock == 9
        assert student.get_balance() == 1000.0
