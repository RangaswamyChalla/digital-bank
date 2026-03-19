import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should display login page correctly', async ({ page }) => {
    await page.goto('/login');

    // Check page title
    await expect(page).toHaveTitle(/Digital Bank/);

    // Check login form elements
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();

    // Check for register link
    await expect(page.getByText(/don't have an account/i)).toBeVisible();
  });

  test('should show validation errors for empty login form', async ({ page }) => {
    await page.goto('/login');

    // Try to submit empty form
    await page.getByRole('button', { name: /sign in/i }).click();

    // Check for validation messages
    await expect(page.getByText(/email is required/i)).toBeVisible();
    await expect(page.getByText(/password is required/i)).toBeVisible();
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    await page.goto('/login');

    // Fill login form
    await page.getByLabel(/email/i).fill('testuser@example.com');
    await page.getByLabel(/password/i).fill('TestPass123!');

    // Submit
    await page.getByRole('button', { name: /sign in/i }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/);

    // Should show user info
    await expect(page.getByText(/welcome/i)).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    // Fill with wrong credentials
    await page.getByLabel(/email/i).fill('wrong@example.com');
    await page.getByLabel(/password/i).fill('WrongPass123!');

    // Submit
    await page.getByRole('button', { name: /sign in/i }).click();

    // Should show error message
    await expect(page.getByText(/invalid email or password/i)).toBeVisible();
  });

  test('should navigate to register page', async ({ page }) => {
    await page.goto('/login');

    // Click register link
    await page.getByRole('link', { name: /register/i }).click();

    // Should navigate to register page
    await expect(page).toHaveURL(/\/register/);
  });
});

test.describe('Registration Flow', () => {
  test('should display registration form correctly', async ({ page }) => {
    await page.goto('/register');

    await expect(page.getByRole('heading', { name: /create account/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/^password$/i)).toBeVisible();
    await expect(page.getByLabel(/full name/i)).toBeVisible();
    await expect(page.getByLabel(/phone/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /register/i })).toBeVisible();
  });

  test('should register a new user successfully', async ({ page }) => {
    await page.goto('/register');

    // Generate unique email
    const uniqueEmail = `testuser${Date.now()}@example.com`;

    // Fill registration form
    await page.getByLabel(/email/i).fill(uniqueEmail);
    await page.getByLabel(/^password$/i).fill('TestPass123!');
    await page.getByLabel(/full name/i).fill('Test User');
    await page.getByLabel(/phone/i).fill('+1234567890');

    // Submit
    await page.getByRole('button', { name: /register/i }).click();

    // Should redirect to dashboard after successful registration
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should show validation errors for weak password', async ({ page }) => {
    await page.goto('/register');

    // Fill with weak password
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/^password$/i).fill('123');
    await page.getByLabel(/full name/i).fill('Test User');

    // Submit
    await page.getByRole('button', { name: /register/i }).click();

    // Should show password validation error
    await expect(page.getByText(/password must be at least/i)).toBeVisible();
  });
});
