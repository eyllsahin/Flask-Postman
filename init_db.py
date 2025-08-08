
"""
Database initialization script for the Flask Chatbot application.
This script creates all the necessary tables in the database.
"""

import os
import sys
import hashlib
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.db_utils import get_db_connection

def init_database():
    """Initialize the database with all tables"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        print("Creating database tables...")
        
       
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(150) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            password VARCHAR(200) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(users_table)
        print("✓ Users table created")
        
        
        session_table = """
        CREATE TABLE IF NOT EXISTS session (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            title VARCHAR(255) DEFAULT 'New Chat',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
        cursor.execute(session_table)
        print("✓ Session table created")
        
      
        message_table = """
        CREATE TABLE IF NOT EXISTS message (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT NOT NULL,
            content TEXT NOT NULL,
            sender VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            mode VARCHAR(50) DEFAULT 'fraude',
            FOREIGN KEY (session_id) REFERENCES session(id) ON DELETE CASCADE
        )
        """
        cursor.execute(message_table)
        print("✓ Message table created")
        
        connection.commit()
        print("\nDatabase tables created successfully!")
        
        
        cursor.execute("SELECT id FROM users WHERE email = %s", ('admin@example.com',))
        admin_exists = cursor.fetchone()
        
        if not admin_exists:
            
            password = 'admin123'
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute(
                "INSERT INTO users (username, email, password, is_admin) VALUES (%s, %s, %s, %s)",
                ('admin', 'admin@example.com', password_hash, True)
            )
            connection.commit()
            print("✓ Default admin user created (admin@example.com / admin123)")
        else:
            print("✓ Admin user already exists")
        
        print("\nVerifying tables...")
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✓ Tables created: {tables}")
        
        return True
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == '__main__':
    try:
        success = init_database()
        if success:
            print("\n✅ Database initialization completed successfully!")
        else:
            print("\n❌ Database initialization failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error initializing database: {str(e)}")
        sys.exit(1)
