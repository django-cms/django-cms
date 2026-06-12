/*
 * Parser half of `_updateSekizai`.
 *
 * Sekizai blocks are server-rendered chunks of `<link>` / `<style>` /
 * `<meta>` (CSS) or `<script>` (JS) tags returned in mutation
 * responses. We need to merge them into the live page without
 * re-running already-loaded scripts.
 *
 * This module handles the parse + classify step:
 *   - Parse the raw HTML chunk into an inert template (no script
 *     execution).
 *   - For each new element, decide: already present? new? skip
 *     (drop because identical exists)?
 *
 * The mutation half (insert / re-create scripts to trigger execution)
 * lives in `dom/content-update.ts`. Splitting them keeps this file
 * pure and testable without jsdom.
 */

import { elementPresent } from './markup';

export type SekizaiBlock = 'css' | 'js';

export interface SekizaiPlan {
    /** Elements that should be inserted into the live DOM. */
    toInsert: Element[];
    /** Count of `<script>` elements in `toInsert` (for refcount). */
    scriptCount: number;
}

/**
 * Selectors per block kind. CSS picks `<link>` / `<style>` / `<meta>`
 * (legacy includes `<meta>` because some sekizai recipes inject
 * meta-tags). JS only picks `<script>`.
 */
const SELECTORS: Record<SekizaiBlock, string> = {
    css: 'link, style, meta',
    js: 'script',
};

/**
 * Parse a sekizai HTML chunk and return the elements that need to be
 * inserted into `current`. Caller picks whether to insert into
 * `<head>` (css) or `<body>` (js) — we don't touch the DOM here.
 *
 * Empty / missing blocks are no-ops (returns an empty plan).
 */
export function planSekizaiUpdate(
    block: SekizaiBlock,
    chunk: string | undefined,
    current: Iterable<Element>,
): SekizaiPlan {
    if (!chunk || chunk.length === 0) {
        return { toInsert: [], scriptCount: 0 };
    }

    // Inert template — script tags inside don't execute on parse.
    const template = document.createElement('template');
    template.innerHTML = chunk;

    const selector = SELECTORS[block];
    const candidates = Array.from(template.content.querySelectorAll(selector));
    const toInsert: Element[] = [];
    let scriptCount = 0;

    for (const element of candidates) {
        if (elementPresent(current, element)) continue;
        toInsert.push(element);
        if (block === 'js' && element.tagName === 'SCRIPT') scriptCount += 1;
    }

    return { toInsert, scriptCount };
}
