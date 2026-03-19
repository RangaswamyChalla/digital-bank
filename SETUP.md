# Digital Bank Project Setup Guide

## Project Overview
A secure digital banking platform with:
- **Backend**: FastAPI (Python)
- **Frontend**: React 18 + Vite + Tailwind CSS
- **Database**: SQLite (local) or PostgreSQL (Docker)

---

## Prerequisites
- Python 3.11+
- Node.js 16+
- npm 8+

---

## Quick Start (Local Development)

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python run.py
```
The backend will run on: http://localhost:8000
API docs available at: http://localhost:8000/docs

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The frontend will run on: http://localhost:5173

---

## Using Docker (Full Stack)

### Start all services
```bash
docker-compose up --build
```

This starts:
- **Backend**: http://localhost:8000 (with auto-reload)
- **Frontend**: http://localhost:5173 (with auto-reload)
- **Database**: PostgreSQL on localhost:5432

### Stop services
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

---

## Environment Variables

### Backend (.env)
```
DATABASE_URL=sqlite+aiosqlite:///./bank.db  # Local SQLite
SECRET_KEY=your-super-secret-key-change-in-production-2024
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Frontend (.env.local)
```
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## Project Structure

### Backend (`/backend`)
- `run.py` - Application entry point
- `app/main.py` - FastAPI app setup
- `app/config.py` - Configuration management
- `app/database.py` - Database initialization
- `app/models/` - SQLAlchemy models
- `app/schemas/` - Pydantic schemas
- `app/routers/` - API endpoints
- `app/services/` - Business logic

### Frontend (`/frontend`)
- `src/main.jsx` - React entry point
- `src/App.jsx` - Main app component
- `src/components/` - Reusable components
- `src/pages/` - Page components
- `src/context/` - React Context (Auth)
- `src/services/api.js` - API client

---

## Available Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token

### Users
- `GET /api/users/me` - Get current user
- `PUT /api/users/me` - Update profile

### Accounts
- `GET /api/accounts` - List user accounts
- `POST /api/accounts` - Create new account
- `GET /api/accounts/{account_id}` - Get account details

### Transactions
- `POST /api/transactions` - Create transaction
- `GET /api/transactions-history` - Get transaction history

### KYC
- `POST /api/kyc/submit` - Submit KYC verification
- `GET /api/kyc/status` - Check KYC status

---

## Frontend Pages

- `/` - Dashboard (requires auth)
- `/login` - Login page
- `/register` - Registration page
- `/accounts` - View accounts
- `/transfer` - Transfer money
- `/transactions` - Transaction history
- `/kyc` - KYC verification
- `/admin` - Admin panel

---

## Development Workflow

### Running Backend Only
```bash
cd backend
python run.py
```
Server will auto-reload on code changes.

### Running Frontend Only
```bash
cd frontend
npm run dev
```
Vite will hot-reload on changes.

### Building Frontend
```bash
cd frontend
npm run build
npm run preview  # Preview production build
```

---

## Database Operations

### Initialize Database (Auto on startup)
The backend automatically creates tables on first run.

### Access PostgreSQL (Docker)
```bash
docker exec -it bank-db psql -U bankuser -d bankdb
```

---

## Troubleshooting

### Port Already in Use
- Backend (8000): `lsof -i :8000` to find process
- Frontend (5173): `lsof -i :5173` to find process
- Database (5432): `lsof -i :5432` to find process

### Dependencies Issues
```bash
# Clear pip cache
pip cache purge
pip install -r requirements.txt

# Clear npm cache
npm cache clean --force
npm install
```

### Database Issues
```bash
# Delete SQLite database
rm backend/bank.db

# Restart backend to recreate
```

---

## Security Notes

⚠️ **Production Configuration**:
- Change `SECRET_KEY` in `.env`
- Set `BACKEND_CORS_ORIGINS` to frontend domain only
- Use PostgreSQL instead of SQLite
- Enable HTTPS
- Set secure cookie flags
- Add rate limiting

---

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure environment variables
3. Run backend: `python backend/run.py`
4. Run frontend: `npm --prefix frontend run dev`
5. Access app: http://localhost:5173
6. See API docs: http://localhost:8000/docs
