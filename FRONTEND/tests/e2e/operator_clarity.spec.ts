import { test, expect } from '@playwright/test';

test.describe('Layer 4: Operator Clarity', () => {
  test.beforeEach(async ({ page }) => {
    // Setup Auth and Tenant
    await page.addInitScript(() => {
      window.localStorage.setItem('auth_token', 'test-token');
      window.localStorage.setItem('auth_tenant_id', '00000000-0000-0000-0000-000000000000');
      window.localStorage.setItem('auth_user', JSON.stringify({
        id: 'user-123', email: 'test@example.com', role: 'OPERATOR', tenant_id: '00000000-0000-0000-0000-000000000000'
      }));
      window.localStorage.setItem('demoMode', 'false');
    });
  });

  test('Task status transitions are rendered correctly', async ({ page }) => {
    // Mock task list with various statuses
    await page.route('**/tasks', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify([
          { id: 't1', status: 'PENDING', task_type: 'DISCOVER' },
          { id: 't2', status: 'CLAIMED', task_type: 'APPLY' },
          { id: 't3', status: 'COMPLETED', task_type: 'APPLY' },
          { id: 't4', status: 'FAILED', task_type: 'APPLY', error_message: 'Timeout' }
        ])
      });
    });

    await page.goto('/tasks');
    await expect(page.locator('text=PENDING')).toBeVisible();
    await expect(page.locator('text=CLAIMED')).toBeVisible();
    await expect(page.locator('text=COMPLETED')).toBeVisible();
    await expect(page.locator('text=FAILED')).toBeVisible();
  });

  test('Confidence score and reasoning are rendered', async ({ page }) => {
    await page.route('**/tasks/task-456', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: 'task-456',
          status: 'COMPLETED',
          result: {
            predictions: {
                "Company Name": { value: "AOP", confidence: 0.95, reasoning: "Matched via RAG" },
                "Website": { value: "https://aop.com", confidence: 0.82, reasoning: "LLM high confidence" }
            }
          }
        })
      });
    });

    await page.goto('/tasks/task-456');
    await expect(page.locator('text=95%')).toBeVisible();
    await expect(page.locator('text=Matched via RAG')).toBeVisible();
  });

  test('Rejection reason is displayed', async ({ page }) => {
    await page.route('**/tasks/task-789', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: 'task-789',
          status: 'FAILED_OPERATOR_CANCEL',
          payload: { cancel_reason: "Duplicate application found" }
        })
      });
    });

    await page.goto('/tasks/task-789');
    await expect(page.locator('text=Duplicate application found')).toBeVisible();
  });

  test('Retry count is visible', async ({ page }) => {
    await page.route('**/tasks/task-retry', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: 'task-retry',
          status: 'FAILED',
          retry_count: 2,
          max_retries: 3
        })
      });
    });

    await page.goto('/tasks/task-retry');
    await expect(page.locator('text=2 / 3')).toBeVisible();
  });
});
