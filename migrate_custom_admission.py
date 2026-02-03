import sqlite3
import os

def migrate():
    db_path = 'instance/dance_academy.db'
    if not os.path.exists(db_path):
        if os.path.exists('dance_academy.db'):
            db_path = 'dance_academy.db'
        else:
            print("Database not found.")
            return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Connecting to {db_path}...")
    print("Adding custom_admission_fee column to student table...")
    try:
        cursor.execute("ALTER TABLE student ADD COLUMN custom_admission_fee FLOAT DEFAULT 0.0")
        conn.commit()
        print("Success!")
    except Exception as e:
        print(f"Error or already exists: {e}")
        
    conn.close()

if __name__ == '__main__':
    migrate()
