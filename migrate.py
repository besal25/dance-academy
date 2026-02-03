import sqlite3
import os

def migrate():
    db_path = 'instance/dance_academy.db'
    if not os.path.exists(db_path):
        # Check root too
        if os.path.exists('dance_academy.db'):
            db_path = 'dance_academy.db'
        else:
            print("Database not found in instance/ or root.")
            return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Add instructor_id to expense
        print("Migrating 'expense' table...")
        cursor.execute("ALTER TABLE expense ADD COLUMN instructor_id INTEGER REFERENCES instructor(id)")
        print("Added instructor_id column to expense table.")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            print("instructor_id already exists in expense table.")
        else:
            print(f"Error migrating expense: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
