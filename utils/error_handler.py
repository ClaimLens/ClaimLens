"""
Error handling and logging middleware for Flask
Provides consistent error responses and request logging
"""
import logging
import traceback
from datetime import datetime
from flask import jsonify, request
from functools import wraps

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling"""
    
    # HTTP Status Codes
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_ERROR = 500
    SERVICE_UNAVAILABLE = 503
    
    # Error Types
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND_ERROR = "NOT_FOUND_ERROR"
    CONFLICT_ERROR = "CONFLICT_ERROR"
    SERVER_ERROR = "SERVER_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    
    @staticmethod
    def success(data=None, message="Success", status_code=200):
        """Return successful response"""
        response = {
            'status': 'success',
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        if data is not None:
            response['data'] = data
        return jsonify(response), status_code
    
    @staticmethod
    def error(error_type, message, details=None, status_code=400):
        """Return error response"""
        response = {
            'status': 'error',
            'error_type': error_type,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        if details:
            response['details'] = details if isinstance(details, list) else [details]
        return jsonify(response), status_code
    
    @staticmethod
    def bad_request(message, details=None):
        """Bad request error (400)"""
        return ErrorHandler.error(
            ErrorHandler.VALIDATION_ERROR,
            message or "Bad request",
            details,
            ErrorHandler.BAD_REQUEST
        )
    
    @staticmethod
    def unauthorized(message="Unauthorized"):
        """Unauthorized error (401)"""
        return ErrorHandler.error(
            ErrorHandler.AUTHENTICATION_ERROR,
            message,
            status_code=ErrorHandler.UNAUTHORIZED
        )
    
    @staticmethod
    def forbidden(message="Forbidden"):
        """Forbidden error (403)"""
        return ErrorHandler.error(
            ErrorHandler.AUTHORIZATION_ERROR,
            message,
            status_code=ErrorHandler.FORBIDDEN
        )
    
    @staticmethod
    def not_found(message="Resource not found"):
        """Not found error (404)"""
        return ErrorHandler.error(
            ErrorHandler.NOT_FOUND_ERROR,
            message,
            status_code=ErrorHandler.NOT_FOUND
        )
    
    @staticmethod
    def conflict(message, details=None):
        """Conflict error (409)"""
        return ErrorHandler.error(
            ErrorHandler.CONFLICT_ERROR,
            message,
            details,
            ErrorHandler.CONFLICT
        )
    
    @staticmethod
    def server_error(message="Internal server error", details=None):
        """Server error (500)"""
        logger.error(f"Server error: {message}", extra={'details': details})
        return ErrorHandler.error(
            ErrorHandler.SERVER_ERROR,
            message,
            details,
            ErrorHandler.INTERNAL_ERROR
        )
    
    @staticmethod
    def service_unavailable(message="Service temporarily unavailable"):
        """Service unavailable (503)"""
        return ErrorHandler.error(
            ErrorHandler.EXTERNAL_SERVICE_ERROR,
            message,
            status_code=ErrorHandler.SERVICE_UNAVAILABLE
        )


def handle_errors(f):
    """Decorator to handle exceptions in route handlers"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            # Log the full traceback
            logger.error(f"Exception in {f.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return generic error to client (don't expose internals)
            return ErrorHandler.server_error(
                "An error occurred processing your request. Please try again."
            )
    
    return decorated_function


def log_request_response(f):
    """Decorator to log all requests and responses"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Log request
            logger.info(
                f"Request: {request.method} {request.path}",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'remote_addr': request.remote_addr,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            # Call the function
            result = f(*args, **kwargs)
            
            # Log response
            if isinstance(result, tuple):
                status_code = result[1] if len(result) > 1 else 200
            else:
                status_code = 200
            
            logger.info(
                f"Response: {request.method} {request.path} - {status_code}",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status': status_code,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return result
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            return ErrorHandler.server_error()
    
    return decorated_function


def register_error_handlers(app):
    """Register error handlers with Flask app"""
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        return ErrorHandler.bad_request("Bad request")
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        return ErrorHandler.unauthorized()
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        return ErrorHandler.forbidden()
    
    @app.errorhandler(404)
    def handle_not_found(error):
        return ErrorHandler.not_found()
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error(f"Internal server error: {error}")
        return ErrorHandler.server_error()
    
    @app.errorhandler(503)
    def handle_service_unavailable(error):
        return ErrorHandler.service_unavailable()
