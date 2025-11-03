from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime
import os
import logging


# Load environment variables
load_dotenv()


# Setup proper logging
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
# 🏢 ENTERPRISE ROUTES
from routes.super_admin import super_admin_bp
from routes.company_admin import company_admin_bp
from routes.agent import agent_bp


# Create Flask app
app = Flask(__name__)


# Configure CORS properly
CORS(app, 
     resources={r"/api/*": {"origins": "*"}},
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=True)


# Configuration
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET')


# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Register blueprints - Original routes
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(claims_bp, url_prefix='/api/claims')
app.register_blueprint(admin_bp, url_prefix='/api/admin')


# Register ENTERPRISE blueprints - Multi-tenant 4-tier system
app.register_blueprint(super_admin_bp, url_prefix='/api/super-admin')
app.register_blueprint(company_admin_bp, url_prefix='/api/company-admin')
app.register_blueprint(agent_bp, url_prefix='/api/agent')


# Root endpoint
@app.route('/')
def index():
    return jsonify({
        'message': 'Insurance Claim Automation API',
        'version': '1.0.0',
        'status': 'running',
        'features': [
            'XGBoost Fraud Detection (3 domains)',
            'Gemini AI Document Analysis',
            'JWT Authentication',
            'Multi-Tenant Enterprise System',
            'Explainable AI'
        ],
        'endpoints': {
            'auth': '/api/auth',
            'claims': '/api/claims',
            'admin': '/api/admin',
            'super_admin': '/api/super-admin',
            'company_admin': '/api/company-admin',
            'agent': '/api/agent',
            'demo': '/api/claims/demo/analyze',
            'health': '/api/health',
            'diagnostics': '/api/diagnostics'
        }
    })


