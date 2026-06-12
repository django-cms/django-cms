/*
 * DOM "actualisation" — read the registry / current state and apply
 * the resulting class flips on placeholder + draggable elements. No
 * network, no XHR.
 *
 * Mirrors legacy `actualizePlaceholders`, `actualizePluginCollapseStatus`,
 * `actualizePluginsCollapsibleStatus`, `_initializeDragItemsStates`,
 * plus three new helper extractions used by the per-action handlers
 * (3e/3f): `relocateDraggable`, `removeDraggable`, `insertDraggable`.
 */

import { getCmsSettings } from '../../plugins/cms-globals';

const PLACEHOLDER_SELECTOR = '.cms-dragarea:not(.cms-clipboard-containers)';

/**
 * Toggle every placeholder's `cms-dragarea-empty` / "copy-all
 * disabled" state based on whether it currently holds non-dragging
 * children. Also reorders the floating add-plugin placeholder so it
 * stays last in its parent.
 *
 * Mirrors legacy `actualizePlaceholders`.
 */
export function actualizePlaceholders(): void {
    const placeholders = document.querySelectorAll<HTMLElement>(
        PLACEHOLDER_SELECTOR,
    );
    placeholders.forEach((placeholder) => {
        const draggables = placeholder.querySelector<HTMLElement>(
            ':scope > .cms-draggables',
        );
        const draggableChildren = draggables
            ? Array.from(
                  draggables.querySelectorAll<HTMLElement>(':scope > .cms-draggable'),
              ).filter((el) => !el.classList.contains('cms-draggable-is-dragging'))
            : [];

        // The dragbar's "Copy All" item — disable when no plugins.
        const copyAll = placeholder
            .querySelector<HTMLElement>('.cms-dragbar')
            ?.querySelector<HTMLElement>(
                '.cms-submenu-item:has(a[data-rel="copy"])',
            );
        const copyAllAnchor = copyAll?.querySelector('a');

        if (draggableChildren.length > 0) {
            placeholder.classList.remove('cms-dragarea-empty');
            copyAll?.classList.remove('cms-submenu-item-disabled');
            copyAllAnchor?.removeAttribute('aria-disabled');
        } else {
            placeholder.classList.add('cms-dragarea-empty');
            copyAll?.classList.add('cms-submenu-item-disabled');
            copyAllAnchor?.setAttribute('aria-disabled', 'true');
        }
    });

    // The floating "plugin will be added here" indicator should be
    // the last child of its parent. After a structure mutation it can
    // end up mid-list; move it back.
    const indicator = document.querySelector<HTMLElement>(
        '.cms-dragarea .cms-add-plugin-placeholder',
    );
    if (indicator?.parentElement && indicator !== indicator.parentElement.lastElementChild) {
        indicator.parentElement.appendChild(indicator);
    }
}

/**
 * Restore the expand state of a single plugin's draggable from
 * `CMS.settings.states`. Only flips when:
 *   - the id IS in `states`, AND
 *   - the draggable actually has nested children to expand.
 *
 * Mirrors legacy `actualizePluginCollapseStatus`.
 */
export function actualizePluginCollapseStatus(
    pluginId: number | string,
): void {
    const el = document.querySelector<HTMLElement>(`.cms-draggable-${pluginId}`);
    if (!el) return;
    const states = getCmsSettings().states ?? [];
    const isOpen = (states as Array<number | string>).some(
        (id) => Number(id) === Number(pluginId),
    );
    if (!isOpen) return;

    const draggables = el.querySelector<HTMLElement>(':scope > .cms-draggables');
    if (!draggables) return;

    el.querySelector<HTMLElement>(':scope > .cms-collapsable-container')?.classList.remove('cms-hidden');
    el.querySelector<HTMLElement>(':scope > .cms-dragitem')?.classList.add('cms-dragitem-expanded');
}

/**
 * For each `.cms-draggables` in the given list, toggle the
 * surrounding plugin's `cms-dragitem-collapsable` class based on
 * whether children exist. Also flips `cms-dragitem-expanded` when
 * the children are visible.
 *
 * Mirrors legacy `actualizePluginsCollapsibleStatus`.
 */
