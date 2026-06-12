// @ts-check
/*
 * Standalone Playwright config for the cms.contrib.frontend_v5
 * integration test suite. Independent of the root /playwright.config.js
 * — tests live under this directory and are scoped to verifying the
 * contrib app's bundles running in a real Django admin.
 *
 * CJS module syntax (not ESM imports) mirrors the root config. The repo
 * has no `"type": "module"` in package.json, so Playwright's config
 * loader runs .js files in CommonJS mode.
 *
 * Run via: `npm run test:v5:e2e`.
 *
 * What the webServer below does:
 *   - Spawns `testserver.py --port=9010` (different port from legacy
 *     test server on 9009 so both can run in parallel locally and in CI).
 *   - Sets `CMS_TEST_CONTRIB_APPS=cms.contrib.frontend_v5` — testserver.py
 *     reads this env var and inserts the listed apps into
 *     INSTALLED_APPS BEFORE `cms`, so Django staticfiles serves the
 *     contrib bundles at the legacy URLs (the drop-in shadow).
 *   - Playwright waits for the admin URL to respond before running tests.
 *
 * If the contrib bundles haven't been built, the tests will still pass
 * in many cases because the legacy bundles cover the same surface area
 * — except the paste-into-title test, which specifically exercises the
 * `input` event upgrade that only exists in the port. That test is the
 * canary: if it fails, the contrib bundle isn't loaded.
 */
const { defineConfig, devices } = require('@playwright/test');
const path = require('path');

const here = __dirname;
const REPO_ROOT = path.resolve(here, '..', '..', '..');
const PORT = Number(process.env.CMS_V5_E2E_PORT || 9010);
const BASE_URL = process.env.BASE_URL || `http://localhost:${PORT}`;

module.exports = defineConfig({
    testDir: path.resolve(here, 'tests/integration'),
    timeout: 30_000,
    expect: { timeout: 5_000 },
    fullyParallel: false,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 1 : 0,
    workers: 1,
    reporter: process.env.CI ? [['github'], ['list']] : 'list',
    use: {
        baseURL: BASE_URL,
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
        viewport: { width: 1280, height: 1024 },
    },
    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
    ],
    // When BASE_URL is set externally, assume the user is running their
    // own dev server and skip spawning one here. Otherwise spawn our own.
    ...(process.env.BASE_URL
        ? {}
        : {
              webServer: {
                  command: `python testserver.py --port=${PORT}`,
                  cwd: REPO_ROOT,
                  url: `${BASE_URL}/en/admin/`,
                  reuseExistingServer: !process.env.CI,
                  timeout: 60_000,
                  stdout: 'pipe',
                  stderr: 'pipe',
                  env: {
                      ...process.env,
                      CMS_TEST_CONTRIB_APPS: 'cms.contrib.frontend_v5',
                  },
              },
          }),
});
