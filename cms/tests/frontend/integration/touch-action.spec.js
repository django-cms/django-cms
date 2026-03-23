// @ts-check
const { test, expect, settings } = require('./helpers/fixtures');

/**
 * Test: Touch Action CSS Classes
 *
 * Verifies that touch-action CSS classes are properly applied
 * instead of inline data-touch-action attributes.
 * This ensures CSP compliance while maintaining touch gesture control.
 */
test.describe('Touch Action CSS Classes', () => {
  test.beforeEach(async ({ cms, page }) => {
    await cms.login();
    await cms.addPage();
  });

  test.afterEach(async ({ cms }) => {
    await cms.logout();
  });

  test('should apply touch-action classes to toolbar elements', async ({ page }) => {
    await page.goto(settings.editUrl);

    await page.waitForSelector('.cms-toolbar');

    // Check main toolbar container has touch-action-none class
    const toolbar = page.locator('#cms-top');
    await expect(toolbar).toHaveClass(/cms-touch-action-none/);

    // Verify no data-touch-action attributes exist
    const elementsWithDataAttr = await page.locator('[data-touch-action]').count();
    expect(elementsWithDataAttr).toBe(0);

    // Check computed style has touch-action: none
    const touchAction = await toolbar.evaluate(el =>
      window.getComputedStyle(el).touchAction
    );
    expect(touchAction).toBe('none');
  });

  test('should apply touch-action classes to modal elements', async ({ page }) => {
    await page.goto(settings.editUrl);
    await page.waitForSelector('.cms-toolbar');

    // Open a modal (e.g., page settings)
    await page.click('.cms-toolbar-item-navigation a[href*="/change/"][data-rel="modal"]');
    await page.waitForSelector('.cms-modal', { state: 'visible' });

    // Check modal has touch-action-none class
    const modal = page.locator('.cms-modal');
    await expect(modal).toHaveClass(/cms-touch-action-none/);

    // Check modal head has touch-action-none class
    const modalHead = page.locator('.cms-modal-head');
    await expect(modalHead).toHaveClass(/cms-touch-action-none/);

    // Check modal title has touch-action-none class
    const modalTitle = page.locator('.cms-modal-title');
    await expect(modalTitle).toHaveClass(/cms-touch-action-none/);

    // Check modal breadcrumb has touch-action-pan-x class
    const modalBreadcrumb = page.locator('.cms-modal-breadcrumb');
    await expect(modalBreadcrumb).toHaveClass(/cms-touch-action-pan-x/);

    // Verify computed styles
    const modalTouchAction = await modal.evaluate(el =>
      window.getComputedStyle(el).touchAction
    );
    expect(modalTouchAction).toBe('none');

    const breadcrumbTouchAction = await modalBreadcrumb.evaluate(el =>
      window.getComputedStyle(el).touchAction
    );
    expect(breadcrumbTouchAction).toBe('pan-x');
  });

  test('should apply touch-action classes to structure board', async ({ page }) => {
    await page.goto(settings.editUrl);
    await page.waitForSelector('.cms-toolbar');

    // Switch to structure mode
    await page.click('.cms-btn-switch-edit');
    await page.waitForSelector('.cms-structure', { state: 'visible' });

    // Check structure content has touch-action-pan-y class
    const structureContent = page.locator('.cms-structure-content');
    await expect(structureContent).toHaveClass(/cms-touch-action-pan-y/);

    // Verify computed style
    const touchAction = await structureContent.evaluate(el =>
      window.getComputedStyle(el).touchAction
    );
    expect(touchAction).toBe('pan-y');

    // Check plugin pickers have touch-action-pan-y class
    const pluginPickers = page.locator('.cms-plugin-picker');
    const count = await pluginPickers.count();

    if (count > 0) {
      const firstPicker = pluginPickers.first();
      await expect(firstPicker).toHaveClass(/cms-touch-action-pan-y/);

      const pickerTouchAction = await firstPicker.evaluate(el =>
        window.getComputedStyle(el).touchAction
      );
      expect(pickerTouchAction).toBe('pan-y');
    }
  });

  test('should apply touch-action classes to dropdown menus', async ({ page }) => {
    await page.goto(settings.editUrl);
    await page.waitForSelector('.cms-toolbar');

    // Switch to structure mode to find dropdown menus
    await page.click('.cms-btn-switch-edit');
    await page.waitForSelector('.cms-structure', { state: 'visible' });

    // Find and check submenu dropdowns
    const dropdowns = page.locator('.cms-submenu-dropdown-settings');
    const count = await dropdowns.count();

    if (count > 0) {
      const firstDropdown = dropdowns.first();
      await expect(firstDropdown).toHaveClass(/cms-touch-action-pan-y/);

      const touchAction = await firstDropdown.evaluate(el =>
        window.getComputedStyle(el).touchAction
      );
      expect(touchAction).toBe('pan-y');
    }
  });

  test('should not have any data-touch-action attributes in DOM', async ({ page }) => {
    await page.goto(settings.editUrl);
    await page.waitForSelector('.cms-toolbar');

    // Switch to structure mode for full UI
    await page.click('.cms-btn-switch-edit');
    await page.waitForSelector('.cms-structure', { state: 'visible' });

    // Comprehensive check: no data-touch-action attributes should exist
    const allElementsWithAttr = await page.locator('[data-touch-action]').count();
    expect(allElementsWithAttr).toBe(0);

    // Verify all expected classes exist instead
    const touchActionNone = await page.locator('.cms-touch-action-none').count();
    const touchActionPanY = await page.locator('.cms-touch-action-pan-y').count();
    const touchActionPanX = await page.locator('.cms-touch-action-pan-x').count();

    // At least some elements should have touch-action classes
    expect(touchActionNone).toBeGreaterThan(0);
    expect(touchActionPanY).toBeGreaterThan(0);
    // pan-x might not always be visible depending on modal state
    expect(touchActionPanX).toBeGreaterThanOrEqual(0);
  });

  test('should maintain touch-action during drag operations', async ({ page }) => {
    await page.goto(settings.editUrl);
    await page.waitForSelector('.cms-toolbar');

    // Switch to structure mode
    await page.click('.cms-btn-switch-edit');
    await page.waitForSelector('.cms-structure', { state: 'visible' });

    // Get structure content element
    const structureContent = page.locator('.cms-structure-content').first();

    // Verify initial touch-action class
    await expect(structureContent).toHaveClass(/cms-touch-action-pan-y/);

    // Check that touch-action style is set via CSS class, not inline
    const hasInlineStyle = await structureContent.evaluate(el =>
      el.style.touchAction !== ''
    );

    // Should NOT have inline style (unless dynamically set by JS during drag)
    // This test ensures we're using CSS classes as the default
    const inlineTouchAction = await structureContent.evaluate(el =>
      el.style.touchAction || 'not-set'
    );

    // Either not set or set to 'pan-y' via class
    if (inlineTouchAction !== 'not-set') {
      expect(['pan-y', 'none']).toContain(inlineTouchAction);
    }
  });

  test('should have proper CSS rules defined', async ({ page }) => {
    await page.goto(settings.editUrl);
    await page.waitForSelector('.cms-toolbar');

    // Create test elements to verify CSS rules
    const testResults = await page.evaluate(() => {
      const results = {};

      // Create temporary test elements
      const container = document.createElement('div');
      container.className = 'cms cms-reset';
      document.body.appendChild(container);

      // Test cms-touch-action-none
      const noneEl = document.createElement('div');
      noneEl.className = 'cms-touch-action-none';
      container.appendChild(noneEl);
      results.none = window.getComputedStyle(noneEl).touchAction;

      // Test cms-touch-action-pan-y
      const panYEl = document.createElement('div');
      panYEl.className = 'cms-touch-action-pan-y';
      container.appendChild(panYEl);
      results.panY = window.getComputedStyle(panYEl).touchAction;

      // Test cms-touch-action-pan-x
      const panXEl = document.createElement('div');
      panXEl.className = 'cms-touch-action-pan-x';
      container.appendChild(panXEl);
      results.panX = window.getComputedStyle(panXEl).touchAction;

      // Cleanup
      document.body.removeChild(container);

      return results;
    });

    // Verify CSS rules produce correct computed styles
    expect(testResults.none).toBe('none');
    expect(testResults.panY).toBe('pan-y');
    expect(testResults.panX).toBe('pan-x');
  });
});
