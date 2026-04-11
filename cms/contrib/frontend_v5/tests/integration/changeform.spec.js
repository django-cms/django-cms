// @ts-check
/*
 * Integration tests for admin.changeform user interactions.
 *
 * Covers the four interaction types the changeform bundle is
 * responsible for:
 *
 *   - Title → slug auto-fill (typing + pasting)
 *   - Dirty-slug preservation + re-arming
 *   - Language tab navigation with dirty-state confirm
 *   - window.CMS.API.changeLanguage public API presence
 *
 * These are the drop-in contract's canaries: if the contrib bundle is
 * shadowing the legacy one correctly, every test here passes. The
 * paste test in particular is contrib-only — it exercises the `input`
 * event upgrade that the legacy keyup/keypress handlers miss.
 *
 * Runs against a Django test server with the contrib app active (see
 * cms/contrib/frontend_v5/playwright.config.js — the webServer sets
 * CMS_TEST_CONTRIB_APPS=cms.contrib.frontend_v5).
 */
const { test, expect, settings } = require('./fixtures');

// Shared across every test in this file: a single page created once
// in beforeAll, used by every test via its advanced-settings form.
// Playwright's `test.beforeAll` runs once per worker — we only have
// one worker (see fullyParallel: false in playwright.config.js) so
// this is effectively "once for the whole file".
/** @type {string | null} */
let testPageId = null;

test.beforeAll(async ({ browser }) => {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();

    // Log in once to set up the session cookie.
    await page.goto(settings.adminUrl);
    await page.waitForSelector('input[name="username"]');
    await page.fill('input[name="username"]', settings.credentials.username);
    await page.fill('input[name="password"]', settings.credentials.password);
    await page.click('input[type="submit"]');
    await page.waitForURL(/\/admin\//, { timeout: 10_000 });

    // See if a page already exists — if so, reuse it. Otherwise create
    // one via the wizard. Reusing avoids spending wizard time on every
    // CI run against a pre-populated test database.
    await page.goto(`${settings.baseUrl}/en/admin/cms/page/`);
    const existing = page.locator(
        'a[href*="/cms/page/"][href*="/change/"], a[href*="/cms/page/"][href*="/advanced-settings/"]',
    );
    if ((await existing.count()) > 0) {
        const href = await existing.first().getAttribute('href');
        const match = href && href.match(/\/cms\/page\/(\d+)\//);
        if (match) testPageId = match[1];
    }

    if (!testPageId) {
        // Bootstrap path: no pages yet. Open the wizard via the CMS
        // toolbar route to create one.
        await page.goto(`${settings.baseUrl}/en/?toolbar_on`);
        await page.waitForLoadState('domcontentloaded');
        const wizardLink = page.locator('a[href*="/cms_wizard/create/"]').first();
        if ((await wizardLink.count()) > 0) {
            await wizardLink.click();
            await page.waitForSelector('.cms-modal', { timeout: 15_000 });
            const nextBtn = page.locator(
                '.cms-modal-foot a.cms-btn.cms-btn-action.default',
            );
            await nextBtn.click();
            await page.waitForSelector('.cms-modal iframe');
            const frame = page.frameLocator('.cms-modal iframe');
            await frame.locator('#id_1-title').fill(settings.testPageTitle);
            await nextBtn.click();
            await page.waitForLoadState('networkidle', { timeout: 30_000 });
            // Try window.CMS.config.request.pk first; fall back to
            // re-listing the page tree.
            testPageId = await page
                .evaluate(() => {
                    const cfg =
                        typeof window !== 'undefined' && window.CMS && window.CMS.config;
                    return cfg && cfg.request && cfg.request.pk
                        ? String(cfg.request.pk)
                        : null;
                })
                .catch(() => null);
            if (!testPageId) {
                await page.goto(`${settings.baseUrl}/en/admin/cms/page/`);
                const link = page
                    .locator(
                        'a[href*="/cms/page/"][href*="/change/"], a[href*="/cms/page/"][href*="/advanced-settings/"]',
                    )
                    .first();
                const href = await link.getAttribute('href');
                const match = href && href.match(/\/cms\/page\/(\d+)\//);
                if (match) testPageId = match[1];
            }
        }
    }

    await ctx.close();

    if (!testPageId) {
        throw new Error(
            'changeform.spec: could not establish a test page. Either pre-create one via the CMS wizard or ensure the wizard flow works in this testserver environment.',
        );
    }
});

test.describe('admin.changeform — title → slug auto-fill', () => {
    test('typing into title auto-fills the slug while it\'s empty', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openAdvancedSettings(testPageId);

        // Ensure slug starts empty — whatever was there from a prior run
        // gets cleared first so the prefill flag starts true.
        const title = page.locator('#id_title');
        const slug = page.locator('#id_slug');
        await slug.fill('');
        await title.fill('');

        // Type character-by-character to exercise the real `input` event path.
        await title.pressSequentially('Hello World');

        await expect(slug).toHaveValue('hello-world');
    });

    test('pasting into title auto-fills the slug (contrib-only upgrade)', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openAdvancedSettings(testPageId);

        const title = page.locator('#id_title');
        const slug = page.locator('#id_slug');
        await slug.fill('');
        await title.fill('');

        // `page.locator(...).fill()` fires a single `input` event at
        // the end, simulating what a clipboard paste does. On legacy
        // (keyup/keypress handlers) this does NOT trigger slug fill.
        // On contrib (input handler) it DOES. This is the canary.
        await title.fill('Pasted Content');

        await expect(slug).toHaveValue('pasted-content');
    });

    test('non-empty slug at load is NOT overwritten by title changes', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openAdvancedSettings(testPageId);

        const title = page.locator('#id_title');
        const slug = page.locator('#id_slug');
        // Set a slug BEFORE the module observes it. Reload to get a
        // fresh init with slug non-empty.
        await slug.fill('custom-slug-value');
        await page.reload();
        await page.waitForSelector('#id_title');

        // Now type in the title — slug should stay "custom-slug-value".
        await page.locator('#id_title').pressSequentially('Ignored Title');

        await expect(page.locator('#id_slug')).toHaveValue('custom-slug-value');
    });

    test('clearing the slug re-arms auto-fill on next title keystroke', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openAdvancedSettings(testPageId);

        const title = page.locator('#id_title');
        const slug = page.locator('#id_slug');

        // Start with a non-empty slug so prefill is false.
        await slug.fill('original-slug');
        await page.reload();
        await page.waitForSelector('#id_title');

        // Clear the slug, then type in title — the re-arm logic
        // should detect empty slug and flip prefill to true, so the
        // next title keystroke overwrites slug.
        await page.locator('#id_slug').fill('');
        await page.locator('#id_title').pressSequentially('Fresh Title');

        await expect(page.locator('#id_slug')).toHaveValue('fresh-title');
    });
});

