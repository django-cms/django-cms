/*
 * Settings menu — the dropdown that pops out next to a plugin's drag
 * handle (and the placeholder dragbar) with edit / copy / cut / paste /
 * delete / add actions.
 *
 * Mirrors legacy `_setSettingsMenu`, `_showSettingsMenu`,
 * `Plugin._hideSettingsMenu`, `_setupActions`, `_delegate`. Native
 * pointer + click handling, no jQuery.
 *
 * Action dispatch
 * ───────────────
 * Clicking an item in the dropdown reads `data-rel` from the link and
 * routes to the matching Plugin method (`editPlugin`, `copyPlugin`,
 * `cutPlugin`, etc.). Optional-chained because tests pass partial
 * fixtures; the real Plugin class implements them all (2g).
 *
 * Positioning
 * ───────────
 * Legacy used jQuery `.offset()` + `.height()` against `$(window)`.
 * Native equivalents are `getBoundingClientRect()` + `offsetHeight` +
 * `window.innerHeight` + `window.scrollY`. The class swap is the same:
 * `cms-submenu-dropdown-top` (drop downward) vs
 * `cms-submenu-dropdown-bottom` (drop upward) when there's no room
 * below.
 */

import { hideLoader, showLoader } from '../../loader';
import { getClipboard, getToolbar } from '../cms-globals';
import { bumpUsageCount } from '../registry';
import type { PluginInstance } from '../types';

void getClipboard;

/**
 * Surface the Plugin class methods this module forwards to. The
 * methods are optional because the menu can be wired against any
 * `PluginInstance` (vitest fixtures, partial test doubles) — the
 * full Plugin class implements them all in 2g.
 */
interface PluginCallable extends PluginInstance {
    addPlugin?: (
        type: string,
        name: string,
        parent?: number | string,
        showAddForm?: boolean,
        position?: number,
    ) => void;
    editPlugin?: (url: string, name?: string, breadcrumb?: unknown[]) => void;
    copyPlugin?: (opts?: PluginInstance['options'], sourceLanguage?: string) => unknown;
    cutPlugin?: () => unknown;
    pastePlugin?: () => unknown;
    deletePlugin?: (url: string, name?: string, breadcrumb?: unknown[]) => void;
    editPluginPostAjax?: (toolbar: unknown, response: unknown) => void;
    /** Optional — present on real Plugin instances (lands in 2g). */
    _getPluginBreadcrumbs?: () => unknown[];
    options: PluginInstance['options'] & { plugin_name?: string };
}

/**
 * Wire the trigger button (`nav`) to open / close the dropdown,
 * delegate dropdown action clicks, and stop propagation on a few
 * touch / pointer paths so legacy DnD glue still works.
 *
 * Returns the resolved `dropdown` element (or null) so the caller can
 * stash it in `plugin.ui.dropdown` for later teardown.
 */
export function setupSettingsMenu(
    plugin: PluginCallable,
    nav: HTMLElement,
    signal?: AbortSignal,
): HTMLElement | null {
    const opts = signal ? { signal } : undefined;

    // The dropdown lives as a sibling of the trigger — same layout
    // as the legacy `nav.siblings('.cms-submenu-dropdown-settings')`.
    const dropdown = findSibling(nav, '.cms-submenu-dropdown-settings');

    // Trigger pointerup → toggle.
    nav.addEventListener(
        'pointerup',
        (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (nav.classList.contains('cms-btn-active')) {
                hideSettingsMenu(nav);
            } else {
                hideSettingsMenu();
                showSettingsMenu(nav, dropdown);
            }
        },
        opts,
    );

    // Trigger touchstart: stopPropagation so legacy DnD on the
    // dragbar doesn't fire pointercancel.
    nav.addEventListener(
        'touchstart',
        (e) => e.stopPropagation(),
        opts,
    );

    // Dropdown swallows mouse + touch events so clicks inside the
    // dropdown don't bubble out and re-close it.
    if (dropdown) {
        for (const type of [
            'mousedown',
            'mousemove',
            'mouseup',
            'touchstart',
        ]) {
            dropdown.addEventListener(
                type,
                (e) => e.stopPropagation(),
                opts,
            );
        }
    }

    // Action click handlers — legacy `_setupActions`.
    setupActions(plugin, nav, opts);

    // Trigger click/dblclick/pointerup/pointerdown swallowed so the
    // surrounding draggable doesn't react.
    for (const type of ['click', 'dblclick', 'pointerup', 'pointerdown']) {
        nav.addEventListener(
            type,
            (e) => e.stopPropagation(),
            opts,
        );
    }

    // Quicksearch + dropdown also swallow clicks (legacy guard).
    const quicksearch = findSibling(nav, '.cms-quicksearch');
    for (const target of [quicksearch, dropdown]) {
        if (!target) continue;
        for (const type of ['pointerup', 'click', 'dblclick']) {
            target.addEventListener(
                type,
                (e) => e.stopPropagation(),
                opts,
            );
        }
    }

    return dropdown;
}

