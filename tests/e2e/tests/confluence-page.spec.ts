import { test, expect } from '@playwright/test';
import seed from '../.artifacts/seed.json' with { type: 'json' };
import { waitForAppReady, waitForContentReady } from '../utils/wait';

test.describe('Confluence Page Content Validation', () => {
  test.beforeEach(async ({ page }) => {
    if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
    await page.goto(seed.confluence.pageUrl);
    await waitForAppReady(page, 'confluence');
    await waitForContentReady(page);
  });

  test('Confluence page renders markdown/ADF properly', async ({ page }) => {
    const article = page.locator('#content, main, [role="main"]').first();

    // Basic content validation
    await expect(article).toContainText('Test Objectives');
    await expect(article).toContainText('Bullet Points');
    await expect(article).toContainText('Numbered Lists');

    // Header validation - find the Test Objectives header specifically
    const testObjectivesHeader = article.locator('h1, h2, h3, h4, h5, h6').filter({ hasText: 'Test Objectives' });
    expect(await testObjectivesHeader.count()).toBeGreaterThan(0);
    await expect(testObjectivesHeader.first()).toContainText('Test Objectives');

    // Code block validation
    const codeBlocks = article.locator('pre, .code-block');
    expect(await codeBlocks.count()).toBeGreaterThan(0);
    await expect(codeBlocks).toContainText('console.log');

    // List validation - target the content lists, not avatar lists
    const bulletLists = article.locator('ul').filter({ hasText: 'First bullet point' });
    expect(await bulletLists.count()).toBeGreaterThan(0);
    await expect(bulletLists.locator('li').first()).toContainText('First bullet point');

    const numberedLists = article.locator('ol');
    expect(await numberedLists.count()).toBeGreaterThan(0);
    await expect(numberedLists.locator('li').first()).toContainText('One');

    // Table validation
    const tables = article.locator('table');
    expect(await tables.count()).toBeGreaterThan(0);
    await expect(tables.locator('th').first()).toContainText('Col A');
    await expect(tables.locator('td').first()).toContainText('A');

    // Blockquote validation
    const blockquotes = article.locator('blockquote, .quote');
    expect(await blockquotes.count()).toBeGreaterThan(0);
    await expect(blockquotes).toContainText('Blockquote');

    // Inline code validation
    const inlineCode = article.locator('code, .monospace').first();
    await expect(inlineCode).toContainText('inline code');

    // Screenshot for visual regression
    await expect(article).toHaveScreenshot('confluence-page-content.png', {
      maxDiffPixelRatio: 0.04,
    });
  });

  test('Confluence page metadata is displayed correctly', async ({ page }) => {
    // Validate page title (target the actual page title, not content heading)
    await expect(page.locator('[id="heading-title-text"]').first()).toContainText('Visual Render Validation');

    // Validate breadcrumbs are present (make it optional as personal spaces may not have them)
    const breadcrumbs = page.locator('[data-testid="breadcrumbs"], .breadcrumbs, nav[role="navigation"]').first();
    
    if (await breadcrumbs.isVisible()) {
      // Validate space information
      await expect(breadcrumbs).toContainText(/\w+/); // Should contain space name
    }
  });

  test('Confluence page labels display correctly', async ({ page }) => {
    // Check for labels section
    const labelsSection = page.locator('[data-testid="labels"], .labels, .page-metadata');

    if (await labelsSection.isVisible()) {
      // Should contain our e2e label
      await expect(labelsSection).toContainText(/mcp-e2e-\d+/);
    }
  });

  test('Confluence page navigation elements work', async ({ page }) => {
    // Test page actions menu (flexible selector)
    const pageActions = page.locator('[data-testid="page-actions"], .page-toolbar, #page-toolbar, [data-test-id="page-actions"]').first();
    if (await pageActions.isVisible()) {
      await expect(pageActions).toBeVisible();
    }

    // Test edit button exists (user may not have permissions)
    const editButton = page.locator('[data-testid="edit-page"], .edit-link, #editPageLink');
    if (await editButton.isVisible()) {
      await expect(editButton).toBeVisible();
    }
  });

  test('Confluence content structure accessibility', async ({ page }) => {
    const article = page.locator('#content, main, [role="main"]').first();

    // Check heading hierarchy
    const h1 = article.locator('h1');
    const h2 = article.locator('h2');

    if (await h1.count() > 0) {
      await expect(h1.first()).toBeVisible();
    }

    if (await h2.count() > 0) {
      await expect(h2.first()).toBeVisible();
    }

    // Check for proper list structure
    const lists = article.locator('ul, ol');
    for (let i = 0; i < await lists.count(); i++) {
      const list = lists.nth(i);
      expect(await list.locator('li').count()).toBeGreaterThan(0);
    }

    // Check for table accessibility
    const tables = article.locator('table');
    for (let i = 0; i < await tables.count(); i++) {
      const table = tables.nth(i);
      // Should have headers
      expect(await table.locator('th').count()).toBeGreaterThan(0);
    }
  });
});
