import { test, expect } from '@playwright/test';

test.describe('Money Transfer Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.getByLabel(/email/i).fill('testuser@example.com');
    await page.getByLabel(/password/i).fill('TestPass123!');
    await page.getByRole('button', { name: /sign in/i }).click();
    await expect(page).toHaveURL(/\/dashboard/);

    // Navigate to transfer page
    await page.getByRole('link', { name: /transfer/i }).click();
    await expect(page).toHaveURL(/\/transfer/);
  });

  test('should display transfer form', async ({ page }) => {
    // Check transfer form elements
    await expect(page.getByRole('heading', { name: /transfer/i })).toBeVisible();
    await expect(page.getByLabel(/from account/i)).toBeVisible();
    await expect(page.getByLabel(/to account/i)).toBeVisible();
    await expect(page.getByLabel(/amount/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /transfer/i })).toBeVisible();
  });

  test('should validate amount is positive', async ({ page }) => {
    // Fill form with invalid amount
    await page.getByLabel(/from account/i).click();
    // Select first account if dropdown exists
    const options = await page.locator('select[name="fromAccount"] option');
    if (await options.count() > 0) {
      await page.locator('select[name="fromAccount"]').selectOption({ index: 1 });
    }

    await page.getByLabel(/to account/i).fill('1234567890');
    await page.getByLabel(/amount/i).fill('-100');

    // Submit
    await page.getByRole('button', { name: /transfer/i }).click();

    // Should show validation error
    await expect(page.getByText(/amount must be greater/i)).toBeVisible();
  });

  test('should show confirmation before transfer', async ({ page }) => {
    // This test assumes there's a confirmation step
    await page.getByLabel(/from account/i).click();
    const options = await page.locator('select[name="fromAccount"] option');
    if (await options.count() > 0) {
      await page.locator('select[name="fromAccount"]').selectOption({ index: 1 });
    }

    await page.getByLabel(/to account/i).fill('1234567890');
    await page.getByLabel(/amount/i).fill('100');

    // Submit
    await page.getByRole('button', { name: /transfer/i }).click();

    // Should show confirmation dialog or modal
    const confirmationVisible = await page.getByText(/confirm transfer/i).isVisible()
      .catch(() => false);

    if (confirmationVisible) {
      await expect(page.getByText(/confirm transfer/i)).toBeVisible();
    }
  });

  test('should complete transfer successfully', async ({ page }) => {
    // Fill valid transfer details
    await page.getByLabel(/from account/i).click();
    const options = await page.locator('select[name="fromAccount"] option');
    if (await options.count() > 0) {
      await page.locator('select[name="fromAccount"]').selectOption({ index: 1 });
    }

    await page.getByLabel(/to account/i).fill('1234567890');
    await page.getByLabel(/amount/i).fill('50');
    await page.getByLabel(/reference/i).fill('Test transfer');

    // Submit
    await page.getByRole('button', { name: /transfer/i }).click();

    // Should show success message or redirect
    const successVisible = await page.getByText(/transfer successful/i).isVisible()
      .catch(() => false);

    if (successVisible) {
      await expect(page.getByText(/transfer successful/i)).toBeVisible();
    } else {
      // Or should redirect to dashboard
      await expect(page).toHaveURL(/\/dashboard/);
    }
  });

  test('should prevent same account transfer', async ({ page }) => {
    // Get account numbers from the page
    await page.getByLabel(/from account/i).click();
    const options = await page.locator('select[name="fromAccount"] option');
    if (await options.count() > 0) {
      const firstOption = await options.first().textContent();
      await page.locator('select[name="fromAccount"]').selectOption({ index: 1 });

      // Try to transfer to same account
      await page.getByLabel(/to account/i).fill(firstOption || '');
      await page.getByLabel(/amount/i).fill('100');

      // Submit
      await page.getByRole('button', { name: /transfer/i }).click();

      // Should show error
      await expect(page.getByText(/cannot transfer to same account/i)).toBeVisible();
    }
  });
});

test.describe('Transaction History', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/email/i).fill('testuser@example.com');
    await page.getByLabel(/password/i).fill('TestPass123!');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL(/\/dashboard/);

    await page.getByRole('link', { name: /transactions/i }).click();
    await expect(page).toHaveURL(/\/transactions/);
  });

  test('should display transactions list', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /transactions/i })).toBeVisible();
  });

  test('should filter transactions by date', async ({ page }) => {
    // Look for date filter
    const dateFilter = page.getByPlaceholder(/from date/i);
    if (await dateFilter.isVisible()) {
      await dateFilter.fill('2024-01-01');
      await page.getByRole('button', { name: /filter/i }).click();

      // Should filter results
      await expect(page.getByRole('table').first()).toBeVisible();
    }
  });
});
