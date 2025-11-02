from flask import Blueprint, request, jsonify
from models.database import db
from models.claim import Claim
from routes.auth import token_required
from datetime import datetime
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to ensure user is admin"""
    @wraps(f)  # THIS IS CRITICAL
    def decorated_function(current_user, *args, **kwargs):
        if current_user['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated_function


@admin_bp.route('/claims', methods=['GET'])
@token_required
@admin_required
def get_all_claims(current_user):
    """Get all claims with filters"""
    try:
        # Get query parameters
        status = request.args.get('status')
        risk_level = request.args.get('risk_level')
        claim_type = request.args.get('claim_type')
        sort_by = request.args.get('sort_by', 'created_at')
        order = request.args.get('order', 'desc')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Build filter query
        filters = {}
        if status:
            filters['status'] = status
        if risk_level:
            filters['ai_analysis.risk_level'] = risk_level.upper()
        if claim_type:
            filters['claim_type'] = claim_type
        
        # Get claims
        claims = db.get_all_claims(filters)
        
        # Sort
        reverse = (order == 'desc')
        claims.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse)
        
        # Paginate
        start = (page - 1) * per_page
        end = start + per_page
        paginated_claims = claims[start:end]
        
        # Convert to safe dict
        claims_list = [Claim.to_dict(claim) for claim in paginated_claims]
        
        return jsonify({
            'claims': claims_list,
            'total': len(claims),
            'page': page,
            'per_page': per_page,
            'total_pages': (len(claims) + per_page - 1) // per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/claims/<claim_id>/approve', methods=['PUT'])
@token_required
@admin_required
def approve_claim(current_user, claim_id):
    """Approve a claim"""
    try:
        data = request.json
        approved_amount = data.get('approved_amount')
        admin_notes = data.get('admin_notes', '')
        
        claim = db.get_claim_by_id(claim_id)
        
        if not claim:
            return jsonify({'error': 'Claim not found'}), 404
        
        # Use claimed amount if approved amount not provided
        if not approved_amount:
            approved_amount = claim.get('amount', 0)
        
        update_data = {
            'status': 'approved',
            'approved_amount': approved_amount,
            'admin_notes': admin_notes,
            'approved_by': str(current_user['_id']),
            'approved_at': datetime.utcnow()
        }
        
        success = db.update_claim(claim_id, update_data)
        
        if success:
            # TODO: Send notification to user
            return jsonify({
                'message': 'Claim approved successfully',
                'claim_id': claim_id,
                'approved_amount': approved_amount
            }), 200
        else:
            return jsonify({'error': 'Failed to update claim'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/claims/<claim_id>/reject', methods=['PUT'])
@token_required
@admin_required
def reject_claim(current_user, claim_id):
    """Reject a claim"""
    try:
        data = request.json
        rejection_reason = data.get('rejection_reason')
        admin_notes = data.get('admin_notes', '')
        
        if not rejection_reason:
            return jsonify({'error': 'Rejection reason is required'}), 400
        
        claim = db.get_claim_by_id(claim_id)
        
        if not claim:
            return jsonify({'error': 'Claim not found'}), 404
        
        update_data = {
            'status': 'rejected',
            'rejection_reason': rejection_reason,
            'admin_notes': admin_notes,
            'rejected_by': str(current_user['_id']),
            'rejected_at': datetime.utcnow()
        }
        
        success = db.update_claim(claim_id, update_data)
        
        if success:
            # TODO: Send notification to user
            return jsonify({
                'message': 'Claim rejected',
                'claim_id': claim_id
            }), 200
        else:
            return jsonify({'error': 'Failed to update claim'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/claims/<claim_id>/review', methods=['PUT'])
@token_required
@admin_required
def mark_under_review(current_user, claim_id):
    """Mark claim as under review"""
    try:
        data = request.json
        admin_notes = data.get('admin_notes', '')
        
        claim = db.get_claim_by_id(claim_id)
        
        if not claim:
            return jsonify({'error': 'Claim not found'}), 404
        
        update_data = {
            'status': 'under_review',
            'admin_notes': admin_notes,
            'reviewer': str(current_user['_id']),
            'review_started_at': datetime.utcnow()
        }
        
        success = db.update_claim(claim_id, update_data)
        
        if success:
            return jsonify({
                'message': 'Claim marked for review',
                'claim_id': claim_id
            }), 200
        else:
            return jsonify({'error': 'Failed to update claim'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/claims/<claim_id>/request-info', methods=['PUT'])
@token_required
@admin_required
def request_additional_info(current_user, claim_id):
    """Request additional information from user"""
    try:
        data = request.json
        requested_info = data.get('requested_info')
        admin_notes = data.get('admin_notes', '')
        
        if not requested_info:
            return jsonify({'error': 'Requested information details required'}), 400
        
        claim = db.get_claim_by_id(claim_id)
        
        if not claim:
            return jsonify({'error': 'Claim not found'}), 404
        
        update_data = {
            'status': 'info_requested',
            'requested_info': requested_info,
            'admin_notes': admin_notes,
            'info_requested_by': str(current_user['_id']),
            'info_requested_at': datetime.utcnow()
        }
        
        success = db.update_claim(claim_id, update_data)
        
        if success:
            # TODO: Send notification to user
            return jsonify({
                'message': 'Additional information requested',
                'claim_id': claim_id
            }), 200
        else:
            return jsonify({'error': 'Failed to update claim'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/dashboard', methods=['GET'])
@token_required
@admin_required
def admin_dashboard(current_user):
    """Get admin dashboard statistics"""
    try:
        # Basic stats
        stats = db.get_claim_statistics()
        
        # High priority claims (high risk + pending)
        high_priority = list(db.claims.find({
            'ai_analysis.risk_level': 'HIGH',
            'status': {'$in': ['pending', 'under_review']}
        }).limit(10))
        
        # Recent claims
        recent_claims = list(db.claims.find().sort('created_at', -1).limit(10))
        
        # Claims by type
        health_claims = db.claims.count_documents({'claim_type': 'Health'})
        motor_claims = db.claims.count_documents({'claim_type': 'Motor'})
        property_claims = db.claims.count_documents({'claim_type': 'Property'})
        
        # Average fraud score
        pipeline = [
            {'$group': {
                '_id': None,
                'avg_fraud_score': {'$avg': '$ai_analysis.fraud_score'}
            }}
        ]
        avg_result = list(db.claims.aggregate(pipeline))
        avg_fraud_score = avg_result[0]['avg_fraud_score'] if avg_result else 0
        
        # Claims needing attention
        needs_attention = db.claims.count_documents({
            '$or': [
                {'ai_analysis.requires_manual_review': True},
                {'status': 'under_review'},
                {'ai_analysis.fraud_score': {'$gte': 70}}
            ]
        })
        
        return jsonify({
            'statistics': stats,
            'high_priority_claims': [Claim.to_dict(c) for c in high_priority],
            'recent_claims': [Claim.to_dict(c) for c in recent_claims],
            'claims_by_type': {
                'Health': health_claims,
                'Motor': motor_claims,
                'Property': property_claims
            },
            'average_fraud_score': round(avg_fraud_score, 2),
            'needs_attention': needs_attention
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_all_users(current_user):
    """Get all users (admin only)"""
    try:
        users = list(db.users.find())
        
        # Remove passwords
        from models.user import User
        users_list = [User.to_dict(user) for user in users]
        
        return jsonify({
            'users': users_list,
            'total': len(users_list)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/analytics', methods=['GET'])
@token_required
@admin_required
def get_analytics(current_user):
    """Get detailed analytics"""
    try:
        # Claims over time (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        pipeline = [
            {'$match': {'created_at': {'$gte': thirty_days_ago}}},
            {'$group': {
                '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$created_at'}},
                'count': {'$sum': 1},
                'total_amount': {'$sum': '$amount'}
            }},
            {'$sort': {'_id': 1}}
        ]
        
        claims_over_time = list(db.claims.aggregate(pipeline))
        
        # Fraud distribution
        low_risk = db.claims.count_documents({'ai_analysis.risk_level': 'LOW'})
        medium_risk = db.claims.count_documents({'ai_analysis.risk_level': 'MEDIUM'})
        high_risk = db.claims.count_documents({'ai_analysis.risk_level': 'HIGH'})
        
        # Average processing time (approved claims only)
        approved_claims = list(db.claims.find({'status': 'approved'}))
        
        total_processing_time = 0
        for claim in approved_claims:
            if claim.get('approved_at') and claim.get('created_at'):
                delta = claim['approved_at'] - claim['created_at']
                total_processing_time += delta.total_seconds()
        
        avg_processing_time = (total_processing_time / len(approved_claims)) if approved_claims else 0
        avg_processing_hours = round(avg_processing_time / 3600, 2)
        
        return jsonify({
            'claims_over_time': claims_over_time,
            'fraud_distribution': {
                'low': low_risk,
                'medium': medium_risk,
                'high': high_risk
            },
            'average_processing_time_hours': avg_processing_hours,
            'total_claims_amount': sum([c.get('amount', 0) for c in approved_claims])
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