export function actualizePluginsCollapsibleStatus(
    draggables: Iterable<Element>,
): void {
    for (const childList of draggables) {
        const draggable = childList.closest<HTMLElement>('.cms-draggable');
        const dragitem = draggable?.querySelector<HTMLElement>(
            ':scope > .cms-dragitem',
        );
        if (!dragitem) continue;

        const children = Array.from(childList.children);
        if (children.length > 0) {
            dragitem.classList.add('cms-dragitem-collapsable');
            // jsdom-friendly visibility check: an element is "visible"
            // if it doesn't have `cms-hidden` (which is how the toggle
            // happens). Legacy used jQuery `:visible` which is layout-
            // based.
            const anyVisible = children.some(
                (c) => !c.classList.contains('cms-hidden'),
            );
            if (anyVisible) dragitem.classList.add('cms-dragitem-expanded');
        } else {
            dragitem.classList.remove('cms-dragitem-collapsable');
        }
    }
}

/**
 * Dedupe `CMS.settings.states` and apply each entry's expand state
 * to its draggable. Idempotent — safe to re-run after structureboard
 * re-renders.
 *
 * Mirrors legacy `_initializeDragItemsStates`.
 */
export function initializeDragItemsStates(): void {
    const settings = getCmsSettings();
    const states = (settings.states ?? []) as Array<number | string>;

    // Dedup while preserving order: legacy used sort + neighbour-skip,
    // which loses order. A Set keyed on string preserves insertion
    // order and removes duplicates.
    const deduped: Array<number | string> = [];
    const seen = new Set<string>();
    for (const id of states) {
        const key = String(id);
        if (!seen.has(key)) {
            seen.add(key);
            deduped.push(id);
        }
    }
    settings.states = deduped;

    for (const id of deduped) {
        const el = document.querySelector<HTMLElement>(`.cms-draggable-${id}`);
        if (!el) continue;
        const collapsableContainer = el.querySelector<HTMLElement>(
            ':scope > .cms-collapsable-container',
        );
        // Only act if the container has at least one nested draggable.
        const nested = collapsableContainer?.querySelector(':scope > .cms-draggable');
        if (!nested) continue;
        collapsableContainer?.classList.remove('cms-hidden');
        el.querySelector<HTMLElement>(':scope > .cms-dragitem')?.classList.add(
            'cms-dragitem-expanded',
        );
    }
}

// ────────────────────────────────────────────────────────────────────
// Draggable mutation helpers (used by 3e/3f handlers)
// ────────────────────────────────────────────────────────────────────

/**
 * Append a new draggable's HTML into the target placeholder's
 * `.cms-draggables` list. Used by `handleAddPlugin` (root path) and
 * the cross-language paste path of `handleMovePlugin`.
 *
 * Returns the inserted `.cms-draggable` element if found in the
 * provided HTML, else null.
 */
export function insertDraggable(
    placeholderId: number | string,
    html: string,
): HTMLElement | null {
    const placeholder = document.querySelector<HTMLElement>(
        `.cms-dragarea-${placeholderId}`,
    );
    if (!placeholder) return null;
    const list = placeholder.querySelector<HTMLElement>(
        ':scope > .cms-draggables',
    );
    if (!list) return null;
    const before = list.children.length;
    list.insertAdjacentHTML('beforeend', html);
    return (list.children[before] as HTMLElement | undefined) ?? null;
}

/**
 * Move an existing draggable into the target placeholder. If
 * `pluginOrder` is provided, position the draggable at the correct
 * slot so DOM order matches the server response. When the
 * draggable is the clipboard original, it's cloned first (the
 * original stays in the clipboard).
 *
 * Used by `handleMovePlugin` for the root-path branch.
 *
 * Returns the relocated draggable (the in-DOM one), or null when
 * the source plugin couldn't be found.
 */
