from tests.test_base import BaseTestCase
from database import db, Student, LedgerTransaction
from app import app

class ModelTestCase(BaseTestCase):
    def test_student_balance_calculation(self):
        """Unit Test: Verify logic of student.get_balance()"""
        with app.app_context():
            s = Student(name="Test Student", phone="9800000000")
            db.session.add(s)
            db.session.commit()
            
            # Initially balance should be 0
            self.assertEqual(s.get_balance(), 0.0)
            
            # Step 1: Add a Fee (Debit)
            t1 = LedgerTransaction(student_id=s.id, description="Monthly Fee", debit=5000.0, balance_after=5000.0)
            db.session.add(t1)
            db.session.commit()
            self.assertEqual(s.get_balance(), 5000.0)
            
            # Step 2: Add a Payment (Credit)
            t2 = LedgerTransaction(student_id=s.id, description="Payment", credit=3000.0, balance_after=2000.0)
            db.session.add(t2)
            db.session.commit()
            self.assertEqual(s.get_balance(), 2000.0)

    def test_void_logic_consistency(self):
        """Unit Test: Verify that void flag exists and defaults to False"""
        with app.app_context():
            t = LedgerTransaction(student_id=1, description="Test", debit=100, balance_after=100)
            self.assertFalse(t.is_void)
            
            t.is_void = True
            db.session.add(t)
            db.session.commit()
            
            re_fetched = LedgerTransaction.query.get(t.id)
            self.assertTrue(re_fetched.is_void)
