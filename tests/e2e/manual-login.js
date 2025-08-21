#!/usr/bin/env node

import { chromium } from '@playwright/test';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables
const envPath = path.resolve(__dirname, '..', '..', '.env');
if (fs.existsSync(envPath)) {
  dotenv.config({ path: envPath });
}

const jiraBase = process.env.JIRA_BASE || process.env.ATLASSIAN_URL;
const confluenceBase = process.env.CONFLUENCE_BASE;

if (!jiraBase) {
  console.error('❌ JIRA_BASE or ATLASSIAN_URL must be set in .env file');
  process.exit(1);
}

console.log('🔐 Starting E2E authentication setup...');
console.log(`🌐 Will navigate to: ${jiraBase}`);
console.log('');
console.log('📋 Instructions:');
console.log('1. A browser window will open automatically');
console.log('2. Log in to your Atlassian account in the browser');
console.log('3. Wait until you can see the Jira dashboard (fully loaded)');
console.log('4. Come back to this terminal and press ENTER when logged in');
console.log('5. The browser will close and save your authentication state');
console.log('');

try {
  const browser = await chromium.launch({
    headless: false,
    args: ['--start-maximized']
  });
  const context = await browser.newContext({
    viewport: null // Use full screen
  });
  const page = await context.newPage();

  console.log('🚀 Opening browser and navigating to Jira...');
  await page.goto(jiraBase, { waitUntil: 'networkidle' });

  console.log('');
  console.log('⏳ Browser opened. Please complete the login process...');
  console.log('💡 Make sure you can see the Jira dashboard before pressing ENTER');
  console.log('');
  console.log('👆 Press ENTER when logged in and ready...');

  // Wait for user input
  process.stdin.setEncoding('utf8');
  await new Promise((resolve) => {
    process.stdin.once('data', () => {
      resolve();
    });
  });

  console.log('💾 Saving authentication state...');
  await context.storageState({ path: 'storageState.json' });

  // Verify the storage state was created and has content
  const storageState = JSON.parse(fs.readFileSync('storageState.json', 'utf8'));
  const hasCookies = storageState.cookies && storageState.cookies.length > 0;

  console.log(`✅ Authentication state saved to storageState.json`);
  console.log(`🍪 Cookies saved: ${hasCookies ? storageState.cookies.length : 0}`);

  if (!hasCookies) {
    console.log('⚠️  Warning: No cookies were saved. You may need to try the login again.');
  }

  await browser.close();

  console.log('');
  console.log('🎉 Authentication setup complete!');
  console.log('');
  console.log('🧪 You can now run the E2E tests:');
  console.log('   npm run test');
  console.log('');
  console.log('📊 Or test specific browsers:');
  console.log('   npx playwright test --project=chromium');
  console.log('   npx playwright test --project=firefox');

} catch (error) {
  console.error('❌ Error during authentication setup:', error.message);
  process.exit(1);
}
