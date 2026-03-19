# Digital Bank Pro

A modern full-stack digital banking application with FastAPI + React.

---

## Project Overview

This is a production-ready digital banking platform featuring:
- **User Authentication** (JWT with access/refresh tokens)
- **Account Management** (Savings, Checking, Business accounts)
- **Money Transfers** (Internal & External)
- **KYC Verification** (Multi-level identity verification)
- **Fraud Detection** (ML-powered with XGBoost)
- **Real-time Notifications** (WebSocket)
- **Admin Dashboard** (User management, analytics, fraud alerts)
- **Background Jobs** (ARQ task queue)

---

## Tech Stack

### Backend
- **FastAPI** - Python async web framework
- **SQLAlchemy 2.0** - Async ORM
- **SQLite** - Development database (PostgreSQL-ready)
- **JWT** - Token authentication with Argon2 password hashing
- **XGBoost** - ML fraud detection
- **Redis** - Caching & pub/sub (optional)

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **Axios** - HTTP client
- **WebSocket** - Real-time updates

---

## Quick Start

### 1. Start Backend
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Start server (runs on port 8001)
python run.py
```

### 2. Start Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start dev server (runs on port 5173)
npm run dev
```

### 3. Access Application
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs

---

## Demo Credentials

| Email | Password | Role |
|-------|----------|------|
| admin@digitalbank.com | Admin@123456 | Admin |
| demo.user@demo.com | Demo@123456 | Customer |
| john.doe@demo.com | Demo@123456 | Customer |
| jane.smith@demo.com | Demo@123456 | Customer |

---

## Project Structure

```
digital-bank/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app entry
│   │   ├── config.py        # Settings
│   │   ├── database.py      # DB connection
│   │   ├── models/         # SQLAlchemy models
│   │   ├── routers/        # API endpoints
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── middleware/      # Custom middleware
│   │   └── ml/            # ML fraud detection
│   ├── alembic/           # DB migrations
│   ├── training/           # ML training scripts
│   └── run.py             # Server runner
│
├── frontend/
│   ├── src/
│   │   ├── pages/         # Route pages
│   │   ├── components/     # Reusable components
│   │   ├── context/       # React context (Auth, etc.)
│   │   ├── hooks/         # Custom hooks
│   │   └── services/      # API client
│   └── vite.config.js     # Vite config
│
└── README.md
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/refresh` | Refresh token |
| POST | `/api/v1/auth/logout` | Logout |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/me` | Get current user |
| PUT | `/api/v1/users/me` | Update user |

### Accounts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/accounts` | List accounts |
| POST | `/api/v1/accounts` | Create account |
| GET | `/api/v1/accounts/balance` | Total balance |

### Transactions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/transactions/transfer` | Transfer funds |
| GET | `/api/v1/transactions` | Transaction history |

### KYC
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/kyc/submit` | Submit KYC |
| GET | `/api/v1/kyc/status` | KYC status |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/stats` | Dashboard stats |
| GET | `/api/v1/admin/users` | List users |
| GET | `/api/v1/admin/fraud-alerts` | Fraud alerts |

---

## Key Features Explained

### Authentication Flow
1. User registers/logins
2. Server returns JWT access token (15 min) + refresh token (7 days)
3. Tokens stored in httpOnly cookies
4. Frontend uses access token for authenticated requests

### Account Types
- **Savings** - Interest-bearing accounts
- **Checking** - Daily transactions
- **Fixed Deposit** - Long-term savings

### Fraud Detection
1. Every transaction is scored by ML model (XGBoost)
2. Features: amount, frequency, account age, KYC level, location
3. Risk levels: Low, Medium, High
4. High-risk transactions trigger admin alerts

### KYC Levels
| Level | Requirements | Limits |
|-------|-------------|--------|
| 0 | None | Account creation only |
| 1 | Basic info | Limited transfers |
| 2 | ID verified | Moderate limits |
| 3 | Full verification | Unlimited |

---

## Database Schema

```
users
├── id (UUID)
├── email (unique)
├── password_hash
├── full_name, phone
├── role (customer/admin)
├── kyc_level, kyc_status
└── is_active

accounts
├── id (UUID)
├── user_id (FK)
├── account_number (unique)
├── account_type
├── balance
└── status

transactions
├── id (UUID)
├── from/to account
├── amount, type, status
└── timestamps

fraud_alerts
├── id (UUID)
├── user_id, transaction_id
├── risk_score, risk_level
└── status (open/escalated/blocked)
```

---

## Docker (Optional)

```bash
# Build and run
docker-compose up --build

# Backend only
docker-compose up backend
```

---

## Environment Variables

```env
# Backend
DATABASE_URL=sqlite+aiosqlite:///./bank.db
SECRET_KEY=your-secret-key
REDIS_URL=redis://localhost:6379

# Frontend (Vite)
VITE_API_BASE_URL=http://localhost:8001
```

---

## Troubleshooting

**Port 8000 in use?**
```bash
# Kill processes on port
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Database issues?**
```bash
cd backend
python -c "from app.database import engine, Base; from app.models import *; import asyncio; asyncio.run(engine.begin())"
```

**Reinstall dependencies?**
```bash
# Backend
pip install -r requirements.txt

# Frontend
rm -rf node_modules package-lock.json
npm install
```

---

## Author

**Rangaswamy Challa**

---

<p align="center">Built with FastAPI + React</p>
