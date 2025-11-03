"""
🏢 COMPANY ADMIN ROUTES
Insurance company admin routes for managing agents and final claim approvals
"""

from flask import Blueprint, request, jsonify
from models.database_enterprise import enterprise_db, serialize_doc
from utils.validators import validate_email
from werkzeug.security import generate_password_hash
from bson import ObjectId
from datetime import datetime

company_admin_bp = Blueprint('company_admin', __name__)


def verify_company_admin(user_email, company_id=None):
    """Verify if user is a company admin"""
    user = enterprise_db.get_user_by_email(user_email)
    if not user or user.get('user_type') != 'company_admin':
        return False
    if company_id and user.get('company_id') != company_id:
        return False
    return True


def get_user_company_id(user_email):
    """Get company_id for a user"""
    user = enterprise_db.get_user_by_email(user_email)
    return user.get('company_id') if user else None


@company_admin_bp.route('/approve-agent', methods=['PUT'])
def approve_agent():
    """
    Company admin approves an agent registration
    
    Request Body:
    {
        "agent_email": "agent@icici.com",
        "company_admin_email": "admin@icici.com"
    }
    """
    try:
        data = request.json
        company_admin_email = data.get('company_admin_email')
        agent_email = data.get('agent_email')
        
        # Verify company admin
        company_id = get_user_company_id(company_admin_email)
        if not verify_company_admin(company_admin_email, company_id):
            return jsonify({"error": "Unauthorized. Company admin access required"}), 403
        
        # Get agent
        agent = enterprise_db.get_user_by_email(agent_email)
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        
        # Verify agent belongs to same company
        if agent.get('company_id') != company_id:
            return jsonify({"error": "Agent does not belong to your company"}), 403
        
        # Approve agent
        success = enterprise_db.update_user_status(agent_email, "active")
        
        if success:
            return jsonify({
                "message": "Agent approved successfully",
                "agent_email": agent_email,
                "status": "active"
            }), 200
        else:
            return jsonify({"error": "Failed to approve agent"}), 500
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@company_admin_bp.route('/agents', methods=['GET'])
def list_agents():
    """
    Get all agents for the company
    Query params: ?status=active|pending|inactive
    """
    try:
        company_admin_email = request.args.get('company_admin_email')
        
        # Verify company admin
        company_id = get_user_company_id(company_admin_email)
        if not verify_company_admin(company_admin_email, company_id):
            return jsonify({"error": "Unauthorized. Company admin access required"}), 403
        
        # Get agents
        agents = enterprise_db.get_users_by_type("agent", company_id)
        
        # Filter by status if provided
        status = request.args.get('status')
        if status:
            agents = [a for a in agents if a.get('status') == status]
        
        # Remove passwords
        for agent in agents:
            agent.pop('password', None)
        
        # Add agent statistics
        for agent in agents:
            agent_claims = enterprise_db.claims.count_documents({
                "agent_id": agent['email'],
                "workflow_status": {"$in": ["agent_review", "admin_review", "approved", "rejected"]}
            })
            agent['total_claims_handled'] = agent_claims
        
        return jsonify({
            "agents": agents,
            "total": len(agents)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@company_admin_bp.route('/claims', methods=['GET'])
def get_company_claims():
    """
    Get all claims for the company
    Query params: ?workflow_status=submitted|agent_review|admin_review|approved|rejected
    """
    try:
        company_admin_email = request.args.get('company_admin_email')
        
        # Verify company admin
        company_id = get_user_company_id(company_admin_email)
        if not verify_company_admin(company_admin_email, company_id):
            return jsonify({"error": "Unauthorized. Company admin access required"}), 403
        
        # Get workflow status filter
        workflow_status = request.args.get('workflow_status')
        
        if workflow_status:
            claims = enterprise_db.get_claims_by_workflow_status(workflow_status, company_id)
        else:
            claims = enterprise_db.get_all_claims({"company_id": company_id})
        
        return jsonify({
            "claims": claims,
            "total": len(claims)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@company_admin_bp.route('/claims/for-review', methods=['GET'])
def get_claims_for_admin_review():
    """
    Get claims forwarded by agents waiting for admin approval
    """
    try:
        company_admin_email = request.args.get('company_admin_email')
        
        # Verify company admin
        company_id = get_user_company_id(company_admin_email)
        if not verify_company_admin(company_admin_email, company_id):
            return jsonify({"error": "Unauthorized. Company admin access required"}), 403
        
        # Get claims forwarded by agents
        claims = enterprise_db.get_claims_for_admin_review(company_id)
        
        return jsonify({
            "claims": claims,
            "total": len(claims),
            "message": "Claims forwarded by agents for final approval"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@company_admin_bp.route('/claims/<claim_id>/approve', methods=['PUT'])
def approve_claim_final(claim_id):
    """
    Company admin final approval of claim
    
    Request Body:
    {
        "company_admin_email": "admin@icici.com",
        "sanction_amount": 45000,
        "admin_notes": "Claim verified and approved for full amount"
    }
    """
    try:
        data = request.json
        company_admin_email = data.get('company_admin_email')
        sanction_amount = data.get('sanction_amount')
        admin_notes = data.get('admin_notes', '')
        
        # Verify company admin
        company_id = get_user_company_id(company_admin_email)
        if not verify_company_admin(company_admin_email, company_id):
            return jsonify({"error": "Unauthorized. Company admin access required"}), 403
        
        # Validate sanction amount
        if not sanction_amount or sanction_amount <= 0:
            return jsonify({"error": "Invalid sanction amount"}), 400
        
        # Get claim
        claim = enterprise_db.get_claim_by_id(claim_id)
        if not claim:
            return jsonify({"error": "Claim not found"}), 404
        
        # Verify claim belongs to company
        if claim.get('company_id') != company_id:
            return jsonify({"error": "Claim does not belong to your company"}), 403
        
        # Approve claim
        success = enterprise_db.approve_claim_final(
            claim_id,
            company_admin_email,
            sanction_amount,
            admin_notes
        )
        
        if success:
            # Update company statistics
            enterprise_db.update_company_stats(company_id, {
                "last_claim_approved": datetime.utcnow()
            })
            
            # Create notification for customer
            enterprise_db.notifications.insert_one({
                "user_id": claim['user_id'],
                "claim_id": claim_id,
                "type": "claim_approved",
                "message": f"Your claim of ₹{sanction_amount:,.0f} has been approved!",
                "created_at": enterprise_db.datetime.utcnow(),
                "read": False
            })
            
            return jsonify({
                "message": "Claim approved successfully",
                "claim_id": claim_id,
                "sanction_amount": sanction_amount,
                "status": "approved"
            }), 200
        else:
            return jsonify({"error": "Failed to approve claim"}), 500
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@company_admin_bp.route('/claims/<claim_id>/reject', methods=['PUT'])
def reject_claim_final(claim_id):
    """
    Company admin final rejection of claim
    
    Request Body:
    {
        "company_admin_email": "admin@icici.com",
        "reason": "Insufficient documentation and high fraud score"
    }
    """
    try:
        data = request.json
        company_admin_email = data.get('company_admin_email')
        reason = data.get('reason', '')
        
        # Verify company admin
        company_id = get_user_company_id(company_admin_email)
        if not verify_company_admin(company_admin_email, company_id):
            return jsonify({"error": "Unauthorized. Company admin access required"}), 403
        
        # Validate reason
        if not reason or len(reason) < 10:
            return jsonify({"error": "Rejection reason must be at least 10 characters"}), 400
        
        # Get claim
        claim = enterprise_db.get_claim_by_id(claim_id)
        if not claim:
            return jsonify({"error": "Claim not found"}), 404
        
        # Verify claim belongs to company
        if claim.get('company_id') != company_id:
            return jsonify({"error": "Claim does not belong to your company"}), 403
        
        # Reject claim
        success = enterprise_db.reject_claim_final(
            claim_id,
            company_admin_email,
            reason
        )
        
        if success:
            # Update company fraud prevention stats
            fraud_amount = claim.get('claim_amount', 0)
            enterprise_db.companies.update_one(
                {"_id": ObjectId(company_id)},
                {"$inc": {"fraud_prevented_amount": fraud_amount}}
            )
            
            # Create notification for customer
            enterprise_db.notifications.insert_one({
                "user_id": claim['user_id'],
                "claim_id": claim_id,
                "type": "claim_rejected",
                "message": f"Your claim has been rejected. Reason: {reason}",
                "created_at": enterprise_db.datetime.utcnow(),
                "read": False
            })
            
            return jsonify({
                "message": "Claim rejected successfully",
                "claim_id": claim_id,
                "reason": reason,
                "status": "rejected"
            }), 200
        else:
            return jsonify({"error": "Failed to reject claim"}), 500
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@company_admin_bp.route('/dashboard', methods=['GET'])
def get_company_dashboard():
    """
    Get company admin dashboard statistics
    """
    try:
        company_admin_email = request.args.get('company_admin_email')
        
        # Verify company admin
        company_id = get_user_company_id(company_admin_email)
        if not verify_company_admin(company_admin_email, company_id):
            return jsonify({"error": "Unauthorized. Company admin access required"}), 403
        
        # Get company info
        company = enterprise_db.get_company_by_id(company_id)
        
        # Get statistics
        stats = enterprise_db.get_company_statistics(company_id)
        
        # Get pending agent approvals
        pending_agents = enterprise_db.get_users_by_type("agent", company_id)
        pending_agents = [a for a in pending_agents if a.get('status') == 'pending']
        
        # Get claims needing admin review
        claims_for_review = enterprise_db.get_claims_for_admin_review(company_id)
        
        # Get recent activity
        recent_claims = list(enterprise_db.claims.find({
            "company_id": company_id
        }).sort("created_at", -1).limit(10))
        recent_claims = [serialize_doc(c) for c in recent_claims]
        
        # Calculate ROI
        total_claim_amount = sum([c.get('claim_amount', 0) for c in recent_claims])
        fraud_prevented = stats['fraud_prevented_amount']
        roi_percentage = (fraud_prevented / total_claim_amount * 100) if total_claim_amount > 0 else 0
        
        return jsonify({
            "company": company,
            "statistics": stats,
            "pending_agent_approvals": len(pending_agents) if pending_agents else 0,
            "claims_for_review": len(claims_for_review) if claims_for_review else 0,
            "recent_claims": recent_claims,
            "roi": {
                "fraud_prevented": fraud_prevented,
                "total_processed": total_claim_amount,
                "savings_percentage": round(roi_percentage, 2)
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@company_admin_bp.route('/analytics', methods=['GET'])
def get_company_analytics():
    """
    Get detailed analytics for company
    """
    try:
        company_admin_email = request.args.get('company_admin_email')
        
        # Verify company admin
        company_id = get_user_company_id(company_admin_email)
        if not verify_company_admin(company_admin_email, company_id):
            return jsonify({"error": "Unauthorized. Company admin access required"}), 403
        
        # Get claims by insurance type
        pipeline = [
            {"$match": {"company_id": company_id}},
            {
                "$group": {
                    "_id": "$insurance_type",
                    "total": {"$sum": 1},
                    "approved": {
                        "$sum": {"$cond": [{"$eq": ["$final_status", "approved"]}, 1, 0]}
                    },
                    "rejected": {
                        "$sum": {"$cond": [{"$eq": ["$final_status", "rejected"]}, 1, 0]}
                    },
                    "total_amount": {"$sum": "$claim_amount"},
                    "avg_amount": {"$avg": "$claim_amount"}
                }
            }
        ]
        
        by_type = list(enterprise_db.claims.aggregate(pipeline))
        
        # Get agent performance
        agent_pipeline = [
            {"$match": {"company_id": company_id, "agent_id": {"$exists": True}}},
            {
                "$group": {
                    "_id": "$agent_id",
                    "claims_handled": {"$sum": 1},
                    "high_risk_caught": {
                        "$sum": {
                            "$cond": [
                                {"$in": ["$fraud_analysis.risk_level", ["HIGH", "MEDIUM"]]},
                                1,
                                0
                            ]
                        }
                    }
                }
            },
            {"$sort": {"claims_handled": -1}},
            {"$limit": 10}
        ]
        
        agent_performance = list(enterprise_db.claims.aggregate(agent_pipeline))
        
        return jsonify({
            "claims_by_type": by_type,
            "top_agents": agent_performance,
            "generated_at": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
