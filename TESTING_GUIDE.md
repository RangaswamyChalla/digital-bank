# 🧪 DIGITAL BANK PRO - PRACTICAL TESTING GUIDE
## Step-by-Step QA Test Cases with Commands

---

## 📌 PREREQUISITES

### Ensure Services Running
```bash
# Terminal 1 - Backend
cd c:\Users\admin\digital-bank\backend
python run.py

# Terminal 2 - Frontend
cd c:\Users\admin\digital-bank\frontend
npm run dev
```

### Tools Needed
- **curl** (built into Windows 10+) or **PowerShell Invoke-WebRequest**
- **Postman** (optional but recommended)
- **Browser DevTools** (F12 in Chrome/Firefox)

### API Base URL
```
http://localhost:8000
```

### API Documentation
```
http://localhost:8000/docs  (Interactive Swagger UI)
```

---

## ✅ TEST EXECUTION GUIDE

### Test 1: User Registration

#### Test Case 1.1: Valid Registration
```powershell
# PowerShell
$body = @{
    email = "alice@bank.local"
    password = "SecurePass123!"
    full_name = "Alice Developer"
    phone = "+1 555-0001"
} | ConvertTo-Json

Invoke-WebRequest -Method POST `
    -Uri "http://localhost:8000/api/auth/register" `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**✅ PASS if:** Status 201, tokens generated

---

#### Test Case 1.2: Weak Password Rejection
```powershell
$body = @{
    email = "bob@bank.local"
    password = "short"
    full_name = "Bob User"
} | ConvertTo-Json

Invoke-WebRequest -Method POST `
    -Uri "http://localhost:8000/api/auth/register" `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body `
    -ErrorAction SilentlyContinue
```

**Expected Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.string.min_length"
    }
  ]
}
```

**✅ PASS if:** Status 422, validation error received

---

#### Test Case 1.3: Duplicate Email Prevention
```powershell
# Register first user
$body1 = @{
    email = "charlie@bank.local"
    password = "ValidPass123!"
    full_name = "Charlie One"
} | ConvertTo-Json

Invoke-WebRequest -Method POST `
    -Uri "http://localhost:8000/api/auth/register" `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body1

# Try to register same email again
$body2 = @{
    email = "charlie@bank.local"
    password = "ValidPass123!"
    full_name = "Charlie Two"
} | ConvertTo-Json

Invoke-WebRequest -Method POST `
    -Uri "http://localhost:8000/api/auth/register" `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body2 `
    -ErrorAction SilentlyContinue
```

**Expected Response:** Status 400/409 with error about duplicate email

**✅ PASS if:** Duplicate rejected

---

### Test 2: User Login

#### Test Case 2.1: Login with Valid Credentials
```powershell
$body = @{
    email = "alice@bank.local"
    password = "SecurePass123!"
} | ConvertTo-Json

$response = Invoke-WebRequest -Method POST `
    -Uri "http://localhost:8000/api/auth/login" `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body

$tokens = $response.Content | ConvertFrom-Json
$access_token = $tokens.access_token
Write-Host "✅ Login successful!"
Write-Host "Access Token: $access_token"
```

**Save the token for next tests!**

**✅ PASS if:** Status 200, tokens returned

---

#### Test Case 2.2: Login with Wrong Password
```powershell
$body = @{
    email = "alice@bank.local"
    password = "WrongPassword123!"
} | ConvertTo-Json

Invoke-WebRequest -Method POST `
    -Uri "http://localhost:8000/api/auth/login" `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body `
    -ErrorAction SilentlyContinue
```

**Expected Response:** Status 401 Unauthorized

**✅ PASS if:** Status 401, no tokens issued

---

### Test 3: Account Operations

#### Test Case 3.1: Create Bank Account
```powershell
# Use token from login test above
$token = "YOUR_ACCESS_TOKEN_HERE"

$body = @{
    account_type = "savings"
    initial_deposit = 500.00
} | ConvertTo-Json

$response = Invoke-WebRequest -Method POST `
    -Uri "http://localhost:8000/api/accounts" `
    -Headers @{
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $token"
    } `
    -Body $body

$account = $response.Content | ConvertFrom-Json
$account_id = $account.id
$account_number = $account.account_number

Write-Host "✅ Account created!"
Write-Host "Account ID: $account_id"
Write-Host "Account Number: $account_number"
Write-Host "Balance: $($account.balance)"
```

**Expected Response:**
```json
{
  "id": "12345678-...",
  "account_number": "1234567890",
  "account_type": "savings",
  "balance": 500.00,
  "currency": "USD",
  "status": "active",
  "created_at": "2026-03-18T...",
  "user_id": "..."
}
```

**✅ PASS if:** Status 201, account created with balance = initial_deposit

---

