from app import app, db
from sqlalchemy import text

def migrate_instructor_details():
    with app.app_context():
        # Check if columns exist
        inspector = db.inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('instructor')]
        
        with db.engine.connect() as conn:
            if 'photo_path' not in columns:
                print("Adding 'photo_path' column to 'instructor' table...")
                conn.execute(text("ALTER TABLE instructor ADD COLUMN photo_path VARCHAR(200)"))
            else:
                print("'photo_path' column already exists.")

            if 'citizenship_no' not in columns:
                print("Adding 'citizenship_no' column to 'instructor' table...")
                conn.execute(text("ALTER TABLE instructor ADD COLUMN citizenship_no VARCHAR(50)"))
            else:
                print("'citizenship_no' column already exists.")
                
            if 'document_path' not in columns:
                print("Adding 'document_path' column to 'instructor' table...")
                conn.execute(text("ALTER TABLE instructor ADD COLUMN document_path VARCHAR(200)"))
            else:
                print("'document_path' column already exists.")
                
            conn.commit()
            print("Migration completed successfully.")

if __name__ == '__main__':
    migrate_instructor_details()
