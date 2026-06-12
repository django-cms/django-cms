/*
 * StructureBoard drag-and-drop adapter.
 *
 * Replaces the legacy `_drag` / `_dragRefresh` pair (jQuery UI
 * `nestedSortable` based) with a thin shell over the shared
 * `tree/drag.ts` (`TreeDrag`) controller. This is the FIRST consumer
 * of TreeDrag's multi-container code path — every `.cms-draggables`
 * list (including the clipboard's) is registered as a peer container.
 *
 * Mapping of legacy nestedSortable knobs to TreeDrag (CLAUDE.md §3 + the
 * inventory's "9. DnD coupling" table):
 *
 *   items: '.cms-draggable:not(.cms-drag-disabled):not(.cms-draggable-
 *           disabled .cms-draggable)'  → `canDrag`
 *   connectWith: '.cms-draggables:not(.cms-hidden)'
 *           → `containers: HTMLElement[]` (multi)
 *   isAllowed                          → `canDropAsChild`
 *   update                             → `onDrop` (this module mutates
 *                                                  the DOM, then
 *                                                  dispatches the
 *                                                  `cms-plugins-update` /
 *                                                  `cms-paste-plugin-
 *                                                  update` event the
 *                                                  Plugin layer is
 *                                                  already listening
 *                                                  for)
 *
 * Important divergence from legacy: TreeDrag does NOT mutate the DOM
 * during drag. The dragged node stays put until pointerup, and onDrop
 * does the move. That means the post-drop event dispatch path matches
 * legacy semantics — the listener in `plugins/plugin.ts` reads the
 * NEW position from the DOM after we've moved the node — but the
 * "during drag, source container collapses" jQuery UI behaviour is
 * gone (intentional; it caused reflow churn).
 *
 * Empty-placeholder caveat: TreeDrag derives drop targets from rendered
 * row positions across all containers. An empty `.cms-draggables` (no
 * `.cms-draggable` rows) contributes no rows, so the user can't drop
 * INTO an empty placeholder via this controller. Legacy worked around
 * this with `dropOnEmpty: true`. Wiring an empty-container affordance
 * (e.g. a synthetic drop row) is deferred to a later sub-phase — first
 * we land the happy path.
 */

import TreeDrag, {
    type TreeDragOptions,
    type TreeDropResult,
} from '../../tree/drag';
import { getCmsLocked, getStructureBoard } from '../../plugins/cms-globals';
import { getPlaceholderData, getPluginData } from '../../plugins/cms-data';
import {
    actualizePlaceholders,
    actualizePluginsCollapsibleStatus,
} from '../dom/actualize';
import {
    parseDragareaId,
    parseDraggableId,
} from '../parsers/ids';

/**
 * Build the drag clone for the structureboard. Cloning the
 * `.cms-draggable` directly (rather than wrapping in a `<ul>` shell
 * like the pagetree does) keeps the clone styled by the existing
 * legacy `_structureboard.scss` rules — `.cms-structure
 * .cms-draggable .cms-dragitem`, the `cms-draggable-is-dragging`
 * orange highlight, and the `ui-sortable-helper.cms-draggable
 * .cms-submenu-btn { display: none }` rule that hides the submenu
 * trigger.
 *
 * Children list (`.cms-draggables`) is stripped — the clone shows
 * only the row of the plugin being dragged, matching the pagetree
 * UX where the floating clone is just the dragged page row, not its
 * subtree.
 */
function buildStructureBoardClone(item: HTMLElement): HTMLElement {
    const rect = item.getBoundingClientRect();
    const clone = item.cloneNode(true) as HTMLElement;
    // Drop nested children so the floating clone is just the
    // dragged item's row, like the pagetree.
    clone
        .querySelectorAll<HTMLElement>('.cms-draggables')
        .forEach((el) => el.remove());
    // Pull legacy classes the structureboard SCSS already styles. We
    // keep the source's existing class list (e.g. `cms-draggable-X`)
    // and add the dragging + helper hooks.
    clone.classList.add('cms-draggable-is-dragging', 'ui-sortable-helper');
    // Disable interaction on the clone (it's a visual proxy only).
    clone.style.cssText = [
        'position: fixed',
        'pointer-events: none',
        'z-index: 9999',
        'opacity: 0.85',
        `width: ${rect.width}px`,
    ].join(';');
    return clone;
}

