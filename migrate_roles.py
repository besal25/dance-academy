import sqlite3
import os

db_path = 'instance/dance_academy.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if role column exists in user table
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'role' not in columns:
            print("Adding 'role' column to 'user' table...")
            cursor.execute("ALTER TABLE user ADD COLUMN role VARCHAR(20) DEFAULT 'Staff'")
            
            # Make the existing admin user an actual Admin
            cursor.execute("UPDATE user SET role = 'Admin' WHERE username = 'admin'")
            
            conn.commit()
            print("Migration successful: Added 'role' to 'user' table.")
        else:
            print("'role' column already exists in 'user' table.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()
else:
    print(f"Database not found at {db_path}")
