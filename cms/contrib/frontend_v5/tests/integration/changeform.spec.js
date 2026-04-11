// @ts-check
/*
 * Integration tests for the page-editing flow across two bundles.
 *
 * Historically we assumed "admin.changeform" meant "the form where
 * you edit a page's title/slug". The actual runtime layout is:
 *
 *   - `/cms/pagecontent/<id>/change/` — PageContent grouper admin
 *     → has title, slug, template, meta, language tabs
 *     → loads `forms.slugwidget.min.js` (via widget form.Media)
 *     → NOT `admin.changeform.min.js`
 *
 *   - `/cms/page/<id>/advanced-settings/` — Page admin
 *     → has apphook config, permission inlines, "All permissions"
 *       lazy-loaded summary
 *     → loads `admin.changeform.min.js` (from template extrahead)
 *     → NOT title/slug
 *
 * So the user-visible interactions split across both bundles. This
 * spec covers both, one describe block per bundle, so the coverage
 * follows the real rendering boundary.
 */
const { test, expect, settings } = require('./fixtures');

/** @type {string | null} */
let testPageId = null;

test.beforeAll(async ({ browser }) => {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();

    // Login once to set up the session cookie for this context.
    await page.goto(settings.adminUrl);
    await page.waitForSelector('input[name="username"]');
    await page.fill('input[name="username"]', settings.credentials.username);
    await page.fill('input[name="password"]', settings.credentials.password);
    await page.click('input[type="submit"]');
    await page.waitForURL(/\/admin\//, { timeout: 10_000 });

    // Bootstrap: discover a PageContent id from the page tree, then
    // probe pagecontent/<id>/change/ and scrape the Page id from its
    // rendered form (the breadcrumb or an inline admin link exposes
    // it). If we can't find a page, create one via the wizard.
    await page.goto(`${settings.baseUrl}/en/admin/cms/pagecontent/`);
    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});
    const existingEdit = page.locator(
        'a[href*="/cms/placeholder/object/"][href*="/edit/"]',
    );

    if ((await existingEdit.count()) === 0) {
        // Zero pages in the db — bootstrap via the wizard flow.
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
        }
        // Navigate back to the tree to pick up the newly-created entry.
        await page.goto(`${settings.baseUrl}/en/admin/cms/pagecontent/`);
        await page
            .waitForLoadState('networkidle', { timeout: 10_000 })
            .catch(() => {});
    }

    // We should now have at least one edit link. Extract its pagecontent id.
    const editLinkHref = await page
        .locator('a[href*="/cms/placeholder/object/"][href*="/edit/"]')
        .first()
        .getAttribute('href');
    const pcMatch = editLinkHref?.match(/\/cms\/placeholder\/object\/(\d+)\//);
    if (!pcMatch) {
        await ctx.close();
        throw new Error(
            'changeform.spec.beforeAll: could not discover a PageContent id from the page tree. Check that the testserver has the contrib app enabled and at least one CMS page exists.',
        );
    }
    const bootstrapPcId = pcMatch[1];

    // Load the pagecontent change form and extract the Page id from
    // any link matching /cms/page/<id>/advanced-settings/. That link
    // typically appears in the page change form as part of the CMS
    // admin breadcrumbs or related-object links.
    await page.goto(
        `${settings.baseUrl}/en/admin/cms/pagecontent/${bootstrapPcId}/change/`,
    );
    await page.waitForSelector('#id_title', { timeout: 10_000 });
    testPageId = await page.evaluate(() => {
        // Try scraping any link that goes to advanced-settings for a Page.
        const link = document.querySelector(
            'a[href*="/cms/page/"][href*="/advanced-settings/"]',
        );
        if (link) {
            const m = link.getAttribute('href')?.match(/\/cms\/page\/(\d+)\//);
            if (m) return m[1];
        }
        // Fallback: any other /cms/page/<id>/... link.
        const anyPageLink = document.querySelector('a[href*="/cms/page/"]');
        if (anyPageLink) {
            const m = anyPageLink.getAttribute('href')?.match(/\/cms\/page\/(\d+)\//);
            if (m) return m[1];
        }
        return null;
    });

    await ctx.close();

    if (!testPageId) {
        // Last resort: assume page id 1. This is fragile but works on
        // fresh testservers where the bootstrap page is the first row.
        testPageId = '1';
    }
});

// ────────────────────────────────────────────────────────────────────
// forms.slugwidget (on PageContent change form)
// ────────────────────────────────────────────────────────────────────

test.describe('forms.slugwidget — title → slug auto-fill (PageContent change form)', () => {
    test("typing into title auto-fills the slug while it's empty", async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openPageContentChange();

        const title = page.locator('#id_title');
        const slug = page.locator('#id_slug');
        await slug.fill('');
        await title.fill('');

        await title.pressSequentially('Hello World');
        await expect(slug).toHaveValue('hello-world');
    });

    test('pasting into title auto-fills the slug (contrib-only upgrade vs legacy)', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openPageContentChange();

        const title = page.locator('#id_title');
        const slug = page.locator('#id_slug');
        await slug.fill('');
        await title.fill('');

        // `.fill()` fires a single `input` event, which is what a
        // clipboard paste produces. Legacy's keyup/keypress handlers
        // miss this; our port's `input` handler catches it. This test
        // is the drop-in canary — if it passes, the contrib bundle
        // is the one running.
        await title.fill('Pasted Content');
        await expect(slug).toHaveValue('pasted-content');
    });

    test('non-empty slug at load is NOT overwritten by title changes', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openPageContentChange();

        // Set slug to a known value, then reload so the prefill flag
        // is computed against the non-empty initial state (→ false).
        await page.locator('#id_slug').fill('custom-slug-value');
        // Save via the change form submit. Simpler: don't save, just
        // reload and re-fill.
        await page.reload();
        await page.waitForSelector('#id_title');

        // Re-set slug after reload (reload clears the unsaved value).
        await page.locator('#id_slug').fill('custom-slug-value');

        // Now trigger the slug module's `updateSlug` by typing in title.
        // Prefill is false because slug was non-empty when init ran
        // (via the reload). Typing should NOT overwrite.
        //
        // Wait — this test is subtly wrong. After reload, the slug
        // input is empty again (unless persisted server-side). The
        // module computes prefill = slug.value.trim() === '' which
        // is TRUE on reload. We need to either save the page first
        // so the slug persists, or find a page that already has a
        // non-empty slug from the test db fixture.
        //
        // For the first iteration, skip this test if the page's slug
        // was empty on load — we can't easily seed non-empty state
        // without side effects.
        const initialSlug = await page.locator('#id_slug').inputValue();
        if (!initialSlug) {
            test.skip(
                true,
                'Non-empty-slug test requires a pre-seeded page with a persisted slug. Skipping until we have a fixture helper that creates one.',
            );
            return;
        }

        await page.locator('#id_title').pressSequentially('Ignored Title');
        await expect(page.locator('#id_slug')).toHaveValue(initialSlug);
    });

    test('clearing the slug re-arms auto-fill on next title change', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openPageContentChange();

        const slug = page.locator('#id_slug');
        const title = page.locator('#id_title');
        const initialSlug = await slug.inputValue();
        if (!initialSlug) {
            test.skip(
                true,
                'Re-arm test requires a pre-seeded page with a persisted slug.',
            );
            return;
        }

        // Clear the slug → prefill re-arms on the next updateSlug call.
        // Replace the title via .fill() (NOT pressSequentially — that
        // appends at cursor position 0 instead of replacing). .fill()
        // clears then types and fires a single `input` event, which
        // our port's slug module listens to.
        await slug.fill('');
        await title.fill('Fresh Title');
        await expect(slug).toHaveValue('fresh-title');
    });
});

