from flask import Blueprint, request, jsonify
from .db import get_db_connection
import mysql.connector
import hashlib
import jwt
import datetime
import os
#from .utils import token_required

main = Blueprint('main', __name__)

@main.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if not email or not password or not username:
        return jsonify({'error': 'Email, username, and password required'}), 400

    hashed = hashlib.sha256(password.encode()).hexdigest()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (email, username, password) VALUES (%s, %s, %s)",
            (email, username, hashed)
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

@main.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user and user['password'] == hashlib.sha256(password.encode()).hexdigest():
            token = jwt.encode(
                {
                    'email': user['email'],
                    'username': user['username'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
                },
                os.getenv('SECRET_KEY'),
                algorithm="HS256"
            )
            if isinstance(token, bytes):
                token = token.decode('utf-8')
            return jsonify({'token': token}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@main.route('/chat', methods=['GET'])
#@token_required
def chat_route():
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
            if token.startswith('Bearer '):
                token = token.split(" ")[1]

        if not token:
            return jsonify({'error': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
            current_user = data.get('username')  
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token!'}), 401

        return chat(current_user)

def chat(current_user):
    return jsonify({'message': f'Chat opened for {current_user}'}), 200

@main.route('/')
def home():
    return jsonify({"message": "Chatbot API is running!"})


