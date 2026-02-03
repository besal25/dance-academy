import os
from app import app
from database import db, Student, Instructor, Class, Enrollment, Attendance, LedgerTransaction
from datetime import datetime, date

def run_verification():
    print("starting verification...")
    
    # Use a fresh db for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        print("[OK] Database initialized (InMemory).")

        # 1. Create Instructor & Class
        inst = Instructor(name="Ms. Dance", phone="9876543210", specialty="Ballet")
        db.session.add(inst)
        db.session.commit()
        
        cls = Class(name="Ballet Beginners", instructor_id=inst.id, schedule="Mon 5PM", capacity=10)
        db.session.add(cls)
        db.session.commit()
        print("[OK] Instructor and Class created.")

        # 2. Register Student & Enroll
        # Case: Ram, 4500 custom fee
        ram = Student(name="Ram", phone="9841000000", custom_monthly_fee=4500, status="Active")
        db.session.add(ram)
        db.session.commit()
        
        enroll = Enrollment(student_id=ram.id, class_id=cls.id)
        db.session.add(enroll)
        db.session.commit()
        print(f"[OK] Student '{ram.name}' created with Fee: {ram.custom_monthly_fee}.")

        # 3. Test Ledger - Step 1: Monthly Fee Generation
        # Simulate "Generate Fees"
        from routes.finance import add_transaction
        add_transaction(ram.id, description="Monthly Fee - Jan", debit=ram.custom_monthly_fee, credit=0)
        
        ram_bal_1 = ram.get_balance()
        print(f"[Check] After Monthly Fee (4500): Balance is {ram_bal_1}")
        assert ram_bal_1 == 4500.0, f"Expected 4500, got {ram_bal_1}"

        # 4. Test Ledger - Step 2: Advance Payment
        # Ram pays 10,000
        add_transaction(ram.id, description="Payment - Cash", debit=0, credit=10000)
        
        ram_bal_2 = ram.get_balance()
        print(f"[Check] After Payment (10000): Balance is {ram_bal_2}")
        assert ram_bal_2 == -5500.0, f"Expected -5500 (Advance), got {ram_bal_2}"

        # 5. Test Ledger - Step 3: Next Month Fee
        add_transaction(ram.id, description="Monthly Fee - Feb", debit=ram.custom_monthly_fee, credit=0)
        
        ram_bal_3 = ram.get_balance()
        print(f"[Check] After Feb Fee (4500): Balance is {ram_bal_3}")
        assert ram_bal_3 == -1000.0, f"Expected -1000 (Still Advance), got {ram_bal_3}"
        
        print("[OK] Ledger Logic (Advance/Carry-over) Verified.")

        # 6. Test Attendance
        # Mark Ram Present
        att = Attendance(student_id=ram.id, class_id=cls.id, date=date.today(), status="Present")
        db.session.add(att)
        db.session.commit()
        print("[OK] Attendance marked.")

        # 7. Check Reports Logic
        # Ram has balance -1000, so he should NOT be in defaulters
        defaulters = [s for s in Student.query.all() if s.get_balance() > 0]
        assert len(defaulters) == 0, f"Ram shouldn't be a defaulter. Defaulters: {defaulters}"
        print("[Check] Defaulter Report Verified (Correctly Empty).")
        
        # Add a defaulter
        shyam = Student(name="Shyam", phone="999", custom_monthly_fee=5000)
        db.session.add(shyam)
        db.session.commit()
        add_transaction(shyam.id, description="Fee", debit=5000, credit=0)
        
        defaulters_2 = [s for s in Student.query.all() if s.get_balance() > 0]
        assert len(defaulters_2) == 1, "Should have 1 defaulter now."
        print("[Check] Defaulter Report Verified (Found verification case).")

    print("\n------------------------------------------------")
    print("ALL SYSTEM CHECKS PASSED SUCCESSFULLY.")
    print("------------------------------------------------")

if __name__ == '__main__':
    run_verification()
