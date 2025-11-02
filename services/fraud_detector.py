from datetime import datetime, timedelta
from models.database import db
import random

class FraudDetector:
    
    # Fraud detection thresholds
    HIGH_AMOUNT_THRESHOLD = 500000  # ₹5L
    MEDIUM_AMOUNT_THRESHOLD = 200000  # ₹2L
    MULTIPLE_CLAIMS_PERIOD = 180  # 6 months
    NEW_POLICY_PERIOD = 30  # days
    
    def calculate_fraud_score(self, claim_data, user_history, extracted_data):
        """
        Calculate fraud risk score (0-100)
        Returns: (score, risk_factors, recommendation)
        """
        
        score = 0
        risk_factors = []
        
        # 1. Amount-based risk
        amount_score, amount_factors = self._check_amount_risk(claim_data['amount'])
        score += amount_score
        risk_factors.extend(amount_factors)
        
        # 2. User history analysis
        history_score, history_factors = self._check_user_history(
            claim_data['user_id'], 
            user_history
        )
        score += history_score
        risk_factors.extend(history_factors)
        
        # 3. Document analysis risk
        doc_score, doc_factors = self._check_document_risk(extracted_data)
        score += doc_score
        risk_factors.extend(doc_factors)
        
        # 4. Timing patterns
        timing_score, timing_factors = self._check_timing_patterns(claim_data)
        score += timing_score
        risk_factors.extend(timing_factors)
        
        # 5. Policy age check
        policy_score, policy_factors = self._check_policy_age(claim_data)
        score += policy_score
        risk_factors.extend(policy_factors)
        
        # Cap at 100
        final_score = min(score, 100)
        
        # Determine recommendation
        recommendation = self._get_recommendation(final_score)
        
        return {
            'fraud_score': final_score,
            'risk_level': self._get_risk_level(final_score),
            'risk_factors': risk_factors,
            'recommendation': recommendation,
            'requires_manual_review': final_score > 60
        }
    
    def _check_amount_risk(self, amount):
        """Check if claim amount is suspicious"""
        score = 0
        factors = []
        
        if amount > self.HIGH_AMOUNT_THRESHOLD:
            score += 35
            factors.append(f"Very high claim amount: ₹{amount:,}")
        elif amount > self.MEDIUM_AMOUNT_THRESHOLD:
            score += 20
            factors.append(f"High claim amount: ₹{amount:,}")
        
        # Check for round numbers (often fraudulent)
        if amount > 100000 and amount % 100000 == 0:
            score += 10
            factors.append("Suspiciously round amount")
        
        return score, factors
    
    def _check_user_history(self, user_id, user_history):
        """Analyze user's claim history"""
        score = 0
        factors = []
        
        if not user_history:
            return score, factors
        
        # Multiple recent claims
        recent_claims = len([c for c in user_history if c['status'] in ['approved', 'pending']])
        
        if recent_claims >= 3:
            score += 25
            factors.append(f"{recent_claims} claims in last 6 months")
        elif recent_claims == 2:
            score += 15
            factors.append("Multiple claims recently")
        
        # Check rejection history
        rejected_claims = len([c for c in user_history if c['status'] == 'rejected'])
        if rejected_claims > 0:
            score += 20
            factors.append(f"{rejected_claims} previously rejected claims")
        
        return score, factors
    
    def _check_document_risk(self, extracted_data):
        """Analyze document-related risks"""
        score = 0
        factors = []
        
        if not extracted_data:
            return score, factors
        
        # Check red flags from AI
        red_flags = extracted_data.get('red_flags', [])
        if red_flags:
            score += len(red_flags) * 10
            factors.extend([f"Document issue: {flag}" for flag in red_flags])
        
        # Check document quality
        if extracted_data.get('document_quality') == 'blurry':
            score += 15
            factors.append("Poor document quality")
        
        # Check confidence score
        confidence = extracted_data.get('confidence_score', 100)
        if confidence < 50:
            score += 20
            factors.append("Low AI confidence in document")
        
        # Missing critical information
        missing = extracted_data.get('missing_information', [])
        if missing:
            score += len(missing) * 5
            factors.append(f"Missing information: {', '.join(missing)}")
        
        return score, factors
    
    def _check_timing_patterns(self, claim_data):
        """Check suspicious timing patterns"""
        score = 0
        factors = []
        
        created_at = claim_data.get('created_at', datetime.utcnow())
        
        # Weekend/holiday submissions (slightly suspicious)
        if created_at.weekday() >= 5:  # Saturday or Sunday
            score += 5
            factors.append("Claim filed on weekend")
        
        # Late night submissions
        if created_at.hour >= 22 or created_at.hour <= 5:
            score += 10
            factors.append("Claim filed at unusual hour")
        
        return score, factors
    
    def _check_policy_age(self, claim_data):
        """Check if policy is suspiciously new"""
        score = 0
        factors = []
        
        # This would normally check actual policy purchase date
        # For demo, we'll use random logic
        
        # Simulate checking policy age
        # In real system: query insurance company API
        
        return score, factors
    
    def _get_risk_level(self, score):
        """Convert score to risk level"""
        if score >= 70:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_recommendation(self, score):
        """Get action recommendation based on score"""
        if score >= 80:
            return "REJECT - High fraud risk, recommend investigation"
        elif score >= 60:
            return "MANUAL_REVIEW - Requires detailed verification"
        elif score >= 40:
            return "VERIFY - Standard verification needed"
        else:
            return "APPROVE - Low risk, fast-track approval"
    
    def get_user_claim_history(self, user_id, days=180):
        """Get user's recent claim history"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        claims = db.claims.find({
            'user_id': user_id,
            'created_at': {'$gte': cutoff_date}
        })
        
        return list(claims)

# Singleton instance
fraud_detector = FraudDetector()