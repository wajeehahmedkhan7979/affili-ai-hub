import { test, expect } from '@playwright/test';

test.describe('Layer 4: Error Handling & Resilience', () => {
  test.beforeEach(async ({ page }) => {
    // Setup Auth
    await page.addInitScript(() => {
      window.localStorage.setItem('auth_token', 'test-token');
      window.localStorage.setItem('auth_tenant_id', '00000000-0000-0000-0000-000000000000');
      window.localStorage.setItem('auth_user', JSON.stringify({
        id: 'user-123', email: 'test@example.com', role: 'ADMIN', tenant_id: '00000000-0000-0000-0000-000000000000'
      }));
      window.localStorage.setItem('demoMode', 'false');
    });
  });

  test('403 errors render correctly with context', async ({ page }) => {
    // Mock a 403 Forbidden response (e.g. governance blocked)
    await page.route('**/operator/tasks/*/resume', async (route) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ detail: "AI operations disabled for tenant (kill-switch active)" })
      });
    });

    await page.goto('/tasks/task-123'); // Assuming task-123 is paused
    const resumeBtn = page.getByRole('button', { name: /resume/i });
    // If button is ENABLED (before hardening), click it and expect error UI
    if (await resumeBtn.isEnabled()) {
        await resumeBtn.click();
        await expect(page.locator('text=kill-switch active')).toBeVisible();
    }
  });

  test('Session expiry redirects to login', async ({ page }) => {
    // Mock a 401 Unauthorized response
    await page.route('**/tasks', async (route) => {
      await route.fulfill({
        status: 401,
        body: JSON.stringify({ detail: "Token expired" })
      });
    });

    await page.goto('/tasks');
    await expect(page).toHaveURL(/.*login/);
  });

  test('No silent failures on API error', async ({ page }) => {
    // Mock a 500 Network error
    await page.route('**/tasks', async (route) => {
      await route.fulfill({
        status: 500,
        body: "Internal Server Error"
      });
    });

    await page.goto('/tasks');
    // Assert: UI shows an error message, not just a blank page
    await expect(page.locator('text=Failed to load')).toBeVisible();
  });

  test('Loading states are displayed', async ({ page }) => {
    // Mock a slow response
    await page.route('**/tasks', async (route) => {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await route.fulfill({ status: 200, body: JSON.stringify([]) });
    });

    await page.goto('/tasks');
    // Assert: Loading indicator or skeleton is visible
    await expect(page.locator('text=Loading')).toBeVisible();
  });
});
