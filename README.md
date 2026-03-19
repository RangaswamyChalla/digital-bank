# Digital Bank Pro

A production-grade full-stack digital banking application with FastAPI + React, featuring fraud detection, real-time notifications, and an admin dashboard.

---

## Project Overview

This is a modern banking platform with:
- **User Authentication** (JWT with access/refresh tokens, Argon2 hashing)
- **Account Management** (Savings, Checking, Business accounts)
- **Money Transfers** (Internal & External with fraud scoring)
- **KYC Verification** (Multi-level identity verification)
- **Fraud Detection** (ML-powered with XGBoost)
- **Real-time Notifications** (WebSocket)
- **Admin Dashboard** (User management, analytics, fraud alerts)
- **Analytics** (Transaction insights, account analytics)
- **Background Jobs** (ARQ task queue)
- **Observability** (OpenTelemetry, Sentry, Prometheus metrics)

---

## Tech Stack

### Backend
- **FastAPI** - Python async web framework
- **SQLAlchemy 2.0** - Async ORM
- **PostgreSQL** - Production database (SQLite for dev)
- **JWT** - Token authentication with Argon2 password hashing
- **XGBoost** - ML fraud detection
- **Redis** - Caching & pub/sub (optional)
- **ARQ** - Background task queue
- **OpenTelemetry** - Distributed tracing
- **Sentry** - Error tracking

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **Axios** - HTTP client
- **WebSocket** - Real-time updates

---

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up --build

# Start with Redis (optional caching)
docker-compose --profile with-cache up --build

# Access application
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Manual Setup

#### 1. Start Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"

# Create admin user
python create_admin_simple.py

# Start server (runs on port 8001)
python run.py
```

#### 2. Start Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start dev server (runs on port 5173)
npm run dev
```

### Option 3: Setup Script (Windows)
```bash
./setup.bat
```

---

## Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8001 |
| API Docs (Swagger) | http://localhost:8001/docs |
| API Docs (ReDoc) | http://localhost:8001/api/docs/redoc |
| Prometheus Metrics | http://localhost:8001/metrics |

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
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Settings
│   │   ├── database.py          # DB connection
│   │   ├── models/              # SQLAlchemy models
│   │   ├── routers/             # API endpoints
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic
│   │   ├── middleware/          # Custom middleware
│   │   │   ├── error_handling.py
│   │   │   ├── rate_limit.py
│   │   │   ├── per_user_rate_limit.py
│   │   │   ├── security_headers.py
│   │   │   ├── timeout.py
│   │   │   └── rbac.py
│   │   ├── ml/                  # ML fraud detection
│   │   │   ├── models/
│   │   │   └── features/
│   │   ├── dependencies/        # FastAPI dependencies
│   │   └── secrets/             # Secrets management
│   ├── alembic/                 # DB migrations
│   ├── training/                # ML training scripts
│   ├── tests/                   # Test suite
│   ├── run.py                   # Server runner
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── pages/              # Route pages
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Accounts.jsx
│   │   │   ├── Transfer.jsx
│   │   │   ├── Transactions.jsx
│   │   │   ├── KYC.jsx
│   │   │   ├── Admin.jsx
│   │   │   └── EnhancedAdmin.jsx
│   │   ├── components/         # Reusable components
│   │   │   ├── Layout.jsx
│   │   │   ├── StatisticsView.jsx
│   │   │   └── FraudAlertsView.jsx
│   │   ├── context/            # React context (Auth)
│   │   ├── hooks/              # Custom hooks (useWebSocket)
│   │   └── services/           # API client
│   ├── vite.config.js
│   └── Dockerfile
│
├── docker-compose.yml
├── setup.bat
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
| GET | `/api/v1/transactions/history` | Detailed history |

### KYC
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/kyc/submit` | Submit KYC |
| GET | `/api/v1/kyc/status` | KYC status |

### Fraud Detection
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/fraud/alerts` | Fraud alerts |
| PUT | `/api/v1/fraud/alerts/{id}` | Update alert |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/overview` | System overview |
| GET | `/api/v1/analytics/user-insights` | User insights |
| GET | `/api/v1/analytics/accounts-insights` | Account analytics |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/stats` | Dashboard stats |
| GET | `/api/v1/admin/users` | List users |
| GET | `/api/v1/admin/fraud-alerts` | Fraud alerts |

### Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/notifications` | List notifications |
| PUT | `/api/v1/notifications/{id}/read` | Mark as read |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API root |
| GET | `/health` | Health check |
| GET | `/health/ready` | Readiness probe |
| GET | `/health/live` | Liveness probe |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/v1/system/status` | Detailed status |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `ws://host/ws/{user_id}` | Real-time notifications |

---

## Key Features

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

### Middleware Stack
1. Rate Limiting (global + per-user)
2. Error Handling
3. Request/Response Logging
4. CORS
5. Security Headers
6. Request Timeout

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

notifications
├── id (UUID)
├── user_id
├── title, message
└── is_read, created_at
```

---

## Environment Variables

### Backend
```env
DATABASE_URL=sqlite+aiosqlite:///./bank.db
SECRET_KEY=your-secret-key
REDIS_URL=redis://localhost:6379
ENVIRONMENT=development
DEBUG=true
```

### Frontend
```env
VITE_API_BASE_URL=http://localhost:8001
```

---

## Testing

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

---

## Troubleshooting

**Port 8001 in use?**
```bash
# Windows
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8001
kill -9 <PID>
```

**Database issues?**
```bash
cd backend
rm bank.db
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
python create_admin_simple.py
```

**Reinstall dependencies?**
```bash
# Backend
pip install -r requirements.txt --force-reinstall

# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

## Author

**Rangasamy Challa**

---

<p align="center">Built with FastAPI + React</p>
