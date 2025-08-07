#!/usr/bin/env python3
"""
Check all users with detailed info
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from app.db_utils import get_db_connection

def check_all_users():
    """Check all users with detailed info"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check all users
        cursor.execute("SELECT * FROM users ORDER BY created_at")
        users = cursor.fetchall()
        print(f"Total users: {len(users)}\n")
        
        for user in users:
            print(f"ID: {user['id']}")
            print(f"Username: {user['username']}")
            print(f"Email: {user['email']}")
            print(f"Admin: {bool(user['is_admin'])}")
            print(f"Created: {user['created_at']}")
            print("-" * 40)
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking users: {str(e)}")
        return False

if __name__ == '__main__':
    check_all_users()
