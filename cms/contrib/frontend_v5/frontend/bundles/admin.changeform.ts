/*
 * Entry point for the admin.changeform bundle.
 *
 * Drop-in replacement for the legacy bundle.admin.changeform.min.js.
 * Runs on Django's admin "change page" form. All actual behavior lives
 * in `modules/changeform.ts` — this entry just waits for DOMContentLoaded
 * and calls `initChangeForm()`.
 *
 * Why no explicit `window.CMS = { API: {} }` stub here, unlike the
 * legacy entry? `initChangeForm()` sets `window.CMS` and
 * `window.CMS.API` itself (with `??=` fallbacks, so existing values
 * from admin.base or other bundles are preserved). Consolidating the
 * CMS.API setup inside the module keeps the entry trivial and the
 * module's public-API-attachment code unit-testable without a bundle
 * entry wrapper.
 */

import { initChangeForm } from '../modules/changeform';

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initChangeForm(), { once: true });
} else {
    initChangeForm();
}
