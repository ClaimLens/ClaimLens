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


# ---------------------------------------------
# 📊 Admin Dashboard (High-Level Overview)
# ---------------------------------------------
@admin_bp.route('/dashboard', methods=['GET'])
@token_required
@admin_required
def get_dashboard(current_user):
    """Get admin dashboard with key metrics and priority claims"""
    try:
        # Get statistics
        stats = db.get_claim_statistics()
        
        # Get all claims for analysis
        all_claims = db.get_all_claims()
        
        # High priority claims (high fraud score or large amounts)
        high_priority = [
            c for c in all_claims 
            if c.get('ai_analysis', {}).get('xgboost_risk_level') == 'HIGH' 
            or c.get('amount', 0) > 500000
        ]
        high_priority.sort(key=lambda x: x.get('ai_analysis', {}).get('xgboost_fraud_score', 0), reverse=True)
        
        # Recent claims (last 10)
        recent_claims = sorted(
            all_claims, 
            key=lambda x: x.get('created_at', datetime.min), 
            reverse=True
        )[:10]
        
        # Claims by type
        claims_by_type = {
            'Health': len([c for c in all_claims if c.get('claim_type') == 'Health']),
            'Motor': len([c for c in all_claims if c.get('claim_type') == 'Motor']),
            'Property': len([c for c in all_claims if c.get('claim_type') == 'Property'])
        }
        
        # Average fraud score
        fraud_scores = [
            c.get('ai_analysis', {}).get('xgboost_fraud_score', 0) 
            for c in all_claims 
            if c.get('ai_analysis', {}).get('xgboost_fraud_score') is not None
        ]
        avg_fraud_score = sum(fraud_scores) / len(fraud_scores) if fraud_scores else 0
        
        # Claims needing attention
        needs_attention = len([c for c in all_claims if c.get('status') == 'under_review'])
        
        return jsonify({
            'statistics': stats,
            'high_priority_claims': [Claim.to_dict(c) for c in high_priority[:5]],
            'recent_claims': [Claim.to_dict(c) for c in recent_claims],
            'claims_by_type': claims_by_type,
            'average_fraud_score': round(avg_fraud_score, 2),
            'needs_attention': needs_attention,
            'status': 'success'
        }), 200
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return jsonify({'error': 'Failed to load dashboard', 'details': str(e)}), 500


