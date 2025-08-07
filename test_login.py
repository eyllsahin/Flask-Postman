#!/usr/bin/env python3
"""
Test login functionality directly
"""

import os
import sys
from dotenv import load_dotenv
from werkzeug.security import check_password_hash

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from app.db_utils import get_db_connection

def test_login(email, password):
    """Test login functionality"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        print(f"🔍 Testing login for: {email}")
        
        # Get user from database
        cursor.execute("SELECT id, email, password, is_admin, username FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ No user found with email: {email}")
            return False
            
        print(f"✅ User found: {user['username']} (ID: {user['id']})")
        print(f"🔐 Password hash starts with: {user['password'][:20]}...")
        
        # Test password
        password_match = check_password_hash(user['password'], password)
        
        if password_match:
            print(f"✅ Password matches!")
            print(f"👤 User details:")
            print(f"   - Username: {user['username']}")
            print(f"   - Email: {user['email']}")
            print(f"   - Admin: {user['is_admin']}")
            return True
        else:
            print(f"❌ Password does not match")
            return False
        
    except Exception as e:
        print(f"❌ Error testing login: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    # Test with our known credentials
    test_login("testlogin@example.com", "password123")
    
    print("\n" + "="*50)
    
    # Test with admin user (you can try with a known password)
    print("\nTesting admin user...")
    test_login("admin@example.com", "admin123")  # This might fail if password is different
