from flask import Blueprint, request, jsonify
from .db import get_db_connection
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
from app.gemini import chat_with_gemini
from app.gemini import generate_session_title
from flask import request, jsonify
from marshmallow import Schema, fields, validate, ValidationError
from marshmallow import ValidationError

class MessageSchema(Schema):
    sender = fields.String(required=True, validate=validate.OneOf(["user", "bot"]))
    content = fields.String(required=True)
    created_at = fields.DateTime()

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
                    'email': user['email'],
                    'user_id': user['id'],  
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  
                },
                os.getenv('SECRET_KEY'),
                algorithm="HS256"
            )
            
            cursor.execute(
                "INSERT INTO session (user_id, title) VALUES (%s, %s)",
                (user['id'], 'Default Session')
            )
            conn.commit()
            
            return jsonify({
                'token': token,
                'message': 'Login successful',
                'expires_in': 3600  
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    finally:
        cursor.close()
        conn.close()

@main.route('/chat/message', methods=['POST'])
def post_message():
    schema = MessageSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify(err.messages), 400

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token is missing!'}), 401

    token = auth_header.split(" ")[1]

    try:
        decoded = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        user_id = decoded.get('user_id')
        if not user_id:
            return jsonify({'error': 'Invalid token format'}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM session WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        session = cursor.fetchone()
        if not session:
            cursor.execute(
                "INSERT INTO session (user_id, title) VALUES (%s, %s)",
                (user_id, 'Default Session')
            )
            session_id = cursor.lastrowid
        else:
            session_id = session['id']

        cursor.execute(
            "INSERT INTO message (session_id, content, sender) VALUES (%s, %s, %s)",
            (session_id, data['content'], 'user')
        )

        cursor.execute(
            "SELECT sender, content FROM message WHERE session_id = %s ORDER BY created_at ASC",
            (session_id,)
        )
        history = cursor.fetchall()
        reply = chat_with_gemini(history)

        cursor.execute(
            "INSERT INTO message (session_id, content, sender) VALUES (%s, %s, %s)",
            (session_id, reply, 'chatbot')
        )

        conn.commit()

        cursor.execute(
            "SELECT COUNT(*) as count FROM message WHERE session_id = %s AND sender = 'user'",
            (session_id,)
        )
        message_count = cursor.fetchone()['count']

        if message_count == 1:
            title = generate_session_title(data['content'])
            cursor.execute(
                "UPDATE session SET title = %s WHERE id = %s",
                (title, session_id)
            )
            conn.commit()

        cursor.execute(
            "SELECT sender, content, created_at FROM message WHERE session_id = %s ORDER BY created_at ASC",
            (session_id,)
        )
        messages = cursor.fetchall()
        result = schema.dump(messages, many=True)

        return jsonify({
            'user_message': data['content'],
            'chatbot_reply': reply,
            'session_id': session_id,
            'history': result
        }), 201

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired!'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token!'}), 401
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@main.route('/chat/message', methods=['GET'])
def get_messages():
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

    session_id_param = request.args.get('session_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if session_id_param:
            session_id = int(session_id_param)
            cursor.execute("SELECT id FROM session WHERE id = %s AND user_id = %s", (session_id, user_id))
            session = cursor.fetchone()
            if not session:
                return jsonify({'error': 'Session not found or unauthorized'}), 403
        else:
            cursor.execute("SELECT id FROM session WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
            session = cursor.fetchone()
            if not session:
                return jsonify({'messages': []}), 200
            session_id = session['id']

       
        cursor.execute(
            "SELECT id AS message_id, sender, content, created_at FROM message WHERE session_id = %s ORDER BY created_at ASC",
            (session_id,)
        )
        messages = cursor.fetchall()

        
        cursor.execute(
            "SELECT id FROM message WHERE session_id = %s ORDER BY created_at DESC LIMIT 1",
            (session_id,)
        )
        latest_msg = cursor.fetchone()
        latest_msg_id = latest_msg['id'] if latest_msg else None

        return jsonify({
            'session_id': session_id,
            'latest_message_id': latest_msg_id,
            'messages': messages
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@main.route('/chat/sessions', methods=['GET'])
def list_session():
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
    data = request.get_json()
    title = data.get('title') or "New Chat"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT id, title, created_at, is_active FROM session WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        sessions = cursor.fetchall()
        return jsonify({'sessions': sessions}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@main.route('/chat/sessions', methods=['POST'])
def create_new_session():
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

    data = request.get_json() or {}
    title = "New Chat"
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "INSERT INTO session (user_id, title) VALUES (%s, %s)",
            (user_id, title)
        )
        session_id = cursor.lastrowid
        conn.commit()
        return jsonify({
            'message': 'New session created successfully',
            'session_id': session_id,
            'title': title
        }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@main.route('/chat/sessions/<int:session_id>', methods=['DELETE']) #soft delete
def delete_session(session_id):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token is missing!'}), 401

    token = auth_header.split(" ")[1]

    try:
        decoded = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        user_id = decoded['user_id']

        if not user_id:
            return jsonify({'error': 'Invalid token format'}), 401
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM session WHERE id = %s AND user_id = %s AND is_active = TRUE", (session_id, user_id))
        session = cursor.fetchone()

        if not session:
            return jsonify({'error': 'Session not found or unauthorized'}), 403
        
        cursor.execute("UPDATE session SET is_active =FALSE WHERE id = %s AND user_id = %s", (session_id, user_id))
        conn.commit()
        return jsonify({'message': 'Session marked inactive'}), 200
    
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
