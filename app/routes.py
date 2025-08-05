from flask import Blueprint, request, jsonify, render_template, redirect
from .db import get_db_connection
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
import logging
from app.gemini import chat_with_gemini
from app.gemini import generate_session_title
from flask import request, jsonify
from marshmallow import Schema, fields, validate, ValidationError
from marshmallow import ValidationError

# Configure logging - reduced verbosity
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)

@main.route('/')
def home():
    return redirect('/login')

@main.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

@main.route('/chat', methods=['GET'])
def chat_page():
    return render_template('chat.html')

@main.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@main.route('/login', methods=['POST'])
def login():
    is_json = request.is_json
    data = request.get_json() if is_json else request.form

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        if is_json:
            return jsonify({'error': 'Email and password required'}), 400
        else:
            return render_template('login.html', error="Please enter both email and password"), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id, email, password, is_admin FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            payload = {
                'email': user['email'],
                'user_id': user['id'],
                'is_admin': user['is_admin'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }
            
            token = jwt.encode(
                payload,
                os.getenv('SECRET_KEY'),
                algorithm="HS256"
            )
            
            # Use string token for consistent handling
            if isinstance(token, bytes):
                token = token.decode('utf-8')
           
            redirect_url = '/admin' if user['is_admin'] else '/chat'

            if is_json:
                response = jsonify({
                    'token': token,
                    'is_admin': user['is_admin'],
                    'message': 'Login successful',
                    'redirect': redirect_url,
                    'user_id': user['id']
                })
            else:
                response = redirect(redirect_url)

            # Set both cookie and localStorage token
            response.set_cookie(
                'token', token,
                httponly=False,  
                secure=False,  
                samesite='Strict',
                max_age=3600
            )
            
            return response

        else:
            if is_json:
                return jsonify({'error': 'Invalid email or password'}), 401
            else:
                return render_template('login.html', error="Invalid email or password"), 401

    except Exception as e:
        print(f"Login error: {str(e)}")
        if is_json:
            return jsonify({'error': str(e)}), 500
        else:
            return render_template('login.html', error="Server error. Please try again."), 500

    finally:
        cursor.close()
        conn.close()


@main.route('/admin', methods=['GET'])
def admin_dashboard():
   
    token = request.cookies.get('token')
    
    if not token:
        return redirect('/login')
    
    try:
      
        decoded = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        if not decoded.get('is_admin'):
            return redirect('/login')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) as total_users FROM users WHERE is_admin = 0")
        total_users = cursor.fetchone()['total_users']

        cursor.execute("SELECT COUNT(*) as active_sessions FROM session WHERE is_active = TRUE AND user_id IN (SELECT id FROM users)")
        active_sessions = cursor.fetchone()['active_sessions']

        cursor.execute("SELECT COUNT(*) as total_messages FROM message")
        total_messages = cursor.fetchone()['total_messages']

        stats = {
            'total_users': total_users,
            'active_sessions': active_sessions,
            'total_messages': total_messages
        }

        # Clean up orphaned sessions first
        cursor.execute("DELETE FROM session WHERE user_id NOT IN (SELECT id FROM users)")
        conn.commit()
        
        # Get users with their sessions - only show users who actually exist
        cursor.execute("""
            SELECT 
                u.id,
                u.username,
                u.email,
                DATE_FORMAT(u.created_at, '%Y-%m-%d') as created_at
            FROM users u
            WHERE u.is_admin = 0
            ORDER BY u.created_at DESC
        """)
        
        user_results = cursor.fetchall()
        
        users = {}
        for user_row in user_results:
            users[user_row['id']] = {
                'id': user_row['id'],
                'username': user_row['username'],
                'email': user_row['email'],
                'created_at': user_row['created_at'], 
                'sessions': []
            }
        
        # Now get sessions for each user
        if users:
            user_ids = list(users.keys())
            format_strings = ','.join(['%s'] * len(user_ids))
            cursor.execute(f"""
                SELECT 
                    s.user_id,
                    s.id as session_id,
                    COALESCE(s.title, 'Untitled') as title,
                    DATE_FORMAT(s.created_at, '%Y-%m-%d') as session_created,
                    s.is_active,
                    COUNT(m.id) as message_count
                FROM session s
                LEFT JOIN message m ON s.id = m.session_id
                WHERE s.user_id IN ({format_strings})
                GROUP BY s.id, s.user_id
                ORDER BY s.created_at DESC
            """, user_ids)
            
            session_results = cursor.fetchall()
            
            for session_row in session_results:
                user_id = session_row['user_id']
                if user_id in users:
                    # Clean and validate session title
                    session_title = session_row['title'] or 'Untitled Session'
                    # Remove any problematic characters and truncate if too long
                    session_title = ''.join(char for char in session_title if ord(char) < 127)  # Remove non-ASCII
                    session_title = session_title.strip()
                    if len(session_title) > 100:
                        session_title = session_title[:97] + '...'
                    
                    users[user_id]['sessions'].append({
                        'id': session_row['session_id'],
                        'title': session_title,
                        'created_at': session_row['session_created'],
                        'is_active': bool(session_row['is_active']),
                        'message_count': session_row['message_count'] or 0
                    })

        cursor.close()
        conn.close()

        return render_template('admin_overview.html', 
                            users=users.values(),
                            stats=stats)
    except Exception as e:
        print("Admin dashboard error:", e)
        return redirect('/login')

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

        total_pages = max(1, (total_sessions + limit - 1) // limit)

        if page > total_pages and total_sessions > 0:
            return jsonify({
                'error': 'Page does not exist',
                'page': page,
                'total_pages': total_pages
            }), 404

        cursor.execute("""
            SELECT 
                session.id,
                session.user_id,
                session.title,
                DATE_FORMAT(session.created_at, '%Y-%m-%d') as created_at,
                session.is_active,
                users.username
            FROM session 
            JOIN users ON session.user_id = users.id
            ORDER BY session.created_at DESC 
            LIMIT %s OFFSET %s
        """, (limit, offset))
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
    created_at = fields.String(dump_only=True)

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
    created_at = fields.String(dump_only=True)
    title = fields.String(dump_only=True)
    session_id = fields.Integer(load_only=True)
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

        session_id = None
        if 'session_id' in data:
          
            cursor.execute("SELECT id FROM session WHERE id = %s AND user_id = %s", 
                         (data['session_id'], user_id))
            session = cursor.fetchone()
            if session:
                session_id = session['id']
        
        if not session_id:
          
            cursor.execute("SELECT id FROM session WHERE user_id = %s AND is_active = TRUE ORDER BY id DESC LIMIT 1", (user_id,))
            session = cursor.fetchone()
            
            if not session:
                
                cursor.execute("SELECT id FROM session WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
                session = cursor.fetchone()
            
            if not session:
                cursor.execute(
                    "INSERT INTO session (user_id, title, is_active) VALUES (%s, %s, TRUE)",
                    (user_id, 'Default Session')
                )
                session_id = cursor.lastrowid
            else:
                session_id = session['id']

        current_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        
        cursor.execute(
            "INSERT INTO message (session_id, content, sender, created_at) VALUES (%s, %s, %s, %s)",
            (session_id, data['content'], 'user', current_date)
        )
        conn.commit()  

        cursor.execute(
            "SELECT sender, content FROM message WHERE session_id = %s ORDER BY created_at ASC",
            (session_id,)
        )
        history = cursor.fetchall()
        
        # Convert history to the format expected by Gemini
        conversation_history = [{"sender": msg["sender"], "content": msg["content"]} for msg in history]
        
        try:
            reply = chat_with_gemini(conversation_history)
            print(f"✅ Gemini response received for session {session_id}")
        except Exception as e:
            print(f"🚨 ERROR calling Gemini API: {str(e)}")
            # More specific error messages based on the error type
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                reply = "The ancient spirits are overwhelmed by too many voices at once. Please wait a moment before speaking again... *The digital serpent retreats to recharge its mystical energies*"
            elif "timeout" in error_str:
                reply = "The mystical channels echo with silence. The serpent's thoughts are slow to form... Try again, patient seeker."
            else:
                reply = "The digital mists cloud my vision momentarily. Please, speak again..."

        cursor.execute(
            "INSERT INTO message (session_id, content, sender, created_at) VALUES (%s, %s, %s, %s)",
            (session_id, reply, 'chatbot', current_date)
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
            "SELECT title, is_active FROM session WHERE id = %s",
            (session_id,)
        )
        session_info = cursor.fetchone()
    
        return jsonify({
            'message': 'Message posted successfully',
            'user_message': data['content'],
            'chatbot_reply': reply,
            'session_id': session_id,
            'session_title': session_info['title'],
            'is_active': bool(session_info['is_active']),
            'status': 'success'
        }), 201

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired!'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token!'}), 401
    except Exception as e:
        logger.error(f"Error in post_message: {str(e)}")
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
        logger.debug(f"get_messages: user_id={user_id}, session_id_param={session_id_param}, page={page}, limit={limit}")
        
        if session_id_param:
            session_id = int(session_id_param)
           
            cursor.execute("SELECT id, is_active FROM session WHERE id = %s AND user_id = %s", (session_id, user_id))
            session = cursor.fetchone()
            if not session:
                logger.error(f"Session not found or unauthorized: session_id={session_id}, user_id={user_id}")
                return jsonify({'error': 'Session not found or unauthorized'}), 403
            logger.debug(f"Found session: id={session['id']}, is_active={session['is_active']}")
        else:
            
            cursor.execute("SELECT id, is_active FROM session WHERE user_id = %s AND is_active = TRUE ORDER BY created_at DESC LIMIT 1", (user_id,))
            session = cursor.fetchone()
            if not session:
                
                logger.debug("No active sessions found for user, looking for any session")
                cursor.execute("SELECT id, is_active FROM session WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", (user_id,))
                session = cursor.fetchone()
                if not session:
                    logger.debug(f"No sessions found for user_id={user_id}")
                    return jsonify({'messages': []}), 200
            session_id = session['id']
            logger.debug(f"Using session_id={session_id}, is_active={session['is_active']}")

      
        cursor.execute("SELECT COUNT(*) as total FROM message WHERE session_id = %s", (session_id,))
        total_messages = cursor.fetchone()['total']

        cursor.execute("""
            SELECT 
                id, 
                sender, 
                content, 
                DATE_FORMAT(created_at, '%Y-%m-%d') as created_at 
            FROM message 
            WHERE session_id = %s 
            ORDER BY created_at ASC 
            LIMIT %s OFFSET %s
        """, (session_id, limit, offset))
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

