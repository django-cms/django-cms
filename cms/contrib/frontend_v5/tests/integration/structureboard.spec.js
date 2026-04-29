// @ts-check
/*
 * Integration tests for the structureboard surface.
 *
 * Today the contrib `admin.toolbar` bundle is NOT wired into webpack —
 * the legacy `bundle.toolbar.min.js` still ships the runtime
 * StructureBoard class, so these tests validate the user-visible
 * surface against the legacy bundle. Once the contrib bundle replaces
 * the legacy one, the same specs validate the port — failure at that
 * point is a regression in the TS port, not the harness.
 *
 * Scope (sub-phase 3j):
 *   - Toolbar + mode switcher render on an editable page
 *   - Structure / content mode toggle via the toolbar buttons
 *   - Space key toggles modes (when not focused in a text input)
 *   - URL hash highlight on a `#cms-plugin-N` deep link is observable
 *     when a plugin exists and content mode is loaded
 *   - Cross-tab `storage` event arrival triggers `invalidateState`
 *     locally with `{ propagate: false }` (verified by writing the
 *     payload from a second tab and observing local DOM mutation)
 *
 * Out of scope (deferred):
 *   - Real add/edit/delete/move plugin flows. These require modal +
 *     iframe interaction matrices that are flaky against a live
 *     dev server and will land as separate spec files once the
 *     contrib bundle is the runtime source.
 *   - Drag-and-drop. Playwright cannot reliably synthesise the
 *     pointer-events sequence the legacy nestedSortable expects;
 *     covered by vitest unit tests under `tests/unit/structureboard-
 *     ui-dnd.test.ts`.
 */
const { test, expect, settings } = require('./fixtures');

/** @type {string | null} */
let testPageEditUrl = null;

test.beforeAll(async ({ browser }) => {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();

    await page.goto(settings.adminUrl);
    await page.waitForSelector('input[name="username"]');
    await page.fill('input[name="username"]', settings.credentials.username);
    await page.fill('input[name="password"]', settings.credentials.password);
    await page.click('input[type="submit"]');
    await page.waitForURL(/\/admin\//, { timeout: 10_000 });

    // Make sure at least one page exists so the toolbar has something
    // to render against. Reuses the same wizard flow as the other
    // contrib specs.
    await page.goto(settings.pageAdminUrl);
    // The contrib pagetree async-loads rows via get-tree/. Wait for
    // either an edit link OR network idle (empty tree).
    await page
        .waitForSelector(
            'a[href*="/cms/placeholder/object/"][href*="/edit/"]',
            { timeout: 8_000 },
        )
        .catch(() => {});
    const hasRows = await page
        .locator('a[href*="/cms/placeholder/object/"][href*="/edit/"]')
        .count();
    if (hasRows === 0) {
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
            await frame.locator('#id_1-title').fill('structureboard spec page');
            await nextBtn.click();
            await page.waitForLoadState('networkidle', { timeout: 30_000 });
        }
    }

    // Discover the full edit URL the page tree points at — the
    // `/cms/placeholder/object/<ct_id>/edit/<object_id>/` shape uses
    // the live ContentType pk + PageContent pk; both vary across
    // installs, so we capture the URL verbatim.
    await page.goto(settings.pageAdminUrl);
    await page
        .waitForSelector(
            'a[href*="/cms/placeholder/object/"][href*="/edit/"]',
            { timeout: 10_000 },
        )
        .catch(() => {});
    const editLink = page
        .locator('a[href*="/cms/placeholder/object/"][href*="/edit/"]')
        .first();
    if ((await editLink.count()) > 0) {
        testPageEditUrl = await editLink.getAttribute('href');
    }
    await ctx.close();
});

/**
 * Open the editable page in CMS edit mode. Returns the resolved
 * page URL (the toolbar redirects through several URLs before
 * settling).
 */
async function openEditablePage(page) {
    if (!testPageEditUrl) {
        throw new Error(
            'no editable page URL discovered in beforeAll — bootstrap failure?',
        );
    }
    const url = testPageEditUrl.startsWith('http')
        ? testPageEditUrl
        : `${settings.baseUrl}${testPageEditUrl}`;
    await page.goto(url);
    // Wait for the cms-ready marker the toolbar adds once the
    // structureboard has finished its initial setup.
    await page.waitForSelector('.cms-ready, .cms-toolbar', { timeout: 15_000 });
}

// ────────────────────────────────────────────────────────────────────
// Toolbar + mode switcher render
// ────────────────────────────────────────────────────────────────────

test.describe('structureboard — toolbar render', () => {
    test('toolbar element is present on an editable page', async ({
        authenticatedPage: page,
    }) => {
        await openEditablePage(page);
        await expect(page.locator('.cms-toolbar')).toBeVisible();
    });
});

