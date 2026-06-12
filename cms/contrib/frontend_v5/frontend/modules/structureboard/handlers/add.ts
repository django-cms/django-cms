/*
 * ADD plugin handler.
 *
 * Mirrors legacy `StructureBoard.handleAddPlugin`. Two paths:
 *
 *   1. Nested add (`data.plugin_parent` set) — the server returned a
 *      replacement for the parent draggable that includes the new
 *      child. Replace the parent draggable's outerHTML in place.
 *   2. Root add (no `plugin_parent`) — append the new draggable's
 *      HTML to the placeholder's first `.cms-draggables` list.
 *
 * After mutation: refresh placeholder empty/disabled state, write new
 * descriptors into the registry, restore each new draggable's expand
 * state from `CMS.settings.states`.
 *
 * Returns void — the structureboard dispatcher (`invalidate.ts`,
 * coming in 3f) decides whether to follow up with
 * `updateContentFromDataBridge` or a full refresh based on the
 * `data.structure.content` shape.
 */

import {
    actualizePlaceholders,
    actualizePluginCollapseStatus,
} from '../dom/actualize';
import { updateRegistry } from '../../plugins/tree';
import type { PluginOptions } from '../../plugins/types';

export interface AddPluginData {
    placeholder_id?: number | string;
    plugin_parent?: number | string | null;
    structure?: {
        html?: string;
        plugins?: PluginOptions[];
        [key: string]: unknown;
    };
    [key: string]: unknown;
}

export function handleAddPlugin(data: AddPluginData): void {
    const html = data.structure?.html;

    if (data.plugin_parent !== undefined && data.plugin_parent !== null && data.plugin_parent !== '') {
        // Nested add: the server returned a replacement for the parent
        // draggable that already contains the new child draggable.
        const parent = document.querySelector<HTMLElement>(
            `.cms-draggable-${data.plugin_parent}`,
        );
        if (parent && html) {
            replaceOuterHTML(parent, html);
        }
    } else if (data.placeholder_id !== undefined && html) {
        // Root add: append to the placeholder's first `.cms-draggables`.
        const list = document.querySelector<HTMLElement>(
            `.cms-dragarea-${data.placeholder_id} > .cms-draggables`,
        );
        list?.insertAdjacentHTML('beforeend', html);
    }

    actualizePlaceholders();

    const plugins = data.structure?.plugins ?? [];
    if (plugins.length > 0) {
        updateRegistry(plugins);
        for (const plugin of plugins) {
            const id = plugin.plugin_id;
            if (id !== undefined && id !== null) {
                actualizePluginCollapseStatus(id);
            }
        }
    }
}

/**
 * Replace `el` with the first element parsed from `html`. jQuery's
 * `replaceWith(html)` does this with a temporary parser; we do it
 * directly with `outerHTML` (faster, no fragment intermediates).
 */
function replaceOuterHTML(el: HTMLElement, html: string): void {
    el.outerHTML = html;
}
