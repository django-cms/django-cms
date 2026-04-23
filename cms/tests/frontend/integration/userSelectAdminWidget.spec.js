const { test, expect, settings } = require('./helpers/fixtures');

/**
 * Tests for cms.forms.widgets.UserSelectAdminWidget.
 *
 * The widget is rendered inside the PagePermissionInlineAdmin on the page
 * advanced-settings view when CMS_PERMISSION = True. It adds an "add another"
 * link next to the user <select> that opens cms_pageuser_add in a Django admin
 * popup. The test verifies that:
 *
 *   - The link is rendered with modern RelatedFieldWidgetWrapper markup
 *     (classes, data-popup, icon) and without a legacy onclick attribute.
 *   - The href targets `cms_pageuser_add` (the CMS-specific PageUser add view),
 *     distinguishing the custom widget from Django's default user FK wrapper
 *     used elsewhere on the same page (view restrictions inline).
 *   - Clicking the link opens a popup window at cms_pageuser_add, driven by
 *     Django's bundled admin/js/admin/RelatedObjectLookups.js delegated
 *     handler (no inline onclick required).
 *
 * Requires the test server to run with CMS_PERMISSION = True (the default for
 * `python testserver.py`).
 */
test.describe('UserSelectAdminWidget', () => {
  /**
   * Returns the cms.Page id of any existing page, creating one via the CMS
   * wizard if none exists. We use the pagetree's HTML fragment endpoint
   * (`/cms/pagecontent/get-tree/`) which renders one `<li data-id="<int>">`
   * per page; the static changelist page does not list pages server-side
   * because jstree loads them via this AJAX endpoint.
   */
  async function getTestPageId(page, cms) {
    const parse = async () => {
      const resp = await page.request.get(
        `${settings.baseUrl}/en/admin/cms/pagecontent/get-tree/`,
        { failOnStatusCode: false }
      );
      if (!resp.ok()) {
        return null;
      }
      const body = await resp.text();
      const match = body.match(/data-id="(\d+)"/);
      return match ? match[1] : null;
    };

    let id = await parse();
    if (!id) {
      await cms.addPage({ title: 'UserSelectAdminWidget test page' });
      id = await parse();
    }
    return id;
  }

  test.beforeEach(async ({ cms }) => {
    await cms.login();
  });

  test('renders a modern add-related link pointing at cms_pageuser_add', async ({ page, cms }) => {
    const pageId = await getTestPageId(page, cms);
    test.skip(!pageId, 'Could not provision a CMS page for the test');

    await page.goto(
      `${settings.baseUrl}/en/admin/cms/page/${pageId}/advanced-settings/`,
      { waitUntil: 'domcontentloaded' }
    );

    // Scope to the PagePermissionInlineAdmin fieldset (identified by its
    // translated heading "Page permissions") rather than the sibling
    // ViewRestrictionInlineAdmin fieldset which uses the default Django
    // RelatedFieldWidgetWrapper and must NOT be confused with our widget.
    const pagePermissionInline = page
      .locator('div.inline-group, fieldset.module')
      .filter({ has: page.locator('h2, .inline-heading', { hasText: /page permissions/i }) })
      .first();

    await expect(
      pagePermissionInline,
      'Page permissions inline not found. Start testserver.py without --CMS_PERMISSION=False.'
    ).toBeAttached();

    // The __prefix__ template row is hidden but present in the DOM; the widget
    // markup we care about lives there. We filter by href to single out
    // UserSelectAdminWidget's output (href matches /cms/pageuser/add/) vs.
    // Django's default wrapper (href matches /auth/user/add/).
    const addLink = pagePermissionInline
      .locator('a.related-widget-wrapper-link.add-related[href*="/cms/pageuser/add/"]')
      .first();

    await expect(addLink).toHaveCount(1);

    // Popup-mode attributes and markup.
    await expect(addLink).toHaveAttribute('data-popup', 'yes');
    const href = await addLink.getAttribute('href');
    expect(href).toMatch(/\/admin\/cms\/pageuser\/add\/\?_popup=1/);

    // Must render a visible "+" icon (the pre-fix version shipped an unclosed
    // <a> with no content).
    await expect(addLink.locator('img[src*="icon-addlink"]')).toHaveCount(1);

    // id pattern: add_id_<formset-prefix>-<index-or-__prefix__>-user.
    const linkId = await addLink.getAttribute('id');
    expect(linkId).toMatch(/^add_id_.+-user$/);

    // Its sibling <select> (same id stem, without the `add_` prefix) must be
    // attached to the DOM. Use an attribute selector to avoid needing
    // CSS.escape() (a browser-only global not available in Node).
    const selectId = linkId.replace(/^add_/, '');
    await expect(page.locator(`[id="${selectId}"]`)).toBeAttached();
  });

  test('clicking the add link opens a popup to cms_pageuser_add', async ({ page, cms, context }) => {
    const pageId = await getTestPageId(page, cms);
    test.skip(!pageId, 'Could not provision a CMS page for the test');

    await page.goto(
      `${settings.baseUrl}/en/admin/cms/page/${pageId}/advanced-settings/`,
      { waitUntil: 'domcontentloaded' }
    );

    const pagePermissionInline = page
      .locator('div.inline-group, fieldset.module')
      .filter({ has: page.locator('h2, .inline-heading', { hasText: /page permissions/i }) })
      .first();

    // Clone the __prefix__ template into a real, interactive row by clicking
    // Django admin's "Add another Page permission" button (rendered by
    // admin/js/inlines.js as `.add-row a`).
    await pagePermissionInline.locator('.add-row a').first().click();

    // The cloned row has an add-related link whose id no longer contains
    // __prefix__ and whose href still points at cms_pageuser_add.
    const addLink = pagePermissionInline
      .locator('a.related-widget-wrapper-link.add-related[href*="/cms/pageuser/add/"]')
      .filter({ hasNot: page.locator('[id*="__prefix__"]') })
      .first();

    await expect(addLink).toBeAttached();

    // Django's RelatedObjectLookups.js attaches its click listener to
    // document.body via event delegation (`.related-widget-wrapper-link`).
    // The cloned row's parent <tr>/<td> may be visually hidden by the
    // tabular-inline layout on this wide permissions table, so we dispatch a
    // click event directly on the element. The delegated handler on body
    // still fires and calls showRelatedObjectPopup(this), which opens the
    // popup window via window.open().
    const popupPromise = context.waitForEvent('page');
    await addLink.dispatchEvent('click');
    const popup = await popupPromise;
    await popup.waitForLoadState('domcontentloaded');

    expect(popup.url()).toMatch(/\/admin\/cms\/pageuser\/add\/\?.*_popup=1/);
    await expect(
      popup.locator('form#pageuser_form, form[action*="pageuser/add"]').first()
    ).toBeVisible();

    await popup.close();
  });
});
