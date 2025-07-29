import mysql
from app.db import get_db_connection
from flask import Blueprint, request, jsonify
import hashlib  # string Hashing is not encryption — you can't decrypt a hash
# `request`: This lets you **access data that was sent** to your backend (like JSON in a POST request).
# - `jsonify`: This converts your Python dictionary to **JSON format**, so your backend can reply with proper API responses.

main = Blueprint('main', __name__)  # Define a Blueprint to organize your routeslask import Blueprint,request ,jsonify
import hashlib #string Hashing is not encryption — you can’t decrypt a hash
#`request`: This lets you **access data that was sent** to your backend (like JSON in a POST request).
#- `jsonify`: This converts your Python dictionary to **JSON format**, so your backend can reply with proper API responses.

main=Blueprint('main',__name__)# Define a Blueprint to organize your routes



@main.route('/')
def home():
    return jsonify({"message": "Chatbot API is running!"})

@main.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    # 🔐 Hash the password
    hashed = hashlib.sha256(password.encode()).hexdigest()

    # 🧠 Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 📥 Insert user into database
        cursor.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (email, hashed)  # Don't forget to complete this line
        )
        conn.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    except mysql.connector.IntegrityError:
        return jsonify({'error': 'User already exists'}), 409
    finally:
        cursor.close()
        conn.close()