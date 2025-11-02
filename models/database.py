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
        try:
            # Get MongoDB connection URI from .env
            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                raise ValueError("MONGO_URI not found in environment variables")

            # Connect to MongoDB (with timeout)
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
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

            logging.info("✅ Connected to MongoDB successfully!")

        except Exception as e:
            logging.error(f"❌ MongoDB connection failed: {e}")
            raise

    # ------------------- USER OPERATIONS -------------------

    def get_user_by_email(self, email):
        user = self.users.find_one({"email": email})
        return serialize_doc(user)

    def create_user(self, user_data):
        user_data["created_at"] = datetime.utcnow()
        result = self.users.insert_one(user_data)
        return str(result.inserted_id)

    # ------------------- CLAIM OPERATIONS -------------------

    def create_claim(self, claim_data):
        claim_data["created_at"] = datetime.utcnow()
        result = self.claims.insert_one(claim_data)
        return str(result.inserted_id)

    def get_claim_by_id(self, claim_id):
        claim = self.claims.find_one({"claim_id": claim_id})
        return serialize_doc(claim)

    def get_claims_by_user(self, user_id):
        claims = list(self.claims.find({"user_id": user_id}).sort("created_at", -1))
        return [serialize_doc(c) for c in claims]

    def get_all_claims(self, filters=None):
        query = filters if filters else {}
        claims = list(self.claims.find(query).sort("created_at", -1))
        return [serialize_doc(c) for c in claims]

    def update_claim(self, claim_id, update_data):
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
