import sqlite3
import os

db_path = 'instance/dance_academy.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        new_cols = [
            ('can_manage_students', "INTEGER DEFAULT 1"),
            ('can_manage_classes', "INTEGER DEFAULT 1"),
            ('can_view_attendance', "INTEGER DEFAULT 1"),
            ('can_view_finance', "INTEGER DEFAULT 0"),
            ('can_manage_expenses', "INTEGER DEFAULT 0"),
            ('can_view_reports', "INTEGER DEFAULT 0"),
            ('can_manage_settings', "INTEGER DEFAULT 0"),
            ('can_manage_workshops', "INTEGER DEFAULT 0"),
            ('can_manage_packages', "INTEGER DEFAULT 0"),
            ('can_manage_inventory', "INTEGER DEFAULT 0")
        ]
        
        for col_name, col_type in new_cols:
            if col_name not in columns:
                print(f"Adding '{col_name}' column...")
                cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")
        
        # Ensure 'admin' user has all permissions
        cursor.execute("""
            UPDATE user SET 
                can_manage_students = 1,
                can_manage_classes = 1,
                can_view_attendance = 1,
                can_view_finance = 1,
                can_manage_expenses = 1,
                can_view_reports = 1,
                can_manage_settings = 1,
                can_manage_workshops = 1,
                can_manage_packages = 1,
                can_manage_inventory = 1
            WHERE role = 'Admin' OR username = 'admin'
        """)
        
        conn.commit()
        print("Migration for granular permissions successful.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()
else:
    print(f"Database not found at {db_path}")
