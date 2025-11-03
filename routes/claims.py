from flask import Blueprint, request, jsonify
from models.database import db
from models.claim import Claim
from routes.auth import token_required
from services.ai_service import ai_service
from services.fraud_detector import fraud_detector
from services.document_processor import document_processor
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

claims_bp = Blueprint('claims', __name__)

@claims_bp.route('/create', methods=['POST'])
@token_required
def create_claim(current_user):
    """
    Create new insurance claim
    CRITICAL FIX #4: Added validation
    """
    try:
        # Get form data with trimming
        policy_number = request.form.get('policy_number', '').strip()
        claim_type = request.form.get('claim_type', '').strip()
        description = request.form.get('description', '').strip()
        
        # CRITICAL FIX #4: Validate required fields
        validation_errors = []
        
        if not policy_number:
            validation_errors.append('Policy number is required')
        elif len(policy_number) < 5:
            validation_errors.append('Policy number must be at least 5 characters')
        
        valid_claim_types = ['Health', 'Motor', 'Property']
        if not claim_type:
            validation_errors.append('Claim type is required')
        elif claim_type not in valid_claim_types:
            validation_errors.append(f'Claim type must be one of: {", ".join(valid_claim_types)}')
        
        if not description:
            validation_errors.append('Description is required')
        elif len(description) < 10:
            validation_errors.append('Description must be at least 10 characters')
        elif len(description) > 2000:
            validation_errors.append('Description must be less than 2000 characters')
        
        if validation_errors:
            return jsonify({'error': 'Validation failed', 'details': validation_errors}), 400
        
        # Process uploaded documents
        uploaded_files = request.files.getlist('documents')
        
        if not uploaded_files or uploaded_files[0].filename == '':
            return jsonify({'error': 'At least one document is required'}), 400
        
        # CRITICAL FIX #4: Validate file count and sizes
        if len(uploaded_files) > 5:
            return jsonify({'error': 'Maximum 5 documents allowed'}), 400
        
        # Create initial claim
        claim_data = Claim.create(
            user_id=str(current_user['_id']),
            policy_number=policy_number,
            claim_type=claim_type,
            description=description
        )
        
        document_paths = []
        total_size = 0
        
        for file in uploaded_files:
            # Check individual file size
            file.seek(0, 2)  # Move to end of file
            file_size = file.tell()
            file.seek(0)  # Reset file pointer
            
            total_size += file_size
            
            if file_size > 10 * 1024 * 1024:
                # Clean up uploaded files if any
                for path in document_paths:
                    document_processor.delete_document(path)
                return jsonify({'error': f'File {file.filename} exceeds 10MB limit'}), 400
            
            success, result = document_processor.save_document(file, claim_data['claim_id'])
            
            if not success:
                for path in document_paths:
                    document_processor.delete_document(path)
                return jsonify({'error': result}), 400
            
            document_paths.append(result)
        
        claim_data['documents'] = document_paths
        
        # AI Processing with error handling
        logger.info(f"Processing document with AI: {document_paths[0]}")
        
        try:
            ai_result = ai_service.extract_document_data(document_paths[0])
            
            if ai_result['success']:
                extracted_data = ai_result['data']
                claim_data['ai_analysis']['extracted_data'] = extracted_data
                claim_data['ai_analysis']['processed'] = True
                
                if extracted_data.get('claim_amount'):
                    claim_data['amount'] = extracted_data['claim_amount']
                
                validation_result = ai_service.validate_claim_narrative(description, extracted_data)
                claim_data['ai_analysis']['narrative_validation'] = validation_result
                
                tampering_result = ai_service.detect_document_tampering(document_paths[0])
                claim_data['ai_analysis']['tampering_check'] = tampering_result
                
                user_history = fraud_detector.get_user_claim_history(str(current_user['_id']))
                
                fraud_analysis = fraud_detector.calculate_fraud_score(claim_data, user_history, extracted_data)
                
                claim_data['ai_analysis']['fraud_score'] = fraud_analysis['fraud_score']
                claim_data['ai_analysis']['risk_level'] = fraud_analysis['risk_level']
                claim_data['ai_analysis']['risk_factors'] = fraud_analysis['risk_factors']
                claim_data['ai_analysis']['recommendation'] = fraud_analysis['recommendation']
                claim_data['ai_analysis']['requires_manual_review'] = fraud_analysis['requires_manual_review']
                
                if fraud_analysis['fraud_score'] >= 80:
                    claim_data['status'] = 'under_review'
                elif fraud_analysis['fraud_score'] < 30 and claim_data.get('amount', 0) < 50000:
                    claim_data['status'] = 'approved'
                    claim_data['approved_amount'] = claim_data.get('amount', 0)
            
            else:
                logger.warning(f"AI extraction failed: {ai_result.get('error')}")
                claim_data['ai_analysis']['error'] = ai_result.get('error')
                claim_data['ai_analysis']['processed'] = False
            
        except Exception as ai_error:
            logger.error(f"AI processing exception: {str(ai_error)}")
            claim_data['ai_analysis']['error'] = 'AI processing failed'
            claim_data['ai_analysis']['processed'] = False
        
        # Save claim to database
        db.create_claim(claim_data)
        
        return jsonify({
            'message': 'Claim created successfully',
            'claim': Claim.to_dict(claim_data)
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating claim: {str(e)}")
        return jsonify({'error': 'Failed to create claim', 'details': str(e)}), 500


@claims_bp.route('/user', methods=['GET'])
@token_required
def get_user_claims(current_user):
    """Get all claims for current user"""
    try:
        user_id = str(current_user['_id'])
        claims = db.get_claims_by_user(user_id)
        
        return jsonify([Claim.to_dict(claim) for claim in claims]), 200
        
    except Exception as e:
        logger.error(f"Error fetching user claims: {str(e)}")
        return jsonify({'error': 'Failed to fetch claims'}), 500


@claims_bp.route('/<claim_id>', methods=['GET'])
@token_required
def get_claim_details(current_user, claim_id):
    """Get specific claim details"""
    try:
        claim = db.get_claim_by_id(claim_id)
        
        if not claim:
            return jsonify({'error': 'Claim not found'}), 404
        
        # Check if user owns this claim or is admin
        if str(claim.get('user_id')) != str(current_user['_id']) and current_user.get('role') != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify(Claim.to_dict(claim)), 200
        
    except Exception as e:
        logger.error(f"Error fetching claim details: {str(e)}")
        return jsonify({'error': 'Failed to fetch claim details'}), 500
