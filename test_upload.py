import requests

# Login
login_response = requests.post('http://localhost:5000/api/auth/login', json={
    'email': 'customer1@test.com',
    'password': 'pass123'
})

token = login_response.json()['token']

# Upload claim with document
files = {'documents': open('hospital_bill.jpg', 'rb')}
data = {
    'policy_number': 'POL12345678',
    'claim_type': 'Health',
    'description': 'Hospital treatment for fever'
}
headers = {'Authorization': f'Bearer {token}'}

response = requests.post(
    'http://localhost:5000/api/claims/create',
    headers=headers,
    data=data,
    files=files
)

print(response.json())