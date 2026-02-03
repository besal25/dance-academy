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

    try:
        print("Migrating 'student' table...")
        cursor.execute("ALTER TABLE student ADD COLUMN photo_path VARCHAR(200)")
        print("Added photo_path column to student table.")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            print("photo_path already exists in student table.")
        else:
            print(f"Error migrating student: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
