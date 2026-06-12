/*
 * Plugin descriptor storage on DOM elements — wraps `core/element-data`
 * with the placeholder=object / plugin=array shape contract.
 *
 * Why this file exists
 * ────────────────────
 * Legacy `cms.plugins.js` stores plugin descriptors via jQuery's
 * `.data('cms', ...)`. Two different shapes share the same key:
 *
 *   - Placeholder elements: `data('cms')` → a single descriptor object
 *     (set with `.data('cms', options)`).
 *   - Plugin / generic elements: `data('cms')` → an ARRAY of
 *     descriptor objects (set initially to `[]`, then `.push(opts)`).
 *     One DOM node can carry several descriptors when content is
 *     reused across multiple render targets — each push adds one.
 *
 * That bifurcation is a real footgun: every reader has to know which
 * shape to expect, and forgetting the `[0]` for the array case
 * silently breaks. This module encodes the contract once so call
 * sites stop reasoning about it.
 *
 * The underlying store (`core/element-data`) handles WeakMap
 * persistence + jQuery `.data()` mirror for legacy bundles still
 * reading via `$(el).data('cms')`. We just sit on top with the right
 * shape semantics per consumer.
 */

import {
    deleteElementData,
    getElementData,
    setElementData,
} from '../core/element-data';
import type { PluginOptions } from './types';

const KEY = 'cms';

/**
 * Read the descriptor for a placeholder element. Returns the stored
 * single object, or undefined if nothing is stored.
 *
 * Consumers expecting placeholder semantics can call this directly;
 * if the element happens to carry the array shape (a misconfigured
 * page / data race), the first array entry is returned to match
 * legacy `data('cms').name` access patterns.
 */
export function getPlaceholderData(el: Element): PluginOptions | undefined {
    const value = getElementData<PluginOptions | PluginOptions[]>(el, KEY);
    if (value === undefined) return undefined;
    if (Array.isArray(value)) return value[0];
    return value;
}

/**
 * Write the descriptor for a placeholder element (single object form).
 * Overwrites any prior value, including an existing array.
 */
export function setPlaceholderData(el: Element, value: PluginOptions): void {
    setElementData(el, KEY, value);
}

/**
 * Read the descriptor array for a plugin/generic element. Returns the
 * live array reference (mutations are visible to subsequent readers,
 * matching the legacy `data('cms').push(...)` pattern). Returns
 * `undefined` if nothing is stored — different from an empty array.
 */
export function getPluginData(el: Element): PluginOptions[] | undefined {
    const value = getElementData<PluginOptions | PluginOptions[]>(el, KEY);
    if (value === undefined) return undefined;
    if (Array.isArray(value)) return value;
    // Legacy resilience: if the element somehow carries the placeholder
    // shape, return it as a single-entry array so plugin readers don't
    // crash on `.push`.
    return [value];
}

/**
 * Initialize the descriptor array for a plugin/generic element if it
 * doesn't already exist, and return the live array. Equivalent to the
 * legacy `_ensureData` step:
 *
 *   if (!container.data('cms')) container.data('cms', []);
 *   return container.data('cms');
 *
 * Subsequent `push` calls mutate the returned array in place.
 */
export function ensurePluginDataArray(el: Element): PluginOptions[] {
    let arr = getPluginData(el);
    if (!arr) {
        arr = [];
        setElementData(el, KEY, arr);
    }
    return arr;
}

/**
 * Append a descriptor to the plugin/generic array for `el`. Initializes
 * the array if it doesn't exist. Returns the live array.
 */
export function pushPluginData(
    el: Element,
    options: PluginOptions,
): PluginOptions[] {
    const arr = ensurePluginDataArray(el);
    arr.push(options);
    // The WeakMap and jQuery mirror already hold the array reference,
    // so the in-place push is visible to every reader. No re-set
    // needed — matches legacy behaviour exactly.
    return arr;
}

/**
 * Replace a descriptor at the given index in the plugin/generic array.
 * Used by the legacy `_setSettings` flow when an instance's options
 * are updated post-edit. No-op if the array doesn't exist or the
 * index is out of range.
 */
export function setPluginDataAt(
    el: Element,
    index: number,
    options: PluginOptions,
): void {
    const arr = getPluginData(el);
    if (!arr || index < 0 || index >= arr.length) return;
    arr[index] = options;
}

/**
 * Remove all stored descriptor data from `el`. Used on plugin destroy
 * / placeholder cleanup paths.
 */
export function clearCmsData(el: Element): void {
    deleteElementData(el, KEY);
}
