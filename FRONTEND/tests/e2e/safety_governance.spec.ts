import { test, expect } from '@playwright/test';

test.describe('Layer 4: Safety Visibility', () => {
  test.beforeEach(async ({ page }) => {
    // Setup Auth and Tenant
    await page.addInitScript(() => {
      window.localStorage.setItem('auth_token', 'test-token');
      window.localStorage.setItem('auth_tenant_id', '00000000-0000-0000-0000-000000000000');
      window.localStorage.setItem('auth_user', JSON.stringify({
        id: 'user-123',
        email: 'test@example.com',
        role: 'ADMIN',
        tenant_id: '00000000-0000-0000-0000-000000000000'
      }));
      window.localStorage.setItem('demoMode', 'false'); // Force real API
    });
  });

  test('Kill-switch banner is visible when AI is disabled', async ({ page }) => {
    // Mock the governance status endpoint to return disabled
    await page.route('**/governance/tenant/**/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ai_enabled: false,
          status: 'DISABLED',
          reason: 'Emergency Safety Shutdown triggered by Admin',
          disabled_at: new Date().toISOString()
        })
      });
    });

    await page.goto('/');
    
    // Assert: Banner is visible with correct reason
    const banner = page.locator('text=Emergency Safety Shutdown');
    await expect(banner).toBeVisible();
    await expect(page.locator('text=AI Operations Disabled')).toBeVisible();
  });

  test('Resume button is disabled if tenant is disabled', async ({ page }) => {
    // Mock task endpoint (PAUSED)
    await page.route('**/tasks/task-123', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'task-123',
          status: 'PAUSED_FOR_CAPTCHA',
          task_type: 'SUBMIT_APPLICATION',
          payload: { signup_url: 'https://example.com' },
          retry_count: 0,
          max_retries: 3
        })
      });
    });

    // Mock governance status to disabled
    await page.route('**/governance/tenant/**/status', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ ai_enabled: false }) });
    });

    await page.goto('/tasks/task-123');
    
    // Assert: Resume button exists but is disabled (or shows blocked message)
    const resumeBtn = page.getByRole('button', { name: /resume/i });
    await expect(resumeBtn).toBeDisabled();
    await expect(page.locator('text=Action blocked by governance')).toBeVisible();
  });

  test('HITL required before submission', async ({ page }) => {
    // Mock program application flow
    await page.goto('/programs');
    const applyBtn = page.getByRole('button', { name: /apply/i }).first();
    await applyBtn.click();

    // Assert: UI shows "Awaiting Approval" or "Review Required" marker
    await expect(page.locator('text=Review Required')).toBeVisible();
    await expect(page.locator('text=Agent is waiting for your approval')).toBeVisible();
  });

  test('Whitelist rejection is shown clearly on 403', async ({ page }) => {
    // Mock a 403 rejection from whitelist policy
    await page.route('**/tasks', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({ detail: "Domain 'blocked.com' is not whitelisted for this tenant." })
        });
      } else {
        await route.fallback();
      }
    });

    await page.goto('/programs');
    // Simulate creating a task for a blocked domain (this might need specific UI interaction)
    // For now, we verify the error handling on the UI
    await page.evaluate(() => {
        // Trigger a fake 403 from the frontend code's perspective
        fetch('/api/v1/tasks', { method: 'POST', body: JSON.stringify({ payload: { url: 'blocked.com' } }) });
    });

    await expect(page.locator('text=not whitelisted')).toBeVisible();
  });
});
