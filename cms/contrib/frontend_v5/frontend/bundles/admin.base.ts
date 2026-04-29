/*
 * Entry point for the admin.base bundle.
 *
 * Drop-in replacement for the legacy `bundle.admin.base.min.js`. The
 * bundle's job is to set up the `window.CMS` public API surface that
 * every other admin bundle depends on:
 *
 *   - `window.CMS.$` — jQuery, lazy-loaded on first access. The
 *     property starts as a getter that returns `Promise<JQueryStatic>`
 *     from `loadCmsJquery()`; once the promise resolves the property
 *     replaces itself with the resolved instance, so subsequent
 *     accesses are synchronous (`CMS.$('selector')` works).
 *
 *     Strategy: jQuery is OPTIONAL. If nothing on the page reads
 *     `CMS.$`, jQuery never loads. This bundle does NOT import
 *     jquery directly — webpack code-splits the lazy `import('jquery')`
 *     in `core/cms-jquery.ts` into `bundle.cms.jquery.min.js`.
 *
 *   - `window.CMS.API.Helpers` — the grab-bag of cross-feature
 *     helpers ported in `modules/cms-base.ts`. None of those helpers
 *     touch jQuery at module-load time; the only jQuery user
 *     (`Helpers.csrf`) is async and lazy-loads jQuery itself.
 *
 *   - `window.CMS.KEYS` — legacy key-code lookup.
 *
 * Merges into an existing `window.CMS` without clobbering — if
 * another bundle (e.g. admin.changeform) has already set
 * `window.CMS.API.changeLanguage`, it survives the merge.
 *
 * `window.$` / `window.jQuery` are NEVER assigned by this bundle.
 * Third-party code that depends on those globals must bring its own
 * jQuery (Django admin's `django.jQuery` is the canonical source).
 *
 * Webpack contract
 * ────────────────
 * `webpack.config.js` declares `library: { name: 'CMS', type: 'window',
 * export: 'default' }` for this entry, so the default export below is
 * what webpack assigns to `window.CMS` at the end of bundle execution.
 * We also assign manually inside the if-block so the merge with any
 * pre-existing `window.CMS` happens BEFORE the library mechanism runs;
 * because the default export is the same object reference, webpack's
 * assignment afterwards is idempotent.
 */

import { Helpers, KEYS } from '../modules/cms-base';
import { loadCmsJquery } from '../modules/core/cms-jquery';

// Reuse an existing `window.CMS` (created by an earlier-loaded bundle)
// so we don't clobber API attachments like `CMS.API.changeLanguage`.
const CMS: CmsGlobal = ((typeof window !== 'undefined' ? window.CMS : undefined) ?? {}) as CmsGlobal;

CMS.API = { ...(CMS.API ?? {}), Helpers };
(CMS as { KEYS?: typeof KEYS }).KEYS = KEYS;

// Lazy `CMS.$` — only triggers a jQuery load if something reads it.
// The first read returns the loadCmsJquery() promise; once it resolves,
// the property replaces itself with the jQuery instance so later reads
// are synchronous.
Object.defineProperty(CMS, '$', {
    configurable: true,
    enumerable: true,
    get() {
        return loadCmsJquery().then((jq) => {
            Object.defineProperty(CMS, '$', {
                value: jq,
                writable: true,
                configurable: true,
                enumerable: true,
            });
            return jq;
        });
    },
});

if (typeof window !== 'undefined') {
    window.CMS = CMS;
}

export default CMS;
