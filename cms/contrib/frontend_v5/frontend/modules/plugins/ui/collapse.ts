/*
 * Collapsable plugin tree state.
 *
 * Mirrors legacy `_collapsables`, `_toggleCollapsable`, `_expandAll`,
 * `_collapseAll`, `_updatePlaceholderCollapseState`. Owns the tree's
 * expand/collapse persistence in `CMS.settings.states` (per-plugin)
 * and `CMS.settings.dragbars` (per-placeholder dragbar title).
 *
 * Why structureboard touches this
 * ───────────────────────────────
 * `_collapsables` is called from the constructor in structure mode
 * AND re-called by structureboard whenever it re-renders the tree
 * (after a move, paste, etc.). The *event wiring* must therefore be
 * idempotent at the listener level — we use the per-instance
 * AbortController signal to detach when the instance is destroyed,
 * and don't re-bind on the same draggable twice in a single instance.
 *
 * `cms-hidden` class
 * ──────────────────
 * Legacy toggles `.cms-collapsable-container` between `.cms-hidden`
 * and not-hidden. Same here — keep the class name so the existing
 * SCSS still applies. The collapse "expanded" indicator on the
 * dragitem is `.cms-dragitem-expanded`; on the dragbar title it's
 * `.cms-dragbar-title-expanded`.
 */

import { Helpers } from '../../cms-base';
import { getCmsSettings, getPluginsRegistry } from '../cms-globals';
import type { PluginInstance } from '../types';
import { isExpandMode } from './global-handlers';

/**
 * Wire collapse/expand on the dragitem text. Called from the Plugin
 * constructor in structure mode (and re-called after structureboard
 * re-renders).
 */
export function setupCollapsable(
    plugin: PluginInstance,
    signal?: AbortSignal,
): void {
    const pluginId = plugin.options.plugin_id;
    if (pluginId === undefined || pluginId === null) return;

    const draggable = document.querySelector<HTMLElement>(
        `.cms-draggable-${pluginId}`,
    );
    if (!draggable) return;

    const dragitem = directChild(draggable, '.cms-dragitem');
    if (!dragitem) return;

    // If every collapsable item under this draggable is already
    // expanded, mark the matching dragbar title accordingly.
    const collapsables = draggable.querySelectorAll('.cms-dragitem-collapsable');
    const expanded = draggable.querySelectorAll('.cms-dragitem-collapsable.cms-dragitem-expanded');
    if (collapsables.length > 0 && collapsables.length === expanded.length) {
        draggable
            .querySelector('.cms-dragbar-title')
            ?.classList.add('cms-dragbar-title-expanded');
    }

    // Click on the dragitem text → toggle collapse (only when the
    // dragitem is itself collapsable).
    const text = directChild(dragitem, '.cms-dragitem-text');
    if (!text) return;

    const opts = signal ? { signal } : undefined;
    const handler = (e: Event): void => {
        if (!dragitem.classList.contains('cms-dragitem-collapsable')) return;
        e.stopPropagation();
        toggleCollapsable(plugin, dragitem);
    };
    text.addEventListener('click', handler, opts);
    text.addEventListener('touchend', handler, opts);
}

/**
 * Flip the collapse state of `dragitem`, persist the result to
 * `CMS.settings.states`, and (when shift-expand-mode is on) recurse
 * into the subtree.
 *
 * Mirrors legacy `_toggleCollapsable` exactly: the recursive expand
 * uses `find('.cms-draggable').find('.cms-dragitem-collapsable')`
 * which Sizzle treats as descendant — keep the descendant semantics.
 */
export function toggleCollapsable(
    plugin: PluginInstance,
    dragitem: HTMLElement,
): void {
    const draggable = dragitem.closest<HTMLElement>('.cms-draggable');
    if (!draggable) return;

    // Child id lookup: legacy did `_getId(el.parent())`, where parent
    // was the .cms-draggable. We parse the id straight off the class.
    const parent = dragitem.parentElement;
    const id = parseDraggableId(parent ?? draggable);

    const settings = getCmsSettings();
    if (!Array.isArray(settings.states)) settings.states = [];

    const wasExpanded = dragitem.classList.contains('cms-dragitem-expanded');

    if (wasExpanded) {
        // Collapse: drop id from states, hide the container.
        if (id !== undefined) {
            const idx = settings.states.indexOf(id);
            if (idx >= 0) settings.states.splice(idx, 1);
        }
        dragitem.classList.remove('cms-dragitem-expanded');
        directChild(parent ?? draggable, '.cms-collapsable-container')?.classList.add(
            'cms-hidden',
        );

        // Shift held → also collapse every nested expanded item.
        if (isExpandMode()) {
            const nested = draggable.querySelectorAll<HTMLElement>(
                '.cms-draggable .cms-dragitem-collapsable.cms-dragitem-expanded',
            );
            for (const item of Array.from(nested)) {
                toggleCollapsable(plugin, item);
            }
        }
    } else {
        // Expand: push id, show the container.
        if (id !== undefined) settings.states.push(id);
        dragitem.classList.add('cms-dragitem-expanded');
        directChild(parent ?? draggable, '.cms-collapsable-container')?.classList.remove(
            'cms-hidden',
        );

        if (isExpandMode()) {
            const nested = draggable.querySelectorAll<HTMLElement>(
                '.cms-draggable .cms-dragitem-collapsable:not(.cms-dragitem-expanded)',
            );
            for (const item of Array.from(nested)) {
                toggleCollapsable(plugin, item);
            }
        }
    }

    updatePlaceholderCollapseState(plugin);
    persistSettings(settings);
}

