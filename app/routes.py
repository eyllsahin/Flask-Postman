from flask import Blueprint, request, jsonify
import hashlib
from .db import get_db_connection  
import mysql.connector
import jwt
import datetime
import os

main = Blueprint('main', __name__)

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
    
    
    hashed = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        
        cursor.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (email, hashed)
        )
        conn.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except mysql.connector.IntegrityError:
        return jsonify({'error': 'User already exists'}), 409
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@main.route('/login', methods=['POST']) #not visible in the URL because sensitive data
def login():
    data=request.get_json()
    email= data.get('email')
    password= data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    conn=get_db_connection()
    cursor=conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user is None:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        hashed_input=hashlib.sha256(password.encode()).hexdigest()

        if hashed_input != user['password']:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        payload={
            'email':email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm='HS256')
        return jsonify({'token': token}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
        

