#!/usr/bin/env python3
"""
Reset password for an existing user
"""

import os
import sys
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from app.db_utils import get_db_connection

def reset_user_password(email, new_password):
    """Reset password for an existing user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user exists
        cursor.execute("SELECT id, username, email FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ No user found with email: {email}")
            return False
            
        # Hash the new password
        hashed_password = generate_password_hash(new_password)
        
        # Update password
        cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
        conn.commit()
        
        print(f"✅ Password updated for user: {user['username']} ({email})")
        print(f"🔑 New credentials:")
        print(f"Email: {email}")
        print(f"Password: {new_password}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error resetting password: {str(e)}")
        return False

if __name__ == '__main__':
    # Reset admin password
    reset_user_password("admin@example.com", "admin123")
    
    print("\n" + "="*40)
    
    # Reset another user password
    reset_user_password("test@example.com", "test123")
