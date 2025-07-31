'''import os
from functools import wraps
from flask import request, jsonify
import jwt

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'error': 'Token is missing!'}), 401

        try:
            # Force verification of expiration
            data = jwt.decode(
                token, 
                os.getenv('SECRET_KEY'), 
                algorithms=["HS256"],
                options={"verify_exp": True}
            )
            current_user = data.get('email')
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated'''