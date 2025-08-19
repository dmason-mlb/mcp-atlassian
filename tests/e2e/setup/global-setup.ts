import { chromium, FullConfig } from '@playwright/test';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import dotenv from 'dotenv';

export default async function globalSetup(config: FullConfig) {
  // Load project root .env
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = path.dirname(__filename);
  const root = path.resolve(__dirname, '..');
  const envPath = path.resolve(root, '..', '.env');
  if (fs.existsSync(envPath)) dotenv.config({ path: envPath });
  const atlassianUrl = process.env.ATLASSIAN_URL;
  const jiraBase = process.env.JIRA_BASE || atlassianUrl;
  const confluenceBase = process.env.CONFLUENCE_BASE || (jiraBase ? `${jiraBase.replace(/\/$/, '')}/wiki` : undefined);
  if (!jiraBase || !confluenceBase) {
    console.warn('JIRA_BASE/ATLASSIAN_URL and CONFLUENCE_BASE not set; UI tests may fail.');
  } else {
    process.env.JIRA_BASE = jiraBase;
    process.env.CONFLUENCE_BASE = confluenceBase;
  }

  if (process.env.REUSE_AUTH === 'true') {
    return; // assume storageState.json already present
  }

  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  // Navigate to Jira for login flow; SSO will propagate to Confluence
  if (jiraBase) {
    await page.goto(jiraBase);
  }
  // Give manual time if running locally; CI should preload storageState
  await page.waitForLoadState('load');
  // If an interactive login is required, pause here for local runs
  if (process.env.INTERACTIVE_LOGIN === 'true') {
    console.log('Complete login in the opened browser window...');
    await page.waitForTimeout(15000);
  }
  await context.storageState({ path: 'storageState.json' });
  await browser.close();
}
