from flask import Blueprint, request, jsonify
from models.database import db
from models.claim import Claim
from routes.auth import token_required
from datetime import datetime, timedelta
from functools import wraps  # ✅ CRITICAL: Must be imported
import logging

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

# ---------------------------------------------
# 🔒 Admin Authentication Decorator (FIXED)
# ---------------------------------------------
def admin_required(f):
    """Decorator to ensure user is admin"""
    @wraps(f)  # ✅ CRITICAL FIX: ensures Flask routing context works
    def decorated_function(current_user, *args, **kwargs):
        if current_user.get('role') != 'admin':
            logger.warning(f"Non-admin access attempt by: {current_user.get('email')}")
            return jsonify({'error': 'Admin access required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated_function


# ---------------------------------------------
# 🧾 View All Claims
# ---------------------------------------------
@admin_bp.route('/claims', methods=['GET'])
@token_required
@admin_required
def get_all_claims(current_user):
    try:
        claims = list(db.claims.find({}))
        for claim in claims:
            claim['_id'] = str(claim['_id'])
        return jsonify(claims), 200
    except Exception as e:
        logger.error(f"Error fetching claims: {e}")
        return jsonify({'error': 'Failed to fetch claims'}), 500


# ---------------------------------------------
# 🔍 View a Specific Claim
# ---------------------------------------------
@admin_bp.route('/claims/<claim_id>', methods=['GET'])
@token_required
@admin_required
def get_claim(current_user, claim_id):
    try:
        claim = db.claims.find_one({'claim_id': claim_id})
        if not claim:
            return jsonify({'error': 'Claim not found'}), 404
        claim['_id'] = str(claim['_id'])
        return jsonify(claim), 200
    except Exception as e:
        logger.error(f"Error fetching claim: {e}")
        return jsonify({'error': 'Failed to fetch claim details'}), 500


# ---------------------------------------------
# ✏️ Update Claim Status
# ---------------------------------------------
@admin_bp.route('/claims/<claim_id>/status', methods=['PUT'])
@token_required
@admin_required
def update_claim_status(current_user, claim_id):
    try:
        data = request.get_json()
        new_status = data.get('status')

        if not new_status:
            return jsonify({'error': 'Status field is required'}), 400

        result = db.claims.update_one(
            {'claim_id': claim_id},
            {'$set': {
                'status': new_status,
                'approved_at': datetime.utcnow() if new_status == 'approved' else None
            }}
        )

        if result.modified_count == 0:
            return jsonify({'error': 'Claim not found or status unchanged'}), 404

        return jsonify({'message': f'Claim status updated to {new_status}'}), 200
    except Exception as e:
        logger.error(f"Error updating claim status: {e}")
        return jsonify({'error': 'Failed to update claim status'}), 500


# ---------------------------------------------
# 🧠 Analytics Dashboard
# ---------------------------------------------
@admin_bp.route('/analytics', methods=['GET'])
@token_required
@admin_required
def get_analytics(current_user):
    """Generate detailed admin analytics"""
    try:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Claims over time
        try:
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
        except Exception as e:
            logger.warning(f"Aggregation fallback triggered: {e}")
            from collections import defaultdict
            all_claims = db.get_all_claims() if hasattr(db, 'get_all_claims') else []
            filtered = [c for c in all_claims if c.get('created_at') and c['created_at'] >= thirty_days_ago]
            grouped = defaultdict(lambda: {'count': 0, 'total_amount': 0})
            for c in filtered:
                d = c['created_at'].strftime('%Y-%m-%d')
                grouped[d]['count'] += 1
                grouped[d]['total_amount'] += c.get('amount', 0)
            claims_over_time = [{'_id': k, **v} for k, v in sorted(grouped.items())]

        # Fraud distribution
        try:
            low_risk = db.claims.count_documents({'ai_analysis.risk_level': 'LOW'})
            medium_risk = db.claims.count_documents({'ai_analysis.risk_level': 'MEDIUM'})
            high_risk = db.claims.count_documents({'ai_analysis.risk_level': 'HIGH'})
        except Exception:
            all_claims = db.get_all_claims() if hasattr(db, 'get_all_claims') else []
            low_risk = sum(1 for c in all_claims if c.get('ai_analysis', {}).get('risk_level') == 'LOW')
            medium_risk = sum(1 for c in all_claims if c.get('ai_analysis', {}).get('risk_level') == 'MEDIUM')
            high_risk = sum(1 for c in all_claims if c.get('ai_analysis', {}).get('risk_level') == 'HIGH')

        # Average processing time
        try:
            approved_claims = list(db.claims.find({'status': 'approved'}))
        except Exception:
            approved_claims = db.get_all_claims() if hasattr(db, 'get_all_claims') else []
            approved_claims = [c for c in approved_claims if c.get('status') == 'approved']

        total_time = 0
        count = 0
        for c in approved_claims:
            if c.get('created_at') and c.get('approved_at'):
                total_time += (c['approved_at'] - c['created_at']).total_seconds()
                count += 1
        avg_processing_time = round(total_time / count / 3600, 2) if count else 0

        total_amount = sum(c.get('amount', 0) for c in approved_claims)

        return jsonify({
            'claims_over_time': claims_over_time,
            'fraud_distribution': {
                'low': low_risk,
                'medium': medium_risk,
                'high': high_risk
            },
            'average_processing_time_hours': avg_processing_time,
            'total_claims_amount': total_amount,
            'claims_processed': count
        }), 200

    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return jsonify({
            'error': 'Failed to generate analytics',
            'claims_over_time': [],
            'fraud_distribution': {'low': 0, 'medium': 0, 'high': 0},
            'average_processing_time_hours': 0,
            'total_claims_amount': 0
        }), 200


# ---------------------------------------------
# 👥 View All Users
# ---------------------------------------------
@admin_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_all_users(current_user):
    try:
        users = list(db.users.find({}, {'password': 0}))
        for u in users:
            u['_id'] = str(u['_id'])
        return jsonify(users), 200
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return jsonify({'error': 'Failed to fetch users'}), 500
