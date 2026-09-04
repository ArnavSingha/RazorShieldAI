import { test, expect } from '@playwright/test';
import { DETERMINISTIC_E2E_CASES, DETERMINISTIC_GRAPH } from './fixtures/test-fixtures';

test.describe('RazorShield AI — Strict E2E User Journeys & Fixture Suite', () => {

  test.beforeEach(async ({ page }) => {
    // Intercept API routes to serve deterministic mock data
    await page.route('**/api/v1/work-queue**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'SUCCESS',
          data: {
            total_count: 3,
            queue_items: [
              {
                incident_id: 'CASE-1042',
                investigation_id: 'cust_ring_01',
                name: 'TechSolutions Pvt Ltd',
                severity: 'CRITICAL',
                priority: 'P1_CRITICAL',
                risk_score: 94,
                confidence: 0.95,
                protected_exposure_inr: 310000,
                status: 'OPEN',
                owner: 'RISK_ANALYST_01',
                affected_entities: ['cust_ring_01', 'dev_shared_ring_09'],
                detected_patterns: ['SHARED_DEVICE_CLUSTER'],
                created_at: Date.now() / 1000,
                updated_at: Date.now() / 1000,
                sla_target_seconds: 3600,
                sla_deadline: Date.now() / 1000 + 3600,
                sla_seconds_remaining: 1800,
                sla_status: 'HEALTHY',
                age_seconds: 1800,
                required_action: 'BLOCK',
              },
            ],
          },
        }),
      });
    });

    await page.route('**/api/v1/cases**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'SUCCESS', data: DETERMINISTIC_E2E_CASES }),
      });
    });

    await page.route('**/api/v1/graph**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'SUCCESS', data: DETERMINISTIC_GRAPH }),
      });
    });
  });

  test('TEST 1 — Application Load & Base Branding Structure', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/RazorShield/i);

    // Verify main brand header using exact text matching
    await expect(page.getByText('RazorShield AI', { exact: true })).toBeVisible();

    // Verify main sidebar navigation container exists
    const nav = page.getByRole('navigation', { name: 'Main Navigation' });
    await expect(nav).toBeVisible();
  });

  test('TEST 2 — Complete Sidebar Route Navigation (13 Destinations)', async ({ page }) => {
    await page.goto('/');

    const routes = [
      { id: 'Analyst Work Queue', expectedText: /Work Queue|Intake/i },
      { id: 'Command Center', expectedText: /Command Center|System Health|Risk/i },
      { id: 'Live Transactions', expectedText: /Transactions|Live/i },
      { id: 'Investigations', expectedText: /Investigation|Case/i },
      { id: 'Fraud Graph', expectedText: /Fraud Graph|Graph|Connection/i },
      { id: 'AI Investigator', expectedText: /AI Investigator|Gemini|Reasoning/i },
      { id: 'Evidence Explorer', expectedText: /Evidence|Explorer|Proven/i },
      { id: 'Policy Decisions', expectedText: /Policy|Decisions|SLA/i },
      { id: 'Action Gateway', expectedText: /Action Gateway|Execution|Safety/i },
      { id: 'Audit Trail', expectedText: /Audit Trail|Ledger|SHA-256/i },
      { id: 'Attack Simulator', expectedText: /Attack Simulator|Scenario/i },
      { id: 'Chaos Lab', expectedText: /Chaos Lab|Fault/i },
      { id: 'Benchmarks', expectedText: /Benchmarks|Evaluation|Metrics/i },
    ];

    for (const route of routes) {
      const btn = page.getByRole('button', { name: new RegExp(route.id, 'i') });
      await expect(btn).toBeVisible();
      await btn.click();
      await expect(page.locator('main')).toContainText(route.expectedText);
    }
  });

  test('TEST 3 — Keyboard Accessibility & Focus Ring Navigation', async ({ page }) => {
    await page.goto('/');

    const firstBtn = page.getByRole('button', { name: /Analyst Work Queue/i });
    await firstBtn.focus();
    await expect(firstBtn).toBeFocused();

    await page.keyboard.press('Enter');
    await expect(page.locator('main')).toBeVisible();
  });

  test('TEST 4 — Work Queue Operations & Deterministic Case Data', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Analyst Work Queue/i }).click();

    // Strict assertion: Work queue header must be visible
    await expect(page.getByRole('heading', { name: /Analyst Work Queue/i })).toBeVisible();

    // Filter CRITICAL cases
    const criticalFilter = page.getByRole('button', { name: /Critical Risk/i });
    await expect(criticalFilter).toBeVisible();
    await criticalFilter.click();

    // Verify deterministic fixture data CASE-1042 renders explicitly
    await expect(page.getByText('CASE-1042').first()).toBeVisible();
  });

  test('TEST 5 — Strict Case Narrative & Guided Mode Wizard', async ({ page }) => {
    await page.goto('/');

    // Open Guided Mode via TopBar (Mandatory UI component)
    const guidedBtn = page.getByRole('button', { name: /Guided Mode/i });
    await expect(guidedBtn).toBeVisible();
    await guidedBtn.click();

    // Mandatory Step 1
    await expect(page.getByText('Step 1: What Happened?')).toBeVisible();

    // Step 2
    const nextBtn1 = page.getByRole('button', { name: 'Next' });
    await expect(nextBtn1).toBeVisible();
    await nextBtn1.click();
    await expect(page.getByText('Step 2: Why Is It Suspicious?')).toBeVisible();

    // Step 3
    const nextBtn2 = page.getByRole('button', { name: 'Next' });
    await expect(nextBtn2).toBeVisible();
    await nextBtn2.click();
    await expect(page.getByText('Step 3: What Does RazorShield Recommend?')).toBeVisible();

    // Step 4
    const nextBtn3 = page.getByRole('button', { name: 'Next' });
    await expect(nextBtn3).toBeVisible();
    await nextBtn3.click();
    await expect(page.getByText('Step 4: Review & Take Action')).toBeVisible();

    // Close guided mode via Done button
    const doneBtn = page.getByRole('button', { name: 'Done' });
    await expect(doneBtn).toBeVisible();
    await doneBtn.click();
  });

  test('TEST 6 — Action Gateway Pre-Execution Safety Verification', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Action Gateway/i }).click();

    // Verify Gateway State Machine Header & Active Badge
    await expect(page.getByRole('heading', { name: /Fail-Closed Action Gateway State Machine/i })).toBeVisible();
    await expect(page.getByText(/GATEWAY ACTIVE/i)).toBeVisible();
  });

  test('TEST 7 — Role Switcher & Active Role Indicator', async ({ page }) => {
    await page.goto('/');

    // Role indicator in sidebar footer
    await expect(page.getByText(/RISK_ANALYST/i).first()).toBeVisible();
  });

  test('TEST 8 — Global Command Search Palette (Ctrl+K)', async ({ page }) => {
    await page.goto('/');

    // Focus document and trigger Ctrl+K shortcut
    await page.locator('body').click();
    await page.keyboard.press('Control+KeyK');

    // Search input MUST appear
    const searchInput = page.getByPlaceholder(/Search database/i);
    await expect(searchInput).toBeVisible();
    await searchInput.fill('CASE-1042');
    await expect(searchInput).toHaveValue('CASE-1042');

    // Close modal via Escape
    await page.keyboard.press('Escape');
    await expect(searchInput).not.toBeVisible();
  });

  test('TEST 9 — Fraud Graph Connected-Account Analysis', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Fraud Graph/i }).click();

    // Fraud graph canvas container must be visible
    await expect(page.locator('main')).toContainText(/Fraud Graph|Graph|Connection/i);
  });
});
