/*
 * Data-bridge content update — apply the rendered HTML the server
 * embedded in a mutation response so structureboard doesn't have to
 * round-trip back to content-mode.
 *
 * Mirrors legacy `_updateContentFromDataBridge`, `_updateSingleContent`,
 * `_findNextElement`, and the *mutation half* of `_updateSekizai`.
 *
 * Pipeline
 * ────────
 * `applyContentBridge(data)` — entry point. Returns true when a full
 * content refresh is still required (i.e. the bridge couldn't apply
 * the update from the data alone).
 *
 *   1. Sanity-check `data.content`. Empty / missing → full refresh.
 *   2. If a source placeholder lost its last plugin, the placeholder
 *      itself may need to be re-rendered (alternative-content, etc.)
 *      → full refresh.
 *   3. For each `data.content[i]`, `applySingleContent` either swaps
 *      the rendered nodes in place or signals that a full refresh is
 *      needed.
 *   4. Surface any `data.messages` toasts via `contentChanged`.
 *
 * Sekizai (CSS / JS) blocks are merged from each content entry. The
 * mutation half lives here so the script-execution refcount can be
 * tracked alongside the page swap (legacy keeps the count on the
 * StructureBoard instance — we keep it on `body-swap` since that
 * already owns the script-load callback).
 */

import { incrementScriptCount, scriptLoaded } from './body-swap';
import { contentChanged, type ServerMessageLike } from './messages';
import { getAllInstances } from '../../plugins/registry';
import { planSekizaiUpdate, type SekizaiBlock } from '../parsers/sekizai';

/**
 * Single-content payload entry. The server emits one of these per
 * placeholder/plugin chunk that should swap into the live page.
 */
export interface ContentEntry {
    /** Plugin ids represented by this content chunk. */
    pluginIds?: Array<number | string>;
    /** Replacement HTML for the affected `.cms-plugin-<id>` nodes. */
    html?: string;
    /**
     * Forces the inserted-after-position lookup even when an existing
     * `.cms-plugin-start` is found. Used when an ADD happens at a
     * non-trivial position.
     */
    insert?: boolean;
    /** 1-based position within the placeholder. */
    position?: number;
    /** Target placeholder id. */
    placeholder_id?: number | string;
    /** CSS sekizai chunk to merge into `<head>`. */
    css?: string;
    /** JS sekizai chunk to merge into `<body>`. */
    js?: string;
}

export interface ContentBridgeData {
    content?: ContentEntry[];
    messages?: ServerMessageLike[];
    /**
     * The placeholder a plugin was moved out of. When set + that
     * placeholder no longer has any plugins in `CMS._instances`, the
     * bridge bails (alternative-content render path needs full refresh).
     */
    source_placeholder_id?: number | string;
}

/**
 * Returns true when a full content refresh is still required after
 * the call (the data alone can't satisfy the update). False means
 * the bridge handled it.
 */
export function applyContentBridge(data: ContentBridgeData | undefined | null): boolean {
    if (!data || !data.content || data.content.length === 0) return true;

    if (data.source_placeholder_id !== undefined && data.source_placeholder_id !== null) {
        const stillHasPlugins = getAllInstances().some(
            (i) =>
                i.options.type === 'plugin' &&
                i.options.placeholder_id !== undefined &&
                i.options.placeholder_id !== null &&
                Number(i.options.placeholder_id) ===
                    Number(data.source_placeholder_id),
        );
        if (!stillHasPlugins) return true;
    }

    for (const entry of data.content) {
        if (applySingleContent(entry)) return true;
    }

    contentChanged(data.messages);
    return false;
}

/**
 * Apply a single content entry. Returns true when the entry can't be
 * placed (signals "full refresh needed"), false when applied.
 */
export function applySingleContent(entry: ContentEntry): boolean {
    const ids = entry.pluginIds;
    if (!ids || ids.length === 0 || entry.html === undefined) return true;

    // Anchor: the existing rendered start-marker for the first plugin
    // in the entry (the `cms-plugin-start` token). If absent, or if
    // `insert: true` forces it, walk forward via `findNextElement`.
    const firstId = ids[0]!;
    let anchor = findStartMarker(firstId);

    if (!anchor || entry.insert) {
        if (entry.position !== undefined && entry.placeholder_id !== undefined) {
            anchor = findNextElement(entry.position, entry.placeholder_id, ids);
        }
    }
    if (!anchor) return true;

    // Insert the new HTML before the anchor, then drop the previous
    // rendered nodes for these plugin ids.
    anchor.insertAdjacentHTML('beforebegin', entry.html);
    for (const id of ids) {
        document
            .querySelectorAll(`.cms-plugin.cms-plugin-${id}`)
            .forEach((el) => {
                if (!isInsideTemplate(el)) el.remove();
            });
        document
            .querySelectorAll(
                `script[data-cms-plugin]#cms-plugin-${id}`,
            )
            .forEach((el) => el.remove());
    }

    // Sekizai merge — CSS into `<head>`, JS into `<body>`.
    if (entry.css) applySekizai('css', entry.css);
    if (entry.js) applySekizai('js', entry.js);

    return false;
}

