/*
 * DOM resolution for plugin/placeholder/generic wrappers.
 *
 * Replaces the legacy `_setupUI` / `_extractContentWrappers` /
 * `_processTemplateGroup` triplet from `cms.plugins.js`. Native DOM
 * throughout — no jQuery — but preserves the load-bearing template-
 * bracket extraction behaviour:
 *
 *   <template class="cms-plugin cms-plugin-4711 cms-plugin-start"></template>
 *   <p>Some text</p>
 *   <template class="cms-plugin cms-plugin-4711 cms-plugin-end"></template>
 *
 * For multi-render plugins (e.g. `{% page_url %}` rendered both in
 * the header and the footer), the server emits multiple wrappers
 * sharing the same class. Some content may live between two
 * `<template>` tags (start/end markers); we splice that into a real
 * `<cms-plugin>` wrapper so the rest of the code can treat each
 * occurrence as a single element.
 *
 * Why this is its own module
 * ──────────────────────────
 * Pure DOM in/out — no events, no state. Vitest can run it against
 * jsdom fixtures without setting up `window.CMS`. Phase 2c's Plugin
 * class consumes `setupContainer(container)` and stops there; if the
 * extraction behaviour needs to evolve (e.g. when the server moves to
 * Web Components markers), only this file changes.
 */

import nextUntil from '../../nextuntil';
import { getPluginData } from '../cms-data';

/**
 * Resolve all DOM elements that participate in the wrapper for
 * `containerClass` (e.g. `'cms-plugin-4711'` or
 * `'cms-placeholder-99'`). Mirrors legacy `_setupUI`.
 *
 * Behaviour matrix:
 *   - Single match → return that single element.
 *   - Multiple matches AND `cms-plugin-*` class AND wrappers are
 *     `<template>` start/end markers → splice the bracketed content
 *     into real `<cms-plugin>` elements and return them all.
 *   - Multiple matches without template markers → return them all
 *     (legacy fallback for static placeholders rendered twice).
 *   - No matches → return a single fresh `<div>` so callers can still
 *     attach `data` and event listeners (matches the legacy
 *     `$('<div></div>')` default for clipboard-only plugins).
 */
export function setupContainer(containerClass: string): Element[] {
    const wrapper = Array.from(
        document.getElementsByClassName(containerClass),
    );

    if (wrapper.length > 1 && /cms-plugin/.test(containerClass)) {
        const groups = extractContentWrappers(wrapper);
        const firstGroup = groups[0];
        const firstElement = firstGroup?.[0];
        if (firstElement && firstElement.tagName === 'TEMPLATE') {
            const expanded = groups
                .map((items) => processTemplateGroup(items, containerClass))
                .filter((nodes) => nodes.length > 0);

            // Remove the now-replaced <template> tags.
            for (const el of wrapper) {
                if (el.tagName === 'TEMPLATE') el.remove();
            }
            const flattened = expanded.flat();
            if (flattened.length > 0) return flattened;
        } else {
            return wrapper;
        }
    } else if (wrapper.length > 0) {
        return wrapper;
    }

    return [document.createElement('div')];
}

/**
 * Group a flat list of wrapper elements into start/end clusters,
 * keyed off the `cms-plugin-start` class. Mirrors legacy
 * `_extractContentWrappers`.
 *
 * Result shape: `[[startEl, ...members], [startEl, ...members], ...]`
 * Each subarray is one render of the plugin.
 */
export function extractContentWrappers(wrapper: Element[]): Element[][] {
    const groups: Element[][] = [];
    for (const el of wrapper) {
        if (el.classList.contains('cms-plugin-start') || groups.length === 0) {
            groups.push([el]);
        } else {
            groups[groups.length - 1]!.push(el);
        }
    }
    return groups;
}

/**
 * Expand a single template-bracketed group into real
 * `<cms-plugin>`-class-bearing elements. Mirrors legacy
 * `_processTemplateGroup`.
 *
 * Steps:
 *   1. Walk siblings of the start `<template>` until the matching
 *      `<template class="cms-plugin-end">` (or a different
 *      container class).
 *   2. Wrap any non-empty text nodes in a `<cms-plugin
 *      class="cms-plugin-text-node">`.
 *   3. Drop pure whitespace text nodes and comments.
 *   4. Tag every survivor with the shared plugin class. Mark the
 *      first as `cms-plugin-start`, the last as `cms-plugin-end`.
 */
export function processTemplateGroup(
    items: Element[],
    containerClass: string,
): Element[] {
    const start = items[0];
    if (!start || start.tagName !== 'TEMPLATE') return [];

    const startClassAttr = start.getAttribute('class') ?? '';
    const sharedClass = startClassAttr.replace('cms-plugin-start', '').trim();

    // Walk until we hit another element with the same container class.
    // `nextUntil` returns Node[] (including text/comment nodes).
    const between = nextUntil(start, `.${containerClass}`);
    const expanded: Element[] = [];

    for (const node of between) {
        if (node.nodeType === Node.TEXT_NODE) {
            const text = node.textContent ?? '';
            if (/^\s*$/.test(text)) continue; // skip whitespace
            // Wrap the text node in a <cms-plugin> element so it has
            // a real DOM target for class / data / event hooks.
            const wrap = document.createElement('cms-plugin');
            wrap.classList.add('cms-plugin-text-node');
            const parent = node.parentNode;
            if (!parent) continue;
            parent.insertBefore(wrap, node);
            wrap.appendChild(node);
            expanded.push(wrap);
            continue;
        }
        if (node.nodeType === Node.COMMENT_NODE) continue;
        if (node.nodeType !== Node.ELEMENT_NODE) continue;
        expanded.push(node as Element);
    }

    // Tag every survivor with the shared plugin class. Skip empty
    // tokens so we don't double-add (split('') leaves '' on edges).
    const sharedTokens = sharedClass.split(/\s+/).filter(Boolean);
    for (const el of expanded) {
        for (const token of sharedTokens) el.classList.add(token);
    }
    if (expanded.length > 0) {
        expanded[0]!.classList.add('cms-plugin-start');
        expanded[expanded.length - 1]!.classList.add('cms-plugin-end');
    }
    return expanded;
}

/**
 * True when `el` carries multiple `data('cms')` descriptor objects.
 * Mirrors legacy `Plugin._isContainingMultiplePlugins`. Used by content
 * events to decide whether to bind dblclick-to-edit — we don't bind
 * when the same DOM node represents several plugins (ambiguous: which
 * one does a dblclick edit?).
 */
export function isMultiPlugin(el: Element): boolean {
    const data = getPluginData(el);
    return Boolean(data && data.length > 1);
}

// Test/migration hook — surface the internals so tests can drive
// each step in isolation without rebuilding the wrapper triplet.
export const _internals = { extractContentWrappers, processTemplateGroup };
