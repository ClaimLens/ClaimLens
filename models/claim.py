from datetime import datetime
import random
import string

class Claim:
    @staticmethod
    def generate_claim_id():
        """Generate unique claim ID: CLM + random 6 digits"""
        return 'CLM' + ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    def create(user_id, policy_number, claim_type, description, amount=0):
        return {
            'claim_id': Claim.generate_claim_id(),
            'user_id': user_id,
            'policy_number': policy_number,
            'claim_type': claim_type,  # Health, Motor, Property
            'description': description,
            'amount': amount,
            'status': 'pending',  # pending, approved, rejected, under_review
            'documents': [],
            'ai_analysis': {
                'fraud_score': 0,
                'risk_factors': [],
                'extracted_data': {},
                'processed': False
            },
            'admin_notes': '',
            'rejection_reason': '',
            'approved_amount': 0,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    
    @staticmethod
    def to_dict(claim):
        """Convert claim to safe dict"""
        claim_dict = dict(claim)
        claim_dict['_id'] = str(claim_dict.get('_id', ''))
        return claim_dict