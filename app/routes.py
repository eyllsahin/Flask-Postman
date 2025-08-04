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

main = Blueprint('main', __name__)

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)

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
        cursor.execute("SELECT id, email, password, is_admin FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            token = jwt.encode(
                {
                    'email': user['email'],
                    'user_id': user['id'],
                    'is_admin': user['is_admin'],  # Include admin flag
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
                },
                os.getenv('SECRET_KEY'),
                algorithm="HS256"
            )

            if not user['is_admin']:
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

        return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@main.route('/admin/sessions', methods=['GET'])
def get_admin_sessions():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token is missing!'}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        is_admin = decoded.get('is_admin')  
        if not is_admin:
            return jsonify({'error': 'Admin privileges required'}), 403

        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        offset = (page - 1) * limit

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS total FROM session")
        total_sessions = cursor.fetchone()['total']

    
        total_pages = (total_sessions + limit - 1) // limit  

        if page > total_pages:
            return jsonify({
                'error': 'Page does not exist',
                'page': page,
                'total_pages': total_pages
            }), 404

    
        cursor.execute(
            "SELECT * FROM session ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (limit, offset)
        )
        sessions = cursor.fetchall()

        return jsonify({
            'page': page,
            'limit': limit,
            'total_sessions': total_sessions,
            'total_pages': total_pages,
            'sessions': sessions
        }), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired!'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token!'}), 401
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


class RegisterSchema(Schema):
    email = fields.Email(required=True)
    username = fields.String(
        required=True,
        validate=[
            validate.Length(min=3, max=30),
            validate.Regexp(r'^[a-zA-Z0-9_]+$', error="Only letters, numbers and underscores allowed")
        ]
    )
    password = fields.String(required=True, validate=validate.Length(min=4))
    confirm_password = fields.String(required=True)
    created_at = fields.DateTime(dump_only=True)

@main.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not email or not password or not username or not confirm_password:
        return jsonify({'error': 'All fields are required'}), 400

   
    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (email, username, password, is_admin) VALUES (%s, %s, %s, %s)",
            (email, username, hashed_password, 0) 
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


class MessageSchema(Schema):
    id = fields.Integer(dump_only=True)
    sender = fields.String(dump_only=True)
    content = fields.String(required=True)
    created_at = fields.DateTime(dump_only=True)
    title= fields.String(dump_only=True)
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
            "SELECT id, sender, content, created_at FROM message WHERE session_id = %s ORDER BY created_at ASC",
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
    schema = MessageSchema()

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
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)
    offset = (page - 1) * limit

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

      
        cursor.execute("SELECT COUNT(*) as total FROM message WHERE session_id = %s", (session_id,))
        total_messages = cursor.fetchone()['total']

        cursor.execute(
            "SELECT id, sender, content, created_at FROM message WHERE session_id = %s ORDER BY created_at ASC LIMIT %s OFFSET %s",
            (session_id, limit, offset)
        )
        messages = cursor.fetchall()
        result = schema.dump(messages, many=True)

        return jsonify({
            'session_id': session_id,
            'page': page,
            'limit': limit,
            'total_messages': total_messages,
            'messages': result
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@main.route('/chat/sessions', methods=['GET'])
@main.route('/chat/sessions', methods=['GET'])
def list_sessions():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token is missing!'}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        user_id = decoded['user_id']
        is_admin = decoded.get('is_admin', False)
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if is_admin:
            # Admin: see everything, including usernames
            cursor.execute("""
                SELECT session.id, session.title, session.created_at, session.is_active, users.username
                FROM session
                JOIN users ON session.user_id = users.id
                ORDER BY session.created_at DESC
            """)
        else:
            # Regular user: only their own active sessions
            cursor.execute("""
                SELECT session.id, session.title, session.created_at, session.is_active
                FROM session
                WHERE session.user_id = %s AND session.is_active = 1
                ORDER BY session.created_at DESC
            """, (user_id,))
        
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

import datetime

@main.route('/chat/session', methods=['POST'])
def create_session():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token is missing!'}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        user_id = decoded.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)


        cursor.execute(
            "INSERT INTO session (user_id, title, created_at) VALUES (%s, %s, %s)",
            (user_id, 'New Session', datetime.datetime.utcnow())
        )
        session_id = cursor.lastrowid
        conn.commit()

        return jsonify({'message': 'Session created successfully', 'session_id': session_id}), 201

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired!'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token!'}), 401
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