/**
 * Selector for participating drop containers. Mirrors the legacy
 * `ui.sortables` filter — clipboard's `.cms-draggables` is included
 * (so users can drag FROM clipboard); only `.cms-drag-disabled`
 * containers are excluded.
 */
const CONTAINER_SELECTOR = '.cms-draggables:not(.cms-drag-disabled)';

const ITEM_SELECTOR = '.cms-draggable';
const ROW_SELECTOR = '.cms-dragitem';
const HANDLE_SELECTOR = '.cms-dragitem';

/**
 * Indent step for TreeDrag's depth math. Structureboard nests draggables
 * inside `.cms-collapsable-container > .cms-draggables`; visual depth
 * varies by CSS but 24px is a reasonable nominal step.
 */
const DEPTH_PX = 24;

/**
 * Decide whether a `.cms-draggable` can start a drag. Mirrors the
 * legacy `nestedSortable.items` selector predicate:
 *   `.cms-draggable:not(.cms-drag-disabled):not(.cms-draggable-disabled .cms-draggable)`
 *
 * Plus a short-circuit when CMS.API.locked is set (the legacy
 * `isAllowed` did this; the items predicate didn't, but locking the
 * source-side too is cheaper and avoids spurious clones).
 */
export function canDrag(item: HTMLElement): boolean {
    if (getCmsLocked()) return false;
    if (item.classList.contains('cms-drag-disabled')) return false;
    // Walk ancestors up to the placeholder; any `.cms-draggable-disabled`
    // ancestor blocks the drag.
    let cursor: HTMLElement | null = item.parentElement;
    while (cursor && !cursor.classList.contains('cms-dragarea')) {
        if (cursor.classList.contains('cms-draggable-disabled')) return false;
        cursor = cursor.parentElement;
    }
    return true;
}

/**
 * Decide whether `item` may land as a child of `target`. Direct port
 * of the legacy `isAllowed` predicate.
 *
 * Reads:
 *   - dragged item's `data('cms')` → `plugin_type`,
 *     `plugin_parent_restriction`
 *   - target draggable's `data('cms')` → `plugin_restriction`,
 *     `plugin_type` (when target is a draggable)
 *   - placeholder element's `data('cms')` → fallback when the target
 *     has no parent draggable (drop at placeholder root)
 *
 * Returns false when:
 *   - CMS.API.locked
 *   - target is in the clipboard (you can't drop INTO clipboard)
 *   - target's container has cms-drag-disabled / cms-draggable-disabled
 *   - the dragged plugin's `plugin_type` isn't in the target's
 *     `plugin_restriction`
 *   - the target's `plugin_type` isn't in the dragged plugin's
 *     `plugin_parent_restriction` (when present)
 */
