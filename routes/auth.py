from flask import Blueprint, request, jsonify
from models.database import db
from models.user import User
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

def token_required(f):
    """
    Decorator to protect routes
    CRITICAL FIX #6: Enhanced token validation
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Validate JWT secret exists
            jwt_secret = os.getenv('JWT_SECRET')
            if not jwt_secret:
                logger.error("JWT_SECRET not configured!")
                return jsonify({'error': 'Server configuration error'}), 500
            
            # Decode token
            data = jwt.decode(token, jwt_secret, algorithms=['HS256'])
            
            # CRITICAL FIX #6: Validate required fields in token
            if 'email' not in data or 'user_id' not in data:
                return jsonify({'error': 'Invalid token structure'}), 401
            
            # Get user from database
            try:
                current_user = db.get_user_by_email(data['email'])
            except Exception as e:
                logger.error(f"Database error fetching user: {e}")
                return jsonify({'error': 'Database error'}), 500
            
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
            
            # Check if user is active
            if not current_user.get('is_active', True):
                return jsonify({'error': 'Account is disabled'}), 403
            
            # Verify user ID matches
            if str(current_user['_id']) != data['user_id']:
                logger.warning(f"Token user_id mismatch for {data['email']}")
                return jsonify({'error': 'Invalid token'}), 401
            
            # Optional: Check if role changed
            if current_user.get('role') != data.get('role'):
                logger.warning(f"User role changed since token issued: {data['email']}")
                return jsonify({'error': 'Token expired - please login again'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return jsonify({'error': 'Token validation failed'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.json
        
        # Validate input - accept both 'name' and 'full_name'
        name = data.get('name') or data.get('full_name')
        email = data.get('email')
        password = data.get('password')
        phone = data.get('phone')
        
        if not all([email, password, name]):
            return jsonify({'error': 'Missing required fields: email, password, and name are required'}), 400
        
        # Check if user exists
        if db.get_user_by_email(email):
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create user
        user_data = User.create(
            email=email,
            password=password,
            name=name,
            phone=phone,
            role=data.get('role', 'customer')
        )
        
        user_id = db.create_user(user_data)
        
        # Get the created user
        user = db.get_user_by_email(email)
        
        # Generate JWT token for automatic login
        jwt_secret = os.getenv('JWT_SECRET')
        if not jwt_secret:
            logger.error("JWT_SECRET not configured!")
            return jsonify({'error': 'Server configuration error'}), 500
        
        token = jwt.encode({
            'email': user['email'],
            'user_id': str(user['_id']),
            'role': user['role'],
            'exp': datetime.utcnow() + timedelta(days=7)
        }, jwt_secret, algorithm='HS256')
        
        # Return user info with token
        user_info = User.to_dict(user)
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': user_info
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.json
        
        # Validate input
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        # Get user
        user = db.get_user_by_email(data['email'])
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        if not User.verify_password(user['password'], data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        jwt_secret = os.getenv('JWT_SECRET')
        if not jwt_secret:
            logger.error("JWT_SECRET not configured!")
            return jsonify({'error': 'Server configuration error'}), 500
        
        token = jwt.encode({
            'email': user['email'],
            'user_id': str(user['_id']),
            'role': user['role'],
            'exp': datetime.utcnow() + timedelta(days=7)
        }, jwt_secret, algorithm='HS256')
        
        # Return user info
        user_info = User.to_dict(user)
        
        return jsonify({
            'token': token,
            'user': user_info
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    """Verify if token is valid"""
    return jsonify({
        'valid': True,
        'user': User.to_dict(current_user)
    }), 200
