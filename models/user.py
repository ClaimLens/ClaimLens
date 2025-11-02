from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User:
    @staticmethod
    def create(email, password, name, role='customer'):
        return {
            'email': email,
            'password': generate_password_hash(password),
            'name': name,
            'role': role,  # 'customer' or 'admin'
            'phone': '',
            'created_at': datetime.utcnow(),
            'is_active': True
        }
    
    @staticmethod
    def verify_password(stored_password, provided_password):
        return check_password_hash(stored_password, provided_password)
    
    @staticmethod
    def to_dict(user):
        """Convert user object to safe dict (remove password)"""
        user_dict = dict(user)
        user_dict.pop('password', None)
        user_dict['_id'] = str(user_dict.get('_id', ''))
        return user_dict