"""
Explainable AI Module - Makes fraud detection transparent and trustworthy
This module explains WHY a claim was flagged as fraudulent
"""

from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ExplainableAI:
    """
    Provides human-readable explanations for fraud detection decisions
    Similar to LIME/SHAP but rule-based for speed and clarity
    """
    
    # Risk factor weights (for scoring)
    WEIGHTS = {
        'amount_very_high': 35,
        'amount_high': 20,
        'amount_round': 10,
        'multiple_recent_claims': 25,
        'previous_rejections': 20,
        'document_red_flags': 10,
        'poor_document_quality': 15,
        'low_ai_confidence': 20,
        'missing_information': 5,
        'weekend_filing': 5,
        'late_night_filing': 10,
        'new_policy': 15,
        'tampering_detected': 30,
        'narrative_inconsistent': 25
    }
    
    # Thresholds from config
    HIGH_AMOUNT = 500000
    MEDIUM_AMOUNT = 200000
    AUTO_APPROVE_AMOUNT = 50000
    
    def explain_fraud_decision(self, claim_data, user_history=None, extracted_data=None):
        """
        Generate detailed explanation for why claim was flagged/approved
        
        Returns:
        {
            'decision': 'APPROVE' | 'REVIEW' | 'FLAG',
            'confidence': 0-100,
            'primary_reasons': [list of main factors],
            'contributing_factors': [list of secondary factors],
            'red_flags': [list of concerns],
            'green_flags': [list of positive indicators],
            'explanation_text': 'Human-readable summary',
            'recommendation': 'What admin should do'
        }
        """
        
        try:
            explanation = {
                'decision': 'REVIEW',
                'confidence': 0,
                'primary_reasons': [],
                'contributing_factors': [],
                'red_flags': [],
                'green_flags': [],
                'risk_breakdown': {},
                'explanation_text': '',
                'recommendation': ''
            }
            
            # Get fraud score from claim
            fraud_score = claim_data.get('ai_analysis', {}).get('xgboost_fraud_score', 50)
            risk_level = claim_data.get('ai_analysis', {}).get('xgboost_risk_level', 'MEDIUM')
            amount = claim_data.get('amount', 0)
            
            # Analyze amount-based risk
            amount_risk = self._analyze_amount_risk(amount, explanation)
            
            # Analyze user history
            if user_history:
                history_risk = self._analyze_user_history(user_history, explanation)
            else:
                history_risk = 0
            
            # Analyze document quality
            if extracted_data:
                doc_risk = self._analyze_document_risk(extracted_data, explanation)
            else:
                doc_risk = 0
            
            # Analyze timing patterns
            timing_risk = self._analyze_timing_patterns(claim_data, explanation)
            
            # Analyze AI confidence
            ai_risk = self._analyze_ai_confidence(claim_data, explanation)
            
            # Calculate risk breakdown
            explanation['risk_breakdown'] = {
                'amount_risk': amount_risk,
                'history_risk': history_risk,
                'document_risk': doc_risk,
                'timing_risk': timing_risk,
                'ai_model_risk': fraud_score
            }
            
            # Determine decision
            if fraud_score >= 70 or risk_level == 'HIGH':
                explanation['decision'] = 'FLAG'
                explanation['confidence'] = fraud_score
                explanation['recommendation'] = '🚨 HIGH RISK: Detailed investigation required. Contact claimant for verification.'
            elif fraud_score >= 40 or risk_level == 'MEDIUM':
                explanation['decision'] = 'REVIEW'
                explanation['confidence'] = fraud_score
                explanation['recommendation'] = '⚠️ MEDIUM RISK: Manual review recommended. Verify documentation.'
            else:
                explanation['decision'] = 'APPROVE'
                explanation['confidence'] = 100 - fraud_score
                explanation['recommendation'] = '✅ LOW RISK: Safe to approve. Standard processing.'
            
            # Generate human-readable explanation
            explanation['explanation_text'] = self._generate_explanation_text(
                explanation, fraud_score, amount, risk_level
            )
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            return {
                'decision': 'REVIEW',
                'confidence': 0,
                'explanation_text': 'Unable to generate detailed explanation. Manual review required.',
                'error': str(e)
            }
    
    def _analyze_amount_risk(self, amount, explanation):
        """Analyze claim amount for fraud patterns"""
        risk_score = 0
        
        if amount > self.HIGH_AMOUNT:
            explanation['red_flags'].append(f'⚠️ Very high claim amount: ₹{amount:,.0f} (>₹5L)')
            explanation['primary_reasons'].append(f'Claim amount ₹{amount:,.0f} exceeds high-value threshold')
            risk_score += self.WEIGHTS['amount_very_high']
        elif amount > self.MEDIUM_AMOUNT:
            explanation['red_flags'].append(f'⚠️ High claim amount: ₹{amount:,.0f}')
            explanation['contributing_factors'].append('Above-average claim amount requires verification')
            risk_score += self.WEIGHTS['amount_high']
        else:
            explanation['green_flags'].append(f'✓ Reasonable claim amount: ₹{amount:,.0f}')
        
        # Check for suspiciously round numbers
        if amount > 100000 and amount % 100000 == 0:
            explanation['red_flags'].append(f'⚠️ Suspiciously round amount: ₹{amount:,.0f}')
            explanation['contributing_factors'].append('Round numbers are more common in fraudulent claims')
            risk_score += self.WEIGHTS['amount_round']
        
        return risk_score
    
    def _analyze_user_history(self, user_history, explanation):
        """Analyze user's claim history"""
        risk_score = 0
        
        if not user_history:
            return 0
        
        recent_claims = len([c for c in user_history if c.get('status') in ['approved', 'pending']])
        
        if recent_claims >= 3:
            explanation['red_flags'].append(f'⚠️ {recent_claims} claims filed in last 6 months')
            explanation['primary_reasons'].append('Multiple recent claims indicate possible fraud pattern')
            risk_score += self.WEIGHTS['multiple_recent_claims']
        elif recent_claims == 2:
            explanation['contributing_factors'].append('2 recent claims - slightly elevated frequency')
            risk_score += 15
        else:
            explanation['green_flags'].append('✓ No excessive claim history')
        
        # Check rejections
        rejected = len([c for c in user_history if c.get('status') == 'rejected'])
        if rejected > 0:
            explanation['red_flags'].append(f'⚠️ {rejected} previously rejected claim(s)')
            explanation['primary_reasons'].append('Previous rejections raise credibility concerns')
            risk_score += self.WEIGHTS['previous_rejections']
        
        return risk_score
    
    def _analyze_document_risk(self, extracted_data, explanation):
        """Analyze document quality and content"""
        risk_score = 0
        
        # Check for red flags from AI
        red_flags = extracted_data.get('red_flags', [])
        if red_flags:
            for flag in red_flags:
                explanation['red_flags'].append(f'⚠️ Document issue: {flag}')
            explanation['primary_reasons'].append(f'{len(red_flags)} suspicious pattern(s) detected in documents')
            risk_score += len(red_flags) * self.WEIGHTS['document_red_flags']
        
        # Check document quality
        quality = extracted_data.get('document_quality', 'clear')
        if quality == 'blurry' or quality == 'damaged':
            explanation['red_flags'].append('⚠️ Poor document quality - may hide alterations')
            explanation['contributing_factors'].append('Low-quality documents are harder to verify')
            risk_score += self.WEIGHTS['poor_document_quality']
        else:
            explanation['green_flags'].append('✓ Clear, readable documents')
        
        # Check AI confidence
        confidence = extracted_data.get('confidence_score', 100)
        if confidence < 50:
            explanation['red_flags'].append(f'⚠️ Low AI confidence: {confidence}%')
            explanation['contributing_factors'].append('AI uncertain about document authenticity')
            risk_score += self.WEIGHTS['low_ai_confidence']
        elif confidence > 80:
            explanation['green_flags'].append(f'✓ High AI confidence: {confidence}%')
        
        # Check missing information
        missing = extracted_data.get('missing_information', [])
        if missing:
            explanation['contributing_factors'].append(f'Missing: {", ".join(missing[:3])}')
            risk_score += len(missing) * self.WEIGHTS['missing_information']
        
        return risk_score
    
    def _analyze_timing_patterns(self, claim_data, explanation):
        """Analyze when claim was filed"""
        risk_score = 0
        
        created_at = claim_data.get('created_at', datetime.utcnow())
        
        # Weekend filing
        if created_at.weekday() >= 5:
            explanation['contributing_factors'].append('Filed on weekend (slightly unusual)')
            risk_score += self.WEIGHTS['weekend_filing']
        
        # Late night filing
        if created_at.hour >= 22 or created_at.hour <= 5:
            explanation['red_flags'].append(f'⚠️ Filed at unusual hour: {created_at.hour}:00')
            explanation['contributing_factors'].append('Late-night filings correlate with fraud')
            risk_score += self.WEIGHTS['late_night_filing']
        else:
            explanation['green_flags'].append('✓ Filed during normal business hours')
        
        return risk_score
    
    def _analyze_ai_confidence(self, claim_data, explanation):
        """Analyze AI model predictions"""
        risk_score = 0
        
        ai_analysis = claim_data.get('ai_analysis', {})
        
        # Check for tampering
        tampering = ai_analysis.get('tampering_check', {})
        if tampering.get('tampering_detected'):
            explanation['red_flags'].append('🚨 DOCUMENT TAMPERING DETECTED')
            explanation['primary_reasons'].append('AI detected signs of document manipulation')
            risk_score += self.WEIGHTS['tampering_detected']
        
        # Check narrative consistency
        narrative = ai_analysis.get('narrative_validation', {})
        if narrative.get('verification_status') == 'inconsistent':
            explanation['red_flags'].append('⚠️ Story doesn\'t match documents')
            explanation['primary_reasons'].append('Narrative inconsistent with extracted data')
            risk_score += self.WEIGHTS['narrative_inconsistent']
        elif narrative.get('verification_status') == 'consistent':
            explanation['green_flags'].append('✓ Story matches documents')
        
        return risk_score
    
    def _generate_explanation_text(self, explanation, fraud_score, amount, risk_level):
        """Generate human-readable summary"""
        
        decision = explanation['decision']
        
        if decision == 'FLAG':
            text = f"🚨 **HIGH FRAUD RISK ({fraud_score}%)** - This ₹{amount:,.0f} claim has been flagged for investigation.\n\n"
            text += f"**Primary Concerns:**\n"
            for reason in explanation['primary_reasons'][:3]:
                text += f"• {reason}\n"
            
            if explanation['red_flags']:
                text += f"\n**Red Flags Detected:**\n"
                for flag in explanation['red_flags'][:5]:
                    text += f"{flag}\n"
            
            text += f"\n**Recommended Action:** {explanation['recommendation']}"
            
        elif decision == 'REVIEW':
            text = f"⚠️ **MEDIUM RISK ({fraud_score}%)** - This ₹{amount:,.0f} claim requires manual review.\n\n"
            
            if explanation['primary_reasons']:
                text += f"**Key Factors:**\n"
                for reason in explanation['primary_reasons'][:2]:
                    text += f"• {reason}\n"
            
            if explanation['contributing_factors']:
                text += f"\n**Additional Considerations:**\n"
                for factor in explanation['contributing_factors'][:3]:
                    text += f"• {factor}\n"
            
            if explanation['green_flags']:
                text += f"\n**Positive Indicators:**\n"
                for flag in explanation['green_flags'][:2]:
                    text += f"{flag}\n"
            
            text += f"\n**Recommended Action:** {explanation['recommendation']}"
            
        else:  # APPROVE
            text = f"✅ **LOW RISK ({100 - fraud_score}% confidence)** - This ₹{amount:,.0f} claim appears legitimate.\n\n"
            
            if explanation['green_flags']:
                text += f"**Positive Indicators:**\n"
                for flag in explanation['green_flags'][:4]:
                    text += f"{flag}\n"
            
            if explanation['contributing_factors']:
                text += f"\n**Minor Notes:**\n"
                for factor in explanation['contributing_factors'][:2]:
                    text += f"• {factor}\n"
            
            text += f"\n**Recommended Action:** {explanation['recommendation']}"
        
        return text
    
    def get_feature_importance(self, claim_data):
        """
        Returns which features contributed most to the fraud score
        Like SHAP values but simplified
        """
        
        ai_analysis = claim_data.get('ai_analysis', {})
        amount = claim_data.get('amount', 0)
        
        importance = []
        
        # Amount impact
        if amount > self.HIGH_AMOUNT:
            importance.append({
                'feature': 'Claim Amount',
                'value': f'₹{amount:,.0f}',
                'impact': 'HIGH',
                'contribution': '+35%'
            })
        elif amount > self.MEDIUM_AMOUNT:
            importance.append({
                'feature': 'Claim Amount',
                'value': f'₹{amount:,.0f}',
                'impact': 'MEDIUM',
                'contribution': '+20%'
            })
        
        # XGBoost contribution
        xgb_score = ai_analysis.get('xgboost_fraud_score', 0)
        if xgb_score > 60:
            importance.append({
                'feature': 'ML Model Prediction',
                'value': f'{xgb_score}% fraud probability',
                'impact': 'HIGH',
                'contribution': f'+{xgb_score}%'
            })
        
        # Document quality
        extracted = ai_analysis.get('extracted_data', {})
        doc_quality = extracted.get('document_quality', 'clear')
        if doc_quality != 'clear':
            importance.append({
                'feature': 'Document Quality',
                'value': doc_quality,
                'impact': 'MEDIUM',
                'contribution': '+15%'
            })
        
        return importance


# Singleton instance
explainable_ai = ExplainableAI()
