/*
 * Entry point for the admin.pagetree bundle.
 *
 * Drop-in replacement for the legacy bundle.admin.pagetree.min.js.
 * Phase 4a: read-only tree rendering with expand/collapse + keyboard nav.
 *
 * The legacy entry was 3 lines:
 *   import PageTree from './modules/cms.pagetree';
 *   window.CMS.PageTree = PageTree;
 *
 * We match that shape exactly so template-level init code
 * (`CMS.PageTree._init()` in legacy) still works if called externally.
 *
 * The module self-initializes at DOM-ready time via its own listener
 * (see the bottom of pagetree.ts) — there's no separate init call
 * needed from this entry. But we expose the class on `window.CMS` so
 * third-party code that references `CMS.PageTree` still finds it.
 */

import PageTree from '../modules/pagetree';
import { Helpers } from '../modules/cms-base';

window.CMS = window.CMS ?? {};
window.CMS.PageTree = PageTree;

// Init at DOM-ready. Legacy uses jQuery's $(function() { ... }) in
// the module; we use native DOMContentLoaded here instead.
if (document.readyState === 'loading') {
    document.addEventListener(
        'DOMContentLoaded',
        () => {
            // Set up CMS.config for the pagetree context (legacy does
            // this inside the module's jQuery ready handler — we do it
            // here so it runs before PageTree.init reads config).
            const treeEl = document.querySelector<HTMLElement>('.js-cms-pagetree');
            const settingsUrl = treeEl?.dataset.settingsUrl ?? '';
            window.CMS!.config = {
                ...(window.CMS!.config ?? {}),
                isPageTree: true,
                settings: { toolbar: 'expanded', version: __CMS_VERSION__ },
                urls: {
                    ...(window.CMS!.config?.urls ?? {}),
                    settings: settingsUrl,
                },
            };
            window.CMS!.settings = window.CMS!.settings ?? {};
            try {
                window.CMS!.settings = Helpers.getSettings();
            } catch {
                // localStorage might be unavailable
            }
            PageTree.init();
        },
        { once: true },
    );
} else {
    const treeEl = document.querySelector<HTMLElement>('.js-cms-pagetree');
    const settingsUrl = treeEl?.dataset.settingsUrl ?? '';
    window.CMS!.config = {
        ...(window.CMS!.config ?? {}),
        isPageTree: true,
        settings: { toolbar: 'expanded', version: __CMS_VERSION__ },
        urls: {
            ...(window.CMS!.config?.urls ?? {}),
            settings: settingsUrl,
        },
    };
    try {
        window.CMS!.settings = Helpers.getSettings();
    } catch {
        // localStorage might be unavailable
    }
    PageTree.init();
}
