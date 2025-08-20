import { Page, Locator } from '@playwright/test';

/**
 * Try to dismiss common blockers like cookie banners and modals
 */
async function dismissCommonBlockers(page: Page) {
  try {
    // Check for common cookie/privacy banner dismissal buttons
    const cookieButtons = [
      'button:has-text("Accept")',
      'button:has-text("Accept all")',
      'button:has-text("Allow all")',
      '[id*="onetrust"] button:has-text("Accept")',
      '.cookie-banner button:has-text("Accept")'
    ];
    
    for (const selector of cookieButtons) {
      const button = page.locator(selector).first();
      if (await button.isVisible().catch(() => false)) {
        await button.click();
        await page.waitForTimeout(1000);
        break;
      }
    }
    
    // Check for "What's new" or feedback modals
    const modalDismissButtons = [
      'button:has-text("Close")',
      'button:has-text("Dismiss")',
      'button[aria-label*="Close"]',
      '.modal button:has-text("Got it")',
      '.onboarding button:has-text("Skip")'
    ];
    
    for (const selector of modalDismissButtons) {
      const button = page.locator(selector).first();
      if (await button.isVisible().catch(() => false)) {
        await button.click();
        await page.waitForTimeout(1000);
        break;
      }
    }
  } catch (error) {
    // Silently continue if dismissal fails
  }
}

/**
 * Wait for app-specific ready states instead of networkidle
 * 
 * @param page Playwright page instance
 * @param kind Application type - 'jira' or 'confluence'
 */
export async function waitForAppReady(page: Page, kind: 'jira' | 'confluence') {
  if (kind === 'jira') {
    // First try to dismiss any blockers
    await dismissCommonBlockers(page);
    
    // Jira readiness selectors in priority order with fallbacks
    const jiraSelectors = [
      '[data-test-id="issue.views.issue-base.foundation.root"]',
      '[data-testid="issue-view"]',
      '[data-testid="issue-view-layout"]',
      'main',
      '[role="main"]'
    ];
    
    // Timeboxed polling loop for readiness
    let ready = false;
    const startTime = Date.now();
    const maxTime = 30000;
    
    while (!ready && (Date.now() - startTime) < maxTime) {
      // Try each selector in order
      for (const selector of jiraSelectors) {
        try {
          const element = page.locator(selector).first();
          if (await element.isVisible({ timeout: 2000 }).catch(() => false)) {
            ready = true;
            break;
          }
        } catch (error) {
          // Continue to next selector
        }
      }
      
      if (!ready) {
        // Try dismissing blockers again and wait a bit
        await dismissCommonBlockers(page);
        await page.waitForTimeout(2000);
      }
    }
    
    if (!ready) {
      throw new Error(`Jira page not ready after ${maxTime}ms. Tried selectors: ${jiraSelectors.join(', ')}`);
    }
  } else {
    // Confluence - try to dismiss blockers first
    await dismissCommonBlockers(page);
    
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
 * Get a robust content root locator with fallback options
 * 
 * @param page Playwright page instance
 * @returns First visible content container
 */
export async function getContentRoot(page: Page): Promise<Locator> {
  const candidates = [
    '[data-testid="content-body"]',    // Legacy test selector
    '.ak-renderer-document',           // ADF render root
    'article',                         // Semantic article element
    'main',                           // Main content area
    '[role="document"]',              // ARIA document role
    '[role="main"]'                   // ARIA main role
  ];
  
  for (const selector of candidates) {
    const locator = page.locator(selector).first();
    try {
      if (await locator.isVisible({ timeout: 1000 }).catch(() => false)) {
        return locator;
      }
    } catch (error) {
      // Continue to next candidate
    }
  }
  
  // As last resort, return the first candidate (tests will fail with helpful message)
  return page.locator(candidates[0]).first();
}

/**
 * Wait for content article to be fully loaded and visible
 * 
 * @param page Playwright page instance
 */
export async function waitForContentReady(page: Page) {
  // Get the robust content root
  const contentRoot = await getContentRoot(page);
  
  // Wait for content container to be visible
  await contentRoot.waitFor({
    state: 'visible',
    timeout: 20000
  });
  
  // Wait for content to have actual text (not just loading placeholders)
  await page.waitForFunction(() => {
    const selectors = [
      '[data-testid="content-body"]',
      '.ak-renderer-document',
      'article',
      'main',
      '[role="document"]',
      '[role="main"]'
    ];
    for (const selector of selectors) {
      const container = document.querySelector(selector);
      if (container && container.textContent && container.textContent.trim().length > 50) {
        return true;
      }
    }
    return false;
  }, { timeout: 15000 });
}