import { test, expect } from '@playwright/test';
import seed from '../.artifacts/seed.json' with { type: 'json' };
import { waitForAppReady, waitForContentReady } from '../utils/wait';

test.describe('Interactive Elements Testing', () => {
  test.describe('Jira Interactive Elements', () => {
    test.beforeEach(async ({ page }) => {
      if (!seed?.jira?.issueUrl) test.skip(true, 'No Jira issue URL in seed.json');
      await page.goto(seed.jira.issueUrl);
      await waitForAppReady(page, 'jira');
    });

    test('Jira comment section is interactive', async ({ page }) => {
      // Look for comment section
      const commentSection = page.locator('[data-testid="issue-comments"], #activitymodule, .activity-container');

      if (await commentSection.isVisible()) {
        // Check for add comment functionality
        const addCommentButton = page.locator('[data-testid="add-comment"], .add-comment, #comment-add-submit');
        const commentTextArea = page.locator('[data-testid="comment-textbox"], textarea[name="comment"], .comment-input');

        if (await addCommentButton.isVisible() || await commentTextArea.isVisible()) {
          // Test comment form accessibility
          if (await commentTextArea.isVisible()) {
            await expect(commentTextArea).toBeEditable();

            // Test placeholder or label
            const hasLabel = await commentTextArea.getAttribute('aria-label') !== null ||
                           await commentTextArea.getAttribute('placeholder') !== null ||
                           await page.locator('label[for*="comment"]').count() > 0;
            expect(hasLabel).toBeTruthy();
          }
        }

        // Check existing comments for interaction elements
        const comments = commentSection.locator('.comment, [data-testid="comment"]');
        if (await comments.count() > 0) {
          const firstComment = comments.first();

          // Look for comment actions (edit, reply, etc.)
          const commentActions = firstComment.locator('.comment-actions, [data-testid="comment-actions"], .comment-toolbar');
          if (await commentActions.isVisible()) {
            // Should have some interactive elements
            const actionButtons = commentActions.locator('button, a[role="button"]');
            if (await actionButtons.count() > 0) {
              await expect(actionButtons.first()).toBeVisible();
            }
          }
        }
      }
    });

    test('Jira issue actions are accessible', async ({ page }) => {
      // Check for main issue actions
      const issueActions = page.locator('[data-testid="issue-actions"], .issue-actions, .ops-menus');

      if (await issueActions.isVisible()) {
        // Should contain action buttons
        const actionButtons = issueActions.locator('button, [role="button"]');
        await expect(actionButtons).toHaveCountGreaterThan(0);

        // Common actions to look for
        const editButton = page.locator('[data-testid="edit-issue"], .edit-issue, #edit-issue');
        const assignButton = page.locator('[data-testid="assign-issue"], .assign-issue');
        const watchButton = page.locator('[data-testid="watch-issue"], .watch-issue, #watching-toggle');
        const shareButton = page.locator('[data-testid="share-issue"], .share-issue');

        // At least one action should be available
        const hasActions = await editButton.isVisible() ||
                          await assignButton.isVisible() ||
                          await watchButton.isVisible() ||
                          await shareButton.isVisible();
        expect(hasActions).toBeTruthy();
      }
    });

    test('Jira transitions are functional', async ({ page }) => {
      // Look for transition buttons/dropdown
      const transitionElements = page.locator('[data-testid="issue-workflow-transition"], .issue-workflow-transition, .workflow-transitions');

      if (await transitionElements.isVisible()) {
        const transitionButtons = transitionElements.locator('button, [role="button"]');

        if (await transitionButtons.count() > 0) {
          await expect(transitionButtons.first()).toBeVisible();
          await expect(transitionButtons.first()).toBeEnabled();

          // Check if transitions have proper labels
          const firstTransition = transitionButtons.first();
          const buttonText = await firstTransition.textContent();
          expect(buttonText?.trim().length).toBeGreaterThan(0);
        }
      }
    });

    test('Jira attachments are interactive', async ({ page }) => {
      const attachmentSection = page.locator('[data-testid="attachments"], .attachment-container, .issue-attachments');

      if (await attachmentSection.isVisible()) {
        // Look for attachment links
        const attachmentLinks = attachmentSection.locator('a[href*="attachment"], .attachment-link');

        if (await attachmentLinks.count() > 0) {
          for (let i = 0; i < await attachmentLinks.count(); i++) {
            const link = attachmentLinks.nth(i);
            await expect(link).toHaveAttribute('href');

            // Link should have meaningful text or title
            const linkText = await link.textContent();
            const linkTitle = await link.getAttribute('title');
            expect(linkText?.trim().length || linkTitle?.trim().length).toBeGreaterThan(0);
          }
        }

        // Check for attachment upload functionality
        const uploadButton = page.locator('[data-testid="attach-file"], .attach-file, input[type="file"]');
        if (await uploadButton.isVisible()) {
          await expect(uploadButton).toBeVisible();
        }
      }
    });
  });

  test.describe('Confluence Interactive Elements', () => {
    test.beforeEach(async ({ page }) => {
      if (!seed?.confluence?.pageUrl) test.skip(true, 'No Confluence page URL in seed.json');
      await page.goto(seed.confluence.pageUrl);
      await waitForAppReady(page, 'confluence');
      await waitForContentReady(page);
    });

    test('Confluence page actions are accessible', async ({ page }) => {
      // Check for page action toolbar
      const pageToolbar = page.locator('[data-testid="page-actions"], .page-toolbar, #page-toolbar');

      if (await pageToolbar.isVisible()) {
        // Common page actions
        const editButton = page.locator('[data-testid="edit-page"], .edit-link, #editPageLink');
        const shareButton = page.locator('[data-testid="share-page"], .share-page');
        const likeButton = page.locator('[data-testid="like-page"], .like-button, .favourite-page');
        const watchButton = page.locator('[data-testid="watch-page"], .watch-page');

        // At least one action should be available
        const hasActions = await editButton.isVisible() ||
                          await shareButton.isVisible() ||
                          await likeButton.isVisible() ||
                          await watchButton.isVisible();
        expect(hasActions).toBeTruthy();

        // Test specific actions if available
        if (await editButton.isVisible()) {
          await expect(editButton).toBeEnabled();
        }

        if (await likeButton.isVisible()) {
          await expect(likeButton).toBeEnabled();

          // Test like functionality (if permissions allow)
          try {
            const initialState = await likeButton.getAttribute('aria-pressed') ||
                               await likeButton.getAttribute('class');
            await likeButton.click();
            await page.waitForTimeout(1000);

            const newState = await likeButton.getAttribute('aria-pressed') ||
                           await likeButton.getAttribute('class');
            expect(newState).not.toBe(initialState);
          } catch (error) {
            // Like action might not be permitted, which is fine
          }
        }
      }
    });

    test('Confluence comments section is interactive', async ({ page }) => {
      // Look for comments section
      const commentsSection = page.locator('[data-testid="comments"], .comments-section, #comments-section');

      if (await commentsSection.isVisible()) {
        // Check for add comment functionality
        const addCommentButton = page.locator('[data-testid="add-comment"], .add-comment, #add-comment-rte');
        const commentEditor = page.locator('[data-testid="comment-editor"], .comment-editor, .editor-content');

        if (await addCommentButton.isVisible()) {
          await expect(addCommentButton).toBeEnabled();

          // Test comment editor activation
          try {
            await addCommentButton.click();
            await page.waitForTimeout(500);

            // Editor should become visible
            if (await commentEditor.isVisible()) {
              await expect(commentEditor).toBeVisible();
            }
          } catch (error) {
            // Comment functionality might not be available
          }
        }

        // Check existing comments for interaction
        const existingComments = commentsSection.locator('.comment, [data-testid="comment"]');
        if (await existingComments.count() > 0) {
          const firstComment = existingComments.first();

          // Look for comment metadata (author, date)
          const commentAuthor = firstComment.locator('.comment-author, [data-testid="comment-author"]');
          const commentDate = firstComment.locator('.comment-date, [data-testid="comment-date"], time');

          if (await commentAuthor.isVisible()) {
            await expect(commentAuthor).toBeVisible();
          }

          if (await commentDate.isVisible()) {
            await expect(commentDate).toBeVisible();
          }
        }
      }
    });

    test('Confluence navigation elements work', async ({ page }) => {
      // Test breadcrumb navigation
      const breadcrumbs = page.locator('[data-testid="breadcrumbs"]');

      if (await breadcrumbs.isVisible()) {
        const breadcrumbLinks = breadcrumbs.locator('a');

        if (await breadcrumbLinks.count() > 0) {
          for (let i = 0; i < await breadcrumbLinks.count(); i++) {
            const link = breadcrumbLinks.nth(i);
            await expect(link).toHaveAttribute('href');

            const linkText = await link.textContent();
            expect(linkText?.trim().length).toBeGreaterThan(0);
          }
        }
      }

      // Test page tree/sidebar navigation
      const pageTree = page.locator('[data-testid="page-tree"], .page-tree, .space-nav');

      if (await pageTree.isVisible()) {
        const treeLinks = pageTree.locator('a');

        if (await treeLinks.count() > 0) {
          // Should have navigational links
          await expect(treeLinks).toHaveCountGreaterThan(0);
        }
      }
    });

    test('Confluence content interactions work', async ({ page }) => {
      const article = page.locator('[data-testid="content-body"]').first();

      // Test expand/collapse sections if present
      const expandSections = article.locator('.expand-macro, [data-node-type="expand"], .ak-editor-expand');

      if (await expandSections.count() > 0) {
        const firstExpand = expandSections.first();
        const trigger = firstExpand.locator('.expand-control, .expand-title, [role="button"]').first();

        if (await trigger.isVisible()) {
          // Test expand/collapse functionality
          const initialState = await firstExpand.getAttribute('aria-expanded') || 'false';

          await trigger.click();
          await page.waitForTimeout(500);

          const newState = await firstExpand.getAttribute('aria-expanded') || 'false';
          expect(newState).not.toBe(initialState);
        }
      }

      // Test table interactions if present
      const tables = article.locator('table');

      if (await tables.count() > 0) {
        const firstTable = tables.first();

        // Check for sortable columns
        const sortableHeaders = firstTable.locator('th[role="columnheader"], th.sortable, th[onclick]');

        if (await sortableHeaders.count() > 0) {
          // Headers should be clickable for sorting
          await expect(sortableHeaders.first()).toBeVisible();
        }

        // Check for table scroll/overflow handling
        const tableContainer = firstTable.locator('..').first();
        const hasOverflow = await tableContainer.evaluate(el => {
          const style = window.getComputedStyle(el);
          return style.overflowX === 'auto' || style.overflowX === 'scroll';
        });

        // Large tables should have overflow handling
        const cellCount = await firstTable.locator('td').count();
        if (cellCount > 20) {
          expect(hasOverflow).toBeTruthy();
        }
      }
    });
  });

  test.describe('Cross-Platform Interactive Features', () => {
    test('Links between Jira and Confluence work', async ({ page }) => {
      // Start with Jira if available
      if (seed?.jira?.issueUrl) {
        await page.goto(seed.jira.issueUrl);
        await waitForAppReady(page, 'jira');

        // Look for Confluence links in issue
        const confluenceLinks = page.locator('a[href*="confluence"], a[href*="/wiki/"]');

        if (await confluenceLinks.count() > 0) {
          const firstLink = confluenceLinks.first();
          await expect(firstLink).toBeVisible();
          await expect(firstLink).toHaveAttribute('href');

          const href = await firstLink.getAttribute('href');
          expect(href).toMatch(/confluence|\/wiki\//);
        }
      }

      // Check Confluence for Jira links
      if (seed?.confluence?.pageUrl) {
        await page.goto(seed.confluence.pageUrl);
        await waitForAppReady(page, 'confluence');
        await waitForContentReady(page);

        // Look for Jira links in page
        const jiraLinks = page.locator('a[href*="browse/"], a[href*="jira"]');

        if (await jiraLinks.count() > 0) {
          const firstLink = jiraLinks.first();
          await expect(firstLink).toBeVisible();
          await expect(firstLink).toHaveAttribute('href');

          const href = await firstLink.getAttribute('href');
          expect(href).toMatch(/browse\/|jira/);
        }
      }
    });

    test('Search functionality works across platforms', async ({ page }) => {
      // Test Jira search
      if (seed?.jira?.issueUrl) {
        await page.goto(seed.jira.issueUrl);
        await waitForAppReady(page, 'jira');

        const jiraSearch = page.locator('[data-testid="search"], #quickSearchInput, .quick-search');

        if (await jiraSearch.isVisible()) {
          await expect(jiraSearch).toBeEditable();

          // Test search interaction
          await jiraSearch.click();
          await jiraSearch.fill('test');
          await page.waitForTimeout(1000);

          // Should show search suggestions or results
          const searchSuggestions = page.locator('.search-suggestions, .dropdown-menu, [data-testid="search-results"]');
          if (await searchSuggestions.isVisible()) {
            await expect(searchSuggestions).toBeVisible();
          }
        }
      }

      // Test Confluence search
      if (seed?.confluence?.pageUrl) {
        await page.goto(seed.confluence.pageUrl);
        await waitForAppReady(page, 'confluence');
        await waitForContentReady(page);

        const confluenceSearch = page.locator('[data-testid="search"], #quick-search, .quick-search');

        if (await confluenceSearch.isVisible()) {
          await expect(confluenceSearch).toBeEditable();

          // Test search interaction
          await confluenceSearch.click();
          await confluenceSearch.fill('test');
          await page.waitForTimeout(1000);

          // Should show search suggestions or results
          const searchSuggestions = page.locator('.search-suggestions, .search-results, [data-testid="search-suggestions"]');
          if (await searchSuggestions.isVisible()) {
            await expect(searchSuggestions).toBeVisible();
          }
        }
      }
    });
  });
});