# ---------------------------------------------
# ✅ Approve Claim
# ---------------------------------------------
@admin_bp.route('/claims/<claim_id>/approve', methods=['PUT'])
@token_required
@admin_required
def approve_claim(current_user, claim_id):
    """Approve a claim with approved amount"""
    try:
        data = request.get_json()
        approved_amount = data.get('approved_amount')
        admin_notes = data.get('admin_notes', '')
        
        if not approved_amount:
            return jsonify({'error': 'Approved amount is required'}), 400
        
        # Validate amount
        try:
            approved_amount = float(approved_amount)
            if approved_amount <= 0:
                return jsonify({'error': 'Approved amount must be positive'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid approved amount'}), 400
        
        # Check if claim exists
        claim = db.get_claim_by_id(claim_id)
        if not claim:
            return jsonify({'error': 'Claim not found'}), 404
        
        # Update claim
        update_data = {
            'status': 'approved',
            'approved_amount': approved_amount,
            'admin_notes': admin_notes,
            'approved_by': str(current_user['_id']),
            'approved_at': datetime.utcnow()
        }
        
        success = db.update_claim(claim_id, update_data)
        
        if not success:
            return jsonify({'error': 'Failed to update claim'}), 500
        
        return jsonify({
            'message': 'Claim approved successfully',
            'claim_id': claim_id,
            'approved_amount': approved_amount,
            'status': 'success'
        }), 200
        
    except Exception as e:
        logger.error(f"Error approving claim: {str(e)}")
        return jsonify({'error': 'Failed to approve claim', 'details': str(e)}), 500


# ---------------------------------------------
# ❌ Reject Claim
# ---------------------------------------------
@admin_bp.route('/claims/<claim_id>/reject', methods=['PUT'])
@token_required
@admin_required
def reject_claim(current_user, claim_id):
    """Reject a claim with reason"""
    try:
        data = request.get_json()
        rejection_reason = data.get('rejection_reason')
        admin_notes = data.get('admin_notes', '')
        
        if not rejection_reason:
            return jsonify({'error': 'Rejection reason is required'}), 400
        
        if len(rejection_reason) < 10:
            return jsonify({'error': 'Rejection reason must be at least 10 characters'}), 400
        
        # Check if claim exists
        claim = db.get_claim_by_id(claim_id)
        if not claim:
            return jsonify({'error': 'Claim not found'}), 404
        
        # Update claim
        update_data = {
            'status': 'rejected',
            'rejection_reason': rejection_reason,
            'admin_notes': admin_notes,
            'rejected_by': str(current_user['_id']),
            'rejected_at': datetime.utcnow(),
            'approved_amount': 0
        }
        
        success = db.update_claim(claim_id, update_data)
        
        if not success:
            return jsonify({'error': 'Failed to update claim'}), 500
        
        return jsonify({
            'message': 'Claim rejected successfully',
            'claim_id': claim_id,
            'rejection_reason': rejection_reason,
            'status': 'success'
        }), 200
        
    except Exception as e:
        logger.error(f"Error rejecting claim: {str(e)}")
        return jsonify({'error': 'Failed to reject claim', 'details': str(e)}), 500


# ---------------------------------------------
# 📊 Real-Time Dashboard Data
# ---------------------------------------------
@admin_bp.route('/realtime', methods=['GET'])
@token_required
@admin_required
def get_realtime_data(current_user):
    """Get real-time stats for live dashboard updates"""
    try:
        from datetime import timedelta
        
        # Get recent claims (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        all_claims = db.get_all_claims()
        recent_claims = [c for c in all_claims if c.get('created_at', datetime.min) > yesterday]
        
        # Claims processed in last hour
        last_hour = datetime.utcnow() - timedelta(hours=1)
        last_hour_claims = [c for c in all_claims if c.get('created_at', datetime.min) > last_hour]
        
        # High-risk claims needing immediate attention
        high_risk = [
            c for c in all_claims 
            if c.get('status') == 'under_review' 
            and c.get('ai_analysis', {}).get('xgboost_fraud_score', 0) >= 70
        ]
        
        # Calculate average processing time
        approved_with_times = [
            c for c in all_claims 
            if c.get('status') == 'approved' 
            and c.get('created_at') 
            and c.get('approved_at')
        ]
        
        avg_processing_minutes = 0
        if approved_with_times:
            total_seconds = sum(
                (c['approved_at'] - c['created_at']).total_seconds() 
                for c in approved_with_times
            )
            avg_processing_minutes = round(total_seconds / len(approved_with_times) / 60, 1)
        
        # Fraud detection stats
        total_fraud_caught = len([c for c in all_claims if c.get('status') == 'rejected'])
        fraud_amount_prevented = sum(
            c.get('amount', 0) for c in all_claims 
            if c.get('status') == 'rejected'
        )
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'realtime_stats': {
                'claims_last_24h': len(recent_claims),
                'claims_last_hour': len(last_hour_claims),
                'high_risk_pending': len(high_risk),
                'avg_processing_time_minutes': avg_processing_minutes,
                'fraud_caught_today': total_fraud_caught,
                'money_saved_today': fraud_amount_prevented
            },
            'recent_activity': [
                {
                    'claim_id': c.get('claim_id'),
                    'amount': c.get('amount'),
                    'status': c.get('status'),
                    'fraud_score': c.get('ai_analysis', {}).get('xgboost_fraud_score', 0),
                    'risk_level': c.get('ai_analysis', {}).get('xgboost_risk_level', 'UNKNOWN'),
                    'created_at': c.get('created_at').isoformat() if c.get('created_at') else None
                }
                for c in sorted(all_claims, key=lambda x: x.get('created_at', datetime.min), reverse=True)[:10]
            ],
            'urgent_claims': [
                {
                    'claim_id': c.get('claim_id'),
                    'amount': c.get('amount'),
                    'fraud_score': c.get('ai_analysis', {}).get('xgboost_fraud_score', 0),
                    'explanation': c.get('ai_analysis', {}).get('explanation', {}).get('explanation_text', 'No explanation available')
                }
                for c in sorted(high_risk, key=lambda x: x.get('ai_analysis', {}).get('xgboost_fraud_score', 0), reverse=True)[:5]
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Real-time data error: {e}")
        return jsonify({'error': 'Failed to fetch real-time data', 'details': str(e)}), 500


# ---------------------------------------------
# 💰 Cost Savings Calculator
# ---------------------------------------------
@admin_bp.route('/savings', methods=['GET'])
@token_required
@admin_required
def get_savings_calculator(current_user):
    """Calculate money saved through fraud prevention"""
    try:
        from datetime import timedelta
        
        all_claims = db.get_all_claims()
        
        # Time period filters
        period = request.args.get('period', 'all')  # all, month, week, today
        
        if period == 'today':
            cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0)
        elif period == 'week':
            cutoff = datetime.utcnow() - timedelta(days=7)
        elif period == 'month':
            cutoff = datetime.utcnow() - timedelta(days=30)
        else:
            cutoff = datetime.min
        
        filtered_claims = [c for c in all_claims if c.get('created_at', datetime.min) >= cutoff]
        
        # Calculate savings
        total_claims = len(filtered_claims)
        rejected_claims = [c for c in filtered_claims if c.get('status') == 'rejected']
        high_risk_prevented = [
            c for c in rejected_claims 
            if c.get('ai_analysis', {}).get('xgboost_fraud_score', 0) >= 70
        ]
        
        # Money saved
        total_fraud_prevented = sum(c.get('amount', 0) for c in rejected_claims)
        high_risk_amount = sum(c.get('amount', 0) for c in high_risk_prevented)
        
        # Approved claims
        approved_claims = [c for c in filtered_claims if c.get('status') == 'approved']
        total_approved_amount = sum(c.get('approved_amount', 0) for c in approved_claims)
        
        # Under review
        under_review = [c for c in filtered_claims if c.get('status') == 'under_review']
        under_review_amount = sum(c.get('amount', 0) for c in under_review)
        
        # Processing efficiency
        auto_approved = len([
            c for c in approved_claims 
            if c.get('ai_analysis', {}).get('xgboost_fraud_score', 0) < 30
        ])
        
        # Calculate ROI (assuming fraud detection costs ₹100/claim)
        detection_cost = total_claims * 100
        roi = ((total_fraud_prevented - detection_cost) / detection_cost * 100) if detection_cost > 0 else 0
        
        return jsonify({
            'status': 'success',
            'period': period,
            'savings': {
                'total_fraud_prevented': total_fraud_prevented,
                'high_risk_fraud_prevented': high_risk_amount,
                'total_claims_processed': total_claims,
                'fraud_claims_caught': len(rejected_claims),
                'fraud_catch_rate': round(len(rejected_claims) / total_claims * 100, 2) if total_claims > 0 else 0,
                'total_approved_amount': total_approved_amount,
                'amount_under_review': under_review_amount,
                'auto_approval_rate': round(auto_approved / len(approved_claims) * 100, 2) if approved_claims else 0,
                'detection_cost': detection_cost,
                'net_savings': total_fraud_prevented - detection_cost,
                'roi_percentage': round(roi, 2)
            },
            'breakdown': {
                'approved': len(approved_claims),
                'rejected': len(rejected_claims),
                'under_review': len(under_review),
                'high_risk_detected': len(high_risk_prevented)
            },
            'insights': [
                f"Saved ₹{total_fraud_prevented:,.0f} by preventing {len(rejected_claims)} fraudulent claims",
                f"{len(high_risk_prevented)} high-risk fraud attempts blocked (₹{high_risk_amount:,.0f})",
                f"{auto_approved} low-risk claims auto-approved, saving {auto_approved * 5} minutes of manual review",
                f"ROI: {round(roi, 1)}% - Every ₹1 spent saves ₹{round(total_fraud_prevented / detection_cost, 1) if detection_cost > 0 else 0}"
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Savings calculator error: {e}")
        return jsonify({'error': 'Failed to calculate savings', 'details': str(e)}), 500
