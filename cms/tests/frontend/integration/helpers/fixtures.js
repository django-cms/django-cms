// @ts-check
const playwright = require('@playwright/test');
const baseTest = playwright.test;
const expect = playwright.expect;

/**
 * Configuration settings for django-cms tests
 */
const settings = {
  baseUrl: process.env.BASE_URL || 'http://localhost:8000',
  get editUrl() {
    return `${this.baseUrl}/en/?toolbar_on`;
  },
  get adminUrl() {
    return `${this.baseUrl}/en/admin/`;
  },
  adminTitle: 'Django site admin',
  credentials: {
    username: process.env.TEST_USERNAME || 'admin',
    password: process.env.TEST_PASSWORD || 'admin'
  },
  content: {
    page: {
      title: 'Test Page',
      text: 'Test content text for the page'
    }
  }
};

/**
 * Generate a random string for testing
 * @param {Object} options - Options for string generation
 * @param {number} options.length - Length of the string
 * @param {boolean} options.withWhitespaces - Include whitespaces
 * @returns {string} Random string
 */
function randomString({ length = 10, withWhitespaces = true } = {}) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  const allChars = withWhitespaces ? chars + ' ' : chars;
  let result = '';
  for (let i = 0; i < length; i++) {
    result += allChars.charAt(Math.floor(Math.random() * allChars.length));
  }
  return result;
}

/**
 * Extended test fixtures with CMS helpers
 */
const test = baseTest.extend({
  /**
   * Authenticated page that logs in before each test
   */
  authenticatedPage: async ({ page }, use) => {
    // Navigate to admin login page to get CSRF token
    await page.goto(settings.adminUrl);

    // Clear localStorage but keep cookies (we need CSRF token)
    await page.evaluate(() => localStorage.clear());

    // Wait for login form to be ready
    await page.waitForSelector('input[name="username"]');

    // Fill login form
    await page.fill('input[name="username"]', settings.credentials.username);
    await page.fill('input[name="password"]', settings.credentials.password);
    await page.click('input[type="submit"]');

    // Wait for successful login (redirect to admin)
    await page.waitForURL(/\/admin\//, { timeout: 10000 });

    // Use the authenticated page
    await use(page);

    // Logout after test - just clear cookies instead of POST to logout
    await page.context().clearCookies();
  },

  /**
   * CMS helper utilities
   */
  cms: async ({ page }, use) => {
    const helpers = {
      /**
       * Login to CMS
       */
      login: async () => {
        await page.goto(settings.adminUrl);
        await page.evaluate(() => localStorage.clear());
        await page.waitForSelector('input[name="username"]');
        await page.fill('input[name="username"]', settings.credentials.username);
        await page.fill('input[name="password"]', settings.credentials.password);
        await page.click('input[type="submit"]');
        await page.waitForURL(/\/admin\//, { timeout: 10000 });
      },

      /**
       * Logout from CMS
       */
      logout: async () => {
        // Clear cookies to logout (POST to logout requires CSRF token)
        await page.context().clearCookies();
        await page.waitForTimeout(500);
      },

      /**
       * Add a new page
       * @param {Object} options - Page options
       * @param {string} options.title - Page title
       * @param {string} options.language - Page language
       */
      addPage: async ({ title = 'Test Page', language = 'en' } = {}) => {
        await page.goto(`${settings.baseUrl}/${language}/`);
        await page.waitForSelector('.cms-toolbar-expanded', { timeout: 10000 });
        await page.click('a[href*="/cms_wizard/create/"][data-rel="modal"]');

        // Check if wizard modal appears (for first page)
        const modalVisible = await page.isVisible('.cms-modal');
        if (modalVisible) {
          await page.click('.cms-modal-foot a.cms-btn.cms-btn-action.default');
          await page.waitForSelector('.cms-modal iframe');

          const frame = page.frameLocator('.cms-modal iframe');
          await frame.locator('#id_1-title').fill(title);
          await page.click('.cms-modal-foot a.cms-btn.cms-btn-action.default');

          await page.waitForSelector('.cms-ready');
        }
      },

      /**
       * Remove a page
       */
      removePage: async () => {
        // Navigate to page tree
        await page.goto(`${settings.baseUrl}/en/admin/cms/page/`);

        // Find and delete the first page
        const deleteButton = page.locator('.deletelink').first();
        if (await deleteButton.isVisible()) {
          await deleteButton.click();
          await page.waitForSelector('input[value="Yes, I\'m sure"]');
          await page.click('input[value="Yes, I\'m sure"]');
        }
      },

      /**
       * Add a plugin to the page
       * @param {Object} options - Plugin options
       * @param {string} options.type - Plugin type
       * @param {Object} options.content - Plugin content
       */
      addPlugin: async ({ type = 'TextPlugin', content = {} } = {}) => {
        await page.waitForSelector('.cms-toolbar-expanded');

        // Switch to structure mode
        await helpers.switchTo('structure');

        // Click add plugin button
        await page.click('.cms-submenu-add [data-cms-tooltip="Add plugin"]');
        await page.waitForSelector('.cms-plugin-picker');

        // Search for plugin type
        const pluginName = type.replace('Plugin', '');
        await page.fill('.cms-quicksearch input', pluginName);
        await page.click(`text="${pluginName}"`);

        // Fill plugin form
        await page.waitForSelector('.cms-modal iframe');
        const frame = page.frameLocator('.cms-modal iframe');

        for (const [key, value] of Object.entries(content)) {
          await frame.locator(`#${key}`).fill(value);
        }

        // Save plugin
        await page.click('.cms-modal-buttons .cms-btn-action');
        await page.waitForLoadState('networkidle');
      },

      /**
       * Switch between structure and content mode
       * @param {string} mode - 'structure' or 'content'
       */
      switchTo: async (mode) => {
        const currentMode = await page.evaluate(() => {
          return window.CMS?.config?.mode || 'edit';
        });

        if (mode === 'structure' && currentMode !== 'structure') {
          await page.keyboard.press(' ');
          await page.waitForSelector('.cms-structure', { state: 'visible' });
        } else if (mode === 'content' && currentMode === 'structure') {
          await page.keyboard.press(' ');
          await page.waitForSelector('.cms-structure', { state: 'hidden' });
        }
      },

      /**
       * Wait until content is refreshed
       */
      waitUntilContentIsRefreshed: async () => {
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(500); // Small delay for CMS to update
      },

      /**
       * Open sideframe
       * @param {string} url - URL to open in sideframe
       */
      openSideframe: async (url) => {
        await page.evaluate((sideframeUrl) => {
          window.CMS.API.Sideframe.open({
            url: sideframeUrl
          });
        }, url);
        await page.waitForSelector('.cms-sideframe-frame');
      },

      /**
       * Close sideframe
       */
      closeSideframe: async () => {
        await page.click('.cms-sideframe-close');
        await page.waitForSelector('.cms-sideframe', { state: 'hidden' });
      }
    };

    await use(helpers);
  }
});

module.exports = { test, expect, settings, randomString };