/**
 * Open the dropdown for `nav`. Adds the active-state classes and
 * positions the panel above or below based on viewport room.
 */
export function showSettingsMenu(
    nav: HTMLElement,
    dropdown?: HTMLElement | null,
): void {
    const panel = dropdown ?? findSibling(nav, '.cms-submenu-dropdown-settings');
    nav.classList.add('cms-btn-active');

    // Add z-bump to every ancestor up to the dragarea, matching the
    // legacy `parents.parentsUntil('.cms-dragarea').last()` walk.
    const dragarea = nav.closest('.cms-dragarea');
    let walker: HTMLElement | null = nav.parentElement;
    let topAncestor: HTMLElement | null = null;
    while (walker && walker !== dragarea && walker !== document.body) {
        topAncestor = walker;
        walker = walker.parentElement;
    }
    topAncestor?.classList.add('cms-z-index-9999');

    if (!panel) return;

    // Legacy `.cms-submenu-dropdown-settings` hides via `display: none`.
    // The `--open` modifier (components/_visibility.scss) wins on
    // specificity and reveals the panel.
    panel.classList.add('cms-submenu-dropdown-settings--open');
    panel.removeAttribute('hidden');

    // Positioning
    const MIN_SCREEN_MARGIN = 10;
    const navRect = nav.getBoundingClientRect();
    const dropdownHeight = panel.offsetHeight;
    const viewportBottom = window.innerHeight;

    const noRoomBelow =
        viewportBottom - navRect.top - dropdownHeight <= MIN_SCREEN_MARGIN;
    const roomAbove = navRect.top - dropdownHeight >= 0;

    if (noRoomBelow && roomAbove) {
        panel.classList.remove('cms-submenu-dropdown-top');
        panel.classList.add('cms-submenu-dropdown-bottom');
    } else {
        panel.classList.remove('cms-submenu-dropdown-bottom');
        panel.classList.add('cms-submenu-dropdown-top');
    }
}

/**
 * Close any open settings menu. With no argument, walks the DOM for
 * the active button. Mirrors the static `Plugin._hideSettingsMenu`.
 */
export function hideSettingsMenu(navEl?: HTMLElement | null): void {
    const nav = navEl
        ?? document.querySelector<HTMLElement>('.cms-submenu-btn.cms-btn-active');
    if (!nav) return;
    nav.classList.remove('cms-btn-active');

    // Drop the legacy "active" data flag on the closest draggable.
    const draggable = nav.closest('.cms-draggable');
    if (draggable) {
        // We use elementData via the cms-data wrapper for `cms`; for
        // arbitrary keys like `active` we fall back to dataset to keep
        // the doc surface narrow (legacy used jQuery's data store).
        delete (draggable as HTMLElement).dataset.active;
    }
    document
        .querySelectorAll<HTMLElement>('.cms-z-index-9999')
        .forEach((el) => el.classList.remove('cms-z-index-9999'));

    // Hide the dropdown + quicksearch siblings. Removing the `--open`
    // modifier on the panel restores the base `display: none` rule;
    // `.cms-quicksearch` has its own base hide rule so no extra class
    // is needed.
    const root = nav.parentElement;
    if (root) {
        root.querySelectorAll<HTMLElement>('.cms-submenu-dropdown').forEach(
            (el) => {
                el.classList.remove('cms-submenu-dropdown-settings--open');
            },
        );
        root.querySelectorAll<HTMLElement>('.cms-quicksearch').forEach((el) => {
            const input = el.querySelector<HTMLInputElement>('input');
            if (input) {
                input.value = '';
                input.dispatchEvent(new Event('keyup'));
                input.blur();
            }
        });
    }

    // Reset relative positioning the legacy code added.
    document
        .querySelectorAll<HTMLElement>('.cms-dragbar')
        .forEach((el) => {
            el.style.position = '';
        });
}

// ────────────────────────────────────────────────────────────────────
// Action delegation
// ────────────────────────────────────────────────────────────────────

/**
 * Wire `click` listeners on every action item (`.cms-submenu-edit`,
 * `.cms-submenu-item a`) under the trigger's parent. Each click runs
 * through `delegateAction`.
 */
