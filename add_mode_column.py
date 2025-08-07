#!/usr/bin/env python3
"""
Migration script to add 'mode' column to message table
"""

import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def add_mode_column():
    """Add mode column to message table"""
    try:
        # Database connection
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'message' 
            AND COLUMN_NAME = 'mode' 
            AND TABLE_SCHEMA = %s
        """, (os.getenv('DB_NAME'),))
        
        column_exists = cursor.fetchone()[0] > 0
        
        if not column_exists:
            print("Adding 'mode' column to message table...")
            
            # Add the column
            cursor.execute("""
                ALTER TABLE message 
                ADD COLUMN mode VARCHAR(20) DEFAULT 'fraude' AFTER content
            """)
            
            # Update existing records to have 'fraude' as default mode
            cursor.execute("""
                UPDATE message 
                SET mode = 'fraude' 
                WHERE mode IS NULL
            """)
            
            conn.commit()
            print("✅ Mode column added successfully!")
            print("✅ Existing messages set to 'fraude' mode")
            
        else:
            print("⚠️ Mode column already exists, skipping migration")
            
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"❌ Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    add_mode_column()
