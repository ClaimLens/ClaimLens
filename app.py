from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# CRITICAL FIX: Setup proper logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Import blueprints
from routes.auth import auth_bp
from routes.claims import claims_bp
from routes.admin import admin_bp

# Create Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(claims_bp, url_prefix='/api/claims')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

# Root endpoint
@app.route('/')
def index():
    return jsonify({
        'message': 'Insurance Claim Automation API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'auth': '/api/auth',
            'claims': '/api/claims',
            'admin': '/api/admin'
        }
    })

# Health check
@app.route('/health')
def health():
    # Check if critical services are available
    health_status = {
        'status': 'healthy',
        'database': 'unknown',
        'ai_service': 'unknown'
    }
    
    try:
        from models.database import db
        db.client.server_info()
        health_status['database'] = 'connected'
    except:
        health_status['database'] = 'disconnected'
        health_status['status'] = 'degraded'
    
    try:
        from services.ai_service import ai_service
        if ai_service:
            health_status['ai_service'] = 'configured'
    except:
        health_status['ai_service'] = 'unavailable'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({'error': 'File too large (max 10MB)'}), 413

@app.errorhandler(Exception)
def handle_exception(error):
    logger.error(f"Unhandled exception: {error}", exc_info=True)
    return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    logger.info(f"🚀 Starting Insurance Claim API on port {port}")
    app.run(debug=True, host='0.0.0.0', port=port)