# Digital Banking Application Specification

## Project Overview

**Project Name:** Digital Bank Pro
**Type:** Full-Stack Banking Web Application
**Core Functionality:** A secure digital banking platform enabling users to create accounts, complete KYC verification, transfer money, and manage finances with full audit logging.
**Target Users:** Bank customers, administrators, and compliance staff

---

## Tech Stack

- **Backend:** FastAPI (Python 3.11)
- **Frontend:** React 18 + Tailwind CSS
- **Database:** PostgreSQL 15
- **Authentication:** JWT with refresh tokens
- **State Management:** React Context + Hooks
- **Build Tool:** Vite

---

## UI/UX Specification

### Color Palette
- **Primary:** #0F172A (Slate 900 - deep navy)
- **Secondary:** #1E40AF (Blue 800 - trust blue)
- **Accent:** #10B981 (Emerald 500 - success green)
- **Warning:** #F59E0B (Amber 500)
- **Error:** #EF4444 (Red 500)
- **Background:** #F8FAFC (Slate 50)
- **Card:** #FFFFFF
- **Text Primary:** #1E293B (Slate 800)
- **Text Secondary:** #64748B (Slate 500)
- **Border:** #E2E8F0 (Slate 200)

### Typography
- **Font Family:** "Inter", system-ui, sans-serif
- **Headings:**
  - H1: 32px, font-weight 700
  - H2: 24px, font-weight 600
  - H3: 20px, font-weight 600
- **Body:** 16px, font-weight 400
- **Small:** 14px, font-weight 400
- **Mono (account numbers):** "JetBrains Mono", monospace

### Layout Structure
- **Max Width:** 1440px centered
- **Sidebar:** 280px fixed width (collapsible on mobile)
- **Content Area:** Fluid, min 320px
- **Spacing Scale:** 4px base (4, 8, 12, 16, 24, 32, 48, 64)

### Responsive Breakpoints
- Mobile: < 768px (sidebar becomes drawer)
- Tablet: 768px - 1024px
- Desktop: > 1024px

### Components

#### Navigation Sidebar
- Logo at top (48px height)
- Nav items with icons
- Active state: #1E40AF background with white text
- Hover state: #F1F5F9 background
- User profile at bottom

#### Cards
- Border radius: 12px
- Box shadow: 0 1px 3px rgba(0,0,0,0.1)
- Padding: 24px
- Hover: translateY(-2px) with shadow increase

#### Buttons
- Primary: #1E40AF bg, white text, rounded-lg, py-3 px-6
- Secondary: white bg, #1E40AF text, border
- Danger: #EF4444 bg, white text
- All buttons: transition 200ms, hover: brightness-110

#### Forms
- Input fields: 48px height, rounded-lg, border #E2E8F0
- Focus: ring-2 ring #1E40AF
- Labels: 14px, #64748B, mb-2 block
- Error state: border #EF4444, error text below

#### Tables
- Header: #F8FAFC bg, font-weight 600
- Rows: hover #F8FAFC
- Border: bottom #E2E8F0

#### Status Badges
- Pending: #FEF3C7 bg, #92400E text
- Approved: #D1FAE5 bg, #065F46 text
- Rejected: #FEE2E2 bg, #991B1B text
- Completed: #DBEAFE bg, #1E40AF text

---

## Functionality Specification

### 1. Authentication Module

#### User Registration
- Fields: email, password, confirm password, full name, phone
- Password requirements: min 8 chars, 1 uppercase, 1 number, 1 special
- Email verification link (simulated)
- Auto-login after registration

#### Login
- Email + password
- JWT access token (15 min) + refresh token (7 days)
- Remember me option (extends refresh to 30 days)
- Account lock after 5 failed attempts (15 min lockout)

#### Logout
- Invalidate refresh token
- Clear client-side tokens

### 2. KYC Module (Know Your Customer)

#### KYC Levels
- **Level 0:** Unverified - basic registration only
- **Level 1:** Email verified
- **Level 2:** ID verification (simulated document upload)
- **Level 3:** Full verification (address proof)

#### KYC Submission
- Document type selection (National ID, Passport, Driver License)
- Document number input
- Document upload (simulated - store filename)
- Address input
- Selfie upload (simulated)

#### KYC Review (Admin)
- List all pending KYC applications
- Approve/Reject with reason
- View submitted documents

### 3. Account Management

#### Create Account
- Select account type: Savings, Checking, Fixed Deposit
- Initial deposit amount (min $10 for Savings/Checking)
- Generate unique account number (10 digits)
- Auto-create with Level 0 KYC

#### Account Dashboard
- Total balance across all accounts
- Account list with:
  - Account number (masked: ****1234)
  - Account type badge
  - Current balance
  - Status (Active/Inactive)

