# Digital Bank Pro

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.10+-yellow.svg)
![React](https://img.shields.io/badge/react-18.2-blue.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.109-success.svg)

A modern, full-stack digital banking application built with FastAPI and React. Secure, scalable, and designed for the future of finance.

---

## Features

### Banking Operations
- **Account Management** — Create and manage multiple account types (Savings, Checking, Business)
- **Instant Transfers** — Send money between accounts with real-time processing
- **Transaction History** — Complete audit trail with filtering and search
- **Balance Tracking** — Real-time balance updates and account monitoring

### Security
- **JWT Authentication** — Secure token-based authentication with access/refresh tokens
- **Password Hashing** — Argon2 encryption for password security
- **Rate Limiting** — Protection against brute force attacks (Redis-backed)
- **RBAC** — Role-based access control for admin/users
- **Security Headers** — CSP, HSTS, X-Frame-Options middleware

### KYC Verification
- **Identity Verification** — Document upload and verification workflow
- **Status Tracking** — Real-time KYC application status
- **Admin Approval** — Admin dashboard for verification decisions

### ML-Powered Fraud Detection
- **XGBoost ML Model** — Real-time transaction fraud scoring
- **Rule-Based Detection** — Configurable fraud rules engine
- **Alert Management** — Suspicious activity monitoring and alerts
- **Model Retraining** — Background ML model retraining pipeline

### Admin Dashboard
- **User Management** — View and manage all users
- **Analytics** — Transaction volume, user growth, and fraud detection
- **Fraud Alerts** — Real-time suspicious activity monitoring
- **System Statistics** — Comprehensive dashboard metrics
- **Audit Logs** — Complete action history tracking

### Real-time Features
- **WebSocket Notifications** — Instant in-app notifications
- **Transaction Updates** — Immediate alerts for all account activity
- **Live Dashboard** — Real-time metrics updates

### Observability
- **OpenTelemetry** — Distributed tracing support
- **Sentry** — Error tracking and monitoring
- **Prometheus Metrics** — `/metrics` endpoint for monitoring
- **Structured Logging** — JSON-formatted logs

### Background Processing
- **ARQ** — Async job queue for heavy tasks
- **Scheduled Tasks** — ML model retraining, report generation

---

## Tech Stack

### Backend
- **FastAPI** — High-performance Python web framework
- **SQLAlchemy 2.0** — SQL toolkit and ORM (async)
- **Pydantic v2** — Data validation
- **Uvicorn** — ASGI server
- **JWT (python-jose)** — JSON Web Tokens
- **Argon2** — Password hashing
- **Redis** — Caching, rate limiting, pub/sub
- **XGBoost + Scikit-learn** — ML fraud detection
- **Alembic** — Database migrations
- **ARQ** — Background job processing

### Frontend
- **React 18** — Modern UI library
- **Vite** — Next-gen build tool
- **Tailwind CSS** — Utility-first styling
- **React Router** — Client-side routing
- **Recharts** — Data visualization
- **WebSocket** — Real-time communication

### Infrastructure
- **Docker & Docker Compose** — Containerization
- **PostgreSQL** — Primary database
- **Redis** — Cache and message broker

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn
- Redis (optional, for rate limiting)
- PostgreSQL (optional, SQLite default for dev)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run the server (uses SQLite by default)
python run.py
```

The API will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at http://localhost:5173

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up --build
```

---

## Project Structure

```
digital-bank/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routers/        # API endpoints
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── middleware/     # Custom middleware
│   │   ├── ml/             # ML models and features
│   │   ├── background_tasks/ # ARQ job handlers
│   │   └── main.py         # Application entry
│   ├── alembic/            # Database migrations
│   ├── training/           # ML training scripts
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── pages/          # React pages
│   │   ├── components/     # Reusable components
│   │   ├── context/        # React context
│   │   ├── hooks/          # Custom hooks
│   │   └── services/       # API services
│   ├── package.json
│   └── vite.config.js
├── infrastructure/         # Docker, K8s configs
├── docker-compose.yml
└── README.md
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | User registration |
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/refresh` | Refresh token |
| POST | `/api/v1/auth/logout` | Logout |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/me` | Get current user |
| PUT | `/api/v1/users/me` | Update current user |
| GET | `/api/v1/users/` | List users (admin) |

### Accounts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/accounts` | List user accounts |
| POST | `/api/v1/accounts` | Create account |
| GET | `/api/v1/accounts/{id}` | Get account details |
| GET | `/api/v1/accounts/{id}/balance` | Get account balance |

### Transactions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/transactions/transfer` | Transfer funds |
| GET | `/api/v1/transactions/history` | Transaction history |
| GET | `/api/v1/transactions/{id}` | Transaction details |

### KYC
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/kyc/submit` | Submit KYC application |
| GET | `/api/v1/kyc/status` | Check KYC status |
| PATCH | `/api/v1/kyc/approve/{id}` | Admin approval |
| PATCH | `/api/v1/kyc/reject/{id}` | Admin rejection |

### Fraud Detection
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/fraud/alerts` | List fraud alerts |
| PATCH | `/api/v1/fraud/alerts/{id}` | Update alert status |
| POST | `/api/v1/fraud/retrain` | Trigger model retrain |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/overview` | Dashboard overview |
| GET | `/api/v1/analytics/transactions` | Transaction analytics |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/users` | List all users |
| GET | `/api/v1/admin/stats` | System statistics |
| GET | `/api/v1/admin/audit-logs` | Audit logs |

### Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/notifications` | List notifications |
| PATCH | `/api/v1/notifications/{id}/read` | Mark as read |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/health/ready` | Readiness probe |
| GET | `/health/live` | Liveness probe |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/v1/system/status` | System status |

---

## Environment Variables

### Backend (.env)
```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./bank.db

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_URL=redis://localhost:6379

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Observability (optional)
SENTRY_DSN=your-sentry-dsn
OTLP_ENDPOINT=your-otlp-endpoint
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

---

## Development

### Running Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Database Migrations
```bash
cd backend
alembic upgrade head
```

### ML Model Training
```bash
cd backend
python training/train_model.py
```

---

## License

This project is licensed under the MIT License.

---

## Author

**Rangaswamy Challa**

---

<p align="center">
  Built with for the future of banking
</p>
