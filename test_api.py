import requests
import json

BASE_URL = 'http://localhost:5000/api'

def test_login():
    """Test login"""
    print("\n🔐 Testing Login...")
    
    response = requests.post(f'{BASE_URL}/auth/login', json={
        'email': 'customer1@test.com',
        'password': 'pass123'
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Login successful")
        print(f"  Token: {data['token'][:50]}...")
        return data['token']
    else:
        print(f"✗ Login failed: {response.json()}")
        return None

def test_get_claims(token):
    """Test getting user claims"""
    print("\n📋 Testing Get User Claims...")
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BASE_URL}/claims/user', headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved {data['total']} claims")
        for claim in data['claims'][:3]:
            print(f"  - {claim['claim_id']}: {claim['claim_type']} - {claim['status']}")
        return True
    else:
        print(f"✗ Failed: {response.json()}")
        return False

def test_create_claim(token):
    """Test creating a claim"""
    print("\n➕ Testing Create Claim...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Note: In real test, you'd upload actual files
    # For now, testing without files will show validation error
    
    data = {
        'policy_number': 'POL10099999',
        'claim_type': 'Health',
        'description': 'Test claim for API testing'
    }
    
    response = requests.post(f'{BASE_URL}/claims/create', 
                           headers=headers, 
                           data=data)
    
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")

def test_admin_dashboard(token):
    """Test admin dashboard"""
    print("\n📊 Testing Admin Dashboard...")
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BASE_URL}/admin/dashboard', headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Dashboard data retrieved")
        print(f"  Total Claims: {data['statistics']['total']}")
        print(f"  Approved: {data['statistics']['approved']}")
        print(f"  Pending: {data['statistics']['pending']}")
        print(f"  Avg Fraud Score: {data['average_fraud_score']}")
        return True
    else:
        print(f"✗ Failed: {response.json()}")
        return False

def run_tests():
    """Run all tests"""
    print("=" * 60)
    print("🧪 API Testing Suite")
    print("=" * 60)
    
    # Test customer flow
    customer_token = test_login()
    if customer_token:
        test_get_claims(customer_token)
        test_create_claim(customer_token)
    
    # Test admin flow
    print("\n" + "=" * 60)
    print("Testing Admin Flow")
    print("=" * 60)
    
    response = requests.post(f'{BASE_URL}/auth/login', json={
        'email': 'admin@claimai.com',
        'password': 'admin123'
    })
    
    if response.status_code == 200:
        admin_token = response.json()['token']
        test_admin_dashboard(admin_token)
    
    print("\n" + "=" * 60)
    print("✅ Testing Complete")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()