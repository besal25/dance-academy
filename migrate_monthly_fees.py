import sqlite3
import os

db_path = 'instance/dance_academy.db'

print(f"Using database at: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Add default_monthly_fee to settings
    cursor.execute("ALTER TABLE settings ADD COLUMN default_monthly_fee FLOAT DEFAULT 5000.0")
    print("Added default_monthly_fee to settings table.")
except sqlite3.OperationalError as e:
    print(f"settings table: {e}")

try:
    # Add base_monthly_fee to student
    cursor.execute("ALTER TABLE student ADD COLUMN base_monthly_fee FLOAT DEFAULT 5000.0")
    print("Added base_monthly_fee to student table.")
except sqlite3.OperationalError as e:
    print(f"student table: {e}")

conn.commit()
conn.close()
print("Migration completed.")
