import { test, expect } from '@playwright/test';
import seed from '../.artifacts/seed.json' with { type: 'json' };

test.describe('Confluence Page Content Validation', () => {
  test.beforeEach(async ({ page }) => {
    if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
    await page.goto(seed.confluence.pageUrl);
    await page.waitForLoadState('networkidle');
  });

  test('Confluence page renders markdown/ADF properly', async ({ page }) => {
    const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();

    // Basic content validation
    await expect(article).toContainText('Formatting Elements Being Tested');
    await expect(article).toContainText('Test Objectives');
    await expect(article).toContainText('Bullet Points');
    await expect(article).toContainText('Numbered Lists');

    // Header validation
    const headers = article.locator('h1, h2, h3, h4, h5, h6');
    await expect(headers).toHaveCountGreaterThan(0);
    await expect(headers.first()).toContainText('Formatting Elements Being Tested');

    // Code block validation
    const codeBlocks = article.locator('pre, .code-block');
    await expect(codeBlocks).toHaveCountGreaterThan(0);
    await expect(codeBlocks).toContainText('console.log');

    // List validation
    const bulletLists = article.locator('ul');
    await expect(bulletLists).toHaveCountGreaterThan(0);
    await expect(bulletLists.locator('li')).toContainText('Bullet Points');

    const numberedLists = article.locator('ol');
    await expect(numberedLists).toHaveCountGreaterThan(0);
    await expect(numberedLists.locator('li').first()).toContainText('One');

    // Table validation
    const tables = article.locator('table');
    await expect(tables).toHaveCountGreaterThan(0);
    await expect(tables.locator('th')).toContainText('Col A');
    await expect(tables.locator('td')).toContainText('A');

    // Blockquote validation
    const blockquotes = article.locator('blockquote, .quote');
    await expect(blockquotes).toHaveCountGreaterThan(0);
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
    // Validate page title
    await expect(page.locator('h1, [data-testid="page-title"], .page-title')).toContainText('Visual Render Validation');
    
    // Validate breadcrumbs are present
    const breadcrumbs = page.locator('[data-testid="breadcrumbs"], .breadcrumbs, nav');
    await expect(breadcrumbs).toBeVisible();
    
    // Validate space information
    await expect(breadcrumbs).toContainText(/\w+/); // Should contain space name
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
    // Test page actions menu
    const pageActions = page.locator('[data-testid="page-actions"], .page-toolbar, #page-toolbar');
    await expect(pageActions).toBeVisible();
    
    // Test edit button exists (user may not have permissions)
    const editButton = page.locator('[data-testid="edit-page"], .edit-link, #editPageLink');
    if (await editButton.isVisible()) {
      await expect(editButton).toBeVisible();
    }
  });

  test('Confluence content structure accessibility', async ({ page }) => {
    const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();
    
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
      await expect(list.locator('li')).toHaveCountGreaterThan(0);
    }
    
    // Check for table accessibility
    const tables = article.locator('table');
    for (let i = 0; i < await tables.count(); i++) {
      const table = tables.nth(i);
      // Should have headers
      await expect(table.locator('th')).toHaveCountGreaterThan(0);
    }
  });
});
