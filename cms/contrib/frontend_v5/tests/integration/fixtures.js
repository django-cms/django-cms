// @ts-check
/*
 * Playwright fixtures for the cms.contrib.frontend_v5 integration
 * tests. Provides:
 *
 *   - `settings`: base URL, credentials, admin paths read from env.
 *   - `authenticatedPage`: a fixture that logs in before handing the
 *     page to the test. Matches the shape of the legacy
 *     cms/tests/frontend/integration/helpers/fixtures.js so existing
 *     patterns transfer cleanly.
 *   - `cms`: helper methods for common operations — create/delete a
 *     test page, navigate to a page's advanced settings.
 *
 * Deliberately minimal — only the helpers the changeform specs
 * actually use. No CMS toolbar / plugin / structureboard helpers;
 * those come when we port those bundles.
 */
const playwright = require('@playwright/test');

const baseTest = playwright.test;
const expect = playwright.expect;

const settings = {
    baseUrl: process.env.BASE_URL || 'http://localhost:9010',
    credentials: {
        username: process.env.TEST_USERNAME || 'admin',
        password: process.env.TEST_PASSWORD || 'admin',
    },
    get adminUrl() {
        return `${this.baseUrl}/en/admin/`;
    },
    get pageAdminUrl() {
        return `${this.baseUrl}/en/admin/cms/page/`;
    },
    /** Title used for the auto-created test page in beforeAll. */
    testPageTitle: 'frontend_v5 changeform test page',
};

/**
 * Fill the admin login form. Shared between the authenticatedPage
 * fixture and explicit helpers.
 */
async function login(page) {
    await page.goto(settings.adminUrl);
    // Defensive: clear any pre-existing localStorage from a previous run.
    await page.evaluate(() => localStorage.clear()).catch(() => {});
    await page.waitForSelector('input[name="username"]');
    await page.fill('input[name="username"]', settings.credentials.username);
    await page.fill('input[name="password"]', settings.credentials.password);
    await page.click('input[type="submit"]');
    await page.waitForURL(/\/admin\//, { timeout: 10_000 });
}

/**
 * Helpers bundled into the `cms` fixture. Each takes a `page` implicitly
 * via closure — they're defined inside the fixture below.
 */
const test = baseTest.extend({
    authenticatedPage: async ({ page }, use) => {
        await login(page);
        await use(page);
        // Best-effort cleanup: clear cookies so the next test starts
        // from a clean session if it re-uses the same context.
        await page.context().clearCookies();
    },

    cms: async ({ page }, use) => {
        const helpers = {
            login: () => login(page),

            /**
             * Navigate to the page admin changelist and return the ID
             * of the first page in the tree. Returns null if no pages
             * exist — the caller is responsible for handling that case
             * (typically: create one).
             */
            async getFirstPageId() {
                await page.goto(settings.pageAdminUrl);
                // The page tree renders each page as a row with a link
                // whose href contains the page id. We look for the
                // advanced-settings or change-form link under the first
                // row — the exact selector matches the CMS page tree
                // template output.
                const firstLink = page.locator(
                    'a[href*="/cms/page/"][href*="/change/"], a[href*="/cms/page/"][href*="/advanced-settings/"]',
                ).first();
                if ((await firstLink.count()) === 0) return null;
                const href = await firstLink.getAttribute('href');
                if (!href) return null;
                const match = href.match(/\/cms\/page\/(\d+)\//);
                return match ? match[1] : null;
            },

            /**
             * Create a CMS page via the "add page" wizard flow, which
             * is the only public path to create a page from scratch
             * with this codebase. Returns the page ID of the newly
             * created page. Side effect: navigates the page to the
             * newly-created page's edit URL.
             *
             * If the wizard modal markup differs across versions, this
             * helper is the single point to adjust.
             */
            async createPage(title = settings.testPageTitle) {
                // The wizard lives at the root URL when there are no
                // pages yet. For subsequent pages we use the admin
                // "Add" route. Detect by trying both.
                await page.goto(`${settings.baseUrl}/en/?toolbar_on`);

                // Wait for either the CMS toolbar (no pages yet → wizard
                // auto-opens) or for the page to be rendered.
                await page.waitForLoadState('domcontentloaded');

                // Some builds of django-cms render the first-page
                // wizard immediately. Others require clicking the
                // toolbar "Create" link. Try the simpler path first.
                const wizardLink = page.locator('a[href*="/cms_wizard/create/"]').first();
                if ((await wizardLink.count()) > 0) {
                    await wizardLink.click();
                    // Wait for wizard modal to open.
                    await page.waitForSelector('.cms-modal', { timeout: 10_000 });
                    // Click "Next" to advance to the form step.
                    const nextBtn = page.locator(
                        '.cms-modal-foot a.cms-btn.cms-btn-action.default',
                    );
                    await nextBtn.click();
                    await page.waitForSelector('.cms-modal iframe');
                    const frame = page.frameLocator('.cms-modal iframe');
                    await frame.locator('#id_1-title').fill(title);
                    await nextBtn.click();
                    // Wait for the page to be ready with toolbar.
                    await page.waitForSelector('.cms-ready', { timeout: 15_000 });
                }

                // Pick up the page id from window.CMS.config if the
                // toolbar loaded it; otherwise fall back to the page
                // tree lookup.
                const idFromConfig = await page
                    .evaluate(() => {
                        const cfg = window.CMS && window.CMS.config;
                        return cfg && cfg.request && cfg.request.pk
                            ? String(cfg.request.pk)
                            : null;
                    })
                    .catch(() => null);
                if (idFromConfig) return idFromConfig;
                return this.getFirstPageId();
            },

            /**
             * Navigate to the advanced settings form for a given page.
             * This is the page that renders the admin.changeform bundle.
             */
            async openAdvancedSettings(pageId) {
                await page.goto(
                    `${settings.baseUrl}/en/admin/cms/page/${pageId}/advanced-settings/`,
                );
                // The form renders the title and slug inputs — wait for
                // at least the title input to be ready so follow-up
                // operations can target them immediately.
                await page.waitForSelector('#id_title', { timeout: 10_000 });
            },
        };

        await use(helpers);
    },
});

module.exports = { test, expect, settings, login };