function setupActions(
    plugin: PluginCallable,
    nav: HTMLElement,
    opts: AddEventListenerOptions | undefined,
): void {
    const parent = nav.parentElement;
    if (!parent) return;

    // Actions: edit + every link inside a .cms-submenu-item.
    const actionSelector = '.cms-submenu-edit, .cms-submenu-item a';
    parent.querySelectorAll<HTMLElement>(actionSelector).forEach((el) => {
        el.addEventListener(
            'click',
            (e) => delegateAction(plugin, nav, e),
            opts,
        );
    });

    // Edit button swallows touchstart so it doesn't kick off a drag.
    parent.querySelectorAll<HTMLElement>('.cms-submenu-edit').forEach((el) => {
        el.addEventListener(
            'touchstart',
            (e) => e.stopPropagation(),
            opts,
        );
    });
}

/**
 * Action click handler — reads `data-rel` from the matched element
 * and dispatches to the right Plugin method (or to the toolbar /
 * highlighter for a few cases). Mirrors legacy `_delegate`.
 *
 * Defensive throughout: every Plugin method this calls is optional
 * because they land in 2g. When they're missing, the action is a
 * no-op (loader hidden, menu closed).
 */
export function delegateAction(
    plugin: PluginCallable,
    nav: HTMLElement,
    e: Event,
): void {
    e.preventDefault();
    e.stopPropagation();

    showLoader();

    const target = e.target as Element | null;
    const item = target?.closest<HTMLElement>(
        '.cms-submenu-edit, .cms-submenu-item a',
    );
    hideSettingsMenu(nav);

    if (!item) {
        hideLoader();
        return;
    }

    const rel = item.getAttribute('data-rel') ?? '';
    switch (rel) {
        case 'add': {
            const href = item.getAttribute('href') ?? '';
            const pluginType = href.replace('#', '');
            const showAddForm = item.dataset.addForm !== 'false';
            bumpUsageCount(pluginType);
            const picker = item.closest<HTMLElement>('.cms-plugin-picker');
            const parentRaw = picker?.dataset.parentId;
            const parentId = parentRaw ? Number(parentRaw) : undefined;
            plugin.addPlugin?.(
                pluginType,
                item.textContent ?? '',
                parentId,
                showAddForm,
            );
            break;
        }
        case 'ajax_add': {
            const toolbar = getToolbar() as
                | {
                      openAjax?: (opts: {
                          url: string;
                          post: string;
                          text: string;
                          callback: unknown;
                          onSuccess: unknown;
                      }) => void;
                  }
                | undefined;
            toolbar?.openAjax?.({
                url: item.getAttribute('href') ?? '',
                post: item.dataset.post ?? '',
                text: item.dataset.text ?? '',
                callback: plugin.editPluginPostAjax?.bind(plugin),
                onSuccess: item.dataset.onSuccess,
            });
            break;
        }
        case 'edit':
            plugin.editPlugin?.(
                plugin.options.urls?.edit_plugin ?? '',
                plugin.options.plugin_name,
                plugin._getPluginBreadcrumbs?.() ?? [],
            );
            break;
        case 'copy-lang':
            plugin.copyPlugin?.(
                plugin.options,
                item.getAttribute('data-language') ?? undefined,
            );
            break;
        case 'copy':
            if (item.parentElement?.classList.contains('cms-submenu-item-disabled')) {
                hideLoader();
            } else {
                plugin.copyPlugin?.();
            }
            break;
        case 'cut':
            plugin.cutPlugin?.();
            break;
        case 'paste':
            hideLoader();
            if (!item.parentElement?.classList.contains('cms-submenu-item-disabled')) {
                plugin.pastePlugin?.();
            }
            break;
        case 'delete':
            plugin.deletePlugin?.(
                plugin.options.urls?.delete_plugin ?? '',
                plugin.options.plugin_name,
                plugin._getPluginBreadcrumbs?.() ?? [],
            );
            break;
        case 'highlight': {
            hideLoader();
            const pluginId = plugin.options.plugin_id;
            if (pluginId !== undefined && pluginId !== null) {
                window.location.hash = `cms-plugin-${pluginId}`;
                // Plugin._highlightPluginContent lands in 2f.
            }
            e.stopImmediatePropagation();
            break;
        }
        default: {
            hideLoader();
            const toolbar = getToolbar() as
                | { _delegate?: (el: HTMLElement) => void }
                | undefined;
            toolbar?._delegate?.(item);
        }
    }
}

// ────────────────────────────────────────────────────────────────────
// DOM helpers
// ────────────────────────────────────────────────────────────────────

/**
 * Find the first sibling of `el` matching `selector`. Tiny native
 * replacement for jQuery's `.siblings('.x')`.
 */
function findSibling(
    el: HTMLElement,
    selector: string,
): HTMLElement | null {
    const parent = el.parentElement;
    if (!parent) return null;
    for (const child of Array.from(parent.children)) {
        if (child !== el && child.matches(selector)) {
            return child as HTMLElement;
        }
    }
    return null;
}

export const _internals = { findSibling, setupActions };
