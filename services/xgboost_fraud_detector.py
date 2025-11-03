import xgboost as xgb
import numpy as np
import os

class XGBoostFraudDetector:
    def __init__(self):
        """Load all three pre-trained models"""
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_dir = os.path.join(base_dir, 'models')
        
        try:
            self.health_model = xgb.XGBClassifier()
            self.health_model.load_model(os.path.join(models_dir, 'xgboost_health_fraud.bin'))
            print("✅ Health model loaded")
        except:
            self.health_model = None
        
        try:
            self.vehicle_model = xgb.XGBClassifier()
            self.vehicle_model.load_model(os.path.join(models_dir, 'xgboost_vehicle_fraud.bin'))
            print("✅ Vehicle model loaded")
        except:
            self.vehicle_model = None
        
        try:
            self.auto_model = xgb.XGBClassifier()
            self.auto_model.load_model(os.path.join(models_dir, 'xgboost_auto_fraud.bin'))
            print("✅ Auto model loaded")
        except:
            self.auto_model = None
    
    def _pad_features(self, features, expected_size):
        """Pad or trim features to match model requirements"""
        features = list(features)
        if len(features) < expected_size:
            features.extend([0] * (expected_size - len(features)))
        return features[:expected_size]
    
    def detect_fraud(self, claim_data, insurance_type='health'):
        """Predict fraud probability for a claim"""
        
        if insurance_type.lower() == 'vehicle':
            model = self.vehicle_model
            expected_features = 32
        elif insurance_type.lower() == 'auto':
            model = self.auto_model
            expected_features = 39
        else:
            # Health model - trained on single feature (PotentialFraud column)
            # For demo, we'll use a simple heuristic since the model expects different input
            model = self.health_model
            expected_features = 3  # Use our 3 features but handle specially
        
        if model is None:
            return {
                'fraud_probability': 0.0,
                'fraud_score': 0,
                'risk_level': 'UNKNOWN',
                'recommendation': 'MANUAL REVIEW',
                'error': 'Model not loaded'
            }
        
        if isinstance(claim_data, dict):
            features = list(claim_data.values())
        else:
            features = list(claim_data)
        
        try:
            # Special handling for health model - use rule-based for now
            if insurance_type.lower() == 'health':
                # Extract features
                age = features[0] if len(features) > 0 else 0
                amount = features[1] if len(features) > 1 else 0
                duration = features[2] if len(features) > 2 else 0
                
                # Rule-based fraud probability for health
                fraud_prob = 0.0
                
                # Age risk
                if age < 25:
                    fraud_prob += 0.15
                elif age > 65:
                    fraud_prob += 0.10
                
                # Amount risk
                if amount > 500000:
                    fraud_prob += 0.30
                elif amount > 200000:
                    fraud_prob += 0.15
                
                # Duration risk
                if duration < 6:
                    fraud_prob += 0.20
                elif duration < 12:
                    fraud_prob += 0.10
                
                # Round number suspicious
                if amount > 100000 and amount % 100000 == 0:
                    fraud_prob += 0.10
                
                # Cap at 1.0
                fraud_prob = min(fraud_prob, 1.0)
                
            else:
                # Pad features to expected size for vehicle/auto models
                features = self._pad_features(features, expected_features)
                
                # Use actual model prediction
                prediction = model.predict([features])[0]
                fraud_prob = float(model.predict_proba([features])[0, 1])
            
            fraud_probability = fraud_prob
            
            if fraud_probability > 0.7:
                risk_level = 'HIGH'
            elif fraud_probability > 0.4:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            if fraud_probability > 0.6:
                recommendation = 'FLAG FOR REVIEW'
            else:
                recommendation = 'APPROVE'
            
            return {
                'fraud_probability': fraud_probability,
                'fraud_score': int(fraud_probability * 100),
                'risk_level': risk_level,
                'recommendation': recommendation
            }
        except Exception as e:
            return {
                'fraud_probability': 0.0,
                'fraud_score': 0,
                'risk_level': 'ERROR',
                'recommendation': 'MANUAL REVIEW',
                'error': str(e)
            }

detector = XGBoostFraudDetector()
