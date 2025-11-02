# ClaimLens API Documentation

**Base URL:** `http://localhost:5000/api`

## Authentication

### Login
```
POST /auth/login
Content-Type: application/json

Body:
{
  "email": "customer1@test.com",
  "password": "pass123"
}

Response:
{
  "token": "eyJhbGci...",
  "user": { ... }
}
```

### All Protected Routes
Add header: `Authorization: Bearer {token}`

## Customer Endpoints

### Get My Claims
```
GET /claims/user
Headers: Authorization: Bearer {token}

Response:
{
  "claims": [...],
  "total": 5
}
```

### Get Claim Details
```
GET /claims/{claim_id}
Headers: Authorization: Bearer {token}
```

### Create Claim
```
POST /claims/create
Headers: Authorization: Bearer {token}
Content-Type: multipart/form-data

Form Data:
- policy_number: "POL12345"
- claim_type: "Health" | "Motor" | "Property"
- description: "Claim description"
- documents: [File, File, ...]

Response:
{
  "message": "Claim created successfully",
  "claim": { ... }
}
```

## Admin Endpoints

### Get All Claims
```
GET /admin/claims?status=pending&risk_level=HIGH
Headers: Authorization: Bearer {admin_token}
```

### Approve Claim
```
PUT /admin/claims/{claim_id}/approve
Headers: Authorization: Bearer {admin_token}
Content-Type: application/json

Body:
{
  "approved_amount": 50000,
  "admin_notes": "Approved after verification"
}
```

### Reject Claim
```
PUT /admin/claims/{claim_id}/reject
Headers: Authorization: Bearer {admin_token}
Content-Type: application/json

Body:
{
  "rejection_reason": "Insufficient documentation",
  "admin_notes": "Missing hospital bills"
}
```

### Admin Dashboard
```
GET /admin/dashboard
Headers: Authorization: Bearer {admin_token}

Response:
{
  "statistics": { total, approved, pending, rejected },
  "high_priority_claims": [...],
  "recent_claims": [...],
  "claims_by_type": { Health, Motor, Property },
  "average_fraud_score": 36.3,
  "needs_attention": 5
}
```
```

---

## 🎯 **YOUR BACKEND IS 100% COMPLETE!**

### **What You Have:**
✅ Full REST API  
✅ JWT Authentication  
✅ AI Document Processing (Gemini ready)  
✅ Fraud Detection Logic  
✅ Admin Dashboard  
✅ User Management  
✅ Claim CRUD Operations  
✅ Statistics & Analytics  
✅ Test Data  
✅ Documentation  

---

## 🌙 **TONIGHT'S FINAL TASKS:**

### **1. Create Demo Documents (30 min)**

Create 3 fake insurance documents using Canva/PowerPoint:

**Document 1: Legitimate Hospital Bill**
```
Apollo Hospital
Patient: Rajesh Kumar
Date: 25-Oct-2024
Procedure: Appendicitis Surgery
Amount: ₹45,000
```

**Document 2: Suspicious Motor Claim**
```
XYZ Garage
Vehicle: Honda City
Damage: Total Loss
Estimated Cost: ₹8,50,000
Date: 28-Oct-2024
```

**Document 3: Property Damage**
```
Home Repair Services
Property Damage: Water Leak
Repair Estimate: ₹1,80,000