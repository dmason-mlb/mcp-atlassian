import { Page } from '@playwright/test';

/**
 * Wait for app-specific ready states instead of networkidle
 * 
 * @param page Playwright page instance
 * @param kind Application type - 'jira' or 'confluence'
 */
export async function waitForAppReady(page: Page, kind: 'jira' | 'confluence') {
  if (kind === 'jira') {
    // Wait for Jira issue view to be ready - use the actual page structure
    await page.waitForSelector('main, [data-testid="issue-view"], [data-test-id="issue.views.issue-base.foundation.root"]', { 
      state: 'visible', 
      timeout: 30000 
    });
  } else {
    // Wait for Confluence page content to be ready - use actual page structure  
    await page.waitForSelector('#content, main, [role="main"]', { 
      state: 'visible', 
      timeout: 30000 
    });
    
    // Wait for page title to be present
    await page.waitForSelector('h1', { 
      state: 'visible', 
      timeout: 15000 
    });
  }
}

/**
 * Wait for content article to be fully loaded and visible
 * 
 * @param page Playwright page instance
 */
export async function waitForContentReady(page: Page) {
  // Wait for main content container
  await page.waitForSelector('#content, main, [role="main"]', {
    state: 'visible',
    timeout: 20000
  });
  
  // Wait for content to have actual text (not just loading placeholders)
  await page.waitForFunction(() => {
    const container = document.querySelector('#content, main, [role="main"]');
    return container && container.textContent && container.textContent.trim().length > 50;
  }, { timeout: 15000 });
}