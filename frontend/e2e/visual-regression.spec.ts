import { test, expect } from '@playwright/test';
import { DETERMINISTIC_E2E_CASES, DETERMINISTIC_GRAPH } from './fixtures/test-fixtures';

test.describe('RazorShield AI — Real Visual Regression Screenshot Suite (@visual)', () => {

  test.beforeEach(async ({ page }) => {
    // Intercept backend API routes to serve controlled deterministic fixture data for pixel stability
    await page.route('**/api/v1/cases*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'SUCCESS', data: DETERMINISTIC_E2E_CASES }),
      });
    });

    await page.route('**/api/v1/graph*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'SUCCESS', data: DETERMINISTIC_GRAPH }),
      });
    });
  });

  const majorRoutes = [
    { name: '01-command-center', nav: /Command Center/i },
    { name: '02-work-queue', nav: /Analyst Work Queue/i },
    { name: '03-transactions', nav: /Live Transactions/i },
    { name: '04-investigations', nav: /Investigations/i },
    { name: '05-fraud-graph', nav: /Fraud Graph/i },
    { name: '06-ai-investigator', nav: /AI Investigator/i },
    { name: '07-evidence', nav: /Evidence Explorer/i },
    { name: '08-policy', nav: /Policy Decisions/i },
    { name: '09-action-gateway', nav: /Action Gateway/i },
    { name: '10-audit', nav: /Audit Trail/i },
  ];

  for (const route of majorRoutes) {
    test(`Visual screenshot assertion — ${route.name}`, async ({ page }) => {
      await page.goto('/');
      
      const navBtn = page.getByRole('button', { name: route.nav });
      await expect(navBtn).toBeVisible();
      await navBtn.click();

      // Ensure main page content area is visible and settled
      const mainContainer = page.locator('main');
      await expect(mainContainer).toBeVisible();

      // Real Playwright Visual Snapshot Assertion (Strict 2% pixel tolerance threshold)
      await expect(page).toHaveScreenshot(`${route.name}.png`, {
        maxDiffPixelRatio: 0.02,
        animations: 'disabled',
      });
    });
  }
});
