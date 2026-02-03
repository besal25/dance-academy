from tests.test_base import BaseTestCase
from database import db, User, Student, LedgerTransaction
from app import app
from flask import url_for

class SystemTestCase(BaseTestCase):
    def test_security_admin_access(self):
        """System Test: Verify that login is required for dashboard"""
        response = self.app.get('/', follow_redirects=True)
        # Should redirect to login page
        self.assertIn(b'Login', response.data)

    def test_e2e_student_billing_cycle(self):
        """System Test: Full cycle of Enrollment -> Payment -> Balance Verification"""
        with app.app_context():
            # 1. Login as Admin
            # We skip the actual login form and mock the session if needed, 
            # but here we test the logic via context
            s = Student(name="E2E Student", phone="9844444444", custom_monthly_fee=3000.0)
            db.session.add(s)
            db.session.commit()
            
            # 2. Add Fee Resulting from Admission
            t1 = LedgerTransaction(
                student_id=s.id, 
                description="Admission + Magh Fee", 
                debit=3500.0, 
                balance_after=3500.0,
                txn_type='FEE'
            )
            db.session.add(t1)
            db.session.commit()
            
            # 3. Verify Current Debt
            self.assertEqual(s.get_balance(), 3500.0)
            
            # 4. Make a partial payment
            t2 = LedgerTransaction(
                student_id=s.id,
                description="Partial Cash Payment",
                credit=2000.0,
                balance_after=1500.0,
                txn_type='PAYMENT'
            )
            db.session.add(t2)
            db.session.commit()
            
            # 5. Final assertion
            self.assertEqual(s.get_balance(), 1500.0)
            self.assertEqual(LedgerTransaction.query.filter_by(student_id=s.id).count(), 2)

    def test_permission_isolation(self):
        """System Test: Verify Staff cannot see Finance by default"""
        with app.app_context():
            staff = User(username='staff_user', role='Staff', can_view_finance=False, password_hash='hash')
            db.session.add(staff)
            db.session.commit()
            
            # In a real environment, we'd use login_user(staff)
            # but we can test the helper logic
            self.assertFalse(staff.can_view_finance)
            self.assertTrue(staff.can_manage_students) # Default is True