@main.route('/admin/users', methods=['GET'])
def admin_users():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token is missing!'}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        if not decoded.get('is_admin'):
            return jsonify({'error': 'Admin privileges required'}), 403

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                id, 
                username, 
                email, 
                DATE_FORMAT(created_at, '%Y-%m-%d') as created_at
            FROM users
            WHERE is_admin = FALSE
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()

        return jsonify({'users': users}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@main.route('/admin/user/<int:user_id>/view', methods=['GET'])
def admin_view_user(user_id):
    token = request.cookies.get('token')
    if not token:
        return redirect('/login')
    
    try:
        decoded = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        if not decoded.get('is_admin'):
            return redirect('/login')
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                id, username, email, 
                DATE_FORMAT(created_at, '%Y-%m-%d') as created_at
            FROM users
            WHERE id = %s AND is_admin = FALSE
        """, (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return redirect('/admin')
            
        cursor.execute("""
            SELECT 
                id, title, 
                DATE_FORMAT(created_at, '%Y-%m-%d') as created_at,
                is_active,
                (SELECT COUNT(*) FROM message WHERE message.session_id = session.id) as message_count
            FROM session
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        sessions_raw = cursor.fetchall()
        
        # Clean session titles
        sessions = []
        for session in sessions_raw:
            session_title = session['title'] or 'Untitled Session'
            # Remove any problematic characters and truncate if too long
            session_title = ''.join(char for char in session_title if ord(char) < 127)  # Remove non-ASCII
            session_title = session_title.strip()
            if len(session_title) > 100:
                session_title = session_title[:97] + '...'
            
            session_clean = dict(session)
            session_clean['title'] = session_title
            sessions.append(session_clean)
        
        cursor.execute("""
            SELECT
                COUNT(*) as total_messages,
                SUM(CASE WHEN sender = 'user' THEN 1 ELSE 0 END) as user_messages,
                SUM(CASE WHEN sender = 'chatbot' THEN 1 ELSE 0 END) as bot_messages,
                MIN(DATE_FORMAT(created_at, '%Y-%m-%d')) as first_message,
                MAX(DATE_FORMAT(created_at, '%Y-%m-%d')) as last_message
            FROM message
            JOIN session ON message.session_id = session.id
            WHERE session.user_id = %s
        """, (user_id,))
        message_stats = cursor.fetchone()
        
        return render_template('admin_user_detail.html', 
                             user=user,
                             sessions=sessions,
                             message_stats=message_stats)
                             
    except Exception as e:
        logger.error(f"Error in admin_view_user: {str(e)}")
        return redirect('/admin')
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@main.route('/admin/user/<int:user_id>/chats', methods=['GET'])
def admin_user_chats(user_id):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token is missing!'}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        if not decoded.get('is_admin'):
            return jsonify({'error': 'Admin privileges required'}), 403

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                message.id,
                message.session_id,
                message.content,
                message.sender,
                DATE_FORMAT(message.created_at, '%Y-%m-%d') as created_at,
                session.title as session_title
            FROM message
            JOIN session ON message.session_id = session.id
            WHERE session.user_id = %s
            ORDER BY message.created_at DESC
        """, (user_id,))
        chats = cursor.fetchall()

        return jsonify({'chats': chats}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


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
    except Exception as e:
        return jsonify({'error': 'Token error'}), 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
      
        cursor.execute("""
            SELECT 
                id, 
                title, 
                DATE_FORMAT(created_at, '%Y-%m-%d') as created_at, 
                is_active
            FROM session
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY created_at DESC
        """, (user_id,))
        
        sessions = cursor.fetchall()
        return jsonify({'sessions': sessions}), 200

    except Exception as e:
        print("Error in list_sessions:", e)
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        conn.close()



@main.route('/chat/sessions', methods=['POST'])
def create_new_session():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.warning("Token missing in create_new_session request")
        return jsonify({'error': 'Token is missing!'}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        user_id = decoded['user_id']
        logger.debug(f"Creating new session for user_id={user_id}")
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired in create_new_session request")
        return jsonify({'error': 'Token expired'}), 401     
    except jwt.InvalidTokenError:
        logger.warning("Invalid token in create_new_session request")
        return jsonify({'error': 'Invalid token'}), 401

    data = request.get_json() or {}
    title = data.get('title', "New Chat")
    logger.debug(f"New session title: {title}")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        current_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        
    
        cursor.execute(
            "INSERT INTO session (user_id, title, created_at, is_active) VALUES (%s, %s, %s, TRUE)",
            (user_id, title, current_date)
        )
        session_id = cursor.lastrowid
        conn.commit()
        
        logger.info(f"New session created successfully: session_id={session_id}, title={title}, user_id={user_id}")
        return jsonify({
            'message': 'New session created successfully',
            'session_id': session_id,
            'title': title,
            'created_at': current_date,
            'is_active': True
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
        logger.warning("Token missing in delete_session request")
        return jsonify({'error': 'Token is missing!'}), 401

    token = auth_header.split(" ")[1]

    try:
        decoded = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        user_id = decoded['user_id']
        is_admin = decoded.get('is_admin', False)

        logger.debug(f"delete_session: session_id={session_id}, user_id={user_id}, is_admin={is_admin}")
        
        if not user_id:
            logger.warning("Invalid token format in delete_session")
            return jsonify({'error': 'Invalid token format'}), 401
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        

        if is_admin:
            cursor.execute("SELECT id, user_id, is_active FROM session WHERE id = %s", (session_id,))
        else:
            cursor.execute("SELECT id, user_id, is_active FROM session WHERE id = %s AND user_id = %s", 
                        (session_id, user_id))
            
        session = cursor.fetchone()

        if not session:
            logger.warning(f"Session not found or unauthorized: session_id={session_id}, user_id={user_id}")
            return jsonify({'error': 'Session not found or unauthorized'}), 403
        
        
        logger.info(f"Marking session inactive: session_id={session_id}, user_id={session['user_id']}")
        cursor.execute("UPDATE session SET is_active = FALSE WHERE id = %s", (session_id,))
        conn.commit()
        return jsonify({'message': 'Session deleted successfully'}), 200
    
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

@main.route('/error', methods=['GET'])
def error_page():
    error_message = request.args.get('message', 'Something went wrong with our enchantments.')
    return render_template('error.html', error_message=error_message)

@main.route('/debug/session/<int:session_id>', methods=['GET'])
def debug_session(session_id):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token is missing!'}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        user_id = decoded['user_id']
        is_admin = decoded.get('is_admin', False)
        
    
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if is_admin:
            cursor.execute("""
                SELECT 
                    s.*,
                    DATE_FORMAT(s.created_at, '%Y-%m-%d') as formatted_date,
                    u.username as owner_username,
                    COUNT(m.id) as message_count
                FROM session s
                JOIN users u ON s.user_id = u.id
                LEFT JOIN message m ON s.id = m.session_id
                WHERE s.id = %s
                GROUP BY s.id
            """, (session_id,))
        else:
            cursor.execute("""
                SELECT 
                    s.*,
                    DATE_FORMAT(s.created_at, '%Y-%m-%d') as formatted_date,
                    COUNT(m.id) as message_count
                FROM session s
                LEFT JOIN message m ON s.id = m.session_id
                WHERE s.id = %s AND s.user_id = %s
                GROUP BY s.id
            """, (session_id, user_id))
        
        session_data = cursor.fetchone()
        if not session_data:
            return jsonify({'error': 'Session not found or unauthorized'}), 403

        cursor.execute("""
            SELECT 
                id, sender, content, 
                DATE_FORMAT(created_at, '%Y-%m-%d') as created_at 
            FROM message 
            WHERE session_id = %s 
            ORDER BY created_at ASC
        """, (session_id,))
        messages = cursor.fetchall()
        
        return jsonify({
            'session': session_data,
            'messages': messages,
            'debug_info': {
                'current_user_id': user_id,
                'is_admin': is_admin,
                'timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error in debug_session: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@main.route('/chat/session', methods=['POST'])
def create_session():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.warning("Token missing in create_session request")
        return jsonify({'error': 'Token is missing!'}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        user_id = decoded.get('user_id')
        logger.debug(f"Creating session for user_id={user_id} using alternative endpoint")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        current_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')

        
        cursor.execute(
            "INSERT INTO session (user_id, title, created_at, is_active) VALUES (%s, %s, %s, TRUE)",
            (user_id, 'New Session', current_date)
        )
        session_id = cursor.lastrowid
        conn.commit()

        logger.info(f"New session created successfully: session_id={session_id}, user_id={user_id}")
        return jsonify({
            'message': 'Session created successfully', 
            'session_id': session_id,
            'title': 'New Session',
            'created_at': current_date,
            'is_active': True
        }), 201

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired!'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token!'}), 401
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
