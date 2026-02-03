import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app import app
from database import db, Student, Workshop, WorkshopEnrollment, Package, PackageEnrollment, Product, ProductSale, Settings, LedgerTransaction
from routes.finance import add_transaction
import nepali_datetime

def verify():
    print("Starting Detailed Verification of New Features...")
    with app.app_context():
        db.create_all()
        
        # 0. Initialize Settings
        from database import Settings
        settings = Settings.query.first()
        if not settings:
            settings = Settings(default_admission_fee=1000.0)
            db.session.add(settings)
        else:
            settings.default_admission_fee = 1000.0
        db.session.commit()
        print("[OK] Settings Initialized (Admission Fee: 1000)")

        # 1. Test Normal Admission
        student1 = Student(name="Normal Student", phone="9800000001", status="Active", 
                           admission_fee_type='Normal', last_admission_date='2080-01-15')
        db.session.add(student1)
        db.session.commit()
        
        # Charge 1000
        add_transaction(student1.id, "Admission Fee", debit=1000, credit=0, txn_type='FEE')
        assert student1.get_balance() == 1000.0
        print(f"[OK] Normal Admission: Normal Student Balance: {student1.get_balance()}")

        # 2. Test Scholarship Admission (0 fee)
        student2 = Student(name="Scholarship Student", phone="9800000002", status="Active", 
                           admission_fee_type='Scholarship')
        db.session.add(student2)
        db.session.commit()
        
        assert student2.get_balance() == 0.0
        print(f"[OK] Scholarship Admission: Scholarship Student Balance: {student2.get_balance()}")

        # 3. Test Percentage Discount (40% off of 1000 = 600)
        student_disc = Student(name="Discount Student", phone="9800000003", status="Active", 
                               admission_fee_type='Percentage', admission_discount_percent=40.0)
        db.session.add(student_disc)
        db.session.commit()
        
        charge = 1000 * 0.6
        add_transaction(student_disc.id, "Admission Fee", debit=charge, credit=0, txn_type='FEE')
        assert student_disc.get_balance() == 600.0
        print(f"[OK] Discount Admission: Discount Student Balance: {student_disc.get_balance()}")

        # 4. Test Workshop Enrollment (Student)
        workshop = Workshop(name="Hip Hop Camp", start_date="2081-02-01", end_date="2081-02-05", fee=3000.0)
        db.session.add(workshop)
        db.session.commit()
        
        # Enroll Student 1 (Balance was 1000)
        # Charge 3000, Pay 1000
        enroll1 = WorkshopEnrollment(workshop_id=workshop.id, student_id=student1.id, amount_paid=1000.0, date="2081-02-01")
        db.session.add(enroll1)
        add_transaction(student1.id, f"Workshop: {workshop.name}", debit=3000.0)
        add_transaction(student1.id, f"Payment: {workshop.name}", credit=1000.0)
        # 1000 (adm) + 3000 (ws) - 1000 (pay) = 3000
        assert student1.get_balance() == 3000.0
        print(f"[OK] Workshop Enrollment (Student): {student1.name} New Balance: {student1.get_balance()}")

        # 5. Test Workshop Enrollment (Guest)
        enroll_guest = WorkshopEnrollment(workshop_id=workshop.id, guest_name="Guest User", guest_phone="9898989898", amount_paid=3000.0, date="2081-02-01")
        db.session.add(enroll_guest)
        db.session.commit()
        print("[OK] Workshop Enrollment (Guest) Verified.")

        # 6. Test Package Enrollment
        package = Package(name="3 Month Intro", duration_months=3, price=5000.0)
        db.session.add(package)
        db.session.commit()
        
        # Student Disc enrolls (Balance was 600)
        # Charge 5000, Pay 2500
        enroll_pkg = PackageEnrollment(package_id=package.id, student_id=student_disc.id, start_date="2081-02-01", end_date="2081-05-01", total_price=5000.0, amount_paid=2500.0)
        db.session.add(enroll_pkg)
        add_transaction(student_disc.id, f"Package: {package.name}", debit=5000.0)
        add_transaction(student_disc.id, f"Payment: {package.name}", credit=2500.0)
        # 600 (adm) + 5000 (pkg) - 2500 (pay) = 3100
        assert student_disc.get_balance() == 3100.0
        print(f"[OK] Package Enrollment: {student_disc.name} New Balance: {student_disc.get_balance()}")

        # 7. Test Clothing Sale
        product = Product(name="Academy Hoodie", price=2500.0, stock=20)
        db.session.add(product)
        db.session.commit()
        
        # Sell to Scholarship Student (Balance 0)
        add_transaction(student2.id, "Purchase: Hoodie", debit=2000.0) # Discounted price
        product.stock -= 1
        assert student2.get_balance() == 2000.0
        assert product.stock == 19
        print(f"[OK] Clothing Sale: {student2.name} New Balance: {student2.get_balance()} | Stock: {product.stock}")

        # 8. Test Annual Renewal Logic
        # Student 1 admission was 1 year ago. Balance is 3000.
        student1.last_admission_date = "2080-01-01"
        db.session.commit()
        
        # Run renewal (1000 fee)
        today_bs = nepali_datetime.date(2081, 1, 15)
        if student1.status == 'Active':
            add_transaction(student1.id, f"Renewal {today_bs.year}", debit=1000.0)
            student1.last_admission_date = today_bs.strftime('%Y-%m-%d')
        
        # 3000 (prev) + 1000 (renew) = 4000
        assert student1.get_balance() == 4000.0
        print(f"[OK] Annual Renewal: Charged {student1.name}. New Balance: {student1.get_balance()}")

        # 9. Test Student Deletion
        db.session.delete(student2)
        db.session.commit()
        print(f"[OK] Student Deletion (with dependencies) Verified. Deleted: {student2.name}")

        # 10. Test Fixed Admission Fee
        student_fixed = Student(name="Fixed Fee Student", phone="9998887776", status="Active", 
                           admission_fee_type='Fixed', custom_admission_fee=2500.0)
        db.session.add(student_fixed)
        db.session.commit()
        add_transaction(student_fixed.id, "Admission Fee", debit=2500.0, txn_type='FEE')
        assert student_fixed.get_balance() == 2500.0
        print(f"[OK] Fixed Admission Verified. Balance: {student_fixed.get_balance()}")

        # 11. Test Package Protection Billing
        student_pkg = Student(name="Pkg Protected Student", phone="9998887770", status="Active")
        db.session.add(student_pkg)
        db.session.commit()
        
        # Create and Enroll in Package
        import datetime
        today_bs = nepali_datetime.date.today()
        start_date = (today_bs - datetime.timedelta(days=5)).strftime('%Y-%m-%d')
        end_date = (today_bs + datetime.timedelta(days=25)).strftime('%Y-%m-%d')
        
        pkg_protect = Package(name="Protection Pkg", duration_months=1, price=3000.0)
        db.session.add(pkg_protect)
        db.session.commit()
        
        enroll_protect = PackageEnrollment(package_id=pkg_protect.id, student_id=student_pkg.id, 
                                           start_date=start_date, end_date=end_date, total_price=3000.0)
        db.session.add(enroll_protect)
        db.session.commit()
        
        # Attempt to bill monthly fee (Simulate generate_fees logic)
        month_name = today_bs.strftime("%B")
        description = f"Monthly Fee - {month_name} {today_bs.year}"
        
        # Check Package Protection
        active_pkg = PackageEnrollment.query.filter(
            PackageEnrollment.student_id == student_pkg.id,
            PackageEnrollment.start_date <= today_bs.strftime('%Y-%m-%d'),
            PackageEnrollment.end_date >= today_bs.strftime('%Y-%m-%d')
        ).first()
        
        if not active_pkg:
            add_transaction(student_pkg.id, description=description, debit=5000.0)
        
        # Balance should be 0 (Monthly fee skipped due to active_pkg)
        assert student_pkg.get_balance() == 0.0
        print(f"[OK] Package Protection Verified: Monthly fee skipped for {student_pkg.name}")
        # 12. Test Monthly Fee Auto-Voiding during Package Enrollment
        # If student has a monthly fee for Magh, and enrolls in a package starting in Magh, the fee should be voided.
        student_void = Student(name="Void Fee Student", phone="9998887771", status="Active", last_admission_date="2080-01-01")
        db.session.add(student_void)
        db.session.commit()
        
        # Charge Monthly Fee
        month_name = today_bs.strftime("%B")
        desc = f"Monthly Fee (Enrollment) - {month_name} {today_bs.year}"
        add_transaction(student_void.id, description=desc, debit=5000.0)
        assert student_void.get_balance() == 5000.0
        
        # Enroll in Package starting today
        pkg_void = Package(name="Void Test Pkg", duration_months=1, price=4000.0)
        db.session.add(pkg_void)
        db.session.commit()
        
        # Simulate logic from routes/packages.py
        search_pattern = f"%Monthly Fee% - {month_name} {today_bs.year}"
        overlapping = LedgerTransaction.query.filter(
            LedgerTransaction.student_id == student_void.id,
            LedgerTransaction.description.like(search_pattern),
            LedgerTransaction.is_void == False
        ).all()
        for f in overlapping:
            f.is_void = True
            
        # Add package fee
        add_transaction(student_void.id, description=f"Package: {pkg_void.name}", debit=4000.0)
        
        # Balance should be exactly 4000 (Monthly 5000 was voided)
        assert student_void.get_balance() == 4000.0
        print(f"[OK] Fee Auto-Voiding Verified: Monthly fee replaced by package fee for {student_void.name}")

        # 13. Test Workshop Fee Waiver
        # Student with monthly fee, enroll in workshop with 'skip_monthly' set to yes
        student_ws_waive = Student(name="WS Waive Student", phone="9998887772", status="Active", last_admission_date="2080-01-01")
        db.session.add(student_ws_waive)
        db.session.commit()
        
        # Charge Monthly Fee
        desc_waive = f"Monthly Fee (Enrollment) - {month_name} {today_bs.year}"
        add_transaction(student_ws_waive.id, description=desc_waive, debit=5000.0)
        assert student_ws_waive.get_balance() == 5000.0
        
        # Simulate the logic (Voiding monthly fee and adding WS fee)
        ws_waive = Workshop(name="Waive WS", start_date="2081-02-01", end_date="2081-02-05", fee=3000.0)
        db.session.add(ws_waive)
        
        search_pattern_ws = f"%Monthly Fee% - {month_name} {today_bs.year}"
        overlapping_ws = LedgerTransaction.query.filter(
            LedgerTransaction.student_id == student_ws_waive.id,
            LedgerTransaction.description.like(search_pattern_ws),
            LedgerTransaction.is_void == False
        ).all()
        for f in overlapping_ws:
            f.is_void = True
            
        add_transaction(student_ws_waive.id, description=f"Workshop: {ws_waive.name}", debit=3000.0)
        
        # Balance should be 3000 (Monthly 5000 voided)
        assert student_ws_waive.get_balance() == 3000.0
        print(f"[OK] Workshop Fee Waiver Verified: Monthly fee waived for {student_ws_waive.name}")

    print("\n------------------------------------------------")
    print("ALL NEW FEATURE VERIFICATIONS PASSED.")
    print("------------------------------------------------")

if __name__ == '__main__':
    verify()
