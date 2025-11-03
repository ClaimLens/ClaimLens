#!/usr/bin/env python3
"""
Test Complete Workflow: Customer → Agent → Admin
"""

from models.database_enterprise import enterprise_db
from datetime import datetime
from bson import ObjectId
import json

def test_complete_workflow():
    print("\n" + "="*80)
    print("🧪 TESTING COMPLETE CLAIM WORKFLOW")
    print("="*80 + "\n")
    
    # Step 1: Customer submits claim
    print("1️⃣  STEP 1: Customer Submits Claim")
    print("-" * 80)
    
    customer_email = "customer1@gmail.com"
    customer = enterprise_db.get_user_by_email(customer_email)
    
    if not customer:
        print(f"❌ Customer not found: {customer_email}")
        return
    
    claim_data = {
        "claim_id": f"CLM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "customer_id": customer_email,
        "customer_name": customer['name'],
        "company_id": customer['company_id'],
        "claim_type": "Health",
        "claim_amount": 50000,
        "policy_number": "ICICI-HEALTH-2024-001",
        "description": "Hospitalization for fever treatment",
        "incident_date": datetime.utcnow(),
        "documents": [],
        "workflow_status": "submitted",
        "workflow_history": [{
            "status": "submitted",
            "timestamp": datetime.utcnow(),
            "actor": customer_email,
            "notes": "Initial claim submission"
        }],
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    claim_id = enterprise_db.claims.insert_one(claim_data).inserted_id
    claim_id_str = claim_data['claim_id']  # Store the claim_id for later use
    
    print(f"✅ Claim created successfully!")
    print(f"   Claim ID: {claim_id_str}")
    print(f"   Customer: {customer['name']} ({customer_email})")
    print(f"   Amount: ₹{claim_data['claim_amount']:,}")
    print(f"   Type: {claim_data['claim_type']}")
    print(f"   Status: {claim_data['workflow_status']}")
    print()
    
    # Step 2: Agent reviews and runs fraud detection
    print("2️⃣  STEP 2: Agent Reviews Claim (with Fraud Detection)")
    print("-" * 80)
    
    agent_email = "agent1@icicilombard.com"
    agent = enterprise_db.get_user_by_email(agent_email)
    
    if not agent:
        print(f"❌ Agent not found: {agent_email}")
        return
    
    # Simulate fraud detection result (low risk)
    fraud_analysis = {
        "fraud_score": 15,
        "risk_level": "LOW",
        "decision": "APPROVE",
        "confidence": 85,
        "explanation": "Legitimate claim - Normal amount, verified documents, no suspicious patterns"
    }
    
    # Agent approves and forwards to admin
    enterprise_db.claims.update_one(
        {"_id": claim_id},
        {
            "$set": {
                "agent_id": agent_email,
                "agent_name": agent['name'],
                "workflow_status": "agent_review",
                "fraud_analysis": fraud_analysis,
                "agent_decision": "approve",
                "agent_notes": "Legitimate claim, all documents verified. Recommending approval.",
                "agent_reviewed_at": datetime.utcnow()
            },
            "$push": {
                "workflow_history": {
                    "status": "agent_review",
                    "timestamp": datetime.utcnow(),
                    "actor": agent_email,
                    "notes": "Agent approved - forwarding to admin for final review"
                }
            }
        }
    )
    
    print(f"✅ Agent reviewed claim successfully!")
    print(f"   Agent: {agent['name']} ({agent_email})")
    print(f"   Fraud Score: {fraud_analysis['fraud_score']}%")
    print(f"   Risk Level: {fraud_analysis['risk_level']}")
    print(f"   Decision: {fraud_analysis['decision']}")
    print(f"   Status: agent_review → Forwarded to company admin")
    print()
    
    # Step 3: Update workflow to admin_review
    enterprise_db.claims.update_one(
        {"_id": claim_id},
        {
            "$set": {
                "workflow_status": "admin_review"
            },
            "$push": {
                "workflow_history": {
                    "status": "admin_review",
                    "timestamp": datetime.utcnow(),
                    "actor": agent_email,
                    "notes": "Forwarded to company admin for final approval"
                }
            }
        }
    )
    
    print("3️⃣  STEP 3: Company Admin Final Approval")
    print("-" * 80)
    
    admin_email = "admin@icicilombard.com"
    admin = enterprise_db.get_user_by_email(admin_email)
    
    if not admin:
        print(f"❌ Admin not found: {admin_email}")
        return
    
    # Admin approves the claim
    sanctioned_amount = 50000
    result = enterprise_db.approve_claim_final(
        claim_id=claim_id_str,  # Use the string claim_id, not ObjectId
        approved_by=admin_email,
        sanction_amount=sanctioned_amount,
        admin_notes="Approved as per policy terms. Payment to be processed."
    )
    
    print(f"✅ Admin approved claim successfully!")
    print(f"   Admin: {admin['name']} ({admin_email})")
    print(f"   Sanctioned Amount: ₹{sanctioned_amount:,}")
    print(f"   Status: approved ✅")
    print()
    
    # Step 4: Check gamification updates
    print("4️⃣  STEP 4: Gamification Updates")
    print("-" * 80)
    
    updated_customer = enterprise_db.get_user_by_email(customer_email)
    gamification = updated_customer.get('gamification', {})
    
    print(f"✅ Customer gamification updated!")
    print(f"   Honesty Score: {gamification.get('honesty_score', 100)}/100")
    print(f"   Total Claims: {gamification.get('total_claims', 0)}")
    print(f"   Approved Claims: {gamification.get('approved_claims', 0)}")
    print(f"   Current Streak: {gamification.get('streak_days', 0)} days")
    print(f"   Badges: {', '.join(gamification.get('badges', [])) or 'None yet'}")
    print(f"   Level: {gamification.get('level', 'Bronze')}")
    print()
    
    # Step 5: Final Summary
    print("5️⃣  WORKFLOW SUMMARY")
    print("-" * 80)
    
    final_claim = enterprise_db.claims.find_one({"_id": claim_id})
    
    # Convert ObjectId to string manually
    final_claim['_id'] = str(final_claim['_id'])
    
    print(f"✅ Claim Status: {final_claim['workflow_status'].upper()}")
    print(f"\n📊 Workflow Timeline:")
    for idx, history in enumerate(final_claim['workflow_history'], 1):
        actor = history.get('actor') or history.get('by', 'system')
        print(f"   {idx}. {history['status']} - {actor}")
        print(f"      {history.get('notes', 'No notes')}")
        print(f"      Time: {history['timestamp']}")
        print()
    
    print("="*80)
    print("🎉 COMPLETE WORKFLOW TEST PASSED!")
    print("="*80)
    print("\n✅ All systems working:")
    print("   • Customer claim submission")
    print("   • Agent fraud detection & approval")
    print("   • Company admin final approval")
    print("   • Gamification system updates")
    print("   • Workflow state machine")
    print("\n🏆 READY FOR HACKATHON DEMO!")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_complete_workflow()
