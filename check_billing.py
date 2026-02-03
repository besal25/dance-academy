import nepali_datetime
from database import db, Student, LedgerTransaction
from app import app

with app.app_context():
    today = nepali_datetime.date.today()
    month_name = today.strftime("%B")
    print(f"DEBUG: Today is {today}")
    print(f"DEBUG: month_name (%B) is '{month_name}'")
    
    student = Student.query.get(1)
    if student:
        print(f"DEBUG: Student 1 Fee: {student.custom_monthly_fee}")
        txns = LedgerTransaction.query.filter_by(student_id=1).all()
        print(f"DEBUG: Student 1 Transactions: {len(txns)}")
        for t in txns:
            print(f"  - [{t.id}] {t.description} | D: {t.debit} | C: {t.credit} | Type: {t.txn_type} | Void: {t.is_void}")
    else:
        print("DEBUG: Student 1 not found")
