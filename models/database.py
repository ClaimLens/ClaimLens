from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def serialize_doc(doc):
    """Convert MongoDB ObjectId to string for JSON compatibility."""
    if not doc:
        return None
    doc['_id'] = str(doc['_id'])
    return doc


class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.users = None
        self.claims = None
        self.notifications = None
        self.mock_mode = False
        
        try:
            # Get MongoDB connection URI from .env (try both variable names)
            mongo_uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
            if not mongo_uri:
                logging.warning("MONGODB_URI not found - using mock mode")
                self.mock_mode = True
                self._init_mock_data()
                return

            # Connect to MongoDB with proper SSL settings for pymongo 4.x
            import certifi
            self.client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,
                tlsCAFile=certifi.where(),
                tlsAllowInvalidCertificates=True  # Allow for development
            )
            self.client.server_info()  # Forces connection check

            # Use or create the database
            self.db = self.client["insurance_claims"]

            # Define collections
            self.users = self.db["users"]
            self.claims = self.db["claims"]
            self.notifications = self.db["notifications"]

            # Indexes
            self.users.create_index("email", unique=True)
            self.claims.create_index("claim_id", unique=True)
            self.claims.create_index("user_id")

            logging.info("Connected to MongoDB successfully!")

        except Exception as e:
            logging.warning(f"MongoDB connection failed: {e}")
            logging.info("Running in MOCK MODE - using in-memory data")
            self.mock_mode = True
            self._init_mock_data()

    def _init_mock_data(self):
        """Initialize mock data for development without MongoDB"""
        from werkzeug.security import generate_password_hash
        
        self.mock_users = [
            {
                '_id': '1',
                'full_name': 'Admin User',
                'email': 'admin@claimai.com',
                'password': generate_password_hash('admin123'),
                'role': 'admin',
                'phone': '+91 99999 88888',
                'created_at': datetime.utcnow()
            },
            {
                '_id': '2',
                'full_name': 'John Doe',
                'email': 'customer1@test.com',
                'password': generate_password_hash('pass123'),
                'role': 'customer',
                'phone': '+91 98765 43210',
                'created_at': datetime.utcnow()
            }
        ]
        
        self.mock_claims = [
            {
                '_id': '1',
                'claim_id': 'CLM-2024-001',
                'user_id': '2',
                'policy_number': 'POL123456',
                'claim_type': 'Health Insurance',
                'incident_date': '2024-10-15',
                'claim_amount': 25000,
                'description': 'Medical treatment for fever',
                'status': 'pending',
                'fraud_score': 15,
                'ai_analysis': {
                    'extracted_data': {
                        'policy_number': 'POL123456',
                        'claim_amount': '25000',
                        'diagnosis': 'Viral Fever'
                    },
                    'fraud_indicators': [],
                    'risk_assessment': 'Low Risk'
                },
                'documents': ['medical_bill.pdf'],
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        ]
        
        self.mock_notifications = []
        logging.info("Mock data initialized with admin and customer accounts")

    # ------------------- USER OPERATIONS -------------------

    def get_user_by_email(self, email):
        if self.mock_mode:
            for user in self.mock_users:
                if user['email'] == email:
                    return user.copy()
            return None
            
        if self.users is None:
            return None
            
        user = self.users.find_one({"email": email})
        return serialize_doc(user)

    def create_user(self, user_data):
        if self.mock_mode:
            user_data["_id"] = str(len(self.mock_users) + 1)
            user_data["created_at"] = datetime.utcnow()
            self.mock_users.append(user_data.copy())
            return user_data["_id"]
            
        if self.users is None:
            return None
            
        user_data["created_at"] = datetime.utcnow()
        result = self.users.insert_one(user_data)
        return str(result.inserted_id)

    # ------------------- CLAIM OPERATIONS -------------------

    def create_claim(self, claim_data):
        if self.mock_mode:
            claim_data["_id"] = str(len(self.mock_claims) + 1)
            claim_data["created_at"] = datetime.utcnow()
            claim_data["updated_at"] = datetime.utcnow()
            self.mock_claims.append(claim_data.copy())
            return claim_data["_id"]
            
        if self.claims is None:
            return None
            
        claim_data["created_at"] = datetime.utcnow()
        result = self.claims.insert_one(claim_data)
        return str(result.inserted_id)

    def get_claim_by_id(self, claim_id):
        if self.mock_mode:
            for claim in self.mock_claims:
                if claim.get('claim_id') == claim_id or claim.get('_id') == claim_id:
                    return claim.copy()
            return None
            
        if self.claims is None:
            return None
            
        claim = self.claims.find_one({"claim_id": claim_id})
        return serialize_doc(claim)

    def get_claims_by_user(self, user_id):
        if self.mock_mode:
            return [c.copy() for c in self.mock_claims if c.get('user_id') == user_id]
            
        if self.claims is None:
            return []
            
        claims = list(self.claims.find({"user_id": user_id}).sort("created_at", -1))
        return [serialize_doc(c) for c in claims]

    def get_all_claims(self, filters=None):
        if self.mock_mode:
            return [c.copy() for c in self.mock_claims]
            
        if self.claims is None:
            return []
            
        query = filters if filters else {}
        claims = list(self.claims.find(query).sort("created_at", -1))
        return [serialize_doc(c) for c in claims]

    def update_claim(self, claim_id, update_data):
        if self.mock_mode:
            for claim in self.mock_claims:
                if claim.get('claim_id') == claim_id or claim.get('_id') == claim_id:
                    claim.update(update_data)
                    claim['updated_at'] = datetime.utcnow()
                    return True
            return False
            
        if self.claims is None:
            return False
            
        update_data["updated_at"] = datetime.utcnow()
        result = self.claims.update_one(
            {"claim_id": claim_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    # ------------------- STATISTICS -------------------

    def get_claim_statistics(self):
        total = self.claims.count_documents({})
        approved = self.claims.count_documents({"status": "approved"})
        pending = self.claims.count_documents({"status": "pending"})
        rejected = self.claims.count_documents({"status": "rejected"})

        return {
            "total": total,
            "approved": approved,
            "pending": pending,
            "rejected": rejected
        }


# Singleton instance (import this anywhere in your app)
db = Database()
