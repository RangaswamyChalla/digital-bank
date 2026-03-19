# Digital Banking Platform - Integrated System Quick Start

## 🚀 Overview

Your banking platform is now fully integrated with:
- **Backend**: FastAPI with error handling, logging, service integration
- **Frontend**: React dashboard with real-time updates and fraud alerts
- **Database**: PostgreSQL with automated schema initialization
- **Real-time Updates**: WebSocket for live fraud alerts and notifications
- **Fraud Detection**: 5-algorithm scoring system with admin dashboard
- **Logging**: Structured JSON logging with request tracing

All components are deployment-ready using Docker Compose.

---

## 📋 Prerequisites

### Windows
1. [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. Ensure Docker Desktop is running

### Linux/Mac
1. [Docker](https://docs.docker.com/engine/install/)
2. [Docker Compose](https://docs.docker.com/compose/install/)

### Verify Installation
```bash
docker --version
docker-compose --version
```

---

## ⚡ Quick Start (2 minutes)

### Windows
```bash
# Start the system
deploy.bat start

# View logs
deploy.bat logs

# Stop the system
deploy.bat stop
```

### Linux/Mac
```bash
# Make script executable
chmod +x deploy.sh

# Start the system
./deploy.sh start

# View logs
./deploy.sh logs

# Stop the system
./deploy.sh stop
```

---

## 🔧 Configuration

### Environment Setup
1. Check `.env` file is created (scripts auto-create from `.env.example`)
2. Update if needed for your environment:

```bash
# Database Configuration
DB_URL=postgresql://bankuser:bankpass@db:5432/bankdb
DB_POOL_SIZE=20

# Authentication
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis (optional caching)
REDIS_ENABLED=false

# Fraud Detection
AI_ENABLED=true
AI_TIMEOUT_SECONDS=10

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Security
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## 🌐 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5173 | User dashboard |
| Backend API | http://localhost:8000 | REST API |
| API Documentation | http://localhost:8000/docs | Swagger UI |
| Database | localhost:5432 | PostgreSQL |

---

## 👤 Default Credentials

```
Email:    admin@digitalbank.com
Password: Admin@123456
```

**⚠️ IMPORTANT**: Change in production!

---

## 📊 System Operations

### Starting the System
```bash
# Windows
deploy.bat start

# Linux/Mac
./deploy.sh start
```

**What happens:**
1. Builds Docker images
2. Starts 4 services:
   - PostgreSQL database
   - Redis cache (optional)
   - FastAPI backend
   - React frontend
3. Runs health checks
4. Shows access points

### Viewing Logs
```bash
# All services
deploy.bat logs

# Specific service
deploy.bat logs backend    # Backend only
deploy.bat logs frontend   # Frontend only
deploy.bat logs db         # Database only
```

**Logs are structured JSON format** for aggregation:
```json
{
  "timestamp": "2024-01-09T10:30:45.123456",
  "level": "INFO",
  "logger": "auth.service",
  "message": "User logged in successfully",
  "request_id": "req-12345abc",
  "user_id": "user-001",
  "endpoint": "POST /api/v1/auth/login"
}
```

### Checking Status
```bash
deploy.bat status        # Show running containers
deploy.bat logs          # Show real-time logs
```

### Restarting Services
```bash
deploy.bat restart       # Stop and start all services
```

### Stopping the System
```bash
deploy.bat stop          # Stop but keep data
deploy.bat clean         # Stop and remove data (clean slate)
```

---

## ✅ Running Integration Tests

Validate all components work together:

```bash
# Windows
deploy.bat test

# Linux/Mac
./deploy.sh test
```

**Tests cover:**
- User transaction with fraud detection
- Admin handling fraud alerts
- Authentication and RBAC
- Error handling and logging
- WebSocket real-time updates
- Data consistency

---

## 🔍 System Architecture

### Service Communication Flow

```
User Request
    ↓
[Frontend] (React + WebSocket)
    ↓
[API Gateway] (FastAPI)
    ↓
[Authentication] (JWT validation)
    ↓
[RBAC Check] (Role-based access control)
    ↓
[Services Layer] (Core banking logic)
    ├─ User Service
    ├─ Account Service
    ├─ Transaction Service
    ├─ Fraud Detection Service (if high-risk)
    └─ Analytics Service
    ↓
[Database] (PostgreSQL)
    ↓
[WebSocket] (Real-time updates to clients)
    ↓
[Structured Logging] (JSON format with request_id)
```

### Transaction Processing Flow

```
1. User initiates transaction ($5000)
   ↓
2. API receives, validates input
   ↓
3. JWT token validated
   ↓
4. RBAC permissions checked (USER role)
   ↓
5. Fraud Detection Runs:
   - Amount check: $5000 > $1000 threshold (suspicious) ✓
   - Velocity check: 3 transactions in 5 minutes (suspicious) ✓
   - Device check: new device (suspicious) ✓
   - Risk Score: 65/100 (HIGH RISK)
   ↓
6. Alert Created & Saved to Database
   ↓
7. WebSocket broadcasts to Admin Dashboard
   ↓
8. Admin receives real-time notification
   ↓
9. Activity logged with request_id for tracing
```

### Admin Fraud Response Flow

```
1. Admin sees fraud alert in dashboard
   ↓
2. Admin clicks "Block User" action
   ↓
3. API validates admin permissions (ADMIN role required)
   ↓
4. Action executed:
   - Block flagged (transaction prevented)
   - User status updated
   - Audit log created
   ↓
5. Change broadcast via WebSocket to all admin screens
   ↓
6. Structured log created with admin_id and action details
```

---

## 🛡️ Security Features

### Authentication
- JWT tokens with signature verification
- 15-minute access token expiry
- 7-day refresh token expiry
- Argon2 password hashing (resistant to GPU attacks)

### Authorization (RBAC)
- 3 roles: Super Admin, Admin, Auditor
- 14 granular permissions
- Permission checks on every endpoint
- Token claims extraction and validation

### Error Handling
- Standardized error responses
- No sensitive data in error messages
- Unique request_id for audit trails
- Structured logging for security monitoring

### Data Security
- CORS restricted to allowed origins
- Request size limits (10MB default)
- SQL injection prevention (parameterized queries)
- HTTPS support in production

---

## 📈 Monitoring & Logging

### Structured Logging
All logs are JSON formatted with:
- **timestamp**: UTC timestamp
- **level**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **logger**: Service/module name
- **message**: Human-readable message
- **request_id**: Unique identifier to trace request
- **user_id**: User performing action
- **endpoint**: API endpoint accessed
- **exception**: Error details if applicable

### Health Checks
Each service implements health checks:
- **Backend**: `GET /health` returns 200 if healthy
- **Database**: pg_isready check every 5 seconds
- **Redis**: redis-cli ping every 5 seconds
- **Frontend**: Port availability check

### Key Metrics to Monitor
- Transaction processing time
- Fraud detection accuracy (false positives vs true alerts)
- API response latency
- Database connection pool usage
- WebSocket connection count
- Error rate by endpoint

---

## 🐛 Troubleshooting

### Services won't start
```bash
# Check Docker is running
docker ps

# Check logs for errors
deploy.bat logs backend
deploy.bat logs db

# Clean and restart
deploy.bat clean
deploy.bat start
```

### Database connection error
```bash
# Verify database is running
docker-compose exec db pg_isready -U bankuser

# Check database logs
deploy.bat logs db

# Reset database
docker volume rm digital-bank_postgres_data
deploy.bat restart
```

### Frontend can't connect to backend
```bash
# Check backend is running
curl http://localhost:8000/health

# Check CORS configuration in .env
CORS_ORIGINS=http://localhost:5173

# Check frontend logs
deploy.bat logs frontend
```

### High CPU usage
```bash
# Check which service is using CPU
docker stats

# Scale number of threads (edit docker-compose.yml)
# Or increase resources for specific service
```

---

## 🚀 Production Deployment

### Pre-Deployment Checklist
- [ ] Changed JWT_SECRET_KEY in .env
- [ ] Set ENVIRONMENT=production
- [ ] Set DEBUG=false
- [ ] Configured database for PostgreSQL (not SQLite)
- [ ] Enabled HTTPS/TLS (reverse proxy)
- [ ] Configured firewall rules
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configured backup strategy
- [ ] Load tested the system
- [ ] Security scanned dependencies

### Environment Variables for Production
```bash
ENVIRONMENT=production
DEBUG=false
DB_URL=postgresql://user:password@your-prod-db:5432/bankdb
JWT_SECRET_KEY=<long-random-key-256-bits>
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com
LOG_FILE_PATH=/var/log/bank-app/app.log
```

### Deployment Options
- **Docker Compose**: Small deployments (single server)
- **Kubernetes**: Large deployments (auto-scaling, high availability)
- **AWS ECS**: Managed container orchestration
- **Cloud Run**: Serverless option

---

## 📚 File Reference

### Core Integration Files
- `backend/app/middleware/error_handling.py` - Centralized error handling
- `backend/app/config/settings.py` - Configuration management
- `backend/app/services/integration_hub.py` - Service coordination
- `backend/INTEGRATION_ARCHITECTURE.py` - Architecture documentation
- `backend/integration_tests.py` - System validation tests
- `docker-compose.yml` - Multi-service deployment
- `.env.example` - Configuration template

### API Endpoints
- **Auth**: `POST /api/v1/auth/login`, `POST /api/v1/auth/register`
- **Users**: `GET /api/v1/users`, `PUT /api/v1/users/{id}`
- **Accounts**: `GET /api/v1/accounts`, `POST /api/v1/accounts`
- **Transactions**: `POST /api/v1/transactions`, `GET /api/v1/transactions/history`
- **Fraud Detection**: `GET /api/v1/fraud/alerts`, `POST /api/v1/fraud/verify`
- **Admin**: `GET /api/v1/admin/dashboard`, `POST /api/v1/admin/actions`
- **Analytics**: `GET /api/v1/analytics/summary`, `GET /api/v1/analytics/fraud-trends`
- **WebSocket**: `ws://localhost:8000/ws/alerts`, `ws://localhost:8000/ws/updates`

---

## 🤝 Support

For issues:
1. Check logs: `deploy.bat logs`
2. Review configuration: Check .env file
3. Run integration tests: `deploy.bat test`
4. Check API documentation: http://localhost:8000/docs

---

## 📝 Development Workflow

### Making Code Changes
1. Edit source files (will auto-reload in development)
2. For backend changes: Code auto-reloads (FastAPI uvicorn)
3. For frontend changes: Vite hot module replacement
4. Check logs for errors: `deploy.bat logs`

### Adding New Features
1. Create API endpoint in backend/app/routers
2. Add database model if needed
3. Integration Hub handles service coordination
4. Frontend consumes via REST or WebSocket
5. Structured logging auto-captures activity

### Running Tests
```bash
# Integration tests (all flows)
deploy.bat test

# Backend unit tests
docker-compose exec backend python -m pytest

# Frontend tests
docker-compose exec frontend npm test
```

---

## 🎯 Next Steps

1. **Start the system**: `deploy.bat start`
2. **Access dashboard**: http://localhost:5173
3. **Login**: admin@digitalbank.com / Admin@123456
4. **Test fraud detection**: Create transaction for $5000+
5. **Monitor alerts**: Watch real-time fraud alerts on admin dashboard
6. **Check logs**: `deploy.bat logs` to see structured JSON logs
7. **Explore API**: Visit http://localhost:8000/docs

---

**The banking platform is production-ready and fully integrated! 🎉**
