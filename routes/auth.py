from flask import Blueprint, request, jsonify
from models.database import db
from models.user import User
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    """Decorator to protect routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
            current_user = db.users.find_one({'email': data['email']})
            
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
                
        except:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.json
        
        # Validate input
        required_fields = ['email', 'password', 'name']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user exists
        if db.get_user_by_email(data['email']):
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create user
        user_data = User.create(
            email=data['email'],
            password=data['password'],
            name=data['name'],
            role=data.get('role', 'customer')
        )
        
        user_id = db.create_user(user_data)
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user_id
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
        token = jwt.encode({
            'email': user['email'],
            'user_id': str(user['_id']),
            'role': user['role'],
            'exp': datetime.utcnow() + timedelta(days=7)
        }, os.getenv('JWT_SECRET'), algorithm='HS256')
        
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