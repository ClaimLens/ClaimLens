import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('JWT_SECRET', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    
    # Database
    MONGODB_URI = os.getenv('MONGODB_URI')
    
    # AI Services
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # File Upload
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'tiff'}
    
    # JWT
    JWT_EXPIRATION_DAYS = 7
    
    # Fraud Detection
    HIGH_AMOUNT_THRESHOLD = 500000
    MEDIUM_AMOUNT_THRESHOLD = 200000
    FRAUD_SCORE_AUTO_REJECT = 80
    FRAUD_SCORE_AUTO_APPROVE = 30
    LOW_AMOUNT_AUTO_APPROVE = 50000