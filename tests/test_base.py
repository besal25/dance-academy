import unittest
from app import app
from database import db, User, Student, Class, Instructor, Enrollment, Attendance, LedgerTransaction, Expense

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing
        
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
            # Create a default admin for testing if not exists
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin', role='Admin')
                admin.password_hash = 'test_hash' # Simplified
                db.session.add(admin)
                db.session.commit()
                self.admin_id = admin.id
            else:
                self.admin_id = User.query.filter_by(username='admin').first().id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
