import { test, expect } from '@playwright/test';
import seed from '../.artifacts/seed.json';

test('Confluence page renders markdown/ADF', async ({ page }) => {
  if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
  await page.goto(seed.confluence.pageUrl);

  const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"]').first();

  await expect(article).toContainText('Formatting Elements Being Tested');
  await expect(article.locator('h2, h3')).toHaveCountGreaterThan(0);
  await expect(article.locator('pre')).toHaveCountGreaterThan(0);

  await expect(article).toHaveScreenshot({
    maxDiffPixelRatio: 0.04,
  });
});
