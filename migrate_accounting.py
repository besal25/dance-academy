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
        print("Migrating 'ledger_transaction' table...")
        cursor.execute("ALTER TABLE ledger_transaction ADD COLUMN txn_type VARCHAR(20) DEFAULT 'FEE'")
        cursor.execute("ALTER TABLE ledger_transaction ADD COLUMN is_void BOOLEAN DEFAULT 0")
        print("Added txn_type and is_void columns to ledger_transaction.")
    except sqlite3.OperationalError as e:
        print(f"Notice (ledger_transaction): {e}")

    try:
        print("Migrating 'expense' table...")
        cursor.execute("ALTER TABLE expense ADD COLUMN is_void BOOLEAN DEFAULT 0")
        print("Added is_void column to expense table.")
    except sqlite3.OperationalError as e:
        print(f"Notice (expense): {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
