"""
Input validation and sanitization utilities
Prevents injection attacks and validates all inputs
"""
import re
from datetime import datetime
from typing import Any, Dict, Optional, List
from functools import wraps
from flask import request, jsonify

# Helper function for easy import
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

class ValidationError(Exception):
    """Custom validation error for detailed error reporting"""
    pass

class Validators:
    """Comprehensive input validation class"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000, min_length: int = 0) -> str:
        """Sanitize and validate string input"""
        if not isinstance(value, str):
            raise ValidationError(f"Expected string, got {type(value).__name__}")
        
        value = value.strip()
        
        if len(value) < min_length:
            raise ValidationError(f"String too short (minimum: {min_length} characters)")
        
        if len(value) > max_length:
            raise ValidationError(f"String too long (maximum: {max_length} characters)")
        
        # Check for script tags
        if '<script' in value.lower() or '<?php' in value.lower():
            raise ValidationError("Invalid characters detected - script tags not allowed")
        
        return value
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and sanitize email"""
        email = Validators.sanitize_string(email, max_length=254, min_length=5)
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            raise ValidationError("Invalid email format")
        
        return email.lower()
    
    @staticmethod
    def validate_phone(phone: str) -> str:
        """Validate Indian phone number"""
        phone = re.sub(r'[^\d+\-\s()]', '', phone)
        phone_digits = re.sub(r'[^\d]', '', phone)
        
        if len(phone_digits) < 10:
            raise ValidationError("Phone number must be at least 10 digits")
        
        if len(phone_digits) > 15:
            raise ValidationError("Phone number is too long")
        
        return phone
    
    @staticmethod
    def validate_policy_number(policy_number: str) -> str:
        """Validate policy number format"""
        policy_number = Validators.sanitize_string(policy_number, max_length=50, min_length=5)
        
        if not re.match(r'^[A-Z0-9\-]+$', policy_number):
            raise ValidationError("Policy number must contain only uppercase letters, numbers, and hyphens")
        
        return policy_number
    
    @staticmethod
    def validate_claim_amount(amount: Any) -> float:
        """Validate claim amount"""
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            raise ValidationError("Claim amount must be a valid number")
        
        if amount <= 0:
            raise ValidationError("Claim amount must be greater than zero")
        
        if amount > 10000000:  # 10 million max
            raise ValidationError("Claim amount exceeds maximum limit of 10,000,000")
        
        return round(amount, 2)
    
    @staticmethod
    def validate_date(date_string: str, date_format: str = '%Y-%m-%d') -> str:
        """Validate date format"""
        try:
            parsed_date = datetime.strptime(date_string, date_format)
            # Ensure date is not in future
            if parsed_date > datetime.now():
                raise ValidationError("Date cannot be in the future")
            return date_string
        except ValueError:
            raise ValidationError(f"Invalid date format. Expected {date_format}")
    
    @staticmethod
    def validate_claim_type(claim_type: str) -> str:
        """Validate claim type"""
        valid_types = ['Health', 'Motor', 'Property', 'Travel', 'Life']
        claim_type = Validators.sanitize_string(claim_type, max_length=20)
        
        if claim_type not in valid_types:
            raise ValidationError(f"Invalid claim type. Must be one of: {', '.join(valid_types)}")
        
        return claim_type
    
    @staticmethod
    def validate_password(password: str) -> str:
        """Validate password strength"""
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        if len(password) > 128:
            raise ValidationError("Password is too long (maximum 128 characters)")
        
        has_upper = re.search(r'[A-Z]', password)
        has_lower = re.search(r'[a-z]', password)
        has_digit = re.search(r'\d', password)
        has_special = re.search(r'[!@#$%^&*]', password)
        
        if not (has_upper and has_lower and has_digit):
            raise ValidationError("Password must contain uppercase, lowercase, and numbers")
        
        return password
    
    @staticmethod
    def validate_json_data(data: Dict, required_fields: List[str]) -> Dict:
        """Validate JSON data has all required fields"""
        if not isinstance(data, dict):
            raise ValidationError("Expected JSON object")
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
        
        return data


def validate_form_data(schema: Dict[str, Dict[str, Any]]):
    """
    Decorator to validate form data against schema
    
    Example:
        @validate_form_data({
            'email': {'type': 'email', 'required': True},
            'amount': {'type': 'amount', 'required': True},
            'description': {'type': 'string', 'max_length': 2000, 'min_length': 10}
        })
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.form.to_dict()
                errors = []
                sanitized_data = {}
                
                for field, rules in schema.items():
                    if rules.get('required', False) and field not in data:
                        errors.append(f'{field} is required')
                        continue
                    
                    if field not in data:
                        continue
                    
                    value = data[field]
                    field_type = rules.get('type', 'string')
                    
                    try:
                        if field_type == 'email':
                            sanitized_data[field] = Validators.validate_email(value)
                        elif field_type == 'phone':
                            sanitized_data[field] = Validators.validate_phone(value)
                        elif field_type == 'amount':
                            sanitized_data[field] = Validators.validate_claim_amount(value)
                        elif field_type == 'policy_number':
                            sanitized_data[field] = Validators.validate_policy_number(value)
                        elif field_type == 'claim_type':
                            sanitized_data[field] = Validators.validate_claim_type(value)
                        elif field_type == 'password':
                            sanitized_data[field] = Validators.validate_password(value)
                        else:  # string
                            max_len = rules.get('max_length', 1000)
                            min_len = rules.get('min_length', 0)
                            sanitized_data[field] = Validators.sanitize_string(value, max_length=max_len, min_length=min_len)
                    except ValidationError as e:
                        errors.append(str(e))
                
                if errors:
                    return jsonify({'error': 'Validation failed', 'details': errors}), 400
                
                kwargs['validated_data'] = sanitized_data
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': 'Validation error', 'message': str(e)}), 400
        
        return decorated_function
    return decorator


def validate_json_schema(schema: Dict[str, Dict[str, Any]]):
    """Decorator to validate JSON data against schema"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json()
                
                if data is None:
                    return jsonify({'error': 'Invalid JSON'}), 400
                
                errors = []
                sanitized_data = {}
                
                for field, rules in schema.items():
                    if rules.get('required', False) and field not in data:
                        errors.append(f'{field} is required')
                        continue
                    
                    if field not in data:
                        continue
                    
                    value = data[field]
                    field_type = rules.get('type', 'string')
                    
                    try:
                        if field_type == 'email':
                            sanitized_data[field] = Validators.validate_email(value)
                        elif field_type == 'phone':
                            sanitized_data[field] = Validators.validate_phone(value)
                        elif field_type == 'amount':
                            sanitized_data[field] = Validators.validate_claim_amount(value)
                        elif field_type == 'policy_number':
                            sanitized_data[field] = Validators.validate_policy_number(value)
                        elif field_type == 'claim_type':
                            sanitized_data[field] = Validators.validate_claim_type(value)
                        elif field_type == 'password':
                            sanitized_data[field] = Validators.validate_password(value)
                        else:  # string
                            max_len = rules.get('max_length', 1000)
                            min_len = rules.get('min_length', 0)
                            sanitized_data[field] = Validators.sanitize_string(value, max_length=max_len, min_length=min_len)
                    except ValidationError as e:
                        errors.append(str(e))
                
                if errors:
                    return jsonify({'error': 'Validation failed', 'details': errors}), 400
                
                kwargs['validated_data'] = sanitized_data
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': 'Validation error', 'message': str(e)}), 400
        
        return decorated_function
    return decorator