#### Account Details
- Full account number
- Account type
- Current balance
- Available balance
- Account opening date
- Transaction history link

### 4. Money Transfer

#### Transfer Form
- From account dropdown (user's accounts)
- To account number input (with validation)
- Amount input (numeric, min $1, max balance)
- Transfer type: Internal (same bank), External
- Reference/memo field
- Confirmation step with details

#### Transfer Validation
- Sufficient balance check
- Account existence validation
- Same-account transfer prevention
- Daily limit check ($50,000 daily)
- Suspicious amount alert (>$10,000)

#### Transfer Execution
- Transaction ID generation
- Debit from source account
- Credit to destination account
- Both must succeed or both fail (ACID)
- Notification to both parties

#### Transfer History
- Filter by date range
- Filter by type (Internal/External)
- Filter by status (Pending/Completed/Failed)
- Export to CSV

### 5. Transaction History

#### Transaction List
- Date and time
- Transaction type (Credit/Debit)
- Amount
- From/To account
- Status
- Reference number

#### Transaction Details
- Full transaction info
- Status timeline
- Download receipt (PDF simulation)

### 6. Notifications

#### Notification Types
- Account created
- KYC status change
- Money received
- Money sent
- Transfer failed
- Balance update

#### Notification Display
- Bell icon with unread count
- Dropdown list of notifications
- Mark as read
- Mark all as read

### 7. Admin Dashboard

#### Overview Stats
- Total users
- Total accounts
- Total transaction volume
- Pending KYC applications

#### User Management
- List all users
- View user details
- Lock/Unlock user
- Reset password (simulated)

#### Transaction Monitoring
- All transactions list
- Filter by status, date, amount
- Flag suspicious transactions
- Cancel pending transactions

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'customer',
    kyc_level INTEGER DEFAULT 0,
    kyc_status VARCHAR(20) DEFAULT 'pending',
    kyc_submitted_at TIMESTAMP,
    kyc_reviewed_at TIMESTAMP,
    kyc_reviewed_by UUID,
    kyc_rejection_reason TEXT,
    is_active BOOLEAN DEFAULT true,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Accounts Table
```sql
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    account_number VARCHAR(10) UNIQUE NOT NULL,
    account_type VARCHAR(20) NOT NULL,
    balance DECIMAL(15,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Transactions Table
```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_account_id UUID REFERENCES accounts(id),
    to_account_id UUID REFERENCES accounts(id),
    from_account_number VARCHAR(10),
    to_account_number VARCHAR(10),
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    transaction_type VARCHAR(20) NOT NULL,
    transfer_type VARCHAR(20) NOT NULL,
    reference VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,
    failure_reason TEXT
);
```

### Audit Logs Table
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Notifications Table
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Refresh Tokens Table
```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints

### Auth
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/refresh
- POST /api/auth/logout

### Users
- GET /api/users/me
- PUT /api/users/me
- PUT /api/users/me/password

### KYC
- POST /api/kyc/submit
- GET /api/kyc/status
- GET /api/kyc/admin/list (admin)
- PUT /api/kyc/admin/review/{id} (admin)

### Accounts
- POST /api/accounts
- GET /api/accounts
- GET /api/accounts/{id}
- GET /api/accounts/{id}/transactions

### Transactions
- POST /api/transfers
- GET /api/transfers
- GET /api/transfers/{id}
- GET /api/transactions (history)

### Notifications
- GET /api/notifications
- PUT /api/notifications/{id}/read
- PUT /api/notifications/read-all

### Admin
- GET /api/admin/stats
- GET /api/admin/users
- GET /api/admin/transactions
- PUT /api/admin/users/{id}/lock

---

## Security Requirements

1. **Password Hashing:** bcrypt with 12 rounds
2. **JWT:** HS256 algorithm, short-lived access tokens
3. **Rate Limiting:** 100 req/min IP-based
4. **Input Validation:** Pydantic models
5. **SQL Injection:** Parameterized queries (SQLAlchemy ORM)
6. **CORS:** Restricted to frontend origin
7. **Audit Logging:** All sensitive actions logged
8. **Transaction Safety:** Database transactions with rollback

---

## Acceptance Criteria

1. ✅ User can register with email and password
2. ✅ User can login and receive JWT tokens
3. ✅ User can submit KYC documents
4. ✅ Admin can approve/reject KYC
5. ✅ User can create bank accounts
6. ✅ User can view account balance
7. ✅ User can transfer money between accounts
8. ✅ User can view transaction history
9. ✅ User receives notifications for transactions
10. ✅ Admin can view system stats
11. ✅ All actions are logged in audit trail
12. ✅ Application is Dockerized for deployment