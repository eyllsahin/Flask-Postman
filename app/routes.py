from flask import Blueprint, request, jsonify
from .db import get_db_connection
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
#from .utils import token_required

main = Blueprint('main', __name__)

@main.route('/register', methods=['POST'])
def register():
    print("Registration attempt")
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if not email or not password or not username:
        return jsonify({'error': 'Email, username, and password required'}), 400

    hashed = generate_password_hash(password)
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
        if user and check_password_hash(user['password'], password):
            token = jwt.encode(
                {
                    'user_id': user['id'],
                    'email': user['email'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
                },
                os.getenv('SECRET_KEY'),
                algorithm="HS256"
            )
            # Create a session for the user
            cursor.execute(
                "INSERT INTO session (user_id, title) VALUES (%s, %s)",
                (user['id'], 'Default Session')
            )
            conn.commit()
            
            return jsonify({
                'token': token,
                'message': 'Login successful',
                'expires_in': 1800
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    finally:
        cursor.close()
        conn.close()

@main.route('/chat', methods=['GET'])
def chat():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token is missing!'}), 401
    
    token = auth_header.split(" ")[1]
    try:
        data = jwt.decode(
            token, 
            os.getenv('SECRET_KEY'), 
            algorithms=["HS256"]
        )
        current_user = data.get('email')
        return jsonify({'message': f'Chat opened for {current_user}'}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired!'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token!'}), 401

@main.route('/chat/message', methods=['POST'])
def post_message():
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token is missing!'}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        user_id = decoded['user_id']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401


    data = request.get_json()
    content = data.get('content')
    if not content:
        return jsonify({'error': 'Content is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        
        cursor.execute("SELECT id FROM session WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        session = cursor.fetchone()

        if not session:
            
            cursor.execute("INSERT INTO session (user_id, title) VALUES (%s, %s)", (user_id, 'Default Session'))
            session_id = cursor.lastrowid
        else:
            session_id = session['id']

        
        cursor.execute(
            "INSERT INTO message (session_id, content, sender) VALUES (%s, %s, %s)",
            (session_id, content, 'user')
        )

        
        bot_reply = "This is a mock reply from the bot."
        cursor.execute(
            "INSERT INTO message (session_id, content, sender) VALUES (%s, %s, %s)",
            (session_id, bot_reply, 'bot')
        )

        conn.commit()
        return jsonify({'message': 'Message and reply stored'}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@main.route('/chat/message', methods=['GET'])
def get_message():
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token is missing!'}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        user_id = decoded['user_id']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        
        cursor.execute("SELECT id FROM session WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        session = cursor.fetchone()
        if not session:
            return jsonify({'messages': []}), 200  

        session_id = session['id']
        cursor.execute(
            "SELECT sender, content, created_at FROM message WHERE session_id = %s ORDER BY created_at ASC",
            (session_id,)
        )
        messages = cursor.fetchall()
        return jsonify({'messages': messages}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@main.route('/chat/sessions', methods=['POST'])
def create_new_session():
    auth_header=request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token is missing!'}), 401
    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        user_id = decoded['user_id']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401     
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    data=request.get_json()
    title=data.get('title') or "New Chat"
    
    conn= get_db_connection()
    cursor=conn.cursor()    

    try:
        cursor.execute(
            "INSERT INTO session (user_id, title) VALUES (%s, %s)",
            (user_id, title)
        )
        conn.commit()
        return jsonify({'message': 'New session created successfully'}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()