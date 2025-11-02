import re
from datetime import datetime

class Validators:
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone):
        """Validate Indian phone number"""
        pattern = r'^[6-9]\d{9}$'
        return re.match(pattern, phone) is not None
    
    @staticmethod
    def validate_policy_number(policy_number):
        """Validate policy number format"""
        # Assuming format: POL followed by 8-10 digits
        pattern = r'^POL\d{8,10}$'
        return re.match(pattern, policy_number) is not None
    
    @staticmethod
    def validate_claim_amount(amount):
        """Validate claim amount"""
        try:
            amount = float(amount)
            return amount > 0 and amount <= 10000000  # Max 1 crore
        except:
            return False
    
    @staticmethod
    def validate_date(date_string):
        """Validate date format YYYY-MM-DD"""
        try:
            datetime.strptime(date_string, '%Y-%m-%d')
            return True
        except:
            return False