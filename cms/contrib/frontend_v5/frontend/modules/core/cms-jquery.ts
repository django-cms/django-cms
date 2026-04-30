/*
 * cms-jquery — single accessor for jQuery during the strangler
 * migration.
 *
 * Why this exists
 * ───────────────
 * Decision (Migration Strategy → jQuery Strategy): jQuery is optional
 * and accessed only via this resolver. New TS code calls
 * `getCmsJquery()` / `await loadCmsJquery()` instead of touching
 * `window.$` / `window.jQuery` directly. That gives us:
 *   1. A single search-replaceable boundary when we drop jQuery for
 *      good (Phase 7 of the migration plan).
 *   2. A diagnostic seam where every internal use can be logged or
 *      forbidden behind a flag.
 *   3. Resolution priority: prefer Django admin's bundled jQuery
 *      (`django.jQuery`) over a lazily-loaded chunk, so we share
 *      Django's instance and don't double-load.
 *
 * Resolution order
 * ────────────────
 *   1. `django.jQuery` (always present on Django admin pages)
 *   2. A lazy-loaded webpack chunk (`bundle.cms.jquery.min.js`)
 *      fetched on demand. Use `loadCmsJquery()` to trigger the load.
 *      The chunk is emitted by webpack from the dynamic `import()`
 *      below — no separate entry needed.
 *
 * `window.jQuery` is NOT read or written by this module
 * ─────────────────────────────────────────────────────
 * Reading `window.jQuery` would couple us to whatever third-party
 * code happens to have shimmed it. Writing it would shadow that same
 * third-party code. Both are forbidden by the migration strategy.
 *
 * Sync/async API
 * ──────────────
 * The lazy-load path can't be made synchronous in modern browsers (no
 * sync XHR for scripts), so the API splits in two:
 *
 *   - `getCmsJquery()` — synchronous. Returns the already-resolved
 *     instance (`django.jQuery` or whatever `loadCmsJquery()` cached
 *     earlier). Returns `undefined` when nothing has been resolved yet.
 *
 *   - `loadCmsJquery()` — asynchronous. Resolves `django.jQuery` if
 *     present, otherwise dynamic-imports jQuery (webpack splits the
 *     module into `bundle.cms.jquery.min.js`). Idempotent: a single
 *     in-flight load is shared across concurrent callers.
 *
 * Typical usage from a bundle entry:
 *   await loadCmsJquery();           // once at startup
 *   const $ = getCmsJquery()!;        // sync everywhere afterwards
 */

interface DjangoGlobal {
    jQuery?: JQueryStatic;
}

declare global {
    interface Window {
        django?: DjangoGlobal;
    }
}

let cached: JQueryStatic | undefined;
let loadPromise: Promise<JQueryStatic> | undefined;

/**
 * Returns the jQuery instance resolved earlier, or `undefined` if no
 * resolution has happened yet. Falls back to `django.jQuery` if it's
 * present on the window — that's the fast path on every Django admin
 * page and doesn't require an `await`.
 */
export function getCmsJquery(): JQueryStatic | undefined {
    if (cached) return cached;
    const fromDjango = window.django?.jQuery;
    if (fromDjango) {
        cached = fromDjango;
        return cached;
    }
    return undefined;
}

/**
 * Resolve jQuery — synchronously from `django.jQuery` when present,
 * otherwise dynamically import the bundled jQuery chunk. Idempotent:
 * concurrent calls share a single load promise; subsequent calls
 * return the cached instance.
 *
 * After the dynamic import resolves, `noConflict(true)` is called on
 * the loaded jQuery so it doesn't claim `window.$` / `window.jQuery`.
 * The cached reference returned from this function is the only
 * supported way to reach it.
 */
export function loadCmsJquery(): Promise<JQueryStatic> {
    if (cached) return Promise.resolve(cached);
    const fromDjango = window.django?.jQuery;
    if (fromDjango) {
        cached = fromDjango;
        return Promise.resolve(cached);
    }
    if (!loadPromise) {
        loadPromise = import(/* webpackChunkName: "cms.jquery" */ 'jquery').then(
            (mod) => {
                // Diagnostic: every time the lazy chunk has to load,
                // some caller is still depending on jQuery. Surface it
                // so the migration progress is visible.
                console.warn(
                    '[cms-jquery] jQuery was lazy-loaded from ' +
                        'bundle.cms.jquery.min.js — some code on this page ' +
                        'still depends on jQuery. Migrate the caller to ' +
                        'native DOM/fetch to drop the chunk entirely.',
                );
                // Webpack ESM-interop: jQuery's UMD entry comes through
                // as `mod.default` under TS's esModuleInterop, but some
                // bundlers expose the namespace itself. Accept either.
                const jq = ((mod as { default?: JQueryStatic }).default ??
                    (mod as unknown as JQueryStatic));
                // Release the `window.$` / `window.jQuery` globals that
                // jQuery's UMD entry assigned as a side-effect. We only
                // hand back the local reference; window stays clean.
                if (typeof jq.noConflict === 'function') {
                    jq.noConflict(true);
                }
                cached = jq;
                return jq;
            },
        );
    }
    return loadPromise;
}

/**
 * Test/migration hook: drop the cached resolution and any in-flight
 * load promise so the next call re-resolves from scratch.
 */
export function _resetCmsJqueryCache(): void {
    cached = undefined;
    loadPromise = undefined;
}
