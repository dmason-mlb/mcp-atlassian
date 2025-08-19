import { test, expect } from '@playwright/test';
import seed from '../.artifacts/seed.json' with { type: 'json' };

test.describe('Jira Issue Content Validation', () => {
  test.beforeEach(async ({ page }) => {
    if (!seed?.jira?.issueUrl) test.skip(true, 'No Jira issue URL in seed.json');
    await page.goto(seed.jira.issueUrl);
    await page.waitForLoadState('networkidle');
  });

  test('Jira description renders markdown properly', async ({ page }) => {
    const content = page.locator('main, [data-test-id="issue-view"], [data-testid="issue-view"]').first();

    // Basic content validation
    await expect(content).toContainText('Test Objectives');
    await expect(content).toContainText('Bullet Points');
    await expect(content).toContainText('Numbered Lists');

    // Code block validation
    await expect(content.locator('pre')).toHaveCountGreaterThan(0);
    await expect(content.locator('code')).toContainText('console.log');

    // List validation
    const bulletList = content.locator('ul');
    await expect(bulletList).toHaveCountGreaterThan(0);
    await expect(bulletList.locator('li')).toContainText('Bullet Points');

    const numberedList = content.locator('ol');
    await expect(numberedList).toHaveCountGreaterThan(0);
    await expect(numberedList.locator('li').first()).toContainText('One');

    // Table validation
    const table = content.locator('table');
    await expect(table).toHaveCountGreaterThan(0);
    await expect(table.locator('th')).toContainText('Col A');
    await expect(table.locator('td')).toContainText('A');

    // Blockquote validation
    const blockquote = content.locator('blockquote');
    await expect(blockquote).toHaveCountGreaterThan(0);
    await expect(blockquote).toContainText('Blockquote');

    // Inline code validation
    const inlineCode = content.locator('code').first();
    await expect(inlineCode).toContainText('inline code');

    // Screenshot for visual regression
    await expect(content).toHaveScreenshot('jira-issue-content.png', {
      maxDiffPixelRatio: 0.03,
    });
  });

  test('Jira issue metadata is displayed correctly', async ({ page }) => {
    // Validate issue key is displayed
    await expect(page.locator('[data-testid="issue-header"], .issue-header')).toContainText(/[A-Z]+-\d+/);

    // Validate title is displayed
    await expect(page.locator('h1, [data-testid="issue-title"]')).toContainText('Visual Render Validation');

    // Validate status is displayed
    await expect(page.locator('[data-testid="status"], .status')).toBeVisible();
  });

  test('Jira comments section loads and displays properly', async ({ page }) => {
    // Navigate to comments section
    const commentsSection = page.locator('[data-testid="issue-comments"], #activitymodule, .activity-container');

    if (await commentsSection.isVisible()) {
      // Validate comment content if present
      const comments = commentsSection.locator('.comment, [data-testid="comment"]');
      if (await comments.count() > 0) {
        await expect(comments.first()).toContainText('E2E seed comment');

        // Validate comment formatting
        await expect(comments.first().locator('code')).toContainText('code');
        await expect(comments.first().locator('strong, b')).toContainText('text');
      }
    }
  });

  test('Jira attachments display correctly', async ({ page }) => {
    const attachmentsSection = page.locator('[data-testid="attachments"], .attachment-container, .issue-attachments');

    if (await attachmentsSection.isVisible()) {
      // Check for text attachment
      await expect(attachmentsSection).toContainText('test-attachment.txt');

      // Check for image attachment if present
      const imageAttachment = attachmentsSection.locator('img, [data-testid="attachment-image"]');
      if (await imageAttachment.count() > 0) {
        await expect(imageAttachment.first()).toBeVisible();
      }
    }
  });
});
