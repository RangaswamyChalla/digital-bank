# Digital Bank Pro

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.10+-yellow.svg)
![React](https://img.shields.io/badge/react-18.2-blue.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.109-success.svg)

A modern, full-stack digital banking application built with FastAPI and React. Secure, scalable, and designed for the future of finance.

---

## ✨ Features

### 🏦 Banking Operations
- **Account Management** — Create and manage multiple account types (Savings, Checking, Business)
- **Instant Transfers** — Send money between accounts with real-time processing
- **Transaction History** — Complete audit trail with filtering and search
- **Balance Tracking** — Real-time balance updates and account monitoring

### 🔐 Security
- **JWT Authentication** — Secure token-based authentication
- **Password Hashing** — Argon2 encryption for password security
- **Rate Limiting** — Protection against brute force attacks
- **RBAC** — Role-based access control for admin/users

### 📋 KYC Verification
- **Identity Verification** — Document upload and verification workflow
- **Status Tracking** — Real-time KYC application status
- **Admin Approval** — Admin dashboard for verification decisions

### 📊 Admin Dashboard
- **User Management** — View and manage all users
- **Analytics** — Transaction volume, user growth, and fraud detection
- **Fraud Alerts** — Real-time suspicious activity monitoring
- **System Statistics** — Comprehensive dashboard metrics

### 🔔 Notifications
- **Real-time Alerts** — WebSocket-powered instant notifications
- **Transaction Updates** — Immediate alerts for all account activity

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** — High-performance Python web framework
- **SQLAlchemy** — SQL toolkit and ORM
- **Pydantic** — Data validation
- **Uvicorn** — ASGI server
- **JWT** — JSON Web Tokens
- **Argon2** — Password hashing

### Frontend
- **React 18** — Modern UI library
- **Vite** — Next-gen build tool
- **Tailwind CSS** — Utility-first styling
- **React Router** — Client-side routing
- **Recharts** — Data visualization
- **WebSocket** — Real-time communication

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

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

# Run the server
python run.py
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up --build
```

---

## 📁 Project Structure

```
digital-bank/
├── backend/
│   ├── app/
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routers/       # API endpoints
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── middleware/    # Custom middleware
│   │   └── main.py        # Application entry
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── pages/         # React pages
│   │   ├── components/    # Reusable components
│   │   ├── context/       # React context
│   │   ├── hooks/         # Custom hooks
│   │   └── services/      # API services
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
└── README.md
```

---

## 🔑 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | User registration |
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/refresh` | Refresh token |

### Accounts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/accounts` | List user accounts |
| POST | `/api/accounts` | Create account |
| GET | `/api/accounts/{id}` | Get account details |

### Transactions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/transactions/transfer` | Transfer funds |
| GET | `/api/transactions/history` | Transaction history |
| GET | `/api/transactions/{id}` | Transaction details |

### KYC
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/kyc/submit` | Submit KYC application |
| GET | `/api/kyc/status` | Check KYC status |
| PATCH | `/api/kyc/approve/{id}` | Admin approval |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/users` | List all users |
| GET | `/api/admin/stats` | System statistics |
| GET | `/api/admin/fraud-alerts` | Fraud alerts |

---

## 🔒 Environment Variables

```env
# Backend (.env)
DATABASE_URL=sqlite:///./bank.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Frontend (.env)
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

---

## 📈 Future Enhancements

- [ ] Multi-factor authentication (MFA)
- [ ] biometric authentication
- [ ] Payment gateway integration (Stripe, PayPal)
- [ ] Mobile app (React Native)
- [ ] ATM locator
- [ ] Budgeting tools and insights
- [ ] Investment portfolio tracking
- [ ] Cryptocurrency support

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Rangaswamy Challa**

---

## 🙏 Acknowledgments

- FastAPI team for the amazing framework
- React community for the component ecosystem
- All contributors and testers

---

<p align="center">
  <strong>Built with ❤️ for the future of banking</strong>
</p>