/**
 * Expand every collapsable item under the placeholder reachable from
 * `el`. Used by the dragbar title click handler ("expand all").
 */
export function expandAll(plugin: PluginInstance, el: HTMLElement): void {
    const dragarea = el.closest<HTMLElement>('.cms-dragarea');
    if (!dragarea) return;

    const items = dragarea.querySelectorAll<HTMLElement>(
        '.cms-dragitem-collapsable',
    );
    if (items.length === 0) return;

    items.forEach((item) => {
        if (!item.classList.contains('cms-dragitem-expanded')) {
            toggleCollapsable(plugin, item);
        }
    });

    el.classList.add('cms-dragbar-title-expanded');

    const settings = getCmsSettings();
    if (!Array.isArray(settings.dragbars)) settings.dragbars = [];
    const placeholderId = plugin.options.placeholder_id;
    if (placeholderId !== undefined && placeholderId !== null) {
        settings.dragbars.push(placeholderId);
    }
    persistSettings(settings);
}

/**
 * Collapse every collapsable item under the placeholder reachable
 * from `el`. The mirror of `expandAll`.
 */
export function collapseAll(plugin: PluginInstance, el: HTMLElement): void {
    const dragarea = el.closest<HTMLElement>('.cms-dragarea');
    if (!dragarea) return;

    const items = dragarea.querySelectorAll<HTMLElement>(
        '.cms-dragitem-collapsable',
    );
    items.forEach((item) => {
        if (item.classList.contains('cms-dragitem-expanded')) {
            toggleCollapsable(plugin, item);
        }
    });

    el.classList.remove('cms-dragbar-title-expanded');

    const settings = getCmsSettings();
    if (!Array.isArray(settings.dragbars)) settings.dragbars = [];
    const placeholderId = plugin.options.placeholder_id;
    if (placeholderId !== undefined && placeholderId !== null) {
        const idx = settings.dragbars.indexOf(placeholderId);
        if (idx >= 0) settings.dragbars.splice(idx, 1);
    }
    persistSettings(settings);
}

/**
 * After a single-item toggle, re-derive whether the placeholder's
 * dragbar title should show the "all expanded" indicator. A
 * placeholder is considered fully-expanded when every plugin that has
 * children is in `settings.states`.
 *
 * Reproduces the legacy oddity exactly: leaf plugins (no children)
 * are not required to be in `states` for the placeholder to count as
 * expanded.
 */
export function updatePlaceholderCollapseState(plugin: PluginInstance): void {
    if (plugin.options.type !== 'plugin') return;
    const placeholderId = plugin.options.placeholder_id;
    if (placeholderId === undefined || placeholderId === null) return;

    const allDescriptors = getPluginsRegistry();
    const pluginsInPlaceholder = allDescriptors
        .filter(
            ([, o]) =>
                o.placeholder_id === placeholderId && o.type === 'plugin',
        )
        .map(([, o]) => o.plugin_id);

    const settings = getCmsSettings();
    const opened = Array.isArray(settings.states) ? settings.states : [];
    const closed = pluginsInPlaceholder.filter((id) => {
        if (id === undefined || id === null) return false;
        return !opened.some((o) => o === id);
    });

    const allClosedAreLeaves = closed.every((id) => {
        return !allDescriptors.some(
            ([, o]) =>
                o.placeholder_id === placeholderId && o.plugin_parent === id,
        );
    });

    const dragbarTitle = document.querySelector<HTMLElement>(
        `.cms-dragarea-${placeholderId} .cms-dragbar-title`,
    );

    if (!Array.isArray(settings.dragbars)) settings.dragbars = [];

    if (allClosedAreLeaves) {
        dragbarTitle?.classList.add('cms-dragbar-title-expanded');
        if (!settings.dragbars.includes(placeholderId)) {
            settings.dragbars.push(placeholderId);
        }
    } else {
        dragbarTitle?.classList.remove('cms-dragbar-title-expanded');
        const idx = settings.dragbars.indexOf(placeholderId);
        if (idx >= 0) settings.dragbars.splice(idx, 1);
    }
}

// ────────────────────────────────────────────────────────────────────
// Internal helpers
// ────────────────────────────────────────────────────────────────────

/**
 * `el.querySelector(':scope > selector')` is the standards-compliant
 * version. Wrap so callers don't have to remember the prefix.
 */
function directChild(
    el: Element | null | undefined,
    selector: string,
): HTMLElement | null {
    if (!el) return null;
    return el.querySelector<HTMLElement>(`:scope > ${selector}`);
}

function parseDraggableId(el: Element | null): number | string | undefined {
    if (!el) return undefined;
    for (const cls of Array.from(el.classList)) {
        const match = /^cms-draggable-(\d+)$/.exec(cls);
        if (match && match[1]) return Number(match[1]);
    }
    return undefined;
}

/**
 * Persist settings via Helpers.setSettings, swallowing the
 * "localStorage required" error so the toggle still works visually
 * in environments where storage is disabled. Matches the legacy
 * forgiving behaviour (legacy fell back to sync-ajax which we've
 * dropped).
 */
function persistSettings(settings: Record<string, unknown>): void {
    try {
        Helpers.setSettings(settings);
    } catch {
        /* localStorage unavailable — visual state still applied */
    }
}

export const _internals = { directChild, parseDraggableId };
