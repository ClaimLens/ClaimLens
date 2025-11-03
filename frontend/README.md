# ClaimLens Frontend

Modern, AI-powered insurance claim automation platform built with React, Vite, and Tailwind CSS.

## 🚀 Features

- **Beautiful UI/UX**: Glass morphism design with smooth animations
- **AI-Powered**: Real-time fraud detection visualization
- **Responsive**: Works perfectly on all devices
- **Fast Performance**: Built with Vite for lightning-fast dev experience
- **Modern Stack**: React 18, Framer Motion, Recharts

## 📦 Tech Stack

- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS with custom animations
- **Routing**: React Router v6
- **State Management**: Context API
- **Animations**: Framer Motion
- **Charts**: Recharts
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **Notifications**: React Hot Toast

## 🛠️ Installation

### Prerequisites
- Node.js 16+ or use Miniconda with Node.js

### Quick Start

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

## 📝 Available Scripts

```powershell
# Development
npm run dev          # Start dev server with hot reload

# Production
npm run build        # Build for production
npm run preview      # Preview production build

# Code Quality
npm run lint         # Run ESLint
```

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── pages/
│   │   ├── LandingPage.jsx       # Marketing landing page
│   │   ├── Login.jsx              # Authentication
│   │   ├── Register.jsx           # User registration
│   │   ├── customer/              # Customer portal
│   │   │   ├── Dashboard.jsx      # Customer dashboard
│   │   │   ├── FileClaim.jsx      # Multi-step claim filing
│   │   │   ├── MyClaims.jsx       # Claims list with filters
│   │   │   ├── ClaimDetails.jsx   # Detailed claim view
│   │   │   └── Profile.jsx        # User profile
│   │   └── admin/                 # Admin portal
│   │       ├── Dashboard.jsx      # Admin analytics
│   │       ├── Claims.jsx         # Claims management
│   │       └── Analytics.jsx      # Advanced analytics
│   ├── layouts/
│   │   ├── MainLayout.jsx         # Public pages layout
│   │   └── DashboardLayout.jsx    # Dashboard sidebar layout
│   ├── context/
│   │   └── AuthContext.jsx        # Authentication state
│   ├── utils/
│   │   ├── api.js                 # Axios instance
│   │   └── helpers.js             # Utility functions
│   ├── App.jsx                    # Route configuration
│   ├── main.jsx                   # App entry point
│   └── index.css                  # Global styles
├── public/                        # Static assets
├── index.html                     # HTML template
├── vite.config.js                 # Vite configuration
├── tailwind.config.js             # Tailwind configuration
└── package.json                   # Dependencies
```

## 🎨 Key Features

### Customer Portal
- **Dashboard**: Overview of all claims with statistics
- **File Claim**: 3-step wizard with document upload
- **My Claims**: Filterable claims list with search
- **Claim Details**: Full claim information with AI fraud score
- **Profile**: User account management

### Admin Portal
- **Dashboard**: Real-time analytics and charts
- **Claims Management**: Review, approve, reject claims
- **Analytics**: Advanced insights with charts
- **Fraud Detection**: AI-powered risk scoring

### Design Features
- Glass morphism UI
- Smooth page transitions
- Hover effects and animations
- Loading skeletons
- Toast notifications
- Responsive design
- Dark theme optimized

## 🔌 API Integration

The frontend connects to the Flask backend at `http://localhost:5000/api`.

### Environment Variables

Create `.env` file (optional):

```env
VITE_API_URL=http://localhost:5000/api
```

### API Endpoints Used

```
# Authentication
POST   /api/auth/login
POST   /api/auth/register
GET    /api/auth/verify

# Claims (Customer)
POST   /api/claims/create
GET    /api/claims/user
GET    /api/claims/:id
GET    /api/claims/statistics

# Admin
GET    /api/admin/dashboard
GET    /api/admin/claims
GET    /api/admin/analytics
PUT    /api/admin/claims/:id/approve
PUT    /api/admin/claims/:id/reject
```

## 🎯 Demo Credentials

### Admin Account
- Email: `admin@claimai.com`
- Password: `admin123`

### Customer Account
- Email: `customer1@test.com`
- Password: `pass123`

## 🚀 Deployment

### Build for Production

```powershell
npm run build
```

Output will be in `dist/` folder.

### Deploy to Vercel

```powershell
npm install -g vercel
vercel
```

### Deploy to Netlify

```powershell
npm install -g netlify-cli
netlify deploy --prod
```

## ⚡ Performance Optimizations

- **Code Splitting**: Routes are lazy-loaded
- **Chunk Optimization**: Vendor chunks separated
- **Tree Shaking**: Unused code removed
- **Image Optimization**: Lazy loading implemented
- **Bundle Size**: Optimized for production

## 🎨 Customization

### Theme Colors

Edit `tailwind.config.js`:

```js
theme: {
  extend: {
    colors: {
      primary: { /* your colors */ },
      accent: { /* your colors */ }
    }
  }
}
```

### Animations

Custom animations in `src/index.css`:

```css
@keyframes yourAnimation {
  /* keyframes */
}
```

## 🐛 Troubleshooting

### Port Already in Use

```powershell
# Change port in package.json
"dev": "vite --port 3001"
```

### API Connection Issues

Check backend is running at `http://localhost:5000`

### Build Errors

```powershell
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## 📄 License

MIT License - Built for Hackathon

## 👥 Team

Built with ❤️ by Team StackOverflow

---

**Note**: Make sure the Flask backend is running before starting the frontend.
