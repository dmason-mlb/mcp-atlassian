import { test, expect } from '@playwright/test';
import seed from '../.artifacts/seed.json' with { type: 'json' };

test.describe('ADF-Specific Features Validation', () => {
  test.beforeEach(async ({ page }) => {
    if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
    await page.goto(seed.confluence.pageUrl);
    await page.waitForLoadState('networkidle');
  });

  test('ADF panels render correctly', async ({ page }) => {
    const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();

    // Look for panel elements (info, warning, error, success, note)
    const panels = article.locator('.ak-editor-panel, .confluence-information-macro, .panel, [data-panel-type]');
    
    if (await panels.count() > 0) {
      // Validate panel structure
      for (let i = 0; i < await panels.count(); i++) {
        const panel = panels.nth(i);
        await expect(panel).toBeVisible();
        
        // Panels should have content
        await expect(panel).not.toBeEmpty();
        
        // Check for panel icons or indicators
        const panelIcon = panel.locator('.ak-editor-panel__icon, .panel-icon, .aui-icon');
        if (await panelIcon.count() > 0) {
          await expect(panelIcon.first()).toBeVisible();
        }
      }
    }
  });

  test('ADF status badges render correctly', async ({ page }) => {
    const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();

    // Look for status badge elements
    const statusBadges = article.locator('.status-macro, [data-node-type="status"], .ak-editor-status');
    
    if (await statusBadges.count() > 0) {
      for (let i = 0; i < await statusBadges.count(); i++) {
        const badge = statusBadges.nth(i);
        await expect(badge).toBeVisible();
        
        // Status badges should have text content
        await expect(badge).not.toBeEmpty();
        
        // Should have color styling
        const hasColorClass = await badge.evaluate(el => {
          const classList = Array.from(el.classList);
          return classList.some(className => 
            className.includes('green') || 
            className.includes('blue') || 
            className.includes('red') || 
            className.includes('yellow') ||
            className.includes('grey') ||
            className.includes('purple')
          );
        });
        
        const hasColorStyle = await badge.evaluate(el => {
          const style = window.getComputedStyle(el);
          return style.backgroundColor !== 'rgba(0, 0, 0, 0)' && style.backgroundColor !== 'transparent';
        });
        
        expect(hasColorClass || hasColorStyle).toBeTruthy();
      }
    }
  });

  test('ADF mentions render correctly', async ({ page }) => {
    const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();

    // Look for mention elements
    const mentions = article.locator('.mention, [data-node-type="mention"], .ak-editor-mention');
    
    if (await mentions.count() > 0) {
      for (let i = 0; i < await mentions.count(); i++) {
        const mention = mentions.nth(i);
        await expect(mention).toBeVisible();
        
        // Mentions should start with @ symbol or have user identifier
        const mentionText = await mention.textContent();
        expect(mentionText).toMatch(/@\w+|\w+\s+\w+/);
        
        // Should be clickable (have href or click handler)
        const isClickable = await mention.evaluate(el => {
          return el.hasAttribute('href') || 
                 el.style.cursor === 'pointer' ||
                 el.onclick !== null ||
                 el.getAttribute('role') === 'button';
        });
        
        expect(isClickable).toBeTruthy();
      }
    }
  });

  test('ADF emoji render correctly', async ({ page }) => {
    const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();

    // Look for emoji elements
    const emojis = article.locator('.emoji, [data-node-type="emoji"], .ak-editor-emoji, img[alt*="emoji"]');
    
    if (await emojis.count() > 0) {
      for (let i = 0; i < await emojis.count(); i++) {
        const emoji = emojis.nth(i);
        await expect(emoji).toBeVisible();
        
        // Check if it's an image emoji
        if (await emoji.locator('img').count() > 0) {
          const emojiImg = emoji.locator('img').first();
          await expect(emojiImg).toHaveAttribute('alt');
          await expect(emojiImg).toHaveAttribute('src');
        }
      }
    }
  });

  test('ADF expand/collapse sections work', async ({ page }) => {
    const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();

    // Look for expand/collapse elements
    const expandSections = article.locator('.expand-macro, [data-node-type="expand"], .ak-editor-expand');
    
    if (await expandSections.count() > 0) {
      for (let i = 0; i < await expandSections.count(); i++) {
        const expandSection = expandSections.nth(i);
        await expect(expandSection).toBeVisible();
        
        // Should have a title/trigger element
        const trigger = expandSection.locator('.expand-control, .expand-title, [role="button"]').first();
        if (await trigger.count() > 0) {
          await expect(trigger).toBeVisible();
          
          // Test expand/collapse functionality
          const isExpanded = await expandSection.evaluate(el => {
            return el.getAttribute('aria-expanded') === 'true' ||
                   !el.querySelector('.expand-content')?.hidden;
          });
          
          // Click to toggle
          await trigger.click();
          await page.waitForTimeout(500); // Allow for animation
          
          // Verify state changed
          const newExpandedState = await expandSection.evaluate(el => {
            return el.getAttribute('aria-expanded') === 'true' ||
                   !el.querySelector('.expand-content')?.hidden;
          });
          
          expect(newExpandedState).not.toBe(isExpanded);
        }
      }
    }
  });

  test('ADF date elements render correctly', async ({ page }) => {
    const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();

    // Look for date elements
    const dates = article.locator('.date-macro, [data-node-type="date"], .ak-editor-date, time');
    
    if (await dates.count() > 0) {
      for (let i = 0; i < await dates.count(); i++) {
        const dateElement = dates.nth(i);
        await expect(dateElement).toBeVisible();
        
        const dateText = await dateElement.textContent();
        // Should contain a date-like pattern
        expect(dateText).toMatch(/\d{1,4}[-\/]\d{1,2}[-\/]\d{1,4}|\d{1,2}[-\/]\d{1,4}|\w+\s+\d{1,2},?\s+\d{4}/);
        
        // Should have datetime attribute for time elements
        if (await dateElement.evaluate(el => el.tagName.toLowerCase() === 'time')) {
          await expect(dateElement).toHaveAttribute('datetime');
        }
      }
    }
  });

  test('ADF media elements render correctly', async ({ page }) => {
    const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();

    // Look for media elements
    const mediaElements = article.locator('.media-single, [data-node-type="mediaSingle"], .ak-editor-media, .media-wrapper');
    
    if (await mediaElements.count() > 0) {
      for (let i = 0; i < await mediaElements.count(); i++) {
        const media = mediaElements.nth(i);
        await expect(media).toBeVisible();
        
        // Should contain an image or video
        const mediaContent = media.locator('img, video, iframe');
        await expect(mediaContent).toHaveCountGreaterThan(0);
        
        // Media should have proper attributes
        const firstMedia = mediaContent.first();
        if (await firstMedia.evaluate(el => el.tagName.toLowerCase() === 'img')) {
          await expect(firstMedia).toHaveAttribute('src');
          await expect(firstMedia).toHaveAttribute('alt');
        }
      }
    }
  });

  test('ADF table enhancements render correctly', async ({ page }) => {
    const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();

    const tables = article.locator('table');
    
    if (await tables.count() > 0) {
      for (let i = 0; i < await tables.count(); i++) {
        const table = tables.nth(i);
        await expect(table).toBeVisible();
        
        // Check for ADF table enhancements
        const hasNumberedColumns = await table.locator('th[data-colindex], td[data-colindex]').count() > 0;
        const hasHighlightedCells = await table.locator('.ak-editor-table-cell-selected, .table-cell-highlight').count() > 0;
        const hasResizableColumns = await table.locator('.table-column-resize, [data-resize-handle]').count() > 0;
        
        // At least basic table structure should be present
        await expect(table.locator('th')).toHaveCountGreaterThan(0);
        await expect(table.locator('td')).toHaveCountGreaterThan(0);
        
        // Verify table accessibility
        const hasScope = await table.locator('th[scope]').count() > 0;
        if (!hasScope) {
          // Should at least have proper header structure
          await expect(table.locator('thead th, tbody th')).toHaveCountGreaterThan(0);
        }
      }
    }
  });

  test('ADF layout sections render correctly', async ({ page }) => {
    const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();

    // Look for layout sections (columns)
    const layouts = article.locator('.ak-editor-layout, [data-node-type="layoutSection"], .layout-section');
    
    if (await layouts.count() > 0) {
      for (let i = 0; i < await layouts.count(); i++) {
        const layout = layouts.nth(i);
        await expect(layout).toBeVisible();
        
        // Should contain layout columns
        const columns = layout.locator('.ak-editor-layout-column, .layout-column, [data-node-type="layoutColumn"]');
        await expect(columns).toHaveCountGreaterThan(0);
        
        // Columns should have content
        for (let j = 0; j < await columns.count(); j++) {
          const column = columns.nth(j);
          await expect(column).toBeVisible();
        }
      }
    }
  });
});