/**
 * Find the `.cms-plugin-start` token for a given plugin id. The legacy
 * `:not(template)` jQuery filter is replaced with an explicit walk that
 * skips template descendants — `<template>` content is inert and must
 * not be matched.
 */
function findStartMarker(pluginId: number | string): Element | null {
    const candidates = document.querySelectorAll(
        `.cms-plugin.cms-plugin-${pluginId}.cms-plugin-start`,
    );
    for (const el of Array.from(candidates)) {
        if (!isInsideTemplate(el)) return el;
    }
    return null;
}

function isInsideTemplate(el: Element): boolean {
    return el.closest('template') !== null;
}

/**
 * Find the next plugin's start-marker at or after `position` in
 * `placeholder_id`, excluding `excluded` ids. Falls back to the
 * placeholder element itself when no later plugin exists. Mirrors
 * legacy `_findNextElement`.
 */
export function findNextElement(
    position: number,
    placeholderId: number | string,
    excluded: ReadonlyArray<number | string>,
): Element | null {
    const excludedNumbers = new Set(excluded.map((id) => Number(id)));
    const candidates = getAllInstances().filter((i) => {
        const opts = i.options;
        if (opts.type !== 'plugin') return false;
        if (
            opts.placeholder_id === undefined ||
            opts.placeholder_id === null ||
            Number(opts.placeholder_id) !== Number(placeholderId)
        ) {
            return false;
        }
        if (
            opts.position === undefined ||
            opts.position === null ||
            opts.position < position
        ) {
            return false;
        }
        if (
            opts.plugin_id !== undefined &&
            opts.plugin_id !== null &&
            excludedNumbers.has(Number(opts.plugin_id))
        ) {
            return false;
        }
        return true;
    });

    if (candidates.length > 0) {
        const next = candidates.reduce((min, cur) => {
            const minPos = (min.options.position ?? 0) as number;
            const curPos = (cur.options.position ?? 0) as number;
            return curPos < minPos ? cur : min;
        }, candidates[0]!);
        const id = next.options.plugin_id;
        if (id !== undefined && id !== null) {
            const marker = document.querySelector(
                `.cms-plugin.cms-plugin-${id}.cms-plugin-start`,
            );
            if (marker) return marker;
        }
    }

    return document.querySelector(
        `div.cms-placeholder.cms-placeholder-${placeholderId}`,
    );
}

/**
 * Mutation half of `_updateSekizai`. Parser side (`planSekizaiUpdate`)
 * lives in `parsers/sekizai.ts`; this side does the DOM insertion and
 * script re-cloning.
 *
 * For JS blocks: `<script>` elements are re-created (the cloned node
 * doesn't execute via `appendChild`), `src=` scripts increment the
 * pending-script refcount on `body-swap` so the refresh callback only
 * fires once they've all loaded.
 */
export function applySekizai(block: SekizaiBlock, chunk: string): void {
    const location = block === 'css' ? document.head : document.body;
    const selector = block === 'css' ? 'link, style, meta' : 'script';
    const current = location.querySelectorAll(selector);
    const plan = planSekizaiUpdate(block, chunk, Array.from(current));

    for (const element of plan.toInsert) {
        if (block === 'js' && element.tagName === 'SCRIPT') {
            const replacement = document.createElement('script');
            for (const attr of Array.from(element.attributes)) {
                replacement.setAttribute(attr.name, attr.value);
            }
            const src = (element as HTMLScriptElement).src;
            if (src) {
                incrementScriptCount();
                replacement.async = false;
                const onSettled = (): void => scriptLoaded();
                replacement.onload = onSettled;
                replacement.onerror = onSettled;
            }
            replacement.textContent = element.textContent;
            location.appendChild(replacement);
        } else {
            location.appendChild(element);
        }
    }
}
