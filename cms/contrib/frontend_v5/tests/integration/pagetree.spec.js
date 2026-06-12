// @ts-check
/*
 * Integration tests for the pagetree bundle running against the new
 * nested-<ul> DOM (decision 3 in CLAUDE.md). These tests only match
 * when cms.contrib.frontend_v5 is active — legacy pagetree renders a
 * <table> and none of the `ul[role="tree"]` selectors match.
 *
 * Scope:
 *   - Initial render: tree root is <ul role="tree"> with treeitem rows
 *   - Expand/collapse: caret toggles children, lazy-loads subtree
 *   - Dropdown menus: per-row burger opens, closes on outside click
 *   - Header search/filter: query param pre-renders matching rows
 *
 * Drag-and-drop is deliberately out of scope: Playwright cannot
 * reliably synthesise the pointer-events / mouse sequences SortableJS
 * needs to enter its drag state. DnD is covered by vitest unit tests
 * that mock SortableJS events.
 */
const { test, expect, settings } = require('./fixtures');

test.beforeAll(async ({ browser }) => {
    // Bootstrap: make sure at least one CMS page exists so the tree
    // has something to render. Re-uses the same wizard flow as the
    // changeform spec.
    const ctx = await browser.newContext();
    const page = await ctx.newPage();

    await page.goto(settings.adminUrl);
    await page.waitForSelector('input[name="username"]');
    await page.fill('input[name="username"]', settings.credentials.username);
    await page.fill('input[name="password"]', settings.credentials.password);
    await page.click('input[type="submit"]');
    await page.waitForURL(/\/admin\//, { timeout: 10_000 });

    await page.goto(settings.pageAdminUrl);
    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});

    const hasRows = await page
        .locator('li[role="treeitem"], a[href*="/cms/placeholder/object/"][href*="/edit/"]')
        .count();
    if (hasRows === 0) {
        // Create a page via the wizard.
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
            await frame.locator('#id_1-title').fill('pagetree spec bootstrap');
            await nextBtn.click();
            await page.waitForLoadState('networkidle', { timeout: 30_000 });
        }
    }

    await ctx.close();
});

test.describe('pagetree — initial render (new nested-ul DOM)', () => {
    test('renders a <ul role="tree"> with at least one <li role="treeitem">', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openPageTree();

        const tree = page.locator('ul[role="tree"].cms-pagetree-list');
        await expect(tree).toBeVisible();

        const rows = tree.locator('> li[role="treeitem"]');
        expect(await rows.count()).toBeGreaterThan(0);
    });

    test('top-level rows carry aria-level="1"', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openPageTree();

        const firstRow = page
            .locator('ul[role="tree"] > li[role="treeitem"]')
            .first();
        await expect(firstRow).toHaveAttribute('aria-level', '1');
    });

    test('tree container has no <table>/<tr> remnants', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openPageTree();

        // The new pagetree template replaces the legacy <table> entirely.
        // If we see a <table> inside #changelist that's NOT inside a
        // dropdown/widget, the legacy template is shadowing — the
        // contrib template ordering is broken.
        const tableCount = await page
            .locator('#changelist > table, #changelist .cms-pagetree > table')
            .count();
        expect(tableCount).toBe(0);
    });
});

test.describe('pagetree — expand, collapse, lazy-load', () => {
    test('clicking a caret on a branch node toggles its children', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openPageTree();

        // Find the first row that HAS an enabled toggle (branch node).
        // Leaf nodes also get a .cms-tree-toggle but it's disabled.
        const branchRow = page
            .locator('li[role="treeitem"]:has(.cms-tree-toggle:not([disabled]))')
            .first();

        if ((await branchRow.count()) === 0) {
            test.skip(
                true,
                'No branch nodes in this tree. Add a child page fixture to cover this path.',
            );
            return;
        }

        const caret = branchRow
            .locator(':scope > .cms-tree-row > .cms-tree-toggle')
            .first();
        await caret.click();

        // After expand, the row has aria-expanded="true" and a child <ul>.
        await expect(branchRow).toHaveAttribute('aria-expanded', 'true');
        await expect(branchRow.locator('> ul[role="group"]')).toBeVisible();

        // Click again → collapses.
        await caret.click();
        await expect(branchRow).toHaveAttribute('aria-expanded', 'false');
    });
});