#### Test Case 3.2: Get Account Balance
```powershell
$token = "YOUR_ACCESS_TOKEN_HERE"

$response = Invoke-WebRequest -Method GET `
    -Uri "http://localhost:8000/api/accounts/balance" `
    -Headers @{
        "Authorization" = "Bearer $token"
    }

$balance = $response.Content | ConvertFrom-Json
Write-Host "✅ Total Balance: $($balance.total_balance) $($balance.currency)"
```

**Expected Response:**
```json
{
  "total_balance": 500.0,
  "currency": "USD"
}
```

**✅ PASS if:** Status 200, balance matches

---

#### Test Case 3.3: List All User Accounts
```powershell
$token = "YOUR_ACCESS_TOKEN_HERE"

$response = Invoke-WebRequest -Method GET `
    -Uri "http://localhost:8000/api/accounts" `
    -Headers @{
        "Authorization" = "Bearer $token"
    }

$accounts = $response.Content | ConvertFrom-Json
Write-Host "✅ Found $($accounts.Count) account(s)"
$accounts | ForEach-Object {
    Write-Host "  - $($_.account_number): $$($_.balance)"
}
```

**Expected Response:** Array of account objects

**✅ PASS if:** Status 200, returns user's accounts only

---

#### Test Case 3.4: Minimum Deposit Validation
```powershell
$token = "YOUR_ACCESS_TOKEN_HERE"

$body = @{
    account_type = "savings"
    initial_deposit = 5.00
} | ConvertTo-Json

Invoke-WebRequest -Method POST `
    -Uri "http://localhost:8000/api/accounts" `
    -Headers @{
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $token"
    } `
    -Body $body `
    -ErrorAction SilentlyContinue
```

**Expected Response:** Status 422, validation error

**✅ PASS if:** Rejected due to minimum $10 requirement

---

### Test 4: Security Tests

#### Test Case 4.1: SQL Injection Prevention
```powershell
# Attempt SQL injection in email
$body = @{
    email = "admin' OR '1'='1' --"
    password = "AnyPassword123!"
} | ConvertTo-Json

Invoke-WebRequest -Method POST `
    -Uri "http://localhost:8000/api/auth/login" `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body `
    -ErrorAction SilentlyContinue
```

**Expected Response:** Status 422 (validation error) - not SQL injection

**✅ PASS if:** Invalid email format detected

---

#### Test Case 4.2: Missing Authentication Header
```powershell
# Try to access protected endpoint without token
Invoke-WebRequest -Method GET `
    -Uri "http://localhost:8000/api/accounts" `
    -Headers @{"Content-Type"="application/json"} `
    -ErrorAction SilentlyContinue
```

**Expected Response:** Status 401 Unauthorized

**✅ PASS if:** Access denied without token

---

#### Test Case 4.3: Invalid Token Rejection
```powershell
# Try with malformed token
Invoke-WebRequest -Method GET `
    -Uri "http://localhost:8000/api/accounts" `
    -Headers @{
        "Authorization" = "Bearer invalid.token.here"
    } `
    -ErrorAction SilentlyContinue
```

**Expected Response:** Status 401 Unauthorized

**✅ PASS if:** Invalid token rejected

---

#### Test Case 4.4: Cross-User Access Prevention
```powershell
# User A gets their account
$tokenA = "ALICE_TOKEN_HERE"
$accountB_ID = "SOME_OTHER_USER_ACCOUNT_ID"

# User A tries to access User B's account
Invoke-WebRequest -Method GET `
    -Uri "http://localhost:8000/api/accounts/$accountB_ID" `
    -Headers @{
        "Authorization" = "Bearer $tokenA"
    } `
    -ErrorAction SilentlyContinue
```

**Expected Response:** Status 403 Forbidden or 404 Not Found

**✅ PASS if:** User cannot access other's account

---

### Test 5: Get Current User Info

#### Test Case 5.1: User Profile Access
```powershell
$token = "YOUR_ACCESS_TOKEN_HERE"

$response = Invoke-WebRequest -Method GET `
    -Uri "http://localhost:8000/api/users/me" `
    -Headers @{
        "Authorization" = "Bearer $token"
    }

$user = $response.Content | ConvertFrom-Json
Write-Host "✅ Current User Information:"
Write-Host "  Email: $($user.email)"
Write-Host "  Name: $($user.full_name)"
Write-Host "  Phone: $($user.phone)"
Write-Host "  Role: $($user.role)"
Write-Host "  KYC Level: $($user.kyc_level)"
```

**Expected Response:**
```json
{
  "id": "...",
  "email": "alice@bank.local",
  "full_name": "Alice Developer",
  "phone": "+1 555-0001",
  "role": "customer",
  "kyc_level": 0,
  "kyc_status": "pending",
  "is_active": true,
  "created_at": "2026-03-18T..."
}
```