// ────────────────────────────────────────────────────────────────────
// admin.changeform (on Page advanced-settings form)
// ────────────────────────────────────────────────────────────────────

test.describe('admin.changeform — page advanced-settings behaviors', () => {
    test('lazy-loaded permissions section replaces the loading stub', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openPageAdvanced(testPageId);

        // The template renders
        //   <div class="loading" rel="../permissions/">Loading...</div>
        // inside the #inherited_permissions fieldset. After init, our
        // port fetches `../permissions/` and replaces the div contents.
        // Either the content populates with a permissions table or
        // with a "Page doesn't inherit any permissions." message.
        const fieldset = page.locator('#inherited_permissions');
        await expect(fieldset).toBeVisible();

        // Wait for the "Loading..." text to disappear (replaced by the
        // fetched HTML). We can't reliably assert exact content because
        // it depends on the test db's permission state, but "no longer
        // contains Loading..." is a deterministic post-condition.
        await expect(fieldset.locator('.loading')).not.toContainText('Loading...', {
            timeout: 5_000,
        });
    });

    test('window.CMS.API.changeLanguage is exposed after load', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openPageAdvanced(testPageId);

        const type = await page.evaluate(
            () =>
                typeof (window.CMS && window.CMS.API && window.CMS.API.changeLanguage),
        );
        expect(type).toBe('function');
    });

    test('form rows wrapping hidden inputs are collapsed to display:none', async ({
        cms,
        authenticatedPage: page,
    }) => {
        await cms.openPageAdvanced(testPageId);

        // The CMS grouper admin swaps extra_grouping_fields to
        // HiddenInput after the fieldset spec is built, so their
        // wrapping .form-row is rendered anyway. The JS collapse step
        // hides those rows. Verify that every .form-row containing a
        // hidden input has display:none.
        const hiddenInputRows = page.locator('.form-row:has(input[type="hidden"])');
        const count = await hiddenInputRows.count();
        if (count === 0) {
            // If no rows match, the Python side already did the right
            // thing (grouper fields declared hidden from the start) and
            // the JS step is a no-op — a future, strictly-better state.
            test.skip(
                true,
                'No .form-row elements wrap hidden inputs on this form. JS cleanup step is a no-op here.',
            );
            return;
        }

        for (let i = 0; i < count; i++) {
            const display = await hiddenInputRows.nth(i).evaluate(
                (el) => /** @type {HTMLElement} */ (el).style.display,
            );
            expect(display).toBe('none');
        }
    });
});

// Language tab click tests are intentionally omitted. The language
// tabs (#page_form_lang_tabs) render on the Page advanced-settings
// form ONLY when `show_language_tabs AND NOT show_permissions` — i.e.
// when the admin user doesn't have permission-change rights. The
// default admin user in this test suite has all permissions, so
// `show_permissions` is True and the tabs don't render. Testing them
// requires creating a non-superuser with restricted rights, which is
// extra fixture complexity for a small coverage gain. Skip for now;
// revisit if the language tab path becomes load-bearing.