export function canDropAsChild(target: HTMLElement, item: HTMLElement): boolean {
    if (getCmsLocked()) return false;
    if (target.closest('.cms-clipboard-containers')) return false;

    const targetList = target.parentElement;
    if (targetList?.classList.contains('cms-drag-disabled')) return false;
    if (targetList?.classList.contains('cms-draggable-disabled')) return false;

    // Source plugin descriptor (array shape; pick the first).
    const itemData = getPluginData(item)?.[0];
    if (!itemData) return false;

    const itemType =
        typeof itemData.plugin_type === 'string' ? itemData.plugin_type : undefined;
    const parentRestriction =
        Array.isArray(itemData.plugin_parent_restriction)
            ? (itemData.plugin_parent_restriction as string[]).filter(
                  (r) => r !== '0',
              )
            : [];

    // Target context — prefer the immediate parent draggable's data; if
    // the target is a placeholder-root drop, fall back to the
    // placeholder element's data.
    const targetData = getPluginData(target)?.[0];
    let bounds: string[] = [];
    let immediateParentType: string | undefined;
    if (targetData) {
        if (Array.isArray(targetData.plugin_restriction)) {
            bounds = targetData.plugin_restriction as string[];
        }
        if (typeof targetData.plugin_type === 'string') {
            immediateParentType = targetData.plugin_type;
        }
    } else {
        const dragarea = target.closest<HTMLElement>('.cms-dragarea');
        const dragareaId = dragarea ? parseDragareaId(dragarea) : undefined;
        if (dragareaId !== undefined) {
            const placeholder = document.querySelector<HTMLElement>(
                `.cms-placeholder-${dragareaId}`,
            );
            if (placeholder) {
                const phData = getPlaceholderData(placeholder);
                if (Array.isArray(phData?.plugin_restriction)) {
                    bounds = phData?.plugin_restriction as string[];
                }
                if (typeof phData?.plugin_type === 'string') {
                    immediateParentType = phData.plugin_type;
                }
            }
        }
    }

    // plugin_restriction: the dragged item's plugin_type must be in
    // the bounds (when bounds is non-empty).
    let allowed = !(itemType !== undefined && bounds.length > 0 && !bounds.includes(itemType));

    // plugin_parent_restriction: the target's plugin_type must be in
    // the dragged item's parent_restriction (when non-empty).
    if (parentRestriction.length > 0) {
        allowed =
            immediateParentType !== undefined &&
            parentRestriction.includes(immediateParentType);
    }
    return allowed;
}

/**
 * Commit the drop: mutate the DOM to match the prospective placement,
 * then dispatch the `cms-plugins-update` / `cms-paste-plugin-update`
 * event so the Plugin layer fires its move/paste mutation.
 *
 * Mirrors legacy `_drag().update`. Three placement kinds:
 *   - `'child'`     → append into reference's `.cms-draggables`
 *   - `'sibling-before'` → insert before reference
 *   - `'sibling-after'`  → insert after reference
 *
 * Source-vs-clipboard branching:
 *   - When the dragged item came from `.cms-clipboard-containers`,
 *     dispatch `cms-paste-plugin-update`. The legacy flow then re-
 *     populates the clipboard with a clone — we leave that to the
 *     caller (will be wired in the StructureBoard class shell once
 *     `_updateClipboard` is ported in Phase 4).
 *   - Otherwise dispatch `cms-plugins-update`. The Plugin instance for
 *     the moved draggable already has a listener wired in
 *     `plugins/plugin.ts` and will compute the new position from the
 *     live DOM.
 */
export function onDrop(result: TreeDropResult): void {
    const { item, kind, reference, anchor } = result;
    const fromClipboard = item.closest('.cms-clipboard-containers') !== null;
    const originalContainer = item.closest<HTMLElement>('.cms-draggables');

    let targetList: HTMLElement | null;
    let insertBefore: Element | null = null;

    if (kind === 'child') {
        // Drop INTO reference (as its first child of `.cms-draggables`).
        targetList = reference.querySelector<HTMLElement>(
            ':scope > .cms-draggables',
        );
        if (!targetList) {
            // No children list yet — create one. Append after the
            // dragitem so the new draggable lands in the visually-
            // correct slot.
            targetList = document.createElement('div');
            targetList.className = 'cms-draggables';
            const dragitem = reference.querySelector<HTMLElement>(
                ':scope > .cms-dragitem',
            );
            if (dragitem?.nextSibling) {
                reference.insertBefore(targetList, dragitem.nextSibling);
            } else {
                reference.appendChild(targetList);
            }
        }
    } else if (kind === 'sibling-before') {
        // Sibling placement uses `anchor`, not `reference`. For outdent
        // drops anchor is the ancestor at the chosen depth (see
        // tree/drag.ts::updateProspective); reference still points at
        // the visually-nearest row, which would re-introduce the dragged
        // item at the wrong depth and ignore the indent picked by the
        // user. Mirrors pagetree's `onTreeDrop` (pagetree.ts:746).
        targetList = anchor.parentElement as HTMLElement | null;
        insertBefore = anchor;
    } else {
        // sibling-after — same anchor-vs-reference reasoning.
        targetList = anchor.parentElement as HTMLElement | null;
        insertBefore = anchor.nextElementSibling;
    }

    if (!targetList) return;

    if (insertBefore) {
        targetList.insertBefore(item, insertBefore);
    } else {
        targetList.appendChild(item);
    }

    // Cross-container moves invalidate the collapsible state on both
    // the source and destination lists.
    const newContainer = item.closest<HTMLElement>('.cms-draggables');
    if (
        originalContainer &&
        newContainer &&
        originalContainer !== newContainer
    ) {
        actualizePluginsCollapsibleStatus([originalContainer, newContainer]);
    }

    // Dispatch the right event — listened to by the Plugin instance
    // bound to this draggable (`cms-plugins-update` calls
    // `movePlugin`; `cms-paste-plugin-update` re-derives target +
    // marks `move_a_copy`).
    const id = parseDraggableId(item);
    if (id !== undefined) {
        const detail: { id: number; previousParentPluginId?: number } = { id };
        const previousParent = originalContainer?.closest<HTMLElement>(ITEM_SELECTOR);
        if (previousParent) {
            const ppid = parseDraggableId(previousParent);
            if (ppid !== undefined) detail.previousParentPluginId = ppid;
        }
        const eventName = fromClipboard
            ? 'cms-paste-plugin-update'
            : 'cms-plugins-update';
        item.dispatchEvent(
            new CustomEvent(eventName, { detail, bubbles: true }),
        );
    }

    actualizePlaceholders();
}

