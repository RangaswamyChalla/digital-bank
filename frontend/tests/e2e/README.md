# Digital Bank - E2E Tests

End-to-end tests using Playwright for critical user flows.

## Prerequisites

```bash
npm install
npx playwright install
```

## Running Tests

### Run all tests
```bash
npm run test:e2e
```

### Run with UI mode
```bash
npm run test:e2e:ui
```

### Run headed (see browser)
```bash
npm run test:e2e:headed
```

### Run specific test file
```bash
npx playwright test auth.spec.ts
```

### Run specific test
```bash
npx playwright test auth.spec.ts --grep "should login successfully"
```

## Test Coverage

### Authentication (`auth.spec.ts`)
- Login page display
- Empty form validation
- Successful login
- Invalid credentials error
- Navigation to register
- Registration form display
- New user registration
- Password validation

### Dashboard (`dashboard.spec.ts`)
- Dashboard display with accounts
- Account cards visibility
- Navigation to transfer
- Navigation to transactions
- User profile in header

### Money Transfer (`transfer.spec.ts`)
- Transfer form display
- Amount validation
- Confirmation step
- Successful transfer
- Same account prevention

### Transaction History (`transactions.spec.ts`)
- Transactions list display
- Date filtering

## CI Integration

The tests are configured to run in CI with:
- Retries on failure
- Parallel execution
- HTML report generation

Add to GitHub Actions:

```yaml
- name: Run E2E Tests
  run: npm run test:e2e
  env:
    CI: true
```

## Reports

Test reports are generated in `playwright-report/`.
Open with: `npx playwright show-report`
