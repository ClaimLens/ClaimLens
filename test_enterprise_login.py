#!/usr/bin/env python3
"""
Quick test script to verify enterprise database login
"""
from models.database_enterprise import enterprise_db
from werkzeug.security import check_password_hash

print("Testing Enterprise Database Login...")
print("=" * 50)

# Test credentials
test_email = "admin@lic.in"
test_password = "LIC@Admin123"

try:
    # Try to get user
    print(f"\n1. Looking up user: {test_email}")
    user = enterprise_db.get_user_by_email(test_email)
    
    if user:
        print(f"✅ User found: {user.get('name')}")
        print(f"   Email: {user.get('email')}")
        print(f"   User Type: {user.get('user_type')}")
        print(f"   Company ID: {user.get('company_id')}")
        
        # Test password
        print(f"\n2. Testing password...")
        if check_password_hash(user['password'], test_password):
            print(f"✅ Password correct!")
        else:
            print(f"❌ Password incorrect!")
    else:
        print(f"❌ User not found!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
