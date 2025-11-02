from datetime import datetime
import random
import string

def generate_id(prefix='ID', length=8):
    """Generate random ID with prefix"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=length))
    return f"{prefix}{random_part}"

def format_currency(amount):
    """Format amount in INR"""
    return f"₹{amount:,.2f}"

def calculate_days_difference(date1, date2):
    """Calculate days between two dates"""
    delta = date2 - date1
    return delta.days

def safe_float(value, default=0.0):
    """Safely convert to float"""
    try:
        return float(value)
    except:
        return default

def safe_int(value, default=0):
    """Safely convert to int"""
    try:
        return int(value)
    except:
        return default

def get_risk_color(risk_level):
    """Get color code for risk level"""
    colors = {
        'LOW': '#10B981',    # Green
        'MEDIUM': '#F59E0B', # Orange
        'HIGH': '#EF4444'    # Red
    }
    return colors.get(risk_level, '#6B7280')

def truncate_text(text, max_length=100):
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'