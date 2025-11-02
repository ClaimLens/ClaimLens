# 🚀 Insurance Claim Automation Platform - Backend

AI-powered insurance claim management system with automated document processing and fraud detection.

## ✨ Features

- **AI Document Processing**: Automatic data extraction using Google Gemini
- **Fraud Detection**: ML-based risk scoring and anomaly detection
- **Real-time Status Tracking**: Live claim status updates
- **Admin Dashboard**: Complete claim management interface
- **Secure Authentication**: JWT-based auth system
- **RESTful API**: Well-documented API endpoints

## 🛠️ Tech Stack

- **Backend**: Flask (Python 3.10+)
- **Database**: MongoDB Atlas
- **AI**: Google Gemini 1.5 Flash
- **Authentication**: JWT
- **File Processing**: Pillow

## 📦 Installation

### 1. Clone & Setup
```bash
git clone <your-repo>
cd insurance-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create `.env` file:
```env
FLASK_ENV=development
FLASK_PORT=5000
MONGODB_URI=your_mongodb_connection_string
GEMINI_API_KEY=your_gemini_api_key
JWT_SECRET=your-secret-key-min-32-chars
```

### 3. Get API Keys

**MongoDB Atlas:**
- Sign up at https://www.mongodb.com/cloud/atlas/register
- Create cluster → Get connection string
- Replace `<password>` and `<dbname>` in connection string

**Google Gemini API:**
- Visit https://makersuite.google.com/app/apikey
- Click "Create API Key"
- Copy key to `.env`

### 4. Seed Database
```bash
python seed_data.py
```

### 5. Run Server
```bash
python app.py
```

Server runs at: `http://localhost:5000`

## 🧪 Testing
```bash
# Test API endpoints
python test_api.py
```

## 📚 API Endpoints

### Authentication
```
POST   /api/auth/register    - Register new user
POST   /api/auth/login       - Login user
GET    /api/auth/verify      - Verify token
```

### Claims (User)
```
POST   /api/claims/create              - File new claim
GET    /api/claims/user                - Get user's claims
GET    /api/claims/<claim_id>          - Get claim details
GET    /api/claims/statistics          - Get user statistics
```

### Admin
```
GET    /api/admin/claims               - Get all claims (filtered)
GET    /api/admin/dashboard            - Admin dashboard stats
PUT    /api/admin/claims/<id>/approve  - Approve claim
PUT    /api/admin/claims/<id>/reject   - Reject claim
PUT    /api/admin/claims/<id>/review   - Mark under review
GET    /api/admin/analytics            - Detailed analytics
```

## 🔑 Test Credentials

**Admin:**
- Email: `admin@claimai.com`
- Password: `admin123`

**Customer:**
- Email: `customer1@test.com`
- Password: `pass123`

## 📝 Example Request

### File a Claim
```bash
curl -X POST http://localhost:5000/api/claims/create \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "policy_number=POL10012345" \
  -F "claim_type=Health" \
  -F "description=Hospital bill for treatment" \
  -F "documents=@/path/to/document.jpg"
```

## 🏗️ Project Structure
```
backend/
├── app.py                    # Main Flask app
├── config.py                 # Configuration
├── seed_data.py             # Database seeding
├── test_api.py              # API tests
│
├── routes/
│   ├── auth.py              # Authentication routes
│   ├── claims.py            # Claim routes
│   └── admin.py             # Admin routes
│
├── models/
│   ├── database.py          # MongoDB connection
│   ├── user.py              # User model
│   └── claim.py             # Claim model
│
├── services/
│   ├── ai_service.py        # Gemini AI integration
│   ├── fraud_detector.py    # Fraud detection logic
│   └── document_processor.py # Document handling
│
└── utils/
    ├── validators.py        # Input validation
    └── helpers.py           # Helper functions
```

## 🚨 Common Issues

**Issue: MongoDB connection fails**
- Check connection string format
- Whitelist your IP in MongoDB Atlas

**Issue: Gemini API error**
- Verify API key is correct
- Check API quota limits

**Issue: File upload fails**
- Check file size (max 10MB)
- Verify allowed extensions

## 🔒 Security Notes

- Never commit `.env` file
- Use strong JWT secret (min 32 characters)
- Implement rate limiting for production
- Enable HTTPS in production

## 📊 Fraud Detection Logic

Claims are scored 0-100 based on:
- Claim amount (higher = more risk)
- User claim history
- Document quality
- Timing patterns
- AI-detected anomalies

**Score Interpretation:**
- 0-30: LOW (auto-approve eligible)
- 31-60: MEDIUM (standard verification)
- 61-79: HIGH (manual review required)
- 80-100: CRITICAL (investigate/reject)

## 🎯 Tomorrow's Frontend Integration

Your frontend will call these endpoints. Example flow:

1. User logs in → Gets JWT token
2. User uploads claim → POST `/api/claims/create`
3. Backend processes with AI → Returns fraud score
4. Admin reviews → PUT `/api/admin/claims/<id>/approve`
5. User sees updated status → GET `/api/claims/user`

## 👥 Team

- **Team Lead**: V V Parthiv
- **Backend Dev**: J Prabhu Dayal
- **AI/ML**: A Yashwanth
- **Database**: B Nithin Reddy

## 📄 License

MIT License - Built for Hackathon

---

**Built with ❤️ by Team StackOverflow**
```

---

### **FINAL CHECKLIST FOR TODAY**
```
✅ Backend Setup
  ✓ Project structure created
  ✓ Dependencies installed
  ✓ Environment variables configured
  ✓ API keys obtained

✅ Database Layer
  ✓ MongoDB connection
  ✓ User model
  ✓ Claim model
  ✓ CRUD operations

✅ AI/ML Services
  ✓ Gemini integration
  ✓ Document extraction
  ✓ Fraud detection algorithm
  ✓ Risk scoring system

✅ API Routes
  ✓ Authentication (login/register)
  ✓ Claims (CRUD operations)
  ✓ Admin (dashboard & actions)

✅ Testing & Documentation
  ✓ Seed data script
  ✓ API testing script
  ✓ README documentation

✅ Ready for Tomorrow
  ✓ All endpoints working
  ✓ Test data populated
  ✓ Documentation complete