/*
 * MOVE / PASTE plugin handler.
 *
 * Mirrors legacy `StructureBoard.handleMovePlugin`. Handles four
 * cases (the legacy method has a long branch tree — split below for
 * readability):
 *
 *   1. Nested move/paste (`data.plugin_parent` set) — clean up any
 *      stale leftover with the same id outside the new parent (drag
 *      already visually relocated it; an external update would still
 *      have it in the source), then replace the parent draggable's
 *      outerHTML with the server response (which carries the new
 *      child in its new place).
 *
 *   2. Top-level move with cross-placeholder reposition — find the
 *      LAST draggable with the id (clipboard original is first),
 *      move it into the target placeholder at the position from
 *      `data.plugin_order`. Clipboard items are CLONED so the
 *      clipboard stays populated.
 *
 *   3. Top-level move within the same placeholder, OUT-OF-ORDER —
 *      external update where another tab moved the plugin and the
 *      DOM order doesn't match the server's. Reorder via
 *      `plugin_order`.
 *
 *   4. Cross-language paste — no draggable existed locally;
 *      `data.target_placeholder_id` is set; append the new HTML.
 *
 * After the structural mutation: `actualizePlaceholders`,
 * `updateRegistry`, restore each plugin's expand state, restore the
 * dragbar collapse state via `initializeDragItemsStates`.
 */

import {
    actualizePlaceholders,
    actualizePluginCollapseStatus,
    initializeDragItemsStates,
    relocateDraggable,
} from '../dom/actualize';
import { updateRegistry } from '../../plugins/tree';
import { getIds, parseDragareaId } from '../parsers/ids';
import type { PluginOptions } from '../../plugins/types';

export interface MovePluginData {
    plugin_id?: number | string;
    placeholder_id?: number | string;
    plugin_parent?: number | string | null;
    /**
     * Order of plugin ids inside the target placeholder, post-move.
     * `'__COPY__'` is a sentinel used by the cross-language paste
     * flow when the moved item's id is not yet known locally.
     */
    plugin_order?: Array<number | string>;
    /** Cross-language paste destination placeholder. */
    target_placeholder_id?: number | string;
    html?: string;
    plugins?: PluginOptions[];
    [key: string]: unknown;
}

export function handleMovePlugin(data: MovePluginData): void {
    if (
        data.plugin_parent !== undefined &&
        data.plugin_parent !== null &&
        data.plugin_parent !== ''
    ) {
        applyNestedMove(data);
    } else if (
        data.plugin_id !== undefined &&
        data.plugin_id !== null &&
        data.placeholder_id !== undefined &&
        data.placeholder_id !== null
    ) {
        applyTopLevelMove(data);
    } else if (data.target_placeholder_id !== undefined && data.html) {
        // Cross-language paste fallthrough (no existing draggable).
        appendToPlaceholder(data.target_placeholder_id, data.html);
    }

    actualizePlaceholders();

    const plugins = data.plugins ?? [];
    if (plugins.length > 0) {
        updateRegistry(plugins);
        for (const plugin of plugins) {
            const id = plugin.plugin_id;
            if (id !== undefined && id !== null) {
                actualizePluginCollapseStatus(id);
            }
        }
    }

    initializeDragItemsStates();
}

function applyNestedMove(data: MovePluginData): void {
    // Stale-leftover cleanup: when the dragged item is outside the new
    // parent and not from clipboard, drop it. Drag already visually
    // moved it; an external update wouldn't have, so the source still
    // has the original.
    if (data.plugin_id !== undefined && data.plugin_id !== null) {
        const matches = document.querySelectorAll<HTMLElement>(
            `.cms-draggable-${data.plugin_id}`,
        );
        const last = matches[matches.length - 1];
        if (last) {
            const inNewParent = last.closest(
                `.cms-draggable-${data.plugin_parent}`,
            );
            const fromClipboard = last.classList.contains(
                'cms-draggable-from-clipboard',
            );
            if (!inNewParent && !fromClipboard) last.remove();
        }
    }

    if (!data.html) return;
    const parent = document.querySelector<HTMLElement>(
        `.cms-draggable-${data.plugin_parent}`,
    );
    if (!parent) return;
    // Empty children first — the legacy comment notes this is a perf
    // shortcut to avoid jQuery walking the whole subtree to detach
    // event handlers when replacing.
    parent.innerHTML = '';
    parent.outerHTML = data.html;
}

function applyTopLevelMove(data: MovePluginData): void {
    const matches = document.querySelectorAll<HTMLElement>(
        `.cms-draggable-${data.plugin_id}`,
    );
    let draggable: HTMLElement | null = matches[matches.length - 1] ?? null;

    const inTarget = draggable
        ? isInPlaceholder(draggable, data.placeholder_id!)
        : false;

    if (!inTarget && draggable) {
        // External update or post-drag reposition — relocate into the
        // target placeholder at the order-correct slot. `relocateDraggable`
        // handles the clipboard-clone branch internally.
        const relocated = relocateDraggable(
            data.plugin_id!,
            data.placeholder_id!,
            data.plugin_order,
        );
        if (relocated) draggable = relocated;
    } else if (inTarget && draggable && data.plugin_order) {
        // Same placeholder but order may diverge (cross-tab update).
        reorderWithinPlaceholder(
            draggable,
            data.placeholder_id!,
            data.plugin_id!,
            data.plugin_order,
        );
    }

    if (draggable && data.html) {
        // Empty children before outerHTML swap (perf shortcut, see
        // applyNestedMove).
        draggable.innerHTML = '';
        draggable.outerHTML = data.html;
    } else if (
        !draggable &&
        data.target_placeholder_id !== undefined &&
        data.html
    ) {
        // No existing draggable — cross-language paste. Append.
        appendToPlaceholder(data.target_placeholder_id, data.html);
    }
}

function isInPlaceholder(
    draggable: HTMLElement,
    placeholderId: number | string,
): boolean {
    const list = draggable.closest<HTMLElement>('.cms-draggables');
    const dragarea = list?.parentElement as HTMLElement | null;
    return (
        dragarea !== null &&
        dragarea !== undefined &&
        Number(parseDragareaId(dragarea)) === Number(placeholderId)
    );
}

function reorderWithinPlaceholder(
    draggable: HTMLElement,
    placeholderId: number | string,
    pluginId: number | string,
    pluginOrder: Array<number | string>,
): void {
    const list = document.querySelector<HTMLElement>(
        `.cms-dragarea-${placeholderId} > .cms-draggables`,
    );
    if (!list) return;
    const actual = getIds(
        list.querySelectorAll<HTMLElement>(':scope > .cms-draggable'),
    );
    if (arraysEqual(actual, pluginOrder)) return;

    const idx = pluginOrder.findIndex(
        (id) => Number(id) === Number(pluginId),
    );
    if (idx === 0) {
        list.insertBefore(draggable, list.firstChild);
    } else if (idx > 0) {
        const prevId = pluginOrder[idx - 1];
        const prev = list.querySelector<HTMLElement>(
            `.cms-draggable-${prevId}`,
        );
        prev?.insertAdjacentElement('afterend', draggable);
    }
}

function appendToPlaceholder(
    placeholderId: number | string,
    html: string,
): void {
    const list = document.querySelector<HTMLElement>(
        `.cms-dragarea-${placeholderId} > .cms-draggables`,
    );
    list?.insertAdjacentHTML('beforeend', html);
}

function arraysEqual(
    a: ReadonlyArray<number | string>,
    b: ReadonlyArray<number | string>,
): boolean {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i += 1) {
        if (Number(a[i]) !== Number(b[i])) return false;
    }
    return true;
}
