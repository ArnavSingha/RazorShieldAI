import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('RazorShield AI — Full-Surface Accessibility Scan Suite (@a11y)', () => {

  const routesToScan = [
    { name: 'Command Center', buttonName: /Command Center/i },
    { name: 'Work Queue', buttonName: /Analyst Work Queue/i },
    { name: 'Live Transactions', buttonName: /Live Transactions/i },
    { name: 'Investigations', buttonName: /Investigations/i },
    { name: 'Fraud Graph', buttonName: /Fraud Graph/i },
    { name: 'AI Investigator', buttonName: /AI Investigator/i },
    { name: 'Evidence Explorer', buttonName: /Evidence Explorer/i },
    { name: 'Policy Decisions', buttonName: /Policy Decisions/i },
    { name: 'Action Gateway', buttonName: /Action Gateway/i },
    { name: 'Audit Trail', buttonName: /Audit Trail/i },
  ];

  for (const route of routesToScan) {
    test(`A11y Scan — ${route.name}`, async ({ page }) => {
      await page.goto('/');
      
      const navBtn = page.getByRole('button', { name: route.buttonName });
      await expect(navBtn).toBeVisible();
      await navBtn.click();

      // Execute full axe-core accessibility scan (STRICT color-contrast verification enabled)
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .disableRules(['svg-img-alt'])
        .analyze();

      // Filter critical or serious ARIA violations
      const criticalViolations = accessibilityScanResults.violations.filter(
        (v) => v.impact === 'critical' || v.impact === 'serious'
      );

      if (criticalViolations.length > 0) {
        console.log(`--- VIOLATIONS FOR ${route.name} ---`);
        for (const v of criticalViolations) {
          console.log(`[${v.impact?.toUpperCase()}] ${v.id}: ${v.help}`);
          for (const node of v.nodes) {
            console.log(`  Target: ${node.target.join(', ')}`);
          }
        }
      }

      expect(criticalViolations.length).toBe(0);
    });
  }
});