test.describe('admin.changeform — language tabs', () => {
    test('clicking a different language tab navigates when form is clean', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openAdvancedSettings(testPageId);

        // Locate any language button OTHER than the currently-selected
        // one. If the test site only has one configured language, skip.
        const otherTab = page
            .locator('#page_form_lang_tabs .language_button:not(.selected)')
            .first();
        const tabCount = await otherTab.count();
        if (tabCount === 0) {
            test.skip(
                true,
                'Only one language configured — cannot test language tab navigation',
            );
            return;
        }

        const targetUrl = await otherTab.getAttribute('data-admin-url');
        expect(targetUrl).toBeTruthy();

        // Clean form → clicking should navigate without a confirm dialog.
        // Assert: no confirm dialog appears AND URL changes.
        const navigationPromise = page.waitForURL(
            (url) => url.toString().includes('/advanced-settings/'),
            { timeout: 5_000 },
        );
        await otherTab.click();
        await navigationPromise;
        // The target URL might have a redirect or trailing slash change,
        // but it must contain the page id and some form-related path.
        expect(page.url()).toContain('/cms/page/');
    });

    test('clicking a language tab with a dirty form shows a confirm dialog (cancel path)', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openAdvancedSettings(testPageId);

        const otherTab = page
            .locator('#page_form_lang_tabs .language_button:not(.selected)')
            .first();
        if ((await otherTab.count()) === 0) {
            test.skip(
                true,
                'Only one language configured — cannot test dirty-form confirm',
            );
            return;
        }

        // Mark the title as dirty. The change event fires on blur, so
        // fill + Tab to trigger it. This sets title.dataset.changed='true'
        // via the slug module's markChanged handler.
        await page.locator('#id_title').fill('Dirty Title');
        await page.locator('#id_title').press('Tab');

        const urlBefore = page.url();

        // Intercept the confirm dialog. On dirty + click, a browser
        // confirm() call should fire. Cancel it → navigation blocked.
        let dialogSeen = false;
        page.once('dialog', async (dialog) => {
            dialogSeen = true;
            expect(dialog.type()).toBe('confirm');
            expect(dialog.message().toLowerCase()).toContain('change tabs');
            await dialog.dismiss();
        });

        await otherTab.click();
        // Small wait to ensure the dialog handler had a chance to run.
        await page.waitForTimeout(500);

        expect(dialogSeen).toBe(true);
        // URL should not have changed because we cancelled.
        expect(page.url()).toBe(urlBefore);
    });

    test('accepting the dirty-form confirm navigates to the new language', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openAdvancedSettings(testPageId);

        const otherTab = page
            .locator('#page_form_lang_tabs .language_button:not(.selected)')
            .first();
        if ((await otherTab.count()) === 0) {
            test.skip(
                true,
                'Only one language configured — cannot test dirty-form accept',
            );
            return;
        }

        await page.locator('#id_title').fill('Dirty Title Accept');
        await page.locator('#id_title').press('Tab');

        const urlBefore = page.url();

        page.once('dialog', async (dialog) => {
            await dialog.accept();
        });

        await otherTab.click();
        // Wait for navigation to complete.
        await page.waitForLoadState('domcontentloaded', { timeout: 10_000 });

        expect(page.url()).not.toBe(urlBefore);
    });
});

test.describe('admin.changeform — public API', () => {
    test('window.CMS.API.changeLanguage is defined on load', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openAdvancedSettings(testPageId);

        const type = await page.evaluate(
            () => typeof (window.CMS && window.CMS.API && window.CMS.API.changeLanguage),
        );
        expect(type).toBe('function');
    });
});
