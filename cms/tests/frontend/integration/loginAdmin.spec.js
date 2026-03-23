// @ts-check
const { test, expect, settings } = require('./helpers/fixtures');

/**
 * Test: User Login via Admin Panel
 */
test.describe('User Login (via Admin Panel)', () => {
  test('should fail login with wrong credentials', async ({ page }) => {
    await page.goto(settings.adminUrl);

    // Wait for login form to be ready (this gets CSRF token)
    await page.waitForSelector('input[name="username"]');

    // Verify admin panel is available
    await expect(page).toHaveTitle(new RegExp(settings.adminTitle));
    await expect(page.locator('#login-form')).toBeVisible();

    // Try login with wrong credentials
    await page.fill('input[name="username"]', 'fake');
    await page.fill('input[name="password"]', 'credentials');
    await page.click('input[type="submit"]');

    // Verify error message
    await expect(page.locator('.errornote')).toBeVisible();
  });

  test('should successfully login with correct credentials', async ({ page }) => {
    await page.goto(settings.adminUrl);

    // Wait for login form to be ready
    await page.waitForSelector('input[name="username"]');

    // Login with correct credentials
    await page.fill('input[name="username"]', settings.credentials.username);
    await page.fill('input[name="password"]', settings.credentials.password);
    await page.click('input[type="submit"]');

    // Wait for redirect to admin dashboard
    await page.waitForURL(/\/admin\//, { timeout: 10000 });

    // Verify we're logged in - check for Django admin content
    await expect(page.locator('#content-main')).toBeVisible();
    await expect(page.locator('text=Site administration')).toBeVisible();
  });
});
