/*
 * Entry point for the admin.base bundle.
 *
 * Drop-in replacement for the legacy `bundle.admin.base.min.js`. The
 * bundle's job is to set up the `window.CMS` public API surface that
 * every other admin bundle depends on:
 *
 *   - `window.CMS.$` — jQuery (internal TS code MUST NOT import
 *     jquery directly; this file is the only permitted import site
 *     per CLAUDE.md decision 7).
 *   - `window.CMS.API.Helpers` — the grab-bag of cross-feature
 *     helpers ported in `modules/cms-base.ts`.
 *   - `window.CMS.KEYS` — legacy key-code lookup.
 *
 * Merges into an existing `window.CMS` without clobbering — if
 * another bundle (e.g. admin.changeform) has already set
 * `window.CMS.API.changeLanguage`, it survives the merge.
 *
 * Also aliases `window.$` / `window.jQuery` if no other jQuery is
 * loaded on the page, so third-party code that expects `$` as a
 * page-level global finds it. This is load-bearing for legacy CMS
 * plugins and some admin templates.
 */

import $ from 'jquery';

import { Helpers, KEYS } from '../modules/cms-base';

const CMS = {
    $,
    API: { Helpers },
    KEYS,
};

// Merge into an existing window.CMS (created by an earlier-loaded
// bundle, e.g. admin.changeform's pre-init stub) without clobbering.
// Legacy uses `CMS.$.extend(window.CMS || {}, CMS)` for the same
// semantics — deep-merge-into-existing-or-create. $.extend is the
// right tool because it preserves references inside window.CMS.API
// (like CMS.API.changeLanguage).
if (typeof window !== 'undefined') {
    window.CMS = $.extend(window.CMS ?? {}, CMS) as CmsGlobal;
}

// Make sure jQuery is available on the page as `$` and `jQuery` IF
// nothing else has claimed those names. Django admin's own
// `jquery.init.js` releases them via `$.noConflict(true)` to a
// namespaced `django.jQuery`, so after that script runs, bare `$` /
// `jQuery` are free. Our assignment fills the gap, which is what
// legacy plugins assume is available.
if (typeof window !== 'undefined' && !window.jQuery) {
    window.$ = $;
    window.jQuery = $;
}

export default CMS;