/**
 * Handle returned by `setupStructureBoardDnd` — call `refresh()` after
 * structure mutations that add/remove placeholders (so TreeDrag
 * re-scans the participating containers); call `destroy()` to detach.
 */
export interface StructureBoardDndHandle {
    refresh(): void;
    destroy(): void;
}

/**
 * Wire TreeDrag with the structureboard callbacks. Returns a handle so
 * the caller can refresh on structure rerender or destroy on unload.
 *
 * Pass `host` when the participating containers don't share a parent
 * (the structureboard's `.cms-structure-content` is the typical host).
 */
export function setupStructureBoardDnd(
    opts: { host?: HTMLElement } = {},
): StructureBoardDndHandle {
    let drag: TreeDrag | null = null;

    const build = (): void => {
        const containers = Array.from(
            document.querySelectorAll<HTMLElement>(CONTAINER_SELECTOR),
        );
        if (containers.length === 0) {
            drag = null;
            return;
        }
        const treeOpts: TreeDragOptions = {
            containers,
            handleSelector: HANDLE_SELECTOR,
            itemSelector: ITEM_SELECTOR,
            rowSelector: ROW_SELECTOR,
            depthPx: DEPTH_PX,
            canDrag,
            canDropAsChild,
            onDrop,
            // Mirror legacy `cms.structureboard.js::start/beforeStop`:
            // flip `StructureBoard.dragging` so unrelated UI consults
            // it. Plugin's shift-hover highlight (plugins/plugin.ts)
            // checks `sb.dragging` to suppress overlays mid-drag —
            // without these hooks, hover crosstalk paints highlight
            // overlays while a plugin is being dragged.
            onDragStart: () => {
                const sb = getStructureBoard();
                if (sb) sb.dragging = true;
            },
            onDragEnd: () => {
                const sb = getStructureBoard();
                if (sb) sb.dragging = false;
            },
            // Use legacy structureboard SCSS classes for the visual
            // feedback — the source item flips to
            // `.cms-draggable-is-dragging` (orange highlight from
            // `_structureboard.scss`) and the clone wears
            // `cms-draggable-is-dragging ui-sortable-helper` so the
            // legacy "hide submenu/children on the clone" rules apply.
            sourceClass: 'cms-draggable-is-dragging',
            cloneRenderer: buildStructureBoardClone,
        };
        if (opts.host) treeOpts.host = opts.host;
        drag = new TreeDrag(treeOpts);
    };

    build();

    return {
        refresh(): void {
            drag?.destroy();
            build();
        },
        destroy(): void {
            drag?.destroy();
            drag = null;
        },
    };
}