test.describe('pagetree — dropdown menus (per-row burger)', () => {
    test('clicking a dropdown trigger opens its menu', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openPageTree();

        const trigger = page
            .locator('.js-cms-pagetree-dropdown-trigger')
            .first();
        if ((await trigger.count()) === 0) {
            test.skip(
                true,
                'No dropdown triggers on this tree — nothing to click.',
            );
            return;
        }

        await trigger.click();

        const dropdown = page
            .locator('.js-cms-pagetree-dropdown.cms-pagetree-dropdown-menu-open')
            .first();
        await expect(dropdown).toBeVisible();
    });

    test('clicking outside closes the dropdown', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openPageTree();

        const trigger = page
            .locator('.js-cms-pagetree-dropdown-trigger')
            .first();
        if ((await trigger.count()) === 0) {
            test.skip(true, 'No dropdown triggers on this tree.');
            return;
        }

        await trigger.click();
        await expect(
            page.locator('.js-cms-pagetree-dropdown.cms-pagetree-dropdown-menu-open'),
        ).toHaveCount(1);

        // Click on the tree root (outside the dropdown but inside the page)
        await page.locator('ul[role="tree"]').click({ position: { x: 5, y: 5 } });
        await expect(
            page.locator('.js-cms-pagetree-dropdown.cms-pagetree-dropdown-menu-open'),
        ).toHaveCount(0);
    });
});

test.describe('pagetree — header search / filter', () => {
    test('submitting the search form navigates to ?q= and renders only matches', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openPageTree();

        // Find the search field — may not exist on every tree page
        // (e.g. empty tree). Skip gracefully.
        const searchField = page.locator('#field-searchbar');
        if ((await searchField.count()) === 0) {
            test.skip(true, 'No search field on this tree.');
            return;
        }

        // Type a query that is unlikely to match anything real, so the
        // filter renders an empty-or-near-empty result. We're testing
        // the wiring, not relevance.
        const unlikely = 'zzz-no-match-xyz';
        await searchField.fill(unlikely);
        await searchField.press('Enter');

        await page.waitForURL(/[?&]q=zzz-no-match-xyz/, { timeout: 10_000 });

        // In filtered mode the template adds `.filtered` class to the
        // root container. Verify the filtered render path took effect.
        await expect(page.locator('#changelist.filtered')).toBeVisible();
    });

    test('in filtered mode, get_tree is NOT called (server pre-renders rows)', async ({
        cms,
        authenticatedPage: page,
    }) => {
        let getTreeCalled = false;
        page.on('request', (req) => {
            if (/\/admin\/cms\/pagecontent\/get-tree\//.test(req.url())) {
                getTreeCalled = true;
            }
        });

        // Use an unlikely query so filtered mode is deterministic —
        // we already know from the previous test that `zzz-no-match-xyz`
        // is handled by the admin as a filter (#changelist.filtered).
        // The bug we're regressing: contrib's filtered path must adopt
        // the server-rendered <ul> instead of calling get_tree.
        await page.goto(
            `${settings.pageAdminUrl}?q=zzz-no-match-xyz`,
        );
        // The tree JS runs on DOMContentLoaded; waitForLoadState gives
        // it time to call loadTree() if it's going to.
        await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});

        // Confirm we ARE in filtered mode (canary for query-doesn't-
        // trigger-filtering false positives).
        await expect(page.locator('#changelist.filtered')).toBeVisible();

        expect(getTreeCalled).toBe(false);
    });

    test('filter trigger toggles the filter container', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openPageTree();

        const trigger = page.locator('.js-cms-pagetree-header-filter-trigger');
        const container = page.locator(
            '.js-cms-pagetree-header-filter-container',
        );
        if ((await trigger.count()) === 0) {
            test.skip(true, 'No filter trigger on this tree.');
            return;
        }

        await trigger.click();
        // The JS sets display:block inline on open.
        await expect(container).toBeVisible();

        await trigger.click();
        await expect(container).toBeHidden();
    });
});
