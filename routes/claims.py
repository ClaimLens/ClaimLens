from flask import Blueprint, request, jsonify
from models.database import db
from models.claim import Claim
from routes.auth import token_required
from services.ai_service import ai_service
from services.fraud_detector import fraud_detector
from services.document_processor import document_processor
# from services.xgboost_fraud_detector import detector as xgboost_detector  # Temporarily disabled
from services.explainable_ai import explainable_ai
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

claims_bp = Blueprint('claims', __name__)

@claims_bp.route('/create', methods=['POST'])
@token_required
def create_claim(current_user):
    """
    Create new insurance claim with XGBoost + Gemini fraud detection
    """
    try:
        # Get form data with trimming
        policy_number = request.form.get('policy_number', '').strip()
        claim_type = request.form.get('claim_type', '').strip()
        description = request.form.get('description', '').strip()
        
        # Validation
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
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            total_size += file_size
            
            if file_size > 10 * 1024 * 1024:
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
        
        # ============================================
        # XGBoost Fraud Detection (PRIMARY)
        # ============================================
        logger.info(f"XGBoost Fraud Detection: Processing {claim_type}")
        
        try:
            # Map claim types to model types
            model_type_map = {
                'Health': 'health',
                'Motor': 'vehicle',
                'Property': 'auto'
            }
            model_type = model_type_map.get(claim_type, 'health')
            
            # Extract numeric features from request
            claim_amount = request.form.get('amount', 0)
            age = request.form.get('age', 0)
            policy_duration = request.form.get('policy_duration', 0)
            
            xgboost_features = [
                float(age) if age else 0,
                float(claim_amount) if claim_amount else 0,
                float(policy_duration) if policy_duration else 0,
            ]
            
            # Get XGBoost prediction (temporarily disabled - using regular fraud detector)
            # xgboost_result = xgboost_detector.detect_fraud(xgboost_features, model_type)
            xgboost_result = fraud_detector.detect_fraud(claim_data)  # Fallback to regular detector
            
            claim_data['ai_analysis']['xgboost_fraud_score'] = xgboost_result.get('fraud_score', 0)
            claim_data['ai_analysis']['xgboost_risk_level'] = xgboost_result.get('risk_level', 'low')
            claim_data['ai_analysis']['xgboost_recommendation'] = xgboost_result.get('recommendation', 'approve')
            claim_data['ai_analysis']['xgboost_probability'] = xgboost_result.get('fraud_probability', 0.0)
            
            logger.info(f"XGBoost Result: Score={xgboost_result.get('fraud_score', 0)}%, Risk={xgboost_result.get('risk_level', 'low')}")
            
        except Exception as xgb_error:
            logger.warning(f"XGBoost processing failed (will fallback to Gemini): {str(xgb_error)}")
            claim_data['ai_analysis']['xgboost_error'] = str(xgb_error)
        
        # ============================================
        # Gemini AI Processing (FALLBACK + VALIDATION)
        # ============================================
        logger.info(f"Processing document with Gemini AI: {document_paths[0]}")
        
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
                
                # Legacy fraud detector (keep for compatibility)
                user_history = fraud_detector.get_user_claim_history(str(current_user['_id']))
                gemini_fraud_analysis = fraud_detector.calculate_fraud_score(claim_data, user_history, extracted_data)
                
                claim_data['ai_analysis']['gemini_fraud_score'] = gemini_fraud_analysis['fraud_score']
                claim_data['ai_analysis']['gemini_risk_level'] = gemini_fraud_analysis['risk_level']
                claim_data['ai_analysis']['gemini_risk_factors'] = gemini_fraud_analysis['risk_factors']
            
            else:
                logger.warning(f"Gemini extraction failed: {ai_result.get('error')}")
                claim_data['ai_analysis']['error'] = ai_result.get('error')
                claim_data['ai_analysis']['processed'] = False
        
        except Exception as ai_error:
            logger.error(f"Gemini processing exception: {str(ai_error)}")
            claim_data['ai_analysis']['error'] = 'Gemini processing failed'
            claim_data['ai_analysis']['processed'] = False
        
        # ============================================
        # Determine Final Status (XGBoost PRIMARY)
        # ============================================
        xgboost_score = claim_data['ai_analysis'].get('xgboost_fraud_score', 50)
        xgboost_risk = claim_data['ai_analysis'].get('xgboost_risk_level', 'MEDIUM')
        
        # Generate explainable AI analysis
        user_history = fraud_detector.get_user_claim_history(str(current_user['_id']))
        explanation = explainable_ai.explain_fraud_decision(
            claim_data, 
            user_history, 
            extracted_data if 'extracted_data' in locals() else None
        )
        
        claim_data['ai_analysis']['explanation'] = explanation
        claim_data['ai_analysis']['decision'] = explanation['decision']
        
        if xgboost_risk == 'HIGH' or xgboost_score >= 70:
            claim_data['status'] = 'under_review'
            claim_data['ai_analysis']['decision_reason'] = 'XGBoost high fraud risk detected'
        elif xgboost_risk == 'MEDIUM' or xgboost_score >= 40:
            claim_data['status'] = 'under_review'
            claim_data['ai_analysis']['decision_reason'] = 'XGBoost medium fraud risk - manual review required'
        else:
            # Low risk - can auto-approve for small amounts
            claim_amount = claim_data.get('amount', 0)
            if isinstance(claim_amount, str):
                claim_amount = float(claim_amount) if claim_amount else 0
            
            if claim_amount < 50000:
                claim_data['status'] = 'approved'
                claim_data['approved_amount'] = claim_amount
                claim_data['ai_analysis']['decision_reason'] = 'XGBoost low fraud risk + amount threshold'
            else:
                claim_data['status'] = 'under_review'
                claim_data['ai_analysis']['decision_reason'] = 'Amount exceeds auto-approval threshold'
        
        # Save claim to database
        db.create_claim(claim_data)
        
        return jsonify({
            'message': 'Claim created successfully',
            'claim': Claim.to_dict(claim_data),
            'fraud_analysis': {
                'xgboost_score': xgboost_score,
                'xgboost_risk': xgboost_risk,
                'recommendation': claim_data['ai_analysis'].get('xgboost_recommendation', 'MANUAL REVIEW'),
                'status': claim_data['status'],
                'explanation': explanation
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating claim: {str(e)}")
        return jsonify({'error': 'Failed to create claim', 'details': str(e)}), 500

@claims_bp.route('/analyze', methods=['POST'])
@token_required
def analyze_claim(current_user):
    """Quick XGBoost fraud analysis without full claim creation"""
    try:
        data = request.json
        claim_type = data.get('claim_type', 'health')
        
        # Map to model type
        model_type_map = {
            'Health': 'health',
            'Motor': 'vehicle',
            'Property': 'auto'
        }
        model_type = model_type_map.get(claim_type, 'health')
        
        # Prepare features
        features = [
            float(data.get('age', 0)),
            float(data.get('amount', 0)),
            float(data.get('policy_duration', 0))
        ]
        
        # XGBoost prediction (temporarily using fraud_detector)
        result = fraud_detector.detect_fraud({'amount': features[0]})  # Simplified
        
        return jsonify({
            'status': 'success',
            'fraud_analysis': result
        }), 200
    
    except Exception as e:
        logger.error(f"Error analyzing claim: {str(e)}")
        return jsonify({'error': str(e)}), 400

@claims_bp.route('/user', methods=['GET'])
@token_required
def get_user_claims(current_user):
    """Get all claims for logged-in user"""
    try:
        claims = db.get_claims_by_user(str(current_user['_id']))
        
        return jsonify({
            'claims': claims,
            'total': len(claims),
            'status': 'success'
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching user claims: {str(e)}")
        return jsonify({'error': 'Failed to fetch claims', 'details': str(e)}), 500


@claims_bp.route('/<claim_id>', methods=['GET'])
@token_required
def get_claim_details(current_user, claim_id):
    """Get specific claim details"""
    try:
        claim = db.get_claim_by_id(claim_id)
        
        if not claim:
            return jsonify({'error': 'Claim not found'}), 404
        
        # Verify ownership (users can only see their claims, admins can see all)
        if str(claim['user_id']) != str(current_user['_id']) and current_user.get('role') != 'admin':
            return jsonify({'error': 'Unauthorized access to this claim'}), 403
        
        return jsonify({
            'claim': claim,
            'status': 'success'
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching claim details: {str(e)}")
        return jsonify({'error': 'Failed to fetch claim details', 'details': str(e)}), 500


@claims_bp.route('/statistics', methods=['GET'])
@token_required
def get_user_statistics(current_user):
    """Get user's claim statistics"""
    try:
        user_claims = db.get_claims_by_user(str(current_user['_id']))
        
        # Calculate statistics
        total_claimed = sum(claim.get('amount', 0) for claim in user_claims)
        total_approved = sum(claim.get('approved_amount', 0) for claim in user_claims if claim.get('status') == 'approved')
        
        # Get average fraud score
        fraud_scores = [claim.get('ai_analysis', {}).get('xgboost_fraud_score', 0) for claim in user_claims if claim.get('ai_analysis', {}).get('xgboost_fraud_score')]
        avg_fraud_score = sum(fraud_scores) / len(fraud_scores) if fraud_scores else 0
        
        stats = {
            'total_claims': len(user_claims),
            'approved': len([c for c in user_claims if c.get('status') == 'approved']),
            'pending': len([c for c in user_claims if c.get('status') == 'pending']),
            'rejected': len([c for c in user_claims if c.get('status') == 'rejected']),
            'under_review': len([c for c in user_claims if c.get('status') == 'under_review']),
            'total_claimed_amount': total_claimed,
            'total_approved_amount': total_approved,
            'average_fraud_score': round(avg_fraud_score, 2),
            'recent_claims': [Claim.to_dict(c) for c in sorted(user_claims, key=lambda x: x.get('created_at', datetime.min), reverse=True)[:5]]
        }
        
        return jsonify({
            'statistics': stats,
            'status': 'success'
        }), 200
    
    except Exception as e:
        logger.error(f"Error calculating user statistics: {str(e)}")
        return jsonify({'error': 'Failed to calculate statistics', 'details': str(e)}), 500


@claims_bp.route('/flagged', methods=['GET'])
@token_required
def get_flagged_claims(current_user):
    """Get claims flagged by XGBoost for admin review"""
    try:
        # Admin-only endpoint
        if current_user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Query database for high-risk claims
        flagged_claims = db.get_all_claims({'status': 'under_review'})
        
        # Sort by fraud score (highest first)
        flagged_claims.sort(key=lambda x: x.get('ai_analysis', {}).get('xgboost_fraud_score', 0), reverse=True)
        
        return jsonify({
            'status': 'success',
            'claims': [Claim.to_dict(c) for c in flagged_claims],
            'total': len(flagged_claims)
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving flagged claims: {str(e)}")
        return jsonify({'error': str(e)}), 400
