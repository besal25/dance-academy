from app import app
from database import db
from routes.auth import create_admin_user
import os

def init_db():
    print("Initializing Database...")
    with app.app_context():
        # Create tables
        db.create_all()
        print("Tables created.")
        
        # Ensure Admin User
        create_admin_user()
        print("Admin user ensured.")
        
    print("Database initialization complete!")

if __name__ == '__main__':
    init_db()
