// @ts-check
const { test, expect } = require('./helpers/fixtures');

// Regression coverage for #8977: admin popup responses run inside a CMS
// iframe, where window.opener is null.
for (const extension of [
  { label: 'Page Extension', model: 'mypageextension', field: 'extra' },
  { label: 'Title Extension', model: 'mypagecontentextension', field: 'extra_title' }
]) {
  test(`${extension.label} closes after adding and changing`, async ({ cms, page }) => {
    await cms.login();
    await cms.addPage({ title: `Extension ${extension.model} ${Date.now()}` });
    await cms.enterEditMode();
    const editUrl = page.url();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));

    const openExtension = async () => {
      await cms.openMenu('Page');
      await page.locator('.cms-toolbar-item-navigation a[data-rel="modal"]')
        .filter({ hasText: extension.label }).click();
      await expect(page.locator('.cms-modal')).toBeVisible();
      return page.frameLocator('.cms-modal iframe');
    };

    for (const action of ['add', 'change']) {
      await test.step(`${action} and save`, async () => {
        const frame = await openExtension();
        const value = `${extension.label} ${action}`;
        await frame.locator(`#id_${extension.field}`).fill(value);
        const saved = page.waitForResponse(response =>
          response.request().method() === 'POST' &&
          response.url().includes(`/extensionapp/${extension.model}/`) &&
          response.url().includes(`/${action}/`)
        );
        await page.locator('.cms-modal-foot a.cms-btn-action.default').click();
        expect((await saved).status()).toBe(200);
        await expect(page.locator('.cms-modal')).toBeHidden();

        // Reopen from a fresh toolbar to verify persistence and the change URL.
        await page.goto(editUrl);
        await page.waitForLoadState('networkidle');
        const reopened = await openExtension();
        await expect(reopened.locator(`#id_${extension.field}`)).toHaveValue(value);
        await page.goto(editUrl);
        await page.waitForLoadState('networkidle');
      });
    }
    expect(errors).toEqual([]);
  });
}
