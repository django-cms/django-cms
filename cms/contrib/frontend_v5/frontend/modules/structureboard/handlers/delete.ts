/*
 * DELETE plugin handler.
 *
 * Mirrors legacy `StructureBoard.handleDeletePlugin`. Removes the
 * plugin's draggable + descendants from the structure tree, drops
 * the registry entries (`CMS._plugins`, `CMS._instances`), and
 * refreshes parent collapsible state.
 *
 * The "keep rendered content" branch
 * ──────────────────────────────────
 * Legacy: `if (!contentData.content) { remove rendered .cms-plugin }`.
 * If the response carries fresh content for the affected placeholder
 * (the data-bridge content update will replace the rendered nodes),
 * we leave them in place — otherwise the bridge has nothing to swap
 * onto. Mirrors the legacy semantics via `removeDraggable`'s
 * `keepRenderedContent` option.
 *
 * Always returns void. The "last plugin in placeholder" detection
 * (legacy used this to force a full refresh) is the dispatcher's
 * concern in 3f — the registry state is observable post-call.
 */

import { actualizePlaceholders, actualizePluginsCollapsibleStatus, removeDraggable } from '../dom/actualize';
import { removeFromRegistries } from '../../plugins/tree';

export interface DeletePluginData {
    plugin_id?: number | string;
    /**
     * Server payload carrying replacement content for the affected
     * placeholder. When present, the rendered `.cms-plugin-<id>` nodes
     * are kept in place so the data-bridge can swap them.
     */
    structure?: {
        content?: unknown;
        [key: string]: unknown;
    };
    /**
     * Cut payloads carry `content` directly on `data` rather than
     * inside `data.structure`. Mirrors `_updateContentFromDataBridge`'s
     * `(data.structure || data)` fallback.
     */
    content?: unknown;
    [key: string]: unknown;
}

export function handleDeletePlugin(data: DeletePluginData): void {
    const pluginId = data.plugin_id;
    if (pluginId === undefined || pluginId === null) return;

    // Find the parent BEFORE removing the draggable. Two cases:
    //   - Nested: parent is the closest ancestor `.cms-draggable`
    //   - Root  : parent is the closest ancestor `.cms-dragarea`
    // Either way, `parent.querySelector(':scope > .cms-draggables')`
    // gives the list whose collapsible state needs to be refreshed.
    const draggable = document.querySelector<HTMLElement>(
        `.cms-draggable-${pluginId}`,
    );
    let parentList: HTMLElement | null = null;
    if (draggable) {
        const parentDraggable = draggable.parentElement?.closest<HTMLElement>(
            '.cms-draggable',
        );
        const parent =
            parentDraggable ??
            draggable.closest<HTMLElement>('.cms-dragarea');
        parentList =
            parent?.querySelector<HTMLElement>(':scope > .cms-draggables') ?? null;
    }

    // Decide whether the data-bridge will refresh content for this
    // plugin's placeholder. Legacy precedence: data.structure || data.
    const contentData = data.structure ?? data;
    const keepRenderedContent =
        contentData.content !== undefined && contentData.content !== null;

    const removedIds = removeDraggable(pluginId, { keepRenderedContent });

    if (parentList) {
        actualizePluginsCollapsibleStatus([parentList]);
    }
    actualizePlaceholders();

    for (const id of removedIds) {
        removeFromRegistries(id);
    }
}
