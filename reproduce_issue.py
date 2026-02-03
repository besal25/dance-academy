from app import app
from database import db, Student, Class, Enrollment

def reproduce():
    with app.app_context():
        db.create_all()
        
        # 1. Create a student
        s = Student(name="Test Student", phone="1234567890")
        db.session.add(s)
        
        # 2. Create a class
        c = Class(name="Test Class")
        db.session.add(c)
        db.session.commit()
        
        # 3. Enroll student in class
        e = Enrollment(student_id=s.id, class_id=c.id)
        db.session.add(e)
        db.session.commit()
        
        print(f"Created Class ID: {c.id}, Enrollment ID: {e.id}")
        
        # 4. Attempt to delete class
        print("Attempting to delete class...")
        # Mocking the session delete logic to match our route's logic
        if c.enrollments:
            print("Logic Check: Cannot delete class, first delete students")
            # In the app, this would redirect. Here we just assert the class still exists.
        else:
            db.session.delete(c)
            db.session.commit()
            print("Successfully deleted class")
        
        # Verify class still exists
        remaining_class = Class.query.get(c.id)
        if remaining_class:
            print(f"Class {remaining_class.id} still exists as expected.")
        else:
            print("Class was deleted (Unexpected behavior for this test case)")

if __name__ == "__main__":
    reproduce()
