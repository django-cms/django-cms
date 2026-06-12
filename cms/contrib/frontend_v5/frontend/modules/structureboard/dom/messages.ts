/*
 * Post-content-change hook + server-message dispatch.
 *
 * Mirrors legacy `StructureBoard._contentChanged`. Two responsibilities:
 *
 *   1. Re-run `Plugin._refreshPlugins` so per-instance event wiring
 *      catches up with the post-swap DOM.
 *   2. When a list of server messages is supplied (from the
 *      data-bridge content update), close the prior toast and open
 *      a new combined one. Error-priority is sticky — if any single
 *      message is `error`, the combined toast is rendered as an
 *      error.
 *
 * `_extractMessages` lives in `parsers/markup.ts`. This module is the
 * "now apply them" half.
 */

import { getMessages } from '../../plugins/cms-globals';
import { refreshPlugins } from '../../plugins/tree';

export interface ServerMessageLike {
    /** The displayed message text. */
    message: string;
    /** Severity flag — error toasts render in red. */
    error?: boolean;
    /** Some payloads use `level` instead of `error`. */
    level?: string;
}

/**
 * Re-bind plugin instances to the freshly-swapped DOM, then surface
 * any server messages that came back with the content-bridge update.
 *
 * `messages` is intentionally optional — `refreshContent` (full
 * content reload) doesn't pass any; the single-content data-bridge
 * path passes the toast list extracted from the response.
 */
export function contentChanged(messages?: ServerMessageLike[]): void {
    refreshPlugins();

    if (!messages) return;

    const api = getMessages();
    api?.close?.();
    if (messages.length === 0) return;

    api?.open({
        message: messages.map((m) => `<p>${m.message}</p>`).join(''),
        error: messages.some(
            (m) => m.error === true || m.level === 'error',
        ),
    });
}
