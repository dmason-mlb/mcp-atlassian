import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [
    ['list'], 
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['junit', { outputFile: 'test-results/junit.xml' }]
  ],
  use: {
    baseURL: process.env.BASE_URL || undefined,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    storageState: 'storageState.json',
  },
  globalSetup: './setup/global-setup.ts',
  projects: [
    // Desktop browsers
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    // Mobile browsers
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
      testMatch: /.*mobile.*\.spec\.ts/,
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 12'] },
      testMatch: /.*mobile.*\.spec\.ts/,
    },

    // Tablet
    {
      name: 'tablet',
      use: { ...devices['iPad Pro'] },
      testMatch: /.*tablet.*\.spec\.ts/,
    },

    // High DPI
    {
      name: 'high-dpi',
      use: {
        ...devices['Desktop Chrome'],
        deviceScaleFactor: 2,
      },
      testMatch: /.*visual.*\.spec\.ts/,
    },

    // Accessibility testing (specific configuration)
    {
      name: 'accessibility',
      use: {
        ...devices['Desktop Chrome'],
        // Reduce motion for accessibility testing
        reducedMotion: 'reduce',
        // Force light color scheme for consistent testing
        colorScheme: 'light',
      },
      testMatch: /.*accessibility.*\.spec\.ts/,
    },
  ],

  // Output directories
  outputDir: 'test-results/',
  
  // Global test timeout
  timeout: 30 * 1000,
  
  // Expect timeout for assertions
  expect: {
    timeout: 5 * 1000,
  },
});