export function relocateDraggable(
    pluginId: number | string,
    placeholderId: number | string,
    pluginOrder: Array<number | string> | undefined,
): HTMLElement | null {
    // Multiple draggables can share the id during a paste-in-progress
    // — pick the LAST (the visually-moved one).
    const matches = document.querySelectorAll<HTMLElement>(
        `.cms-draggable-${pluginId}`,
    );
    let draggable = matches[matches.length - 1];
    if (!draggable) return null;

    const placeholder = document.querySelector<HTMLElement>(
        `.cms-dragarea-${placeholderId}`,
    );
    if (!placeholder) return null;
    const list = placeholder.querySelector<HTMLElement>(
        ':scope > .cms-draggables',
    );
    if (!list) return null;

    // Clipboard originals stay in place — clone for the destination.
    if (draggable.classList.contains('cms-draggable-from-clipboard')) {
        draggable = draggable.cloneNode(true) as HTMLElement;
    }

    if (pluginOrder && pluginOrder.length > 0) {
        const index = pluginOrder.findIndex(
            (id) => Number(id) === Number(pluginId) || id === '__COPY__',
        );
        if (index === 0) {
            list.insertBefore(draggable, list.firstChild);
        } else if (index > 0) {
            const prevId = pluginOrder[index - 1];
            const prevEl = list.querySelector<HTMLElement>(
                `.cms-draggable-${prevId}`,
            );
            if (prevEl) {
                prevEl.insertAdjacentElement('afterend', draggable);
            } else {
                list.appendChild(draggable);
            }
        } else {
            list.appendChild(draggable);
        }
    } else {
        list.appendChild(draggable);
    }

    return draggable;
}

/**
 * Options for `removeDraggable`. Default behaviour matches legacy
 * `handleDeletePlugin` (full wipe). The `keep*` flags exist for
 * `handleClearPlaceholder` (keeps rendered content + scripts because
 * the subsequent full-content refresh will replace them) and the
 * "delete with content bridge" path (legacy: `if (!contentData.content)`
 * skips the rendered-content removal, expecting the bridge to refresh
 * those nodes).
 */
export interface RemoveDraggableOptions {
    /**
     * Skip removal of `.cms-plugin.cms-plugin-<id>` rendered content
     * nodes. Used when the caller knows fresh content is about to be
     * applied (CLEAR_PLACEHOLDER, DELETE-with-content-bridge).
     */
    keepRenderedContent?: boolean;
    /**
     * Skip removal of `<script data-cms-plugin id="cms-plugin-<id>">`
     * JSON blobs. Used by CLEAR_PLACEHOLDER (full refresh re-renders
     * the placeholder, scripts included).
     */
    keepScript?: boolean;
}

/**
 * Remove a plugin's draggable wrapper from the structure tree. Also
 * removes its rendered `.cms-plugin-<id>` content nodes and the
 * `<script data-cms-plugin id="cms-plugin-<id>">` JSON blob unless
 * the corresponding `keep*` option is set.
 *
 * Returns the list of plugin ids removed (the target plus any
 * descendants that got dropped along with it).
 *
 * Used by `handleDeletePlugin` and `handleClearPlaceholder`. Does
 * NOT touch `CMS._plugins` / `CMS._instances` — that's the
 * registry's job (called separately).
 */
export function removeDraggable(
    pluginId: number | string,
    options: RemoveDraggableOptions = {},
): Array<number | string> {
    const removed: Array<number | string> = [pluginId];
    const draggable = document.querySelector<HTMLElement>(
        `.cms-draggable-${pluginId}`,
    );
    if (draggable) {
        // Collect descendant plugin ids before removing the wrapper.
        const nested = draggable.querySelectorAll<HTMLElement>('.cms-draggable');
        for (const el of Array.from(nested)) {
            for (const cls of Array.from(el.classList)) {
                const m = /^cms-draggable-(\d+)$/.exec(cls);
                if (m && m[1]) {
                    removed.push(Number(m[1]));
                    break;
                }
            }
        }
        draggable.remove();
    }

    for (const id of removed) {
        if (!options.keepRenderedContent) {
            document
                .querySelectorAll(`.cms-plugin.cms-plugin-${id}`)
                .forEach((el) => el.remove());
        }
        if (!options.keepScript) {
            document
                .querySelectorAll(
                    `script[data-cms-plugin]#cms-plugin-${id}`,
                )
                .forEach((el) => el.remove());
        }
    }

    return removed;
}

/** Test/migration hook: re-export selectors for vitest fixtures. */
export const _internals = {
    PLACEHOLDER_SELECTOR,
};
