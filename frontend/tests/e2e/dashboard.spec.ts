import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.getByLabel(/email/i).fill('admin@example.com');
    await page.getByLabel(/password/i).fill('AdminPass123!');
    await page.getByRole('button', { name: /sign in/i }).click();
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should display dashboard with accounts', async ({ page }) => {
    // Check dashboard elements
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
    await expect(page.getByText(/total balance/i)).toBeVisible();
    await expect(page.getByText(/recent transactions/i)).toBeVisible();
  });

  test('should show account cards', async ({ page }) => {
    // Check for account cards or list
    const accountsSection = page.getByText(/accounts/i).first();
    await expect(accountsSection).toBeVisible();
  });

  test('should navigate to transfer page', async ({ page }) => {
    // Click transfer link/button
    await page.getByRole('link', { name: /transfer/i }).click();

    // Should navigate to transfer page
    await expect(page).toHaveURL(/\/transfer/);
  });

  test('should navigate to transactions page', async ({ page }) => {
    // Click transactions link
    await page.getByRole('link', { name: /transactions/i }).click();

    // Should navigate to transactions page
    await expect(page).toHaveURL(/\/transactions/);
  });

  test('should display user profile in header', async ({ page }) => {
    // Check for user profile elements
    await expect(page.getByText(/admin@example.com/i)).toBeVisible();
  });
});

test.describe('Account Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.getByLabel(/email/i).fill('admin@example.com');
    await page.getByLabel(/password/i).fill('AdminPass123!');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL(/\/dashboard/);
  });

  test('should navigate to accounts page', async ({ page }) => {
    await page.getByRole('link', { name: /accounts/i }).click();
    await expect(page).toHaveURL(/\/accounts/);
  });

  test('should display accounts list', async ({ page }) => {
    await page.getByRole('link', { name: /accounts/i }).click();

    // Should show accounts
    await expect(page.getByText(/account number/i)).toBeVisible();
  });
});