# ============================================
# HEALTH CHECK ENDPOINT - FIXED ROUTE
# ============================================
@app.route('/api/health')
def health():
    """System health check - verifies all critical components"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database_original': 'unknown',
        'database_enterprise': 'unknown',
        'ai_service': 'unknown',
        'xgboost_models': 'unknown'
    }
    
    # Check original database
    try:
        from models.database import db
        db.client.server_info()
        health_status['database_original'] = 'connected'
    except Exception as e:
        logger.warning(f"Original database health check failed: {e}")
        health_status['database_original'] = 'disconnected'
        health_status['status'] = 'degraded'
    
    # Check enterprise database
    try:
        from models.database_enterprise import enterprise_db
        enterprise_db.client.server_info()
        health_status['database_enterprise'] = 'connected'
    except Exception as e:
        logger.warning(f"Enterprise database health check failed: {e}")
        health_status['database_enterprise'] = 'disconnected'
        health_status['status'] = 'degraded'
    
    # Check AI service
    try:
        from services.ai_service import ai_service
        if ai_service:
            health_status['ai_service'] = 'configured'
        else:
            health_status['ai_service'] = 'not_configured'
    except Exception as e:
        logger.warning(f"AI service health check failed: {e}")
        health_status['ai_service'] = 'unavailable'
    
    # Check XGBoost models
    try:
        from services.xgboost_fraud_detector import detector
        test_result = detector.detect_fraud([1, 1, 1], 'health')
        
        if test_result.get('fraud_score') is not None:
            health_status['xgboost_models'] = 'loaded'
            logger.info("✅ XGBoost models verified")
        else:
            health_status['xgboost_models'] = 'error'
            health_status['status'] = 'degraded'
    except Exception as e:
        logger.error(f"XGBoost health check failed: {e}")
        health_status['xgboost_models'] = 'error'
        health_status['status'] = 'degraded'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code


# ============================================
# DIAGNOSTICS ENDPOINT - FIXED ROUTE
# ============================================
@app.route('/api/diagnostics')
def diagnostics():
    """System diagnostics - check models and services availability"""
    diag = {
        'timestamp': datetime.utcnow().isoformat(),
        'models': {},
        'services': {},
        'paths': {},
        'files': {}
    }
    
    # Check model files
    models_dir = './models'
    if os.path.exists(models_dir):
        diag['paths']['models_dir'] = os.path.abspath(models_dir)
        diag['models']['health'] = os.path.exists(f'{models_dir}/xgboost_health_fraud.bin')
        diag['models']['vehicle'] = os.path.exists(f'{models_dir}/xgboost_vehicle_fraud.bin')
        diag['models']['auto'] = os.path.exists(f'{models_dir}/xgboost_auto_fraud.bin')
        
        # Show file sizes
        if os.path.exists(f'{models_dir}/xgboost_health_fraud.bin'):
            diag['files']['health_model_size_mb'] = round(os.path.getsize(f'{models_dir}/xgboost_health_fraud.bin') / 1024 / 1024, 2)
        if os.path.exists(f'{models_dir}/xgboost_vehicle_fraud.bin'):
            diag['files']['vehicle_model_size_mb'] = round(os.path.getsize(f'{models_dir}/xgboost_vehicle_fraud.bin') / 1024 / 1024, 2)
        if os.path.exists(f'{models_dir}/xgboost_auto_fraud.bin'):
            diag['files']['auto_model_size_mb'] = round(os.path.getsize(f'{models_dir}/xgboost_auto_fraud.bin') / 1024 / 1024, 2)
    else:
        diag['paths']['models_dir'] = 'NOT FOUND'
    
    # Check XGBoost service
    try:
        from services.xgboost_fraud_detector import detector
        test = detector.detect_fraud([1]*3, 'health')
        if test.get('fraud_score') is not None:
            diag['services']['xgboost'] = 'operational'
            diag['services']['xgboost_test_result'] = {
                'fraud_score': test.get('fraud_score'),
                'risk_level': test.get('risk_level')
            }
        else:
            diag['services']['xgboost'] = 'error'
    except Exception as e:
        diag['services']['xgboost'] = f'error: {str(e)}'
    
    # Check Gemini AI service
    try:
        from services.ai_service import ai_service
        diag['services']['gemini_ai'] = 'configured' if ai_service else 'not_configured'
    except Exception as e:
        diag['services']['gemini_ai'] = f'unavailable: {str(e)}'
    
    # Check explainable AI
    try:
        from services.explainable_ai import explainable_ai
        diag['services']['explainable_ai'] = 'available'
    except Exception as e:
        diag['services']['explainable_ai'] = f'unavailable: {str(e)}'
    
    # Check upload folder
    diag['paths']['upload_folder'] = os.path.abspath('uploads')
    diag['paths']['upload_folder_exists'] = os.path.exists('uploads')
    
    return jsonify(diag), 200


# ============================================
# PUBLIC DEMO ENDPOINT - NO AUTHENTICATION
# ============================================
@app.route('/api/claims/demo/analyze', methods=['POST'])
def demo_analyze():
    """
    PUBLIC: XGBoost fraud analysis for hackathon demo (NO AUTH REQUIRED)
    
    Expected JSON input:
    {
        "claim_type": "Health|Motor|Property",
        "age": 30,
        "claim_amount": 50000,
        "policy_duration": 12
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        claim_type = data.get('claim_type', 'Health')
        
        # Map claim types to model types
        model_type_map = {
            'Health': 'health',
            'Motor': 'vehicle',
            'Vehicle': 'vehicle',
            'Property': 'auto',
            'Auto': 'auto',
            'health': 'health',
            'vehicle': 'vehicle',
            'auto': 'auto'
        }
        model_type = model_type_map.get(claim_type, 'health')
        
        # Extract features - FIXED: Accept claim_amount (from frontend)
        age = float(data.get('age', 0))
        claim_amount = float(data.get('claim_amount') or data.get('amount', 0))
        policy_duration = float(data.get('policy_duration', 0))
        
        features = [age, claim_amount, policy_duration]
        
        from services.xgboost_fraud_detector import detector
        from services.explainable_ai import explainable_ai
        
        # Get XGBoost prediction
        result = detector.detect_fraud(features, model_type)
        
        # Create mock claim for explanation
        mock_claim = {
            'amount': claim_amount,
            'claim_type': claim_type,
            'age': age,
            'created_at': datetime.utcnow(),
            'ai_analysis': {
                'xgboost_fraud_score': result['fraud_score'],
                'xgboost_risk_level': result['risk_level']
            }
        }
        
        # Generate explanation
        explanation = explainable_ai.explain_fraud_decision(mock_claim)
        
        return jsonify({
            'status': 'success',
            'claim_type': claim_type,
            'model_used': model_type,
            'input_features': {
                'age': age,
                'claim_amount': claim_amount,
                'policy_duration': policy_duration
            },
            'xgboost_analysis': result,
            'explanation': explanation,
            'model_accuracy': {
                'health': '92.39%',
                'vehicle': '94.42%',
                'auto': '77.50%'
            },
            'decision': explanation['decision'],
            'confidence': explanation['confidence']
        }), 200
    
    except ValueError as e:
        logger.error(f"Invalid input in demo analysis: {str(e)}")
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in demo analysis: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'status_code': 404,
        'message': 'The requested URL was not found on the server'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({
        'error': 'Internal server error',
        'status_code': 500,
        'message': 'An unexpected error occurred on the server'
    }), 500


@app.errorhandler(413)
def file_too_large(error):
    """Handle file too large errors"""
    return jsonify({
        'error': 'File too large',
        'status_code': 413,
        'message': 'Maximum file size is 10MB'
    }), 413


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {error}", exc_info=True)
    return jsonify({
        'error': 'An unexpected error occurred',
        'status_code': 500,
        'message': str(error)
    }), 500


# ============================================
# APPLICATION ENTRY POINT
# ============================================

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'
    
    logger.info("=" * 80)
    logger.info("🚀 Starting Insurance Claim Automation API")
    logger.info("=" * 80)
    logger.info(f"📍 Server: 0.0.0.0:{port}")
    logger.info(f"🔧 Debug Mode: {debug_mode}")
    logger.info(f"📂 Upload Folder: {os.path.abspath('uploads')}")
    logger.info("=" * 80)
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
