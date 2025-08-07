#!/usr/bin/env python3
"""
Database initialization script for the Flask Chatbot application.
This script creates all the necessary tables in the database.
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from app import create_app, db
from app.models import User, Session, Message

def init_database():
    """Initialize the database with all tables"""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        
        # Drop all tables (if they exist) and recreate them
        # Comment out the next line if you want to keep existing data
        # db.drop_all()
        
        # Create all tables
        db.create_all()
        
        print("Database tables created successfully!")
        
        # Create a default admin user if it doesn't exist
        admin_user = User.query.filter_by(email='admin@example.com').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin_user.set_password('admin123')  # Change this password!
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created (admin@example.com / admin123)")
        else:
            print("Admin user already exists")
        
        # Verify tables were created
        print("\nVerifying tables...")
        from sqlalchemy import text
        result = db.session.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result.fetchall()]
        print(f"Tables created: {tables}")
        
        return True

if __name__ == '__main__':
    try:
        init_database()
        print("\n✅ Database initialization completed successfully!")
    except Exception as e:
        print(f"\n❌ Error initializing database: {str(e)}")
        sys.exit(1)
