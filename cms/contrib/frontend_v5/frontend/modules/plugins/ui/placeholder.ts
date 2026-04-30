/*
 * Placeholder dragbar wiring: toggler links for collapse/expand,
 * persisted-state restoration, plus seams for the menu and add-plugin
 * modal which land in 2d/2e.
 *
 * Mirrors legacy `_setPlaceholder`. The settings-menu and add-plugin
 * modal hookups are stubs here — `setupSettingsMenu` and
 * `setupAddPluginModal` get implemented in their own modules and
 * called from this file.
 */

import { getCmsSettings } from '../cms-globals';
import type { PluginInstance } from '../types';
import { collapseAll, expandAll } from './collapse';

export interface PlaceholderUi {
    dragbar: HTMLElement | null;
    draggables: HTMLElement | null;
    submenu: HTMLElement | null;
    addSubmenu: HTMLElement | null;
}

/**
 * Resolve the dragbar / draggables / submenu / add-plugin-button
 * elements for a placeholder. Returns nullable references so the
 * caller can decide whether the wiring is even possible (a stripped
 * dragbar means no placeholder UI on this page).
 */
export function resolvePlaceholderUi(
    placeholderId: number | string,
): PlaceholderUi {
    const dragbar = document.querySelector<HTMLElement>(
        `.cms-dragbar-${placeholderId}`,
    );
    const dragarea = dragbar?.closest<HTMLElement>('.cms-dragarea');
    return {
        dragbar,
        draggables: dragarea?.querySelector<HTMLElement>(':scope > .cms-draggables') ?? null,
        submenu: dragbar?.querySelector<HTMLElement>('.cms-submenu-settings') ?? null,
        addSubmenu: dragbar?.querySelector<HTMLElement>('.cms-submenu-add') ?? null,
    };
}

/**
 * Wire placeholder dragbar events. Returns the resolved UI so the
 * caller can stash it on the plugin's `ui` object for later
 * teardown / settings-menu wiring.
 */
export function setupPlaceholderEvents(
    plugin: PluginInstance,
    signal?: AbortSignal,
): PlaceholderUi {
    const placeholderId = plugin.options.placeholder_id;
    if (placeholderId === undefined || placeholderId === null) {
        return {
            dragbar: null,
            draggables: null,
            submenu: null,
            addSubmenu: null,
        };
    }

    const ui = resolvePlaceholderUi(placeholderId);
    if (!ui.dragbar) return ui;

    const opts = signal ? { signal } : undefined;
    const title = ui.dragbar.querySelector<HTMLElement>('.cms-dragbar-title');
    const togglerLinks = ui.dragbar.querySelectorAll<HTMLAnchorElement>(
        '.cms-dragbar-toggler a',
    );
    const expandedClass = 'cms-dragbar-title-expanded';

    // Settings array for restoring expand state across reloads.
    const settings = getCmsSettings();
    if (!Array.isArray(settings.dragbars)) settings.dragbars = [];

    // Apply persisted state first.
    if (
        title &&
        settings.dragbars?.some((id) => Number(id) === Number(placeholderId))
    ) {
        title.classList.add(expandedClass);
    }

    // Wire the toggler links: clicking expands/collapses every
    // collapsable item under this placeholder, mirroring legacy
    // `_expandAll` / `_collapseAll`.
    togglerLinks.forEach((link) => {
        link.addEventListener(
            'click',
            (e) => {
                e.preventDefault();
                if (!title) return;
                if (title.classList.contains(expandedClass)) {
                    collapseAll(plugin, title);
                } else {
                    expandAll(plugin, title);
                }
            },
            opts,
        );
    });

    return ui;
}
