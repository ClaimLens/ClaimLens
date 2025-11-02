from models.database import db
from models.user import User
from models.claim import Claim
from datetime import datetime, timedelta
import random

def seed_database():
    """Populate database with test data"""
    
    print("🌱 Seeding database...")
    
    # Clear existing data (optional - comment out in production!)
    # db.users.delete_many({})
    # db.claims.delete_many({})
    
    # Create test users
    print("Creating users...")
    
    # Admin user
    admin_data = User.create(
        email='admin@claimai.com',
        password='admin123',
        name='Admin User',
        role='admin'
    )
    admin_data['phone'] = '+91 9876543210'
    admin_id = db.create_user(admin_data)
    print(f"✓ Admin created: admin@claimai.com")
    
    # Customer users
    customers = [
        {'email': 'customer1@test.com', 'password': 'pass123', 'name': 'Rajesh Kumar', 'phone': '+91 9123456789'},
        {'email': 'customer2@test.com', 'password': 'pass123', 'name': 'Priya Sharma', 'phone': '+91 9234567890'},
        {'email': 'customer3@test.com', 'password': 'pass123', 'name': 'Amit Patel', 'phone': '+91 9345678901'},
        {'email': 'customer4@test.com', 'password': 'pass123', 'name': 'Sneha Reddy', 'phone': '+91 9456789012'},
    ]
    
    customer_ids = []
    for cust in customers:
        user_data = User.create(
            email=cust['email'],
            password=cust['password'],
            name=cust['name'],
            role='customer'
        )
        user_data['phone'] = cust['phone']
        user_id = db.create_user(user_data)
        customer_ids.append(user_id)
        print(f"✓ Customer created: {cust['email']}")
    
    # Create sample claims
    print("\nCreating sample claims...")
    
    claim_scenarios = [
        {
            'policy_number': 'POL10012345',
            'claim_type': 'Health',
            'description': 'Hospitalization for appendicitis surgery at Apollo Hospital',
            'amount': 45000,
            'status': 'approved',
            'fraud_score': 15,
            'risk_level': 'LOW'
        },
        {
            'policy_number': 'POL10012346',
            'claim_type': 'Motor',
            'description': 'Car accident repair - front bumper and headlight damage',
            'amount': 125000,
            'status': 'pending',
            'fraud_score': 35,
            'risk_level': 'MEDIUM'
        },
        {
            'policy_number': 'POL10012347',
            'claim_type': 'Health',
            'description': 'Emergency treatment for cardiac condition',
            'amount': 850000,
            'status': 'under_review',
            'fraud_score': 75,
            'risk_level': 'HIGH'
        },
        {
            'policy_number': 'POL10012348',
            'claim_type': 'Property',
            'description': 'Water damage to apartment due to pipe burst',
            'amount': 180000,
            'status': 'approved',
            'fraud_score': 25,
            'risk_level': 'LOW'
        },
        {
            'policy_number': 'POL10012349',
            'claim_type': 'Motor',
            'description': 'Total loss - vehicle theft',
            'amount': 650000,
            'status': 'under_review',
            'fraud_score': 80,
            'risk_level': 'HIGH'
        },
        {
            'policy_number': 'POL10012350',
            'claim_type': 'Health',
            'description': 'Maternity expenses - normal delivery',
            'amount': 55000,
            'status': 'approved',
            'fraud_score': 10,
            'risk_level': 'LOW'
        },
        {
            'policy_number': 'POL10012351',
            'claim_type': 'Motor',
            'description': 'Minor accident - scratches and dents',
            'amount': 28000,
            'status': 'pending',
            'fraud_score': 20,
            'risk_level': 'LOW'
        },
        {
            'policy_number': 'POL10012352',
            'claim_type': 'Health',
            'description': 'Dental surgery - root canal treatment',
            'amount': 15000,
            'status': 'rejected',
            'fraud_score': 45,
            'risk_level': 'MEDIUM'
        },
        {
            'policy_number': 'POL10012353',
            'claim_type': 'Property',
            'description': 'Fire damage to kitchen appliances',
            'amount': 95000,
            'status': 'pending',
            'fraud_score': 40,
            'risk_level': 'MEDIUM'
        },
        {
            'policy_number': 'POL10012354',
            'claim_type': 'Health',
            'description': 'COVID-19 hospitalization expenses',
            'amount': 120000,
            'status': 'approved',
            'fraud_score': 18,
            'risk_level': 'LOW'
        },
    ]
    
    for i, scenario in enumerate(claim_scenarios):
        # Assign to random customer
        user_id = random.choice(customer_ids)
        
        # Create claim with backdated timestamps for variety
        days_ago = random.randint(1, 60)
        created_date = datetime.utcnow() - timedelta(days=days_ago)
        
        claim_data = Claim.create(
            user_id=user_id,
            policy_number=scenario['policy_number'],
            claim_type=scenario['claim_type'],
            description=scenario['description'],
            amount=scenario['amount']
        )
        
        # Override timestamps
        claim_data['created_at'] = created_date
        claim_data['updated_at'] = created_date
        
        # Set status
        claim_data['status'] = scenario['status']
        
        # Set AI analysis
        claim_data['ai_analysis'] = {
            'fraud_score': scenario['fraud_score'],
            'risk_level': scenario['risk_level'],
            'risk_factors': generate_risk_factors(scenario),
            'recommendation': get_recommendation(scenario['fraud_score']),
            'requires_manual_review': scenario['fraud_score'] > 60,
            'extracted_data': {
                'policy_number': scenario['policy_number'],
                'claim_amount': scenario['amount'],
                'document_quality': 'clear',
                'confidence_score': random.randint(75, 95)
            },
            'processed': True
        }
        
        # Add approval/rejection details
        if scenario['status'] == 'approved':
            claim_data['approved_amount'] = scenario['amount']
            claim_data['approved_at'] = created_date + timedelta(days=random.randint(1, 7))
            claim_data['admin_notes'] = 'Verified and approved after document review'
        elif scenario['status'] == 'rejected':
            claim_data['rejection_reason'] = 'Insufficient documentation'
            claim_data['rejected_at'] = created_date + timedelta(days=random.randint(2, 10))
        
        db.create_claim(claim_data)
        print(f"✓ Claim created: {claim_data['claim_id']} - {scenario['claim_type']} - {scenario['status']}")
    
    print(f"\n✅ Database seeded successfully!")
    print(f"\n📋 Test Credentials:")
    print(f"   Admin: admin@claimai.com / admin123")
    print(f"   Customer: customer1@test.com / pass123")
    print(f"   Customer: customer2@test.com / pass123")
    print(f"\n🚀 Start server with: python app.py")

def generate_risk_factors(scenario):
    """Generate realistic risk factors"""
    factors = []
    
    if scenario['amount'] > 500000:
        factors.append(f"High claim amount: ₹{scenario['amount']:,}")
    elif scenario['amount'] > 200000:
        factors.append(f"Above average claim amount: ₹{scenario['amount']:,}")
    
    if scenario['fraud_score'] > 70:
        factors.append("Multiple inconsistencies detected in documents")
    
    if scenario['risk_level'] == 'HIGH':
        factors.append("Claim requires detailed investigation")
    
    if scenario['claim_type'] == 'Motor' and scenario['amount'] > 500000:
        factors.append("Total loss claim - vehicle verification needed")
    
    return factors

def get_recommendation(fraud_score):
    """Get recommendation based on fraud score"""
    if fraud_score >= 80:
        return "REJECT - High fraud risk"
    elif fraud_score >= 60:
        return "MANUAL_REVIEW - Requires verification"
    elif fraud_score >= 40:
        return "VERIFY - Standard checks needed"
    else:
        return "APPROVE - Low risk"

if __name__ == '__main__':
    seed_database()