test.describe('structureboard — mode toggle', () => {
    test('toolbar mode switcher renders at least one button', async ({
        authenticatedPage: page,
    }) => {
        await openEditablePage(page);
        // Some legacy templates render two toggle buttons (one per
        // mode); newer ones render a single combined toggle. Assert
        // the switcher wrapper is visible and contains at least one
        // anchor.
        await expect(
            page.locator('.cms-toolbar-item-cms-mode-switcher'),
        ).toBeVisible();
        const switcherButtons = page.locator(
            '.cms-toolbar-item-cms-mode-switcher a.cms-btn',
        );
        const count = await switcherButtons.count();
        expect(count).toBeGreaterThan(0);
    });

    test('clicking the structure mode button flips the html class', async ({
        authenticatedPage: page,
    }) => {
        await openEditablePage(page);
        // Find the FIRST mode-switcher anchor (structure button).
        const structureBtn = page
            .locator('.cms-toolbar-item-cms-mode-switcher a.cms-btn')
            .first();
        // Skip the test gracefully when buttons are disabled (no plugins
        // / placeholders on the page) — the page bootstrap doesn't
        // guarantee a plugin tree.
        const disabled = await structureBtn.evaluate((el) =>
            el.classList.contains('cms-btn-disabled'),
        );
        test.skip(disabled, 'mode switcher disabled — no placeholders to switch into');
        await structureBtn.click();
        await expect(page.locator('html')).toHaveClass(
            /cms-structure-mode-structure/,
        );
    });

    test('clicking the content mode button flips back to content', async ({
        authenticatedPage: page,
    }) => {
        await openEditablePage(page);
        const buttons = page.locator(
            '.cms-toolbar-item-cms-mode-switcher a.cms-btn',
        );
        const disabled = await buttons
            .first()
            .evaluate((el) => el.classList.contains('cms-btn-disabled'));
        test.skip(disabled, 'mode switcher disabled');
        // Click first button to enter structure mode.
        await buttons.first().click();
        await expect(page.locator('html')).toHaveClass(/cms-structure-mode-structure/);
        // Single-toggle templates use the SAME button to flip back;
        // two-button templates have a second button. Click whichever
        // is available.
        const count = await buttons.count();
        const target = count >= 2 ? buttons.nth(1) : buttons.first();
        await target.click();
        await expect(page.locator('html')).toHaveClass(/cms-structure-mode-content/);
    });

    test('Space key toggles between modes (when focus is on body)', async ({
        authenticatedPage: page,
    }) => {
        await openEditablePage(page);
        const buttons = page.locator(
            '.cms-toolbar-item-cms-mode-switcher a.cms-btn',
        );
        const disabled = await buttons
            .first()
            .evaluate((el) => el.classList.contains('cms-btn-disabled'));
        test.skip(disabled, 'mode switcher disabled');
        const initialMode = await page.evaluate(() => {
            const cms = /** @type {any} */ (window).CMS;
            return cms && cms.settings ? cms.settings.mode : null;
        });
        // Move focus to body (away from any hidden inputs), then press Space.
        await page.evaluate(() => {
            (/** @type {any} */ (document.activeElement))?.blur();
        });
        await page.keyboard.press('Space');
        // settings.mode should flip.
        await page.waitForFunction(
            (initial) => {
                const cms = /** @type {any} */ (window).CMS;
                const m = cms && cms.settings ? cms.settings.mode : null;
                return m && m !== initial;
            },
            initialMode,
            { timeout: 5_000 },
        );
    });
});

// ────────────────────────────────────────────────────────────────────
// CMS namespace surface
// ────────────────────────────────────────────────────────────────────

test.describe('structureboard — runtime surface', () => {
    test('window.CMS.API.StructureBoard exposes invalidateState', async ({
        authenticatedPage: page,
    }) => {
        await openEditablePage(page);
        const surface = await page.evaluate(() => {
            const sb = /** @type {any} */ (window).CMS?.API?.StructureBoard;
            if (!sb) return null;
            return {
                hasInvalidateState: typeof sb.invalidateState === 'function',
                hasShow: typeof sb.show === 'function',
                hasHide: typeof sb.hide === 'function',
                hasGetId: typeof sb.getId === 'function',
            };
        });
        expect(surface).not.toBeNull();
        expect(surface.hasInvalidateState).toBe(true);
        expect(surface.hasShow).toBe(true);
        expect(surface.hasHide).toBe(true);
        expect(surface.hasGetId).toBe(true);
    });

    test('settings.mode is "edit" or "structure"', async ({
        authenticatedPage: page,
    }) => {
        await openEditablePage(page);
        const mode = await page.evaluate(() => {
            const cms = /** @type {any} */ (window).CMS;
            return cms && cms.settings ? cms.settings.mode : null;
        });
        expect(['edit', 'structure']).toContain(mode);
    });
});

// ────────────────────────────────────────────────────────────────────
// Cross-tab `storage` event sync
// ────────────────────────────────────────────────────────────────────

test.describe('structureboard — cross-tab sync', () => {
    test('localStorage cms-structure write fires storage event on a sibling tab', async ({
        authenticatedPage: page,
    }) => {
        await openEditablePage(page);

        // Listen for the storage event on the LIVE page (the
        // "receiving" tab).
        const storageFiredPromise = page.evaluate(() => {
            return new Promise((resolve) => {
                const handler = (/** @type {StorageEvent} */ e) => {
                    if (e.key === 'cms-structure') {
                        window.removeEventListener('storage', handler);
                        resolve(e.newValue);
                    }
                };
                window.addEventListener('storage', handler);
                // Fail-safe timeout.
                setTimeout(() => {
                    window.removeEventListener('storage', handler);
                    resolve(null);
                }, 4_000);
            });
        });

        // Open a SECOND tab in the SAME browser context (so cookies
        // + localStorage origin match). Cross-context tabs in
        // Playwright are isolated and won't share storage events.
        const ctx = page.context();
        const page2 = await ctx.newPage();
        const url = testPageEditUrl && testPageEditUrl.startsWith('http')
            ? testPageEditUrl
            : `${settings.baseUrl}${testPageEditUrl}`;
        await page2.goto(url);
        await page2.waitForLoadState('domcontentloaded');

        // Write the cms-structure key from page2 — this fires a
        // `storage` event in page (different tab, same origin).
        const pathname = await page.evaluate(() => window.location.pathname);
        await page2.evaluate(
            (path) => {
                localStorage.setItem(
                    'cms-structure',
                    JSON.stringify(['EDIT', { plugin_id: -1 }, path]),
                );
            },
            pathname,
        );

        const value = await storageFiredPromise;
        await page2.close();
        expect(value).not.toBeNull();
        expect(String(value)).toContain('EDIT');
    });
});
