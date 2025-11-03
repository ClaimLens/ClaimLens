from flask import Blueprint, request, jsonify
from models.database import db
from models.database_enterprise import enterprise_db
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
            
            # Get user from appropriate database
            try:
                database_type = data.get('database', 'regular')
                if database_type == 'enterprise':
                    current_user = enterprise_db.get_user_by_email(data['email'])
                else:
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
    """
    Unified login for both regular users and enterprise users
    Supports: customer, agent, company_admin, super_admin
    """
    try:
        data = request.json
        
        # Validate input
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        user = None
        database_type = None
        
        # Try enterprise database first (for admin, agent, company_admin, super_admin)
        try:
            enterprise_user = enterprise_db.get_user_by_email(email)
            if enterprise_user:
                # Verify password with werkzeug
                from werkzeug.security import check_password_hash
                if check_password_hash(enterprise_user['password'], password):
                    user = enterprise_user
                    database_type = 'enterprise'
                    logger.info(f"Enterprise user logged in: {email} ({enterprise_user.get('user_type', 'unknown')})")
        except Exception as e:
            logger.error(f"Enterprise DB error: {e}")
        
        # Try regular database if not found in enterprise
        if not user:
            try:
                regular_user = db.get_user_by_email(email)
                if regular_user:
                    # Verify password
                    if User.verify_password(regular_user['password'], password):
                        user = regular_user
                        database_type = 'regular'
                        logger.info(f"Regular user logged in: {email}")
            except Exception as e:
                logger.error(f"Regular DB error: {e}")
        
        # If no user found in either database
        if not user:
            logger.warning(f"Failed login attempt for: {email}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        jwt_secret = os.getenv('JWT_SECRET')
        if not jwt_secret:
            logger.error("JWT_SECRET not configured!")
            return jsonify({'error': 'Server configuration error'}), 500
        
        # Determine user role/type
        user_role = user.get('user_type') or user.get('role', 'customer')
        
        token = jwt.encode({
            'email': user['email'],
            'user_id': str(user['_id']),
            'role': user_role,
            'database': database_type,
            'company_id': str(user.get('company_id')) if user.get('company_id') else None,
            'exp': datetime.utcnow() + timedelta(days=7)
        }, jwt_secret, algorithm='HS256')
        
        # Build user response
        user_info = {
            '_id': str(user['_id']),
            'email': user['email'],
            'name': user.get('name', ''),
            'role': user_role,
            'user_type': user_role,
            'company_id': str(user.get('company_id')) if user.get('company_id') else None,
            'company_name': user.get('company_name'),
            'employee_id': user.get('employee_id'),
            'phone': user.get('phone'),
            'status': user.get('status', 'active')
        }
        
        return jsonify({
            'token': token,
            'user': user_info,
            'message': 'Login successful'
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    """Verify if token is valid"""
    return jsonify({
        'valid': True,
        'user': User.to_dict(current_user)
    }), 200


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Get current user info"""
    return jsonify({
        'user': User.to_dict(current_user)
    }), 200
