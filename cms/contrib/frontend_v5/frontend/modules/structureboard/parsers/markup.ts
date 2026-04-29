/*
 * Pure parsers that take a parsed DOM tree (or a Document fragment)
 * and return data. No DOM mutation, no jQuery, no XHR.
 *
 * Used by the content-refresh pipeline (`refresh.ts` parses the
 * server response into a Document, then hands it to these parsers
 * before the DOM-mutating side runs).
 */

import type { PluginOptions } from '../../plugins/types';

/**
 * Read each `<script id="cms-plugin-{id}" data-cms-plugin>` blob and
 * return its parsed JSON. Misses (no script for an id, or unparsable
 * JSON) are dropped silently — same as legacy.
 *
 * Legacy: `_getPluginDataFromMarkup`. Note the legacy querySelector
 * used `#cms-plugin-${pluginId}` (id selector); we keep that contract.
 */
export function getPluginDataFromMarkup(
    body: ParentNode,
    pluginIds: Iterable<number | string>,
): PluginOptions[] {
    const result: PluginOptions[] = [];
    for (const pluginId of pluginIds) {
        const script = body.querySelector(`#cms-plugin-${pluginId}`);
        if (!script || !script.textContent) continue;
        try {
            const parsed = JSON.parse(script.textContent) as PluginOptions;
            result.push(parsed);
        } catch {
            /* malformed descriptor — skip */
        }
    }
    return result;
}

/**
 * Test whether `element`'s outerHTML matches any element already in
 * `current`. Used by Sekizai-block replacement to skip merge inserts
 * that would re-execute already-loaded scripts.
 *
 * Legacy: `_elementPresent`.
 */
export function elementPresent(
    current: Iterable<Element>,
    element: Element,
): boolean {
    const markup = element.outerHTML;
    for (const el of current) {
        if (el.outerHTML === markup) return true;
    }
    return false;
}

export interface ServerMessage {
    /** Trimmed message text. */
    message: string;
    /** True for error/danger-styled messages. */
    error: boolean;
}

/**
 * Extract Django `messagelist` server messages from a server response
 * markup tree. Tries `.messagelist > li` first (legacy admin), then
 * falls back to `[data-cms-messages-container] > [data-cms-message]`
 * (modern CMS templates).
 *
 * Returns the messages as a list. Empty when no messagelist is present
 * or all message elements are blank.
 *
 * Legacy: `_extractMessages`.
 */
export function extractMessages(doc: ParentNode): ServerMessage[] {
    let listSelector = '.messagelist';
    let itemSelector = 'li';
    let list = doc.querySelector(listSelector);
    let items = list?.querySelectorAll(itemSelector);

    if (!list || !items || items.length === 0) {
        listSelector = '[data-cms-messages-container]';
        itemSelector = '[data-cms-message]';
        list = doc.querySelector(listSelector);
        items = list?.querySelectorAll(itemSelector);
    }

    if (!items || items.length === 0) return [];

    const out: ServerMessage[] = [];
    for (const el of Array.from(items)) {
        const text = (el.textContent ?? '').trim();
        if (!text) continue;
        const error =
            (el as HTMLElement).dataset?.cmsMessageTags === 'error' ||
            el.classList.contains('error');
        out.push({ message: text, error });
    }
    return out;
}
