"""
🏢 SUPER ADMIN ROUTES
Platform owner routes for managing insurance companies and platform-wide operations
"""

from flask import Blueprint, request, jsonify
from models.database_enterprise import enterprise_db
from utils.validators import validate_email
from werkzeug.security import generate_password_hash
from bson import ObjectId
from datetime import datetime, timedelta
import re

super_admin_bp = Blueprint('super_admin', __name__)


def verify_super_admin(user_email):
    """Verify if user is a super admin"""
    user = enterprise_db.get_user_by_email(user_email)
    return user and user.get('user_type') == 'super_admin'


@super_admin_bp.route('/create-company-admin', methods=['POST'])
def create_company_admin():
    """
    Super admin creates a company admin account
    
    Request Body:
    {
        "email": "admin@icici.com",
        "password": "SecurePass123",
        "name": "ICICI Admin",
        "company_name": "ICICI Lombard",
        "insurance_types": ["Health", "Vehicle", "Life"],
        "contact": "+91-9876543210",
        "created_by": "superadmin@claimlens.com"
    }
    """
    try:
        data = request.json
        
        # Verify super admin
        created_by = data.get('created_by')
        if not verify_super_admin(created_by):
            return jsonify({"error": "Unauthorized. Super admin access required"}), 403
        
        # Validate required fields
        required_fields = ['email', 'password', 'name', 'company_name', 'insurance_types']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({"error": "Invalid email format"}), 400
        
        # Check if user already exists
        existing_user = enterprise_db.get_user_by_email(data['email'])
        if existing_user:
            return jsonify({"error": "User with this email already exists"}), 400
        
        # Check if company already exists
        existing_company = enterprise_db.get_company_by_name(data['company_name'])
        if existing_company:
            # Use existing company
            company_id = existing_company['_id']
        else:
            # Create new company
            company_data = {
                "name": data['company_name'],
                "insurance_types": data['insurance_types'],
                "contact": data.get('contact', ''),
                "logo": data.get('logo', ''),
                "created_by": created_by
            }
            company_id = enterprise_db.create_company(company_data)
        
        # Create company admin user
        user_data = {
            "email": data['email'],
            "password": generate_password_hash(data['password']),
            "name": data['name'],
            "user_type": "company_admin",
            "company_id": company_id,
            "status": "active",  # Auto-approved by super admin
            "phone": data.get('contact', ''),
            "created_by": created_by
        }
        
        user_id = enterprise_db.create_user(user_data)
        
        return jsonify({
            "message": "Company admin created successfully",
            "user_id": user_id,
            "company_id": company_id,
            "email": data['email'],
            "company_name": data['company_name']
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@super_admin_bp.route('/approve-company/<company_id>', methods=['PUT'])
def approve_company(company_id):
    """
    Approve a company registration request
    """
    try:
        data = request.json
        super_admin_email = data.get('super_admin_email')
        
        if not verify_super_admin(super_admin_email):
            return jsonify({"error": "Unauthorized. Super admin access required"}), 403
        
        # Update company status
        company = enterprise_db.get_company_by_id(company_id)
        if not company:
            return jsonify({"error": "Company not found"}), 404
        
        success = enterprise_db.companies.update_one(
            {"_id": ObjectId(company_id)},
            {"$set": {"status": "active", "approved_by": super_admin_email}}
        )
        
        if success:
            # Also approve associated company admin
            enterprise_db.users.update_many(
                {"company_id": company_id, "user_type": "company_admin"},
                {"$set": {"status": "active"}}
            )
        
        return jsonify({
            "message": "Company approved successfully",
            "company_id": company_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@super_admin_bp.route('/companies', methods=['GET'])
def list_all_companies():
    """
    Get all companies with their statistics
    Query params: ?status=active|pending|inactive
    """
    try:
        super_admin_email = request.args.get('super_admin_email')
        
        if not verify_super_admin(super_admin_email):
            return jsonify({"error": "Unauthorized. Super admin access required"}), 403
        
        status = request.args.get('status')
        companies = enterprise_db.get_all_companies(status)
        
        # Add statistics for each company
        for company in companies:
            stats = enterprise_db.get_company_statistics(company['_id'])
            company['statistics'] = stats
        
        return jsonify({
            "companies": companies,
            "total": len(companies)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@super_admin_bp.route('/platform-stats', methods=['GET'])
def get_platform_statistics():
    """
    Get platform-wide statistics for super admin dashboard
    """
    try:
        super_admin_email = request.args.get('super_admin_email')
        
        if not verify_super_admin(super_admin_email):
            return jsonify({"error": "Unauthorized. Super admin access required"}), 403
        
        stats = enterprise_db.get_platform_statistics()
        
        # Get top performing companies
        companies = enterprise_db.get_all_companies("active")
        company_performance = []
        
        for company in companies[:10]:  # Top 10
            company_stats = enterprise_db.get_company_statistics(company['_id'])
            company_performance.append({
                "company_name": company['name'],
                "total_claims": company_stats['total_claims'],
                "fraud_prevented": company_stats['fraud_prevented_amount'],
                "approval_rate": round((company_stats['approved'] / company_stats['total_claims'] * 100) if company_stats['total_claims'] > 0 else 0, 2)
            })
        
        # Sort by fraud prevented
        company_performance.sort(key=lambda x: x['fraud_prevented'], reverse=True)
        
        return jsonify({
            "platform_stats": stats,
            "top_companies": company_performance,
            "generated_at": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@super_admin_bp.route('/pending-approvals', methods=['GET'])
def get_pending_approvals():
    """
    Get pending company admin approval requests
    """
    try:
        super_admin_email = request.args.get('super_admin_email')
        
        if not verify_super_admin(super_admin_email):
            return jsonify({"error": "Unauthorized. Super admin access required"}), 403
        
        pending_companies = enterprise_db.get_all_companies("pending")
        pending_admins = enterprise_db.get_pending_approvals("company_admin")
        
        return jsonify({
            "pending_companies": pending_companies,
            "pending_admins": pending_admins,
            "total_pending": len(pending_companies) + len(pending_admins)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@super_admin_bp.route('/company/<company_id>', methods=['DELETE'])
def deactivate_company(company_id):
    """
    Deactivate a company (soft delete)
    """
    try:
        data = request.json
        super_admin_email = data.get('super_admin_email')
        
        if not verify_super_admin(super_admin_email):
            return jsonify({"error": "Unauthorized. Super admin access required"}), 403
        
        # Update company status
        success = enterprise_db.companies.update_one(
            {"_id": ObjectId(company_id)},
            {"$set": {"status": "inactive", "deactivated_by": super_admin_email}}
        )
        
        if success:
            # Deactivate all users from this company
            enterprise_db.users.update_many(
                {"company_id": company_id},
                {"$set": {"status": "inactive"}}
            )
        
        return jsonify({
            "message": "Company deactivated successfully",
            "company_id": company_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@super_admin_bp.route('/users', methods=['GET'])
def get_all_users():
    """
    Get all users across platform
    Query params: ?user_type=company_admin|agent|customer
    """
    try:
        super_admin_email = request.args.get('super_admin_email')
        
        if not verify_super_admin(super_admin_email):
            return jsonify({"error": "Unauthorized. Super admin access required"}), 403
        
        user_type = request.args.get('user_type')
        
        if user_type:
            users = enterprise_db.get_users_by_type(user_type)
        else:
            users = list(enterprise_db.users.find({}).sort("created_at", -1))
            users = [enterprise_db.serialize_doc(u) for u in users]
        
        # Remove passwords
        for user in users:
            user.pop('password', None)
        
        return jsonify({
            "users": users,
            "total": len(users)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@super_admin_bp.route('/analytics/fraud-trends', methods=['GET'])
def get_fraud_trends():
    """
    Get fraud detection trends over time
    """
    try:
        super_admin_email = request.args.get('super_admin_email')
        
        if not verify_super_admin(super_admin_email):
            return jsonify({"error": "Unauthorized. Super admin access required"}), 403
        
        # Get last 30 days of claims
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": thirty_days_ago}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "total_claims": {"$sum": 1},
                    "high_risk": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$fraud_analysis.risk_level", "HIGH"]},
                                1,
                                0
                            ]
                        }
                    },
                    "medium_risk": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$fraud_analysis.risk_level", "MEDIUM"]},
                                1,
                                0
                            ]
                        }
                    },
                    "total_amount": {"$sum": "$claim_amount"}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        trends = list(enterprise_db.claims.aggregate(pipeline))
        
        return jsonify({
            "fraud_trends": trends,
            "period": "last_30_days"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
