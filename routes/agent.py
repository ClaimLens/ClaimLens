"""
👮 INSURANCE AGENT ROUTES
Insurance agent routes for verifying claims using AI fraud detection
"""

from flask import Blueprint, request, jsonify
from models.database_enterprise import enterprise_db, serialize_doc
# from services.xgboost_fraud_detector import detector as fraud_detector  # Temporarily disabled
from services.fraud_detector import fraud_detector  # Using regular fraud detector instead
from services.explainable_ai import explainable_ai
from datetime import datetime

agent_bp = Blueprint('agent', __name__)


def verify_agent(user_email, company_id=None):
    """Verify if user is an agent"""
    user = enterprise_db.get_user_by_email(user_email)
    if not user or user.get('user_type') != 'agent':
        return False
    if user.get('status') != 'active':
        return False
    if company_id and user.get('company_id') != company_id:
        return False
    return True


def get_user_company_id(user_email):
    """Get company_id for a user"""
    user = enterprise_db.get_user_by_email(user_email)
    return user.get('company_id') if user else None


@agent_bp.route('/pending-claims', methods=['GET'])
def get_pending_claims():
    """
    Get claims waiting for agent review
    Query params: ?agent_email=agent@icici.com
    """
    try:
        agent_email = request.args.get('agent_email')
        
        # Verify agent
        company_id = get_user_company_id(agent_email)
        if not verify_agent(agent_email, company_id):
            return jsonify({"error": "Unauthorized. Active agent access required"}), 403
        
        # Get pending claims for this company
        claims = enterprise_db.get_pending_claims_for_agent(company_id)
        
        return jsonify({
            "pending_claims": claims if claims else [],
            "total": len(claims) if claims else 0,
            "message": "Claims waiting for your review"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/claims/<claim_id>', methods=['GET'])
def get_claim_details(claim_id):
    """
    Get detailed claim information for review
    """
    try:
        agent_email = request.args.get('agent_email')
        
        # Verify agent
        company_id = get_user_company_id(agent_email)
        if not verify_agent(agent_email, company_id):
            return jsonify({"error": "Unauthorized. Active agent access required"}), 403
        
        # Get claim
        claim = enterprise_db.get_claim_by_id(claim_id)
        if not claim:
            return jsonify({"error": "Claim not found"}), 404
        
        # Verify claim belongs to agent's company
        if claim.get('company_id') != company_id:
            return jsonify({"error": "Claim does not belong to your company"}), 403
        
        return jsonify({
            "claim": claim,
            "customer_history": enterprise_db.get_claims_by_user(claim['user_id'])
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/claims/<claim_id>/verify', methods=['POST'])
def verify_claim_with_fraud_detection(claim_id):
    """
    Verify claim using AI fraud detection
    
    Request Body:
    {
        "agent_email": "agent@icici.com"
    }
    """
    try:
        data = request.json
        agent_email = data.get('agent_email')
        
        # Verify agent
        company_id = get_user_company_id(agent_email)
        if not verify_agent(agent_email, company_id):
            return jsonify({"error": "Unauthorized. Active agent access required"}), 403
        
        # Get claim
        claim = enterprise_db.get_claim_by_id(claim_id)
        if not claim:
            return jsonify({"error": "Claim not found"}), 404
        
        # Verify claim belongs to agent's company
        if claim.get('company_id') != company_id:
            return jsonify({"error": "Claim does not belong to your company"}), 403
        
        # Run fraud detection if not already done
        if not claim.get('fraud_analysis'):
            # Extract features
            features = {
                "age": claim.get('age', 0),
                "claim_amount": claim.get('claim_amount', 0),
                "policy_duration": claim.get('policy_duration', 0)
            }
            
            # Run XGBoost fraud detection
            insurance_type = claim.get('insurance_type', 'health').lower()
            if insurance_type == 'motor':
                insurance_type = 'vehicle'
            
            fraud_result = fraud_detector.detect_fraud(features, insurance_type)
            
            # Generate explanation
            explanation = explainable_ai.explain_fraud_decision(
                fraud_score=fraud_result['fraud_score'],
                claim_data=claim,
                user_history=[],  # Would fetch in production
                document_analysis=claim.get('ai_analysis', {})
            )
            
            # Update claim with fraud analysis
            enterprise_db.claims.update_one(
                {"claim_id": claim_id},
                {"$set": {
                    "fraud_analysis": {
                        "xgboost_result": fraud_result,
                        "explanation": explanation,
                        "analyzed_by": "agent",
                        "analyzed_at": datetime.utcnow()
                    }
                }}
            )
            
            # Refresh claim data
            claim = enterprise_db.get_claim_by_id(claim_id)
        
        # Assign claim to agent
        enterprise_db.assign_claim_to_agent(claim_id, agent_email)
        
        return jsonify({
            "message": "Claim analyzed successfully",
            "claim_id": claim_id,
            "fraud_analysis": claim.get('fraud_analysis'),
            "recommendation": "Review the fraud analysis and take action"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/claims/<claim_id>/approve', methods=['POST'])
def agent_approve_claim(claim_id):
    """
    Agent approves claim and forwards to company admin
    
    Request Body:
    {
        "agent_email": "agent@icici.com",
        "notes": "Documents verified, low fraud risk, recommend approval"
    }
    """
    try:
        data = request.json
        agent_email = data.get('agent_email')
        notes = data.get('notes', '')
        
        # Verify agent
        company_id = get_user_company_id(agent_email)
        if not verify_agent(agent_email, company_id):
            return jsonify({"error": "Unauthorized. Active agent access required"}), 403
        
        # Get claim
        claim = enterprise_db.get_claim_by_id(claim_id)
        if not claim:
            return jsonify({"error": "Claim not found"}), 404
        
        # Verify claim belongs to agent's company
        if claim.get('company_id') != company_id:
            return jsonify({"error": "Claim does not belong to your company"}), 403
        
        # Validate notes
        if not notes or len(notes) < 10:
            return jsonify({"error": "Agent notes must be at least 10 characters"}), 400
        
        # Update claim workflow - forward to admin
        success = enterprise_db.update_claim_workflow(
            claim_id,
            "admin_review",
            agent_email,
            notes=notes,
            fraud_analysis=claim.get('fraud_analysis')
        )
        
        if success:
            # Create notification for company admin
            # Get company admins
            company_admins = enterprise_db.get_users_by_type("company_admin", company_id)
            for admin in company_admins:
                enterprise_db.notifications.insert_one({
                    "user_id": admin['email'],
                    "claim_id": claim_id,
                    "type": "claim_forwarded",
                    "message": f"Agent {agent_email} forwarded claim {claim_id} for your approval",
                    "created_at": datetime.utcnow(),
                    "read": False
                })
            
            return jsonify({
                "message": "Claim approved and forwarded to company admin",
                "claim_id": claim_id,
                "workflow_status": "admin_review"
            }), 200
        else:
            return jsonify({"error": "Failed to update claim"}), 500
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/claims/<claim_id>/reject', methods=['POST'])
def agent_reject_claim(claim_id):
    """
    Agent rejects claim (for obvious fraud cases)
    
    Request Body:
    {
        "agent_email": "agent@icici.com",
        "reason": "Fraudulent documents detected, high fraud score"
    }
    """
    try:
        data = request.json
        agent_email = data.get('agent_email')
        reason = data.get('reason', '')
        
        # Verify agent
        company_id = get_user_company_id(agent_email)
        if not verify_agent(agent_email, company_id):
            return jsonify({"error": "Unauthorized. Active agent access required"}), 403
        
        # Get claim
        claim = enterprise_db.get_claim_by_id(claim_id)
        if not claim:
            return jsonify({"error": "Claim not found"}), 404
        
        # Verify claim belongs to agent's company
        if claim.get('company_id') != company_id:
            return jsonify({"error": "Claim does not belong to your company"}), 403
        
        # Validate reason
        if not reason or len(reason) < 10:
            return jsonify({"error": "Rejection reason must be at least 10 characters"}), 400
        
        # Update claim workflow - reject
        success = enterprise_db.update_claim_workflow(
            claim_id,
            "rejected",
            agent_email,
            notes=reason
        )
        
        if success:
            # Save fraud pattern for learning
            fraud_pattern = {
                "claim_id": claim_id,
                "fraud_score": claim.get('fraud_analysis', {}).get('xgboost_result', {}).get('fraud_score', 0),
                "claim_amount": claim.get('claim_amount', 0),
                "insurance_type": claim.get('insurance_type'),
                "rejected_by": "agent",
                "reason": reason,
                "features": {
                    "age": claim.get('age'),
                    "policy_duration": claim.get('policy_duration')
                }
            }
            enterprise_db.save_fraud_pattern(claim_id, fraud_pattern)
            
            # Create notification for customer
            enterprise_db.notifications.insert_one({
                "user_id": claim['user_id'],
                "claim_id": claim_id,
                "type": "claim_rejected",
                "message": f"Your claim has been rejected. Reason: {reason}",
                "created_at": datetime.utcnow(),
                "read": False
            })
            
            return jsonify({
                "message": "Claim rejected successfully",
                "claim_id": claim_id,
                "workflow_status": "rejected"
            }), 200
        else:
            return jsonify({"error": "Failed to reject claim"}), 500
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/claims/<claim_id>/request-info', methods=['POST'])
def request_additional_info(claim_id):
    """
    Agent requests additional information from customer
    
    Request Body:
    {
        "agent_email": "agent@icici.com",
        "message": "Please provide hospital discharge summary"
    }
    """
    try:
        data = request.json
        agent_email = data.get('agent_email')
        message = data.get('message', '')
        
        # Verify agent
        company_id = get_user_company_id(agent_email)
        if not verify_agent(agent_email, company_id):
            return jsonify({"error": "Unauthorized. Active agent access required"}), 403
        
        # Get claim
        claim = enterprise_db.get_claim_by_id(claim_id)
        if not claim:
            return jsonify({"error": "Claim not found"}), 404
        
        # Verify claim belongs to agent's company
        if claim.get('company_id') != company_id:
            return jsonify({"error": "Claim does not belong to your company"}), 403
        
        # Update claim workflow
        success = enterprise_db.update_claim_workflow(
            claim_id,
            "info_requested",
            agent_email,
            notes=message
        )
        
        if success:
            # Create notification for customer
            enterprise_db.notifications.insert_one({
                "user_id": claim['user_id'],
                "claim_id": claim_id,
                "type": "info_requested",
                "message": f"Agent requested: {message}",
                "created_at": datetime.utcnow(),
                "read": False
            })
            
            return jsonify({
                "message": "Information request sent to customer",
                "claim_id": claim_id
            }), 200
        else:
            return jsonify({"error": "Failed to send request"}), 500
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/dashboard', methods=['GET'])
def get_agent_dashboard():
    """
    Get agent dashboard statistics
    """
    try:
        agent_email = request.args.get('agent_email')
        
        # Verify agent
        company_id = get_user_company_id(agent_email)
        if not verify_agent(agent_email, company_id):
            return jsonify({"error": "Unauthorized. Active agent access required"}), 403
        
        # Get pending claims
        pending = enterprise_db.get_pending_claims_for_agent(company_id)
        
        # Get agent's handled claims
        my_claims = list(enterprise_db.claims.find({
            "agent_id": agent_email
        }).sort("created_at", -1))
        my_claims = [serialize_doc(c) for c in my_claims]
        
        # Calculate statistics
        total_handled = len(my_claims)
        approved_count = len([c for c in my_claims if c.get('workflow_status') == 'approved'])
        rejected_count = len([c for c in my_claims if c.get('workflow_status') == 'rejected'])
        forwarded_count = len([c for c in my_claims if c.get('workflow_status') == 'admin_review'])
        
        # Fraud detection stats
        high_risk_caught = len([
            c for c in my_claims 
            if c.get('fraud_analysis', {}).get('xgboost_result', {}).get('risk_level') in ['HIGH', 'MEDIUM']
        ])
        
        return jsonify({
            "pending_claims": len(pending) if pending else 0,
            "total_claims_handled": total_handled,
            "approved": approved_count,
            "rejected": rejected_count,
            "forwarded_to_admin": forwarded_count,
            "high_risk_caught": high_risk_caught,
            "recent_claims": my_claims[:10]
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
