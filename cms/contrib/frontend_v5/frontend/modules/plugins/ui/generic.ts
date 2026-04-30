/*
 * Generic plugin events: dblclick-to-edit and pointer/touch tooltip.
 *
 * Mirrors legacy `_setGeneric`. Generics are descriptors that don't
 * appear in the structure board — front-end editable fields, page
 * menus, etc. They get a simple dblclick to open the edit modal and
 * a hover tooltip showing the plugin name.
 */

import { getTooltip } from '../cms-globals';
import type { PluginInstance } from '../types';

/**
 * Wire generic-mode events onto each container element. Listener
 * removal happens via the caller's AbortController signal.
 */
export function setupGenericEvents(
    plugin: PluginInstance,
    containers: Element[],
    signal?: AbortSignal,
): void {
    const opts = signal ? { signal } : undefined;

    for (const container of containers) {
        // dblclick → editPlugin
        container.addEventListener(
            'dblclick',
            (e) => {
                e.preventDefault();
                e.stopPropagation();
                const url = plugin.options.urls?.edit_plugin;
                const callable = plugin as PluginInstance & {
                    editPlugin?: (url: string, name?: string, breadcrumb?: unknown[]) => void;
                    options: PluginInstance['options'] & { plugin_name?: string };
                };
                if (!url || !callable.editPlugin) return;
                callable.editPlugin(url, callable.options.plugin_name, []);
            },
            opts,
        );

        // pointerover / pointerout / touchstart → tooltip toggle
        const tooltipHandler = (e: Event) => {
            const target = e.currentTarget as Element | null;
            if (!target) return;
            // Touchstart shouldn't stopPropagation — legacy preserves
            // bubbling so nested plugins still get touch start.
            if (e.type !== 'touchstart') {
                e.stopPropagation();
            }
            const disabled = target.classList.contains('cms-slot');
            const show =
                (e.type === 'pointerover' || e.type === 'touchstart') && !disabled;
            const tooltip = getTooltip();
            const callable = plugin as PluginInstance & {
                options: PluginInstance['options'] & { plugin_name?: string };
            };
            tooltip?.displayToggle(
                show,
                target as HTMLElement,
                callable.options.plugin_name ?? '',
                plugin.options.plugin_id ?? '',
            );
        };

        container.addEventListener('pointerover', tooltipHandler, opts);
        container.addEventListener('pointerout', tooltipHandler, opts);
        container.addEventListener('touchstart', tooltipHandler, opts);
    }
}
