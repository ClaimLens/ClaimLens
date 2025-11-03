from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime, timedelta
from bson import ObjectId
from dotenv import load_dotenv
import os
import logging

# Make datetime accessible as class attribute
import datetime as dt_module

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def serialize_doc(doc):
    """Convert MongoDB ObjectId to string for JSON compatibility."""
    if not doc:
        return None
    if isinstance(doc, list):
        return [serialize_doc(d) for d in doc]
    doc['_id'] = str(doc['_id'])
    return doc


class EnterpriseDatabase:
    """
    🏢 ENTERPRISE-GRADE MULTI-TENANT DATABASE
    
    4-Tier User System:
    1. Super Admin (Platform Owner)
    2. Company Admin (Insurance Companies)
    3. Insurance Agent (Company Employees)
    4. Customer (End Users)
    """
    
    def __init__(self):
        try:
            # Get MongoDB connection URI from .env
            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                raise ValueError("MONGO_URI not found in environment variables")

            # Connect to MongoDB (with timeout)
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            self.client.server_info()  # Forces connection check

            # Use or create the database
            self.db = self.client["insurance_claims_enterprise"]

            # Define collections
            self.users = self.db["users"]
            self.companies = self.db["companies"]
            self.claims = self.db["claims"]
            self.notifications = self.db["notifications"]
            self.gamification = self.db["gamification"]
            self.fraud_patterns = self.db["fraud_patterns"]

            # Create indexes
            self._create_indexes()

            logging.info("✅ Connected to ENTERPRISE MongoDB successfully!")

        except Exception as e:
            logging.error(f"❌ MongoDB connection failed: {e}")
            raise

    def _create_indexes(self):
        """Create indexes for optimal performance"""
        # User indexes
        self.users.create_index("email", unique=True)
        self.users.create_index("user_type")
        self.users.create_index("company_id")
        self.users.create_index([("company_id", ASCENDING), ("user_type", ASCENDING)])
        
        # Company indexes
        self.companies.create_index("name", unique=True)
        self.companies.create_index("status")
        self.companies.create_index("created_by")
        
        # Claim indexes
        self.claims.create_index("claim_id", unique=True)
        self.claims.create_index("user_id")
        self.claims.create_index("company_id")
        self.claims.create_index("agent_id")
        self.claims.create_index("workflow_status")
        self.claims.create_index([("company_id", ASCENDING), ("workflow_status", ASCENDING)])
        self.claims.create_index([("created_at", DESCENDING)])
        
        # Gamification indexes
        self.gamification.create_index("user_id", unique=True)
        self.gamification.create_index("honesty_score")

    # ==================== USER OPERATIONS ====================

    def create_user(self, user_data):
        """
        Create user with role-based fields
        user_type: 'super_admin' | 'company_admin' | 'agent' | 'customer'
        """
        user_data["created_at"] = datetime.utcnow()
        
        # Initialize role-specific fields
        if user_data.get("user_type") == "customer":
            # Create gamification profile
            self.gamification.insert_one({
                "user_id": user_data["email"],
                "claim_streak": 0,
                "honesty_score": 100,
                "total_claims": 0,
                "approved_claims": 0,
                "badges": ["🎉 New User"],
                "discount_eligibility": 0,
                "created_at": datetime.utcnow()
            })
        
        result = self.users.insert_one(user_data)
        return str(result.inserted_id)

    def get_user_by_email(self, email):
        user = self.users.find_one({"email": email})
        return serialize_doc(user)

    def get_users_by_type(self, user_type, company_id=None):
        """Get all users of a specific type"""
        query = {"user_type": user_type}
        if company_id:
            query["company_id"] = company_id
        users = list(self.users.find(query).sort("created_at", -1))
        return serialize_doc(users)

    def update_user_status(self, email, status):
        """Update user approval status"""
        result = self.users.update_one(
            {"email": email},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def get_pending_approvals(self, user_type):
        """Get users pending approval"""
        users = list(self.users.find({
            "user_type": user_type,
            "status": "pending"
        }).sort("created_at", -1))
        return serialize_doc(users)

    # ==================== COMPANY OPERATIONS ====================

    def create_company(self, company_data):
        """
        Create insurance company
        Fields: name, insurance_types[], logo, contact, created_by (super_admin_email)
        """
        company_data["status"] = "active"
        company_data["created_at"] = datetime.utcnow()
        company_data["total_claims"] = 0
        company_data["fraud_prevented_amount"] = 0
        
        result = self.companies.insert_one(company_data)
        return str(result.inserted_id)

    def get_company_by_id(self, company_id):
        company = self.companies.find_one({"_id": ObjectId(company_id)})
        return serialize_doc(company)

    def get_company_by_name(self, name):
        company = self.companies.find_one({"name": name})
        return serialize_doc(company)

    def get_all_companies(self, status=None):
        query = {}
        if status:
            query["status"] = status
        companies = list(self.companies.find(query).sort("created_at", -1))
        return serialize_doc(companies)

    def update_company_stats(self, company_id, stats):
        """Update company statistics"""
        result = self.companies.update_one(
            {"_id": ObjectId(company_id)},
            {"$set": stats, "$inc": {"total_claims": 1}}
        )
        return result.modified_count > 0

    # ==================== CLAIM OPERATIONS ====================

    def create_claim(self, claim_data):
        """
        Create claim with workflow tracking
        workflow_status: 'submitted' -> 'agent_review' -> 'admin_review' -> 'approved'/'rejected'
        """
        claim_data["created_at"] = datetime.utcnow()
        claim_data["workflow_status"] = "submitted"
        claim_data["workflow_history"] = [{
            "status": "submitted",
            "timestamp": datetime.utcnow(),
            "by": claim_data.get("user_id", "system")
        }]
        
        result = self.claims.insert_one(claim_data)
        
        # Update user gamification
        self._update_user_gamification(claim_data["user_id"], "claim_submitted")
        
        return str(result.inserted_id)

    def get_claim_by_id(self, claim_id):
        claim = self.claims.find_one({"claim_id": claim_id})
        return serialize_doc(claim)

    def get_claims_by_user(self, user_id):
        claims = list(self.claims.find({"user_id": user_id}).sort("created_at", -1))
        return serialize_doc(claims)

    def get_claims_by_workflow_status(self, workflow_status, company_id=None, agent_id=None):
        """Get claims by workflow status"""
        query = {"workflow_status": workflow_status}
        if company_id:
            query["company_id"] = company_id
        if agent_id:
            query["agent_id"] = agent_id
        
        claims = list(self.claims.find(query).sort("created_at", -1))
        return serialize_doc(claims)

    def get_pending_claims_for_agent(self, company_id):
        """Get claims waiting for agent review"""
        claims = list(self.claims.find({
            "company_id": company_id,
            "workflow_status": "submitted"
        }).sort("created_at", -1))
        return serialize_doc(claims)

    def get_claims_for_admin_review(self, company_id):
        """Get claims forwarded by agents"""
        claims = list(self.claims.find({
            "company_id": company_id,
            "workflow_status": "admin_review"
        }).sort("created_at", -1))
        return serialize_doc(claims)

    def update_claim_workflow(self, claim_id, workflow_status, updated_by, notes=None, fraud_analysis=None):
        """Update claim workflow status with history tracking"""
        workflow_entry = {
            "status": workflow_status,
            "timestamp": datetime.utcnow(),
            "by": updated_by
        }
        
        if notes:
            workflow_entry["notes"] = notes
        if fraud_analysis:
            workflow_entry["fraud_analysis"] = fraud_analysis
        
        update_data = {
            "workflow_status": workflow_status,
            "updated_at": datetime.utcnow(),
            "$push": {"workflow_history": workflow_entry}
        }
        
        if notes:
            update_data["agent_notes"] = notes
        if fraud_analysis:
            update_data["fraud_analysis"] = fraud_analysis
        
        result = self.claims.update_one(
            {"claim_id": claim_id},
            {"$set": {k: v for k, v in update_data.items() if k != "$push"},
             "$push": update_data.get("$push", {})}
        )
        return result.modified_count > 0

    def approve_claim_final(self, claim_id, approved_by, sanction_amount, admin_notes):
        """Final approval by company admin"""
        update_data = {
            "workflow_status": "approved",
            "final_status": "approved",
            "approved_by": approved_by,
            "sanction_amount": sanction_amount,
            "admin_notes": admin_notes,
            "approved_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        workflow_entry = {
            "status": "approved",
            "timestamp": datetime.utcnow(),
            "by": approved_by,
            "sanction_amount": sanction_amount,
            "notes": admin_notes
        }
        
        result = self.claims.update_one(
            {"claim_id": claim_id},
            {"$set": update_data, "$push": {"workflow_history": workflow_entry}}
        )
        
        if result.modified_count > 0:
            # Update user gamification
            claim = self.get_claim_by_id(claim_id)
            customer_id = claim.get("customer_id") or claim.get("user_id")
            if customer_id:
                self._update_user_gamification(customer_id, "claim_approved")
        
        return result.modified_count > 0

    def reject_claim_final(self, claim_id, rejected_by, reason):
        """Final rejection by company admin"""
        update_data = {
            "workflow_status": "rejected",
            "final_status": "rejected",
            "rejected_by": rejected_by,
            "rejection_reason": reason,
            "rejected_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        workflow_entry = {
            "status": "rejected",
            "timestamp": datetime.utcnow(),
            "by": rejected_by,
            "reason": reason
        }
        
        result = self.claims.update_one(
            {"claim_id": claim_id},
            {"$set": update_data, "$push": {"workflow_history": workflow_entry}}
        )
        
        if result.modified_count > 0:
            # Update user gamification (negative)
            claim = self.get_claim_by_id(claim_id)
            customer_id = claim.get("customer_id") or claim.get("user_id")
            if customer_id:
                self._update_user_gamification(customer_id, "claim_rejected")
        
        return result.modified_count > 0

    def assign_claim_to_agent(self, claim_id, agent_id):
        """Assign claim to specific agent"""
        result = self.claims.update_one(
            {"claim_id": claim_id},
            {"$set": {
                "agent_id": agent_id,
                "workflow_status": "agent_review",
                "assigned_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0

    def get_all_claims(self, filters=None):
        query = filters if filters else {}
        claims = list(self.claims.find(query).sort("created_at", -1))
        return serialize_doc(claims)

    def get_claims_by_risk_level(self, risk_levels):
        """Get claims by risk level or status"""
        if not isinstance(risk_levels, list):
            risk_levels = [risk_levels]
        
        query = {
            "$or": [
                {"status": {"$in": risk_levels}},
                {"ai_analysis.xgboost_risk_level": {"$in": risk_levels}}
            ]
        }
        claims = list(self.claims.find(query).sort("created_at", -1))
        return serialize_doc(claims)

    # ==================== GAMIFICATION ====================

    def _update_user_gamification(self, user_id, event):
        """Update user gamification stats"""
        gamify = self.gamification.find_one({"user_id": user_id})
        
        if not gamify:
            return
        
        update_data = {}
        new_badges = []
        
        if event == "claim_submitted":
            update_data["$inc"] = {"total_claims": 1}
        
        elif event == "claim_approved":
            update_data["$inc"] = {
                "approved_claims": 1,
                "claim_streak": 1,
                "honesty_score": 5
            }
            
            # Award badges
            approved = gamify.get("approved_claims", 0) + 1
            if approved == 1:
                new_badges.append("🎯 First Approved Claim")
            elif approved == 5:
                new_badges.append("⭐ 5 Clean Claims")
            elif approved == 10:
                new_badges.append("💎 Trusted Customer")
            elif approved == 20:
                new_badges.append("👑 Gold Member")
            
            # Streak badges
            streak = gamify.get("claim_streak", 0) + 1
            if streak >= 5:
                new_badges.append("🔥 5-Claim Streak")
                update_data["discount_eligibility"] = 10  # 10% discount
            
        elif event == "claim_rejected":
            update_data["$set"] = {"claim_streak": 0}
            update_data["$inc"] = {"honesty_score": -10}
        
        if new_badges:
            update_data["$push"] = {"badges": {"$each": new_badges}}
        
        if update_data:
            self.gamification.update_one(
                {"user_id": user_id},
                update_data
            )

    def get_user_gamification(self, user_id):
        """Get user gamification stats"""
        gamify = self.gamification.find_one({"user_id": user_id})
        return serialize_doc(gamify)

    def get_leaderboard(self, limit=10):
        """Get top honest customers"""
        leaderboard = list(self.gamification.find().sort("honesty_score", -1).limit(limit))
        return serialize_doc(leaderboard)

    # ==================== STATISTICS ====================

    def get_claim_statistics(self):
        total = self.claims.count_documents({})
        approved = self.claims.count_documents({"final_status": "approved"})
        pending = self.claims.count_documents({"workflow_status": {"$in": ["submitted", "agent_review", "admin_review"]}})
        rejected = self.claims.count_documents({"final_status": "rejected"})

        return {
            "total": total,
            "approved": approved,
            "pending": pending,
            "rejected": rejected
        }

    def get_company_statistics(self, company_id):
        """Get statistics for a specific company"""
        total = self.claims.count_documents({"company_id": company_id})
        approved = self.claims.count_documents({"company_id": company_id, "final_status": "approved"})
        pending = self.claims.count_documents({
            "company_id": company_id,
            "workflow_status": {"$in": ["submitted", "agent_review", "admin_review"]}
        })
        rejected = self.claims.count_documents({"company_id": company_id, "final_status": "rejected"})
        
        # Calculate fraud prevented
        high_risk_flagged = self.claims.count_documents({
            "company_id": company_id,
            "fraud_analysis.risk_level": {"$in": ["HIGH", "MEDIUM"]},
            "final_status": "rejected"
        })
        
        # Estimate fraud amount prevented
        fraud_claims = list(self.claims.find({
            "company_id": company_id,
            "fraud_analysis.risk_level": {"$in": ["HIGH", "MEDIUM"]},
            "final_status": "rejected"
        }))
        
        fraud_prevented = sum([c.get("claim_amount", 0) for c in fraud_claims])

        return {
            "total_claims": total,
            "approved": approved,
            "pending": pending,
            "rejected": rejected,
            "high_risk_flagged": high_risk_flagged,
            "fraud_prevented_amount": fraud_prevented
        }

    def get_platform_statistics(self):
        """Super admin platform-wide statistics"""
        total_companies = self.companies.count_documents({"status": "active"})
        total_agents = self.users.count_documents({"user_type": "agent", "status": "active"})
        total_customers = self.users.count_documents({"user_type": "customer"})
        
        claim_stats = self.get_claim_statistics()
        
        # Calculate total fraud prevented across all companies
        all_fraud_claims = list(self.claims.find({
            "fraud_analysis.risk_level": {"$in": ["HIGH", "MEDIUM"]},
            "final_status": "rejected"
        }))
        
        total_fraud_prevented = sum([c.get("claim_amount", 0) for c in all_fraud_claims])
        
        return {
            "total_companies": total_companies,
            "total_agents": total_agents,
            "total_customers": total_customers,
            "total_claims": claim_stats["total"],
            "approved_claims": claim_stats["approved"],
            "pending_claims": claim_stats["pending"],
            "rejected_claims": claim_stats["rejected"],
            "total_fraud_prevented": total_fraud_prevented,
            "platform_health": "excellent" if claim_stats["total"] > 0 else "new"
        }

    # ==================== FRAUD PATTERN LEARNING ====================

    def save_fraud_pattern(self, claim_id, pattern_data):
        """Save fraud pattern for ML retraining"""
        pattern_data["claim_id"] = claim_id
        pattern_data["created_at"] = datetime.utcnow()
        result = self.fraud_patterns.insert_one(pattern_data)
        return str(result.inserted_id)

    def get_fraud_patterns_for_training(self, limit=1000):
        """Get fraud patterns for model retraining"""
        patterns = list(self.fraud_patterns.find().sort("created_at", -1).limit(limit))
        return serialize_doc(patterns)


# Singleton instance
enterprise_db = EnterpriseDatabase()
