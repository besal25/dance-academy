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

    # Update Student table
    try:
        print("Updating 'student' table...")
        cursor.execute("ALTER TABLE student ADD COLUMN last_admission_date TEXT")
        cursor.execute("ALTER TABLE student ADD COLUMN admission_fee_type TEXT DEFAULT 'Normal'")
        cursor.execute("ALTER TABLE student ADD COLUMN admission_discount_percent REAL DEFAULT 0.0")
        print("Updated 'student' table.")
    except sqlite3.OperationalError as e:
        print(f"Note: student table update may have already run or failed: {e}")

    # Create Workshop related tables
    try:
        print("Creating 'workshop' and 'workshop_enrollment' tables...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workshop (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                fee REAL NOT NULL,
                description TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workshop_enrollment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workshop_id INTEGER NOT NULL,
                student_id INTEGER,
                guest_name TEXT,
                guest_phone TEXT,
                amount_paid REAL DEFAULT 0.0,
                date TEXT NOT NULL,
                FOREIGN KEY (workshop_id) REFERENCES workshop (id),
                FOREIGN KEY (student_id) REFERENCES student (id)
            )
        """)
        print("Created Workshop tables.")
    except sqlite3.OperationalError as e:
        print(f"Error creating workshop tables: {e}")

    # Create Package related tables
    try:
        print("Creating 'package' and 'package_enrollment' tables...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS package (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                duration_months INTEGER NOT NULL,
                price REAL NOT NULL,
                description TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS package_enrollment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                package_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                total_price REAL NOT NULL,
                amount_paid REAL DEFAULT 0.0,
                payment_deadline TEXT,
                FOREIGN KEY (package_id) REFERENCES package (id),
                FOREIGN KEY (student_id) REFERENCES student (id)
            )
        """)
        print("Created Package tables.")
    except sqlite3.OperationalError as e:
        print(f"Error creating package tables: {e}")

    # Create Product related tables
    try:
        print("Creating 'product' and 'product_sale' tables...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_sale (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                price_sold REAL NOT NULL,
                FOREIGN KEY (product_id) REFERENCES product (id),
                FOREIGN KEY (student_id) REFERENCES student (id)
            )
        """)
        print("Created Product tables.")
    except sqlite3.OperationalError as e:
        print(f"Error creating product tables: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
