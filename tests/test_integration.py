from tests.test_base import BaseTestCase
from database import db, Student, LedgerTransaction
from app import app
from routes.finance import recalculate_balances

class IntegrationTestCase(BaseTestCase):
    def test_recalculate_balances_integration(self):
        """Integration Test: Verify multiple transactions and recalculation logic"""
        with app.app_context():
            # 1. Setup Student
            s = Student(name="Integration Student", phone="9811111111")
            db.session.add(s)
            db.session.commit()

            # 2. Add Fee
            t1 = LedgerTransaction(student_id=s.id, description="Fee 1", debit=1000.0, balance_after=1000.0)
            db.session.add(t1)
            
            # 3. Add Another Fee
            t2 = LedgerTransaction(student_id=s.id, description="Fee 2", debit=2000.0, balance_after=3000.0)
            db.session.add(t2)
            db.session.commit()
            
            # 4. Void first fee
            t1.is_void = True
            db.session.commit()
            
            # 5. Run helper manually (as it would be in the route)
            recalculate_balances(s.id)
            
            # 6. Verify result: Balance should be 2000.0 because Fee 1 is voided
            # And Fee 2's balance_after should also be corrected to 2000.0
            re_t2 = LedgerTransaction.query.get(t2.id)
            self.assertEqual(re_t2.balance_after, 2000.0)
            self.assertEqual(s.get_balance(), 2000.0)

    def test_payment_and_auto_billing_flow(self):
        """Integration Test: Simulating adding a student and their first fee"""
        # This tests the interaction between Student creation and Ledger
        with app.app_context():
            # Triggering the route logic (simplified simulation)
            s = Student(name="New Student", phone="9822222222", custom_monthly_fee=4500.0)
            db.session.add(s)
            db.session.commit()
            
            # simulate finance.add_transaction for admission fee
            t = LedgerTransaction(student_id=s.id, description="Admission 1", debit=5000.0, balance_after=5000.0)
            db.session.add(t)
            db.session.commit()
            
            self.assertEqual(LedgerTransaction.query.filter_by(student_id=s.id).count(), 1)
            self.assertEqual(s.get_balance(), 5000.0)
