/*
 * elementData — WeakMap-backed replacement for jQuery `.data()`.
 *
 * Why this exists
 * ───────────────
 * Legacy `cms.plugins.js` and `cms.structureboard.js` attach plugin and
 * placeholder descriptors to DOM nodes via `$(el).data('cms', ...)` —
 * 26 read/write sites between the two. jQuery's `.data()` keeps an
 * internal cache keyed by an expando id stamped on the element; values
 * are arbitrary JS objects, never round-tripped through `data-*` attrs.
 *
 * Native `dataset` won't work as a replacement — it only handles
 * strings, and the legacy code stores arrays of objects under a single
 * key. So we mirror jQuery's API with a `WeakMap<Element, Map<string,
 * unknown>>`. Values are tied to the element by reference and garbage-
 * collect when the node is removed.
 *
 * Strangler bridge
 * ────────────────
 * During the migration, legacy bundles (cms.clipboard, un-ported
 * cms.toolbar code paths) still call `$(el).data('cms')`. Whenever a TS
 * caller writes through `setElementData()`, we mirror to jQuery's data
 * cache when jQuery is present, so the legacy reader keeps seeing a
 * consistent value. The mirror is a one-way write — we don't read back
 * from jQuery, because TS callers should commit through this module.
 *
 * The mirror disappears in Phase 7 of the migration plan, once every
 * `data('cms')` consumer is on TS.
 *
 * Shape contract reminder (CLAUDE.md decision 7)
 * ──────────────────────────────────────────────
 * Placeholders store a single descriptor object under `'cms'`; plugins
 * and generics store an *array* of descriptors. This module does not
 * enforce that — callers do — but the array-vs-object footgun is the
 * reason a typed wrapper for the `'cms'` key may be added later.
 */

const STORE = new WeakMap<Element, Map<string, unknown>>();

/**
 * Read a value previously written by `setElementData`. Returns
 * `undefined` if no value is stored under `key` for `el`.
 *
 * Type parameter `T` is unchecked at runtime — the caller is asserting
 * the shape they previously wrote.
 */
export function getElementData<T = unknown>(el: Element, key: string): T | undefined {
    return STORE.get(el)?.get(key) as T | undefined;
}

/**
 * Write a value for `el` under `key`. Mirrors to jQuery's `.data()`
 * cache when jQuery is present, so legacy bundles reading
 * `$(el).data(key)` see the update.
 */
export function setElementData<T>(el: Element, key: string, value: T): void {
    let bag = STORE.get(el);
    if (!bag) {
        bag = new Map();
        STORE.set(el, bag);
    }
    bag.set(key, value);
    mirrorToJquery(el, key, value);
}

/**
 * Delete a value for `el` under `key`. Returns true if a value was
 * removed, false if there was nothing to remove. Mirrors the deletion
 * to jQuery's `.data()` cache when jQuery is present.
 */
export function deleteElementData(el: Element, key: string): boolean {
    const bag = STORE.get(el);
    if (!bag) return false;
    const had = bag.delete(key);
    if (had) mirrorRemoveFromJquery(el, key);
    return had;
}

/**
 * Drop all stored data for `el`. Used when an element is being recycled
 * but kept in the DOM (rare; normal removal lets the WeakMap collect
 * naturally).
 */
export function clearElementData(el: Element): void {
    const bag = STORE.get(el);
    if (!bag) return;
    const keys = Array.from(bag.keys());
    bag.clear();
    for (const key of keys) mirrorRemoveFromJquery(el, key);
}

/**
 * Internal jQuery-mirror writer. Best-effort: any failure is swallowed
 * so a broken jQuery cache cannot break the native store.
 *
 * Exported under a deliberately ugly name for the test suite. Not part
 * of the public API.
 */
export function _mirrorToJqueryForTest(el: Element, key: string, value: unknown): void {
    mirrorToJquery(el, key, value);
}

function mirrorToJquery(el: Element, key: string, value: unknown): void {
    const $ = window.jQuery;
    if (!$) return;
    try {
        // jQuery's `.data()` accepts arbitrary values at runtime; the
        // @types/jquery signature narrows the parameter to a finite
        // union. Cast through the unconstrained signature to keep the
        // strangler contract intact.
        ($(el) as unknown as { data: (k: string, v: unknown) => void }).data(key, value);
    } catch {
        /* best-effort mirror */
    }
}

function mirrorRemoveFromJquery(el: Element, key: string): void {
    const $ = window.jQuery;
    if (!$) return;
    try {
        $(el).removeData(key);
    } catch {
        /* best-effort mirror */
    }
}
