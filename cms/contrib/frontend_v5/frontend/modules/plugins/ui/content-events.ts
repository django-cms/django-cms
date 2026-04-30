/*
 * Content-mode plugin events: hover-to-highlight (when shift held in
 * structure mode) and double-click to edit.
 *
 * Mirrors legacy `_setPluginContentEvents` and `_dblClickToEditHandler`.
 * Native listeners only — no jQuery namespacing. Per-plugin event
 * removal is handled by the caller's `AbortController` (the `signal`
 * parameter), so we don't have to do `.off().on()` manual bookkeeping.
 *
 * Events wired
 * ────────────
 *   - `mouseover` on the container: when the doc carries the
 *     `expandmode` flag (set by `keydown.shift` in the global
 *     handlers), and we're in `structure` mode, ask the structureboard
 *     to surface and highlight this plugin in the structure tree.
 *   - `mouseout` on the container: clear the success-highlight
 *     classes on the matching draggable.
 *   - `dblclick` on the document, delegated to the plugin's wrapper
 *     class: open the edit modal — but only when this plugin's
 *     descriptor isn't sharing the wrapper with siblings (legacy
 *     `_isContainingMultiplePlugins` check).
 */

import { getCmsConfig, getStructureBoard } from '../cms-globals';
import type { PluginInstance } from '../types';
import { isExpandMode } from './global-handlers';

/**
 * Wire content-mode events for a plugin onto each container element.
 *
 * Returns nothing — listener removal is handled by the caller's
 * `AbortController.signal`. Idempotent at the listener level: native
 * `addEventListener` deduplicates identical (target, type, handler)
 * triples, but we still rely on the AbortController model so callers
 * can wholesale-detach on `destroy()`.
 */
export function setupContentEvents(
    plugin: PluginInstance,
    containers: Element[],
    signal?: AbortSignal,
): void {
    const opts = signal ? { signal } : undefined;

    for (const container of containers) {
        container.addEventListener(
            'mouseover',
            (e) => {
                if (!isExpandMode()) return;
                if (getCmsConfig().settings?.mode !== 'structure') return;
                e.stopPropagation();
                // Clear stale success markers (matches legacy DOM cleanup).
                document
                    .querySelectorAll('.cms-dragitem-success')
                    .forEach((el) => el.remove());
                document
                    .querySelectorAll('.cms-draggable-success')
                    .forEach((el) => el.classList.remove('cms-draggable-success'));
                const sb = getStructureBoard();
                sb?._showAndHighlightPlugin?.(0, true);
            },
            opts,
        );

        container.addEventListener(
            'mouseout',
            (e) => {
                if (getCmsConfig().settings?.mode !== 'structure') return;
                e.stopPropagation();
                // Clear success markers on this plugin's draggable, if any.
                const pluginId = plugin.options.plugin_id;
                if (pluginId === undefined || pluginId === null) return;
                const draggables = document.querySelectorAll<HTMLElement>(
                    `.cms-draggable-${pluginId}`,
                );
                draggables.forEach((draggable) => {
                    draggable
                        .querySelectorAll('.cms-dragitem-success')
                        .forEach((el) => el.remove());
                    draggable.classList.remove('cms-draggable-success');
                });
            },
            opts,
        );
    }

    // dblclick-to-edit is wired once per page in
    // `ui/global-handlers.ts::initializeGlobalHandlers` — a single
    // delegated listener walks `.cms-plugin-<id>` on the dblclick
    // target, resolves the matching instance via the registry, and
    // calls `editPlugin`. Per-instance binding is unnecessary and
    // would scale to N listeners on document with N plugins.
}

/**
 * Internal: open the edit modal unless this dblclick is disabled by a
 * `.cms-drag-disabled` ancestor or by the surrounding draggable being
 * a `.cms-slot`. Caller resolves `target` (delegated handlers walk
 * `e.target.closest(selector)`; direct handlers pass `e.currentTarget`).
 */
export function tryEditPlugin(plugin: PluginInstance, target: Element, e: Event): void {
    const disabled = target.closest('.cms-drag-disabled');
    const editDisabled = target
        .closest('.cms-draggable')
        ?.classList.contains('cms-slot');
    if (disabled || editDisabled) return;
    e.preventDefault();
    e.stopPropagation();

    // Delegate to the plugin's editPlugin if it exists. Defensive:
    // 2c shipped before 2g (modal flows), so this may be a no-op
    // until then.
    const callable = plugin as PluginInstance & {
        editPlugin?: (url: string, name?: string, breadcrumb?: unknown[]) => void;
        options: PluginInstance['options'] & { plugin_name?: string };
    };
    const url = plugin.options.urls?.edit_plugin;
    if (!url || !callable.editPlugin) return;
    callable.editPlugin(url, callable.options.plugin_name, []);
}

/**
 * Backward-compat passthrough used by `Plugin._dblClickToEditHandler`.
 * Resolves the target from the event (jQuery-flavoured `currentTarget`
 * if available, else the literal `target`), then forwards to the
 * shared `tryEditPlugin` helper.
 */
export function dblClickToEdit(plugin: PluginInstance, e: Event): void {
    const candidate =
        (e.currentTarget instanceof Element ? e.currentTarget : null) ??
        (e.target instanceof Element ? e.target : null);
    if (!candidate) return;
    tryEditPlugin(plugin, candidate, e);
}
