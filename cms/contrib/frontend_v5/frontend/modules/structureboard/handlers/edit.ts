/*
 * EDIT plugin handler.
 *
 * Mirrors legacy `StructureBoard.handleEditPlugin`. Two paths:
 *
 *   1. Nested edit (`data.plugin_parent` set) — replace the parent
 *      draggable's outerHTML with the server response, which carries
 *      the freshly-rendered subtree including the edited child.
 *   2. Root edit — replace the edited draggable's outerHTML with the
 *      server response.
 *
 * After mutation: write new descriptors into the registry, restore
 * each new draggable's expand state. Unlike `add`, edit does NOT
 * call `actualizePlaceholders` — the placeholder count is unchanged.
 */

import { actualizePluginCollapseStatus } from '../dom/actualize';
import { updateRegistry } from '../../plugins/tree';
import type { PluginOptions } from '../../plugins/types';

export interface EditPluginData {
    plugin_id?: number | string;
    plugin_parent?: number | string | null;
    structure?: {
        html?: string;
        plugins?: PluginOptions[];
        [key: string]: unknown;
    };
    [key: string]: unknown;
}

export function handleEditPlugin(data: EditPluginData): void {
    const html = data.structure?.html;
    if (!html) {
        // No replacement HTML — nothing to mutate. Still update the
        // registry below in case descriptors changed.
    } else if (
        data.plugin_parent !== undefined &&
        data.plugin_parent !== null &&
        data.plugin_parent !== ''
    ) {
        const parent = document.querySelector<HTMLElement>(
            `.cms-draggable-${data.plugin_parent}`,
        );
        if (parent) parent.outerHTML = html;
    } else if (data.plugin_id !== undefined && data.plugin_id !== null) {
        const draggable = document.querySelector<HTMLElement>(
            `.cms-draggable-${data.plugin_id}`,
        );
        if (draggable) draggable.outerHTML = html;
    }

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
