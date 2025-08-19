#!/usr/bin/env node

import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from repo root
const envPath = path.resolve(__dirname, '..', '..', '.env');
if (fs.existsSync(envPath)) {
  dotenv.config({ path: envPath });
}

console.log('🔍 E2E Environment Validation');
console.log('=============================\n');

const errors = [];
const warnings = [];
const info = [];

// Required environment variables
const requiredVars = [
  {
    name: 'ATLASSIAN_URL',
    description: 'Your Atlassian instance base URL',
    example: 'https://company.atlassian.net',
    validation: (value) => {
      if (!value.startsWith('https://')) {
        return 'URL must start with https://';
      }
      if (!value.includes('atlassian')) {
        return 'URL should contain "atlassian" for Cloud instances or be your custom domain for Server/DC';
      }
      return null;
    }
  },
  {
    name: 'JIRA_PROJECT',
    description: 'Project key for creating test issues',
    example: 'FTEST',
    validation: (value) => {
      if (!/^[A-Z0-9]+$/.test(value)) {
        return 'Project key should be uppercase letters and numbers only';
      }
      if (value.length < 2 || value.length > 10) {
        return 'Project key should be 2-10 characters long';
      }
      return null;
    }
  },
  {
    name: 'CONFLUENCE_SPACE',
    description: 'Space ID or key for creating test pages',
    example: '655361 or SPACE',
    validation: (value) => {
      if (!/^[A-Z0-9~]+$/.test(value)) {
        return 'Space should be numeric ID or uppercase key';
      }
      return null;
    }
  }
];

// Optional environment variables (with fallbacks)
const optionalVars = [
  {
    name: 'JIRA_BASE',
    description: 'Jira base URL (overrides ATLASSIAN_URL)',
    fallback: 'ATLASSIAN_URL',
    example: 'https://company.atlassian.net'
  },
  {
    name: 'CONFLUENCE_BASE',
    description: 'Confluence base URL',
    fallback: 'ATLASSIAN_URL + /wiki',
    example: 'https://company.atlassian.net/wiki'
  }
];

// Authentication variables
const authVars = [
  'JIRA_USERNAME',
  'JIRA_API_TOKEN',
  'JIRA_PERSONAL_TOKEN',
  'CONFLUENCE_USERNAME',
  'CONFLUENCE_API_TOKEN',
  'CONFLUENCE_PERSONAL_TOKEN',
  'ATLASSIAN_OAUTH_CLIENT_ID',
  'ATLASSIAN_OAUTH_CLIENT_SECRET'
];

console.log('📋 Required Variables:');
console.log('======================');

for (const varConfig of requiredVars) {
  const value = process.env[varConfig.name];
  
  if (!value) {
    errors.push(`❌ ${varConfig.name} is not set`);
    console.log(`❌ ${varConfig.name}: MISSING`);
    console.log(`   Description: ${varConfig.description}`);
    console.log(`   Example: ${varConfig.example}\n`);
  } else {
    const validationError = varConfig.validation ? varConfig.validation(value) : null;
    if (validationError) {
      errors.push(`❌ ${varConfig.name}: ${validationError}`);
      console.log(`❌ ${varConfig.name}: ${validationError}`);
      console.log(`   Current value: ${value}\n`);
    } else {
      console.log(`✅ ${varConfig.name}: ${value}`);
      info.push(`✅ ${varConfig.name} is valid`);
    }
  }
}

console.log('\n🔧 Optional Variables:');
console.log('======================');

for (const varConfig of optionalVars) {
  const value = process.env[varConfig.name];
  
  if (!value) {
    console.log(`⚠️  ${varConfig.name}: Not set (will use ${varConfig.fallback})`);
    warnings.push(`${varConfig.name} not set, using fallback: ${varConfig.fallback}`);
  } else {
    console.log(`✅ ${varConfig.name}: ${value}`);
    info.push(`✅ ${varConfig.name} is configured`);
  }
}

console.log('\n🔐 Authentication Check:');
console.log('========================');

const hasAuth = authVars.some(varName => process.env[varName]);
if (!hasAuth) {
  errors.push('❌ No authentication variables found');
  console.log('❌ No authentication variables found');
  console.log('   You need one of:');
  console.log('   - JIRA_USERNAME + JIRA_API_TOKEN (Cloud)');
  console.log('   - JIRA_PERSONAL_TOKEN (Server/DC)');
  console.log('   - OAuth credentials (ATLASSIAN_OAUTH_CLIENT_ID + ATLASSIAN_OAUTH_CLIENT_SECRET)');
} else {
  const setAuthVars = authVars.filter(varName => process.env[varName]);
  console.log(`✅ Authentication configured: ${setAuthVars.join(', ')}`);
  info.push('✅ Authentication variables are set');
}

console.log('\n📁 File Checks:');
console.log('================');

// Check for storageState.json
const storageStatePath = path.join(__dirname, 'storageState.json');
if (fs.existsSync(storageStatePath)) {
  console.log('✅ storageState.json exists (authentication saved)');
  info.push('✅ Authentication state file exists');
} else {
  console.log('⚠️  storageState.json not found (run `npm run auth` first)');
  warnings.push('Authentication state not saved - run `npm run auth`');
}

// Check for .env file
if (fs.existsSync(envPath)) {
  console.log(`✅ .env file found at ${envPath}`);
  info.push('✅ Environment file exists');
} else {
  console.log(`❌ .env file not found at ${envPath}`);
  errors.push('❌ .env file missing from repo root');
}

// Check for artifacts directory
const artifactsPath = path.join(__dirname, '.artifacts');
if (fs.existsSync(artifactsPath)) {
  console.log('✅ .artifacts directory exists');
  const seedPath = path.join(artifactsPath, 'seed.json');
  if (fs.existsSync(seedPath)) {
    console.log('✅ seed.json exists (test data available)');
    info.push('✅ Test data artifacts available');
  } else {
    console.log('⚠️  seed.json not found (run `npm run seed` to create test data)');
    warnings.push('Test data not seeded - run `npm run seed`');
  }
} else {
  console.log('⚠️  .artifacts directory not found (will be created during seeding)');
  warnings.push('Artifacts directory will be created during seeding');
}

console.log('\n🔍 Summary:');
console.log('===========');

if (errors.length === 0) {
  console.log('🎉 Environment validation passed!');
  console.log('✅ All required variables are set and valid');
  
  if (warnings.length > 0) {
    console.log('\n⚠️  Warnings:');
    warnings.forEach(warning => console.log(`   ${warning}`));
  }
  
  console.log('\n🚀 You can now run:');
  console.log('   npm run auth     # Set up authentication (if not done)');
  console.log('   npm run seed     # Create test data');
  console.log('   npm run test     # Run E2E tests');
  
  process.exit(0);
} else {
  console.log('❌ Environment validation failed!');
  console.log('\n🔧 Errors to fix:');
  errors.forEach(error => console.log(`   ${error}`));
  
  console.log('\n📖 To fix these issues:');
  console.log('1. Copy .env.example to .env in the repo root');
  console.log('2. Edit .env with your Atlassian credentials and URLs');
  console.log('3. Run this script again to validate');
  
  process.exit(1);
}