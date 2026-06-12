/*
 * Content-mode refresh pipeline.
 *
 * Mirrors legacy `StructureBoard.updateContent` + `refreshContent`.
 * Two stages:
 *
 *   1. `updateContent()` — invalidate the content cache, GET the
 *      content-mode markup, hand it to `refreshContent`. Loader DOM
 *      is owned by the structureboard class shell (3i) — this module
 *      stays pure transport + apply.
 *
 *   2. `refreshContent(markup)` — diff the head, swap the body,
 *      re-attach the toolbar, restore scroll, fire the post-swap hook.
 *
 *      Order matters:
 *        (a) Detach the live toolbar first — it must survive the body
 *            swap with its event listeners intact.
 *        (b) Strip toolbar markup from the new doc so the swap doesn't
 *            re-introduce a stale copy.
 *        (c) Extract server messages BEFORE diffing/swap (the
 *            messagelist would otherwise leak into the new body).
 *        (d) `dd.diff(head, newHead)` PRE-COMPUTE — must run BEFORE
 *            the body swap because the body swap may modify head
 *            (sekizai etc.). Apply head diff after body swap.
 *        (e) Re-attach toolbar + apply fresh toolbar markup.
 *        (f) Restore scroll + fire `contentChanged`.
 */

import { invalidateModeCache, requestMode } from './network/fetch';
import { replaceBodyWithHTML } from './dom/body-swap';
import { contentChanged } from './dom/messages';
import { DiffDOM } from './parsers/diff';
import { extractMessages } from './parsers/markup';
import { getMessages, getToolbar } from '../plugins/cms-globals';

/**
 * Module-level "content has been loaded at least once" flag. The
 * structureboard class reads it via `getContentLoaded()` (3i wires
 * the integration with `_loadedContent`).
 */
let contentLoaded = false;

/** Read access for the structureboard class shell. */
export function getContentLoaded(): boolean {
    return contentLoaded;
}

/** Test/migration hook — reset module state. */
export function _resetForTest(): void {
    contentLoaded = false;
}

/**
 * Fetch the content-mode markup and apply it. Bypasses the per-mode
 * memo cache (an explicit refresh always wants fresh server state).
 *
 * Returns when the apply completes — caller can chain a follow-up
 * (e.g. hide loader). Errors propagate; caller decides whether to
 * `Helpers.reloadBrowser()`.
 */
export async function updateContent(): Promise<void> {
    invalidateModeCache('content');
    const markup = await requestMode('content');
    refreshContent(markup);
}

/**
 * Apply a content-mode markup string to the live document. Synchronous
 * — the body swap may schedule script-load callbacks via `body-swap`,
 * but the structural changes happen in this call.
 */
export function refreshContent(contentMarkup: string): void {
    const newDoc = new DOMParser().parseFromString(contentMarkup, 'text/html');

    // Snapshot scroll position of the structure scroller. The body
    // swap removes the live element, so we re-query AFTER the swap
    // to get the new node and restore the scroll position there.
    const structureScrollTop =
        document.querySelector<HTMLElement>('.cms-structure-content')
            ?.scrollTop ?? 0;

    // (a) Detach the live toolbar wrappers. `Element.remove()` keeps
    //     the node + its listeners alive in the saved reference; we'll
    //     prepend it back after the swap.
    const liveToolbar = Array.from(
        document.querySelectorAll<HTMLElement>('#cms-top, [data-cms]'),
    );
    for (const el of liveToolbar) el.remove();

    // (b) Strip toolbar markup from the new doc + grab a fresh
    //     `.cms-toolbar` clone for the toolbar's own refresh hook.
    const newToolbar = newDoc.querySelector('.cms-toolbar')?.cloneNode(true) as
        | Element
        | undefined;
    newDoc.querySelectorAll('#cms-top, [data-cms]').forEach((el) => el.remove());

    // (c) Extract server messages.
    const messages = extractMessages(newDoc);
    if (messages.length > 0) {
        const api = getMessages();
        if (api) {
            // Schedule on a microtask so the toolbar/messages module
            // has a chance to re-bind to the post-swap DOM first.
            setTimeout(() => {
                for (const msg of messages) api.open(msg);
            }, 0);
        }
    }

    // (d) Pre-compute the head diff against the new head. Apply AFTER
    //     the body swap (the body swap may insert sekizai blocks into
    //     the head and we want the diff baseline to be pre-swap).
    const dd = new DiffDOM();
    const headDiff = dd.diff(document.head, newDoc.head);

    replaceBodyWithHTML(newDoc.body);
    dd.apply(document.head, headDiff);

    // (e) Re-attach toolbar wrappers + refresh the toolbar markup.
    for (const el of liveToolbar) document.body.prepend(el);
    if (newToolbar) {
        getToolbar()?._refreshMarkup?.(newToolbar);
    }

    // (f) Restore scroll + post-swap hook.
    const newScroller = document.querySelector<HTMLElement>(
        '.cms-structure-content',
    );
    if (newScroller) newScroller.scrollTop = structureScrollTop;
    contentLoaded = true;
    contentChanged();
}
