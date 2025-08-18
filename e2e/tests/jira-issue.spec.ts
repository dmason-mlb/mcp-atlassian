import { test, expect } from '@playwright/test';
import seed from '../.artifacts/seed.json';

test('Jira description renders markdown properly', async ({ page }) => {
  if (!seed?.jira?.issueUrl) test.skip(true, 'No Jira issue URL in seed.json');
  await page.goto(seed.jira.issueUrl);

  const content = page.locator('main, [data-test-id="issue-view"], [data-testid="issue-view"]').first();

  await expect(content).toContainText('Test Objectives');
  await expect(content).toContainText('Bullet Points');
  await expect(content).toContainText('Numbered Lists');
  await expect(content.locator('pre')).toHaveCountGreaterThan(0);

  // Narrow screenshot to the description-like area
  await expect(content).toHaveScreenshot({
    maxDiffPixelRatio: 0.03,
  });
});