**✅ PASS if:** Status 200, returns current user's info

---

### Test 6: Error Handling

#### Test Case 6.1: Invalid UUID Format
```powershell
$token = "YOUR_ACCESS_TOKEN_HERE"

Invoke-WebRequest -Method GET `
    -Uri "http://localhost:8000/api/accounts/not-a-uuid" `
    -Headers @{
        "Authorization" = "Bearer $token"
    } `
    -ErrorAction SilentlyContinue
```

**Expected Response:** Status 422 UNPROCESSABLE ENTITY

**✅ PASS if:** Format validation error received

---

#### Test Case 6.2: Non-existent Resource
```powershell
$token = "YOUR_ACCESS_TOKEN_HERE"

Invoke-WebRequest -Method GET `
    -Uri "http://localhost:8000/api/accounts/00000000-0000-0000-0000-000000000000" `
    -Headers @{
        "Authorization" = "Bearer $token"
    } `
    -ErrorAction SilentlyContinue
```

**Expected Response:** Status 404 NOT FOUND

**✅ PASS if:** Proper error handling for non-existent resource

---

### Test 7: API Documentation

#### Test Case 7.1: Swagger Documentation Access
```
Open in browser: http://localhost:8000/docs
```

**Expected:** Interactive API documentation with:
- All endpoints listed
- Request/response schemas
- Try it Out functionality

**✅ PASS if:** Documentation loads and endpoints visible

---

## 🔐 SECURITY CHECKLIST

### Before Production Deployment
- [ ] Change SECRET_KEY to new random value
- [ ] Update CORS origins to specific domains
- [ ] Enable HTTPS/SSL certificates
- [ ] Set secure cookie flags
- [ ] Enable rate limiting
- [ ] Configure database backups
- [ ] Set up logging and monitoring
- [ ] Implement error tracking (Sentry)
- [ ] Add API versioning
- [ ] Document all API changes

### Generate New SECRET_KEY
```powershell
# Generate secure key
$key = [System.Security.Cryptography.RNGCryptoServiceProvider]::new()
$bytes = [byte[]]::new(32)
$key.GetBytes($bytes)
$secretKey = [System.BitConverter]::ToString($bytes) -replace '-', ''
Write-Host "New SECRET_KEY: $secretKey"
```

Then update `backend/.env`:
```
SECRET_KEY=<generated_value>
```

---

## 📊 TEST SUMMARY TEMPLATE

### Summary Report
```
Date: March 18, 2026
Environment: Development (Local)
Duration: [X hours]

Tests Executed: 20
Tests Passed: __
Tests Failed: __
Tests Skipped: __

Critical Issues: __
High Priority: __
Medium Priority: __
Low Priority: __

Overall Status: ✅ READY / ⚠️ NEEDS FIXES / 🔴 BLOCKED

Next Steps:
- [ ]
- [ ]
```

---

## 🆘 TROUBLESHOOTING

### 401 Unauthorized on Protected Endpoints
**Solution:** Token might be expired or invalid
```powershell
# Get new token by logging in again
$body = @{
    email = "your@email.com"
    password = "YourPassword123!"
} | ConvertTo-Json

$response = Invoke-WebRequest -Method POST `
    -Uri "http://localhost:8000/api/auth/login" `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body

$token = ($response.Content | ConvertFrom-Json).access_token
```

### 422 Validation Error
**Solution:** Check required fields and constraints
```
Common validations:
- email: Must be valid email format
- password: Min 8 characters
- amount: Must be > 0
- account_type: "savings", "checking", or "fixed_deposit"
- phone: Optional, but if provided must be valid format
```

### 500 Internal Server Error
**Solution:** Check backend logs
- Restart backend: `python run.py`
- Review error messages in terminal
- Check database connectivity

### Connection Refused on localhost:8000
**Solution:** Backend not running
```powershell
cd backend
python run.py
```
Should show: `Uvicorn running on http://0.0.0.0:8000`

---

## 💡 TIPS FOR TESTING

1. **Use Postman**: Easier than PowerShell for complex tests
   - Import API docs from: `http://localhost:8000/openapi.json`

2. **Save Tokens**: Keep tokens from login for multiple requests
   - Set as Postman environment variables

3. **Test Flow**: Register → Login → Create Account → Check Balance

4. **Monitor Database**: 
   - SQLite: Check `backend/bank.db` changes
   - PostgreSQL: Query database directly

5. **Use Browser DevTools**:
   - Frontend: Press F12 in browser
   - Network tab: See API calls
   - Console tab: Check for errors

6. **API Response Times**:
   - Should be < 500ms for most operations
   - Login/Register may take up to 1 second

---

*For more details, see: QA_SECURITY_TEST_REPORT.md*
