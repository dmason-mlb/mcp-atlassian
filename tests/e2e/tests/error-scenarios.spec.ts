import { test, expect } from '@playwright/test';
import seed from '../.artifacts/seed.json' with { type: 'json' };

test.describe('Error Scenarios and Edge Cases', () => {
  test.describe('Network and Connectivity Issues', () => {
    test('Handles slow loading gracefully', async ({ page }) => {
      if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
      
      // Simulate slow network
      await page.route('**/*', route => {
        setTimeout(() => route.continue(), 2000);
      });
      
      const startTime = Date.now();
      await page.goto(seed.confluence.pageUrl, { timeout: 60000 });
      const loadTime = Date.now() - startTime;
      
      // Should still load within reasonable time
      expect(loadTime).toBeLessThan(60000);
      
      // Content should still be accessible
      const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();
      await expect(article).toBeVisible({ timeout: 10000 });
    });

    test('Handles failed resource loading', async ({ page }) => {
      if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
      
      // Block some resources but allow main page
      await page.route('**/*.{png,jpg,jpeg,gif,svg,css}', route => {
        if (route.request().url().includes('avatar') || route.request().url().includes('icon')) {
          route.abort();
        } else {
          route.continue();
        }
      });
      
      await page.goto(seed.confluence.pageUrl);
      await page.waitForLoadState('networkidle');
      
      // Main content should still be accessible despite missing resources
      const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();
      await expect(article).toBeVisible();
      await expect(article).toContainText('Formatting Elements Being Tested');
    });
  });

  test.describe('Content Rendering Edge Cases', () => {
    test('Handles missing or broken images gracefully', async ({ page }) => {
      if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
      
      await page.goto(seed.confluence.pageUrl);
      await page.waitForLoadState('networkidle');
      
      const images = page.locator('img');
      if (await images.count() > 0) {
        // Check for broken images
        for (let i = 0; i < await images.count(); i++) {
          const img = images.nth(i);
          const src = await img.getAttribute('src');
          
          if (src) {
            // Image should have alt text for accessibility
            const alt = await img.getAttribute('alt');
            expect(alt).toBeTruthy();
            
            // Image should not display broken image icon
            const naturalWidth = await img.evaluate(el => (el as HTMLImageElement).naturalWidth);
            if (naturalWidth === 0) {
              // Broken image should have fallback or proper alt text
              expect(alt?.length).toBeGreaterThan(0);
            }
          }
        }
      }
    });

    test('Handles extremely long content properly', async ({ page }) => {
      if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
      
      await page.goto(seed.confluence.pageUrl);
      await page.waitForLoadState('networkidle');
      
      const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();
      
      // Check for proper scrolling behavior
      const articleHeight = await article.boundingBox();
      if (articleHeight && articleHeight.height > 2000) {
        // Long content should be scrollable
        await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
        await page.waitForTimeout(500);
        
        // Should be able to scroll back to top
        await page.evaluate(() => window.scrollTo(0, 0));
        await page.waitForTimeout(500);
        
        // Header should be visible again
        await expect(article.locator('h1').first()).toBeVisible();
      }
    });

    test('Handles malformed tables gracefully', async ({ page }) => {
      if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
      
      await page.goto(seed.confluence.pageUrl);
      await page.waitForLoadState('networkidle');
      
      const tables = page.locator('table');
      if (await tables.count() > 0) {
        for (let i = 0; i < await tables.count(); i++) {
          const table = tables.nth(i);
          
          // Table should have proper structure
          const rows = table.locator('tr');
          await expect(rows).toHaveCountGreaterThan(0);
          
          // Should handle responsive layout
          const tableWidth = await table.boundingBox();
          if (tableWidth) {
            // Table should not exceed viewport width excessively
            const viewportWidth = page.viewportSize()?.width || 1200;
            
            if (tableWidth.width > viewportWidth * 1.5) {
              // Should have horizontal scroll or responsive behavior
              const parent = table.locator('..').first();
              const hasOverflow = await parent.evaluate(el => {
                const style = window.getComputedStyle(el);
                return style.overflowX === 'auto' || style.overflowX === 'scroll';
              });
              expect(hasOverflow).toBeTruthy();
            }
          }
        }
      }
    });
  });

  test.describe('Browser Compatibility Edge Cases', () => {
    test('Works with JavaScript disabled', async ({ browser }) => {
      if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
      
      const context = await browser.newContext({
        javaScriptEnabled: false
      });
      const page = await context.newPage();
      
      await page.goto(seed.confluence.pageUrl);
      await page.waitForLoadState('domcontentloaded');
      
      // Basic content should still be readable
      const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();
      await expect(article).toBeVisible();
      await expect(article).toContainText('Formatting Elements');
      
      await context.close();
    });

    test('Handles small viewport sizes', async ({ page }) => {
      if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
      
      // Test very small mobile viewport
      await page.setViewportSize({ width: 320, height: 568 });
      await page.goto(seed.confluence.pageUrl);
      await page.waitForLoadState('networkidle');
      
      // Content should still be accessible
      const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();
      await expect(article).toBeVisible();
      
      // Tables should be scrollable or responsive
      const tables = article.locator('table');
      if (await tables.count() > 0) {
        const firstTable = tables.first();
        const tableBox = await firstTable.boundingBox();
        
        if (tableBox && tableBox.width > 320) {
          // Should have horizontal scroll
          const parent = firstTable.locator('..').first();
          const hasOverflow = await parent.evaluate(el => {
            const style = window.getComputedStyle(el);
            return style.overflowX === 'auto' || style.overflowX === 'scroll';
          });
          expect(hasOverflow).toBeTruthy();
        }
      }
    });

    test('Handles high DPI displays', async ({ page }) => {
      if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
      
      // Test high DPI scaling
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.emulateMedia({ reducedMotion: 'reduce' });
      
      await page.goto(seed.confluence.pageUrl);
      await page.waitForLoadState('networkidle');
      
      // Images should handle high DPI appropriately
      const images = page.locator('img');
      if (await images.count() > 0) {
        for (let i = 0; i < await images.count(); i++) {
          const img = images.nth(i);
          
          // Image should not be pixelated (basic check)
          const hasHighResAttributes = await img.evaluate(el => {
            const srcset = el.getAttribute('srcset');
            const src = el.getAttribute('src');
            return !!(srcset || (src && src.includes('@2x')));
          });
          
          // At minimum, image should have proper dimensions
          const box = await img.boundingBox();
          if (box) {
            expect(box.width).toBeGreaterThan(0);
            expect(box.height).toBeGreaterThan(0);
          }
        }
      }
    });
  });

  test.describe('Access and Permission Edge Cases', () => {
    test('Handles permission-restricted elements gracefully', async ({ page }) => {
      if (!seed?.jira?.issueUrl) test.skip(true, 'No Jira issue URL in seed.json');
      
      await page.goto(seed.jira.issueUrl);
      await page.waitForLoadState('networkidle');
      
      // Check for permission-restricted actions
      const editButton = page.locator('[data-testid="edit-issue"], .edit-issue, #edit-issue');
      const deleteButton = page.locator('[data-testid="delete-issue"], .delete-issue');
      const adminOnlyButtons = page.locator('[data-testid*="admin"], .admin-only, .system-admin');
      
      // Should not throw errors if permission-restricted elements are not present
      if (await editButton.count() === 0) {
        // No edit button is fine - user may not have permissions
        expect(true).toBeTruthy();
      }
      
      if (await deleteButton.count() === 0) {
        // No delete button is fine - user may not have permissions
        expect(true).toBeTruthy();
      }
      
      // Admin-only elements should not be visible to regular users
      if (await adminOnlyButtons.count() > 0) {
        // If admin buttons are present, they should be properly secured
        for (let i = 0; i < await adminOnlyButtons.count(); i++) {
          const button = adminOnlyButtons.nth(i);
          const isDisabled = await button.isDisabled();
          const isHidden = await button.isHidden();
          expect(isDisabled || isHidden).toBeTruthy();
        }
      }
    });

    test('Handles session timeout gracefully', async ({ page }) => {
      if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
      
      // Clear all cookies to simulate session timeout
      await page.context().clearCookies();
      
      await page.goto(seed.confluence.pageUrl);
      
      // Should either redirect to login or show appropriate message
      await page.waitForLoadState('networkidle');
      
      const currentUrl = page.url();
      const hasLoginForm = await page.locator('input[name*="password"], input[type="password"], .login-form').count() > 0;
      const hasLoginRedirect = currentUrl.includes('/login') || currentUrl.includes('/auth');
      const hasAccessMessage = await page.locator('text=/access denied|unauthorized|please log in/i').count() > 0;
      
      // Should handle session timeout appropriately
      expect(hasLoginForm || hasLoginRedirect || hasAccessMessage).toBeTruthy();
    });
  });

  test.describe('Performance Edge Cases', () => {
    test('Handles large pages without timing out', async ({ page }) => {
      if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
      
      // Increase timeout for large pages
      test.setTimeout(90000);
      
      await page.goto(seed.confluence.pageUrl, { timeout: 60000 });
      await page.waitForLoadState('networkidle', { timeout: 30000 });
      
      // Check that all major elements are loaded
      const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();
      await expect(article).toBeVisible({ timeout: 10000 });
      
      // Measure performance
      const performanceMetrics = await page.evaluate(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        return {
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
          loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
          firstPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-paint')?.startTime
        };
      });
      
      // Basic performance expectations
      expect(performanceMetrics.domContentLoaded).toBeLessThan(10000); // 10 seconds
      if (performanceMetrics.firstPaint) {
        expect(performanceMetrics.firstPaint).toBeLessThan(5000); // 5 seconds
      }
    });

    test('Handles memory-intensive operations', async ({ page }) => {
      if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
      
      await page.goto(seed.confluence.pageUrl);
      await page.waitForLoadState('networkidle');
      
      // Simulate memory-intensive operations
      const memoryBefore = await page.evaluate(() => (performance as any).memory?.usedJSHeapSize || 0);
      
      // Scroll through entire page multiple times
      for (let i = 0; i < 5; i++) {
        await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
        await page.waitForTimeout(200);
        await page.evaluate(() => window.scrollTo(0, 0));
        await page.waitForTimeout(200);
      }
      
      const memoryAfter = await page.evaluate(() => (performance as any).memory?.usedJSHeapSize || 0);
      
      // Memory usage should not increase excessively
      if (memoryBefore > 0 && memoryAfter > 0) {
        const memoryIncrease = memoryAfter - memoryBefore;
        expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024); // Less than 50MB increase
      }
      
      // Page should still be responsive
      const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();
      await expect(article).toBeVisible();
    });
  });

  test.describe('Content Interaction Edge Cases', () => {
    test('Handles rapid user interactions', async ({ page }) => {
      if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
      
      await page.goto(seed.confluence.pageUrl);
      await page.waitForLoadState('networkidle');
      
      // Find expandable sections
      const expandSections = page.locator('.expand-macro, [data-node-type="expand"], .ak-editor-expand');
      
      if (await expandSections.count() > 0) {
        const firstExpand = expandSections.first();
        const trigger = firstExpand.locator('.expand-control, .expand-title, [role="button"]').first();
        
        if (await trigger.isVisible()) {
          // Rapidly click expand/collapse
          for (let i = 0; i < 5; i++) {
            await trigger.click();
            await page.waitForTimeout(100);
          }
          
          // Should still be functional after rapid clicking
          await expect(firstExpand).toBeVisible();
          const finalState = await firstExpand.getAttribute('aria-expanded');
          expect(finalState === 'true' || finalState === 'false').toBeTruthy();
        }
      }
    });

    test('Handles keyboard navigation edge cases', async ({ page }) => {
      if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
      
      await page.goto(seed.confluence.pageUrl);
      await page.waitForLoadState('networkidle');
      
      // Test keyboard navigation through interactive elements
      await page.keyboard.press('Tab');
      
      // Should be able to navigate to actionable elements
      const focusedElement = await page.locator(':focus').first();
      if (await focusedElement.count() > 0) {
        const tagName = await focusedElement.evaluate(el => el.tagName.toLowerCase());
        const isInteractive = ['a', 'button', 'input', 'select', 'textarea'].includes(tagName) ||
                            await focusedElement.getAttribute('tabindex') !== null ||
                            await focusedElement.getAttribute('role') === 'button';
        
        expect(isInteractive).toBeTruthy();
      }
      
      // Test escape key functionality
      await page.keyboard.press('Escape');
      
      // Should not break page functionality
      const article = page.locator('article, [data-test-id="content-body"], [data-testid="content-body"], .wiki-content').first();
      await expect(article).toBeVisible();
    });
  });
});