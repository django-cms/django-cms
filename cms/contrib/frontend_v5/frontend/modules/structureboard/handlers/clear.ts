/*
 * CLEAR_PLACEHOLDER handler.
 *
 * Mirrors legacy `StructureBoard.handleClearPlaceholder`. Walks
 * `CMS._instances` for plugins in the target placeholder, drops
 * each from the registry and removes its `.cms-draggable` from the
 * DOM. Rendered `.cms-plugin-<id>` content nodes and JSON script
 * blobs are LEFT IN PLACE — the legacy contract is "always trigger a
 * full content refresh after CLEAR" so they get replaced wholesale.
 *
 * Always returns void. The dispatcher in 3f forces a refresh after
 * CLEAR (legacy: `return true`).
 */

import {
    actualizePlaceholders,
    removeDraggable,
} from '../dom/actualize';
import { getAllInstances } from '../../plugins/registry';
import { removeFromRegistries } from '../../plugins/tree';

export interface ClearPlaceholderData {
    placeholder_id?: number | string;
    [key: string]: unknown;
}

export function handleClearPlaceholder(data: ClearPlaceholderData): void {
    if (data.placeholder_id === undefined || data.placeholder_id === null) return;
    const target = Number(data.placeholder_id);

    // Snapshot the ids before mutating — the registry list is live.
    const ids: Array<number | string> = [];
    for (const instance of getAllInstances()) {
        const opts = instance.options;
        if (opts.type !== 'plugin') continue;
        if (
            opts.plugin_id === undefined ||
            opts.plugin_id === null ||
            opts.placeholder_id === undefined ||
            opts.placeholder_id === null
        ) {
            continue;
        }
        if (Number(opts.placeholder_id) !== target) continue;
        ids.push(opts.plugin_id);
    }

    for (const id of ids) {
        removeFromRegistries(id);
        // Keep rendered content + script blobs — the full refresh that
        // the dispatcher fires after CLEAR will replace them.
        removeDraggable(id, { keepRenderedContent: true, keepScript: true });
    }

    actualizePlaceholders();
}
