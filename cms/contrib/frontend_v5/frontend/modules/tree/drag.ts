/*
 * TreeDrag — pointer-events-based drag-and-drop controller for
 * nested tree widgets.
 *
 * Design goals
 * ────────────
 * 1. **Do not mutate the tree DOM during drag.** The dragged node
 *    stays exactly where it was until pointerup. This is the jsTree
 *    model, and it's what lets us render a stable "prospective drop"
 *    marker without fighting a reflow on every mousemove tick.
 * 2. **One marker element** (absolutely positioned) shows where the
 *    item would land: either a row-highlight ("drop as child") or a
 *    horizontal line with triangle caps ("drop as sibling"). Depth
 *    of the sibling marker comes from cursor.x — every full 24px to
 *    the left of the anchor row outdents one level.
 * 3. **Commit on pointerup.** Emit one `onDrop` callback with the
 *    final placement — kind (child/sibling), the reference li, and
 *    the position within its parent. The caller is responsible for
 *    making the server call and reloading the tree. Between pointer-
 *    up and the reload, the DOM is unchanged.
 * 4. **Shared between pagetree and structureboard.** Per CLAUDE.md
 *    decision 6: "share primitives, not state machines". This module
 *    exposes a class that each screen instantiates with its own
 *    container + selectors + callbacks. No shared global state.
 * 5. **Touch works on iOS.** Pointer events unify mouse and touch;
 *    no separate touch handling path is needed. Legacy pagetree used
 *    jquery.ui.touchpunch to work around this for jstree+jquery-ui;
 *    we get it for free.
 *
 * What we *don't* do
 * ──────────────────
 * - HTML5 native drag-and-drop. Playwright can't synthesise it, iOS
 *   Safari won't fire `dragstart` from touch — see CLAUDE.md decision
 *   5. Pointer events are the only path that works everywhere.
 *
 * Multi-container support
 * ───────────────────────
 * The `containers` option accepts more than one tree root. With a
 * single entry the behaviour matches the original pagetree contract.
 * With multiple entries (the structureboard plugin tree case), drops
 * may span containers — `updateProspective` walks rows across all
 * registered containers in document order to pick the drop target.
 * The clone and marker attach to the shared `host` (defaults to the
 * first container's parentElement).
 */

export interface TreeDragOptions {
    /**
     * The tree roots that participate in this drag session. Pass one
     * for a single-tree screen (pagetree); pass several to enable
     * cross-container drop (structureboard plugin tree).
     */
    containers: HTMLElement[];

    /**
     * Where the drag clone and drop-marker get attached during a
     * drag. Defaults to `containers[0].parentElement`. Pass a
     * higher-up wrapper when multiple containers don't share a parent
     * (e.g. plugin tree's `.cms-structure-content` scroller).
     */
    host?: HTMLElement;

    /**
     * Selector for the drag handle element within a row. PointerDown
     * on a handle starts a drag; clicks elsewhere in the row are
     * ignored so link/button interactions still work.
     */
    handleSelector: string;

    /** Selector for a tree node (li). */
    itemSelector: string;

    /** Selector for the row element inside a node (the visible chrome). */
    rowSelector: string;

    /** Pixels per depth level — must match the CSS `padding-inline-start`. */
    depthPx: number;

    /**
     * Threshold in pixels the pointer must move before a click becomes
     * a drag. Prevents accidental drags from small mouse jitter.
     */
    dragThreshold?: number;

    /**
     * Called before a drag starts. Return false to veto (e.g. the
     * user doesn't have move permission for this node).
     */
    canDrag?: (item: HTMLElement) => boolean;

    /**
     * Called per pointermove to decide whether a row is a valid
     * drop-as-child target. Return false to block the row-highlight
     * for this specific target.
     */
    canDropAsChild?: (target: HTMLElement, item: HTMLElement) => boolean;

    /**
     * Called once on successful drop. The caller performs the server
     * call and reloads the tree. No DOM changes are made by this
     * module before onDrop fires.
     */
    onDrop: (result: TreeDropResult) => void | Promise<void>;

    /**
     * Customise the drag clone. Receives the dragged item; should
     * return an element to attach to `host`. The default implementation
     * wraps the cloned `rowSelector` element in a
     * `<ul class="cms-pagetree-list cms-tree-drag-clone">` shell — the
     * pagetree's CSS scoping requires it. The structureboard adapter
     * passes its own renderer because legacy structureboard SCSS
     * scopes rules differently and a different shell is needed.
     */
    cloneRenderer?: (item: HTMLElement) => HTMLElement;

    /**
     * Class added to the dragged source `<li>` for the lifetime of the
     * drag. Defaults to `cms-tree-dragging-item` (matches pagetree
     * SCSS). The structureboard adapter passes `cms-draggable-is-
     * dragging` so the legacy structureboard SCSS picks up the source
     * styling without any new CSS.
     */
    sourceClass?: string;
}

/** What the caller receives when a drop is committed. */
export interface TreeDropResult {
    /** The `<li>` the user was dragging. */
    item: HTMLElement;

    kind: 'child' | 'sibling-after' | 'sibling-before';

    /**
     * Reference node for the placement:
     * - `child` → the new parent li
     * - `sibling-after` → the li the dragged item should land AFTER
     * - `sibling-before` → the li the dragged item should land BEFORE
     */
    reference: HTMLElement;

    /**
     * The ancestor at the drop depth. Same as `reference` for child
     * drops; walked up from `reference` for outdented sibling drops.
     */
    anchor: HTMLElement;
}

interface DragState {
    item: HTMLElement;
    startX: number;
    startY: number;
    active: boolean; // true once we've crossed dragThreshold
    clone: HTMLElement | null;
    marker: HTMLElement | null;
    lastPointerX: number;
    lastPointerY: number;
    prospective: ProspectiveDrop | null;
}

interface ProspectiveDrop {
    kind: 'child' | 'sibling-after' | 'sibling-before';
    reference: HTMLElement;
    anchor: HTMLElement;
    /**
     * The DOM `<li>` or row element whose bounding-box is used for
     * visual positioning of the marker. For child drops, this is the
     * reference row. For sibling drops, this is the anchor row.
     */
    visualRef: HTMLElement;
    /** Target depth (for the sibling marker indentation). */
    depth: number;
    /**
     * How to render the prospective drop:
     *   - `highlight`: add `.cms-tree-drop-target` to the reference row
     *     (used when the cursor is in the middle 50% of a row).
     *   - `line-after`: render the line marker just BELOW the visualRef.
     *   - `line-before`: render the line marker just ABOVE the visualRef.
     */
    visualMode: 'highlight' | 'line-after' | 'line-before';
}

const DEFAULTS = {
    dragThreshold: 4,
};

export default class TreeDrag {
    private readonly opts: Omit<TreeDragOptions, 'dragThreshold'> & {
        dragThreshold: number;
    };

    private state: DragState | null = null;
    private readonly teardowns: Array<() => void> = [];

    constructor(options: TreeDragOptions) {
        this.opts = {
            dragThreshold: DEFAULTS.dragThreshold,
            ...options,
        };

        if (this.opts.containers.length === 0) {
            throw new Error('TreeDrag: at least one container is required.');
        }

        const onPointerDown = (e: PointerEvent) => this.onPointerDown(e);
        for (const c of this.opts.containers) {
            c.addEventListener('pointerdown', onPointerDown);
            this.teardowns.push(() =>
                c.removeEventListener('pointerdown', onPointerDown),
            );
        }
    }

    /** The element clones / markers attach to during drag. */
    private get host(): HTMLElement {
        return (
            this.opts.host ??
            this.opts.containers[0]!.parentElement ??
            document.body
        );
    }

    destroy(): void {
        this.cancel();
        for (const t of this.teardowns) t();
    }

    // ────────────────────────────────────────────────────────────
    // Drag lifecycle
    // ────────────────────────────────────────────────────────────

    private onPointerDown(e: PointerEvent): void {
        // Left mouse button only, or touch/pen. No right/middle click.
        if (e.button !== 0) return;
        if (!(e.target instanceof Element)) return;

        const handle = e.target.closest(this.opts.handleSelector);
        if (!handle) return;
        const item = handle.closest<HTMLElement>(this.opts.itemSelector);
        if (!item) return;
        if (this.opts.canDrag && !this.opts.canDrag(item)) return;

        e.preventDefault();

        this.state = {
            item,
            startX: e.clientX,
            startY: e.clientY,
            active: false,
            clone: null,
            marker: null,
            lastPointerX: e.clientX,
            lastPointerY: e.clientY,
            prospective: null,
        };

        // Capture future pointermove/up on the window so we keep
        // receiving events even if the cursor leaves the container.
        const onMove = (ev: PointerEvent) => this.onPointerMove(ev);
        const onUp = (ev: PointerEvent) => this.onPointerUp(ev);
        const onKey = (ev: KeyboardEvent) => {
            if (ev.key === 'Escape') this.cancel();
        };
        window.addEventListener('pointermove', onMove);
        window.addEventListener('pointerup', onUp);
        window.addEventListener('pointercancel', onUp);
        window.addEventListener('keydown', onKey);

        const cleanup = () => {
            window.removeEventListener('pointermove', onMove);
            window.removeEventListener('pointerup', onUp);
            window.removeEventListener('pointercancel', onUp);
            window.removeEventListener('keydown', onKey);
        };
        // Stash cleanup on the state so endDrag can call it exactly once.
        (this.state as DragState & { cleanup: () => void }).cleanup = cleanup;
    }

    private onPointerMove(e: PointerEvent): void {
        if (!this.state) return;

        this.state.lastPointerX = e.clientX;
        this.state.lastPointerY = e.clientY;

        if (!this.state.active) {
            // Haven't crossed the threshold yet — wait.
            const dx = e.clientX - this.state.startX;
            const dy = e.clientY - this.state.startY;
            if (Math.hypot(dx, dy) < this.opts.dragThreshold) return;
            this.activate();
        }

        this.updateClonePosition(e);
        this.updateProspective(e);
        this.renderMarker();
        this.maybeAutoScroll(e);
    }

    private onPointerUp(e: PointerEvent): void {
        if (!this.state) return;
        if (!this.state.active) {
            // Was a click, not a drag. Clean up and let the click happen.
            this.endDrag();
            return;
        }

        const result = this.state.prospective;
        const item = this.state.item;
        this.endDrag();

        if (result) {
            void this.opts.onDrop({
                item,
                kind: result.kind,
                reference: result.reference,
                anchor: result.anchor,
            });
        }
        e.preventDefault();
    }

    private cancel(): void {
        if (!this.state) return;
        this.endDrag();
    }

    private activate(): void {
        if (!this.state) return;
        this.state.active = true;
        this.state.clone = this.buildClone(this.state.item);
        this.state.marker = this.buildMarker();
        // Attach BOTH the clone and the marker to the shared host
        // (NOT inside any tree `<ul>`). A `<div>` child inside a
        // `<ul>` is invalid HTML and some browsers handle it by
        // reparenting or by opening an anonymous list-item box —
        // which visibly expands the tree when dragging starts.
        //
        // For pagetree the host is the `.cms-pagetree-jstree` wrapper
        // (parent of the single tree `<ul>`); for the structureboard
        // plugin tree it's the `.cms-structure-content` scroller
        // (which contains all participating `.cms-draggables` lists).
        // Both share the ancestor chain, so scoped selectors apply.
        this.host.appendChild(this.state.clone);
        this.host.appendChild(this.state.marker);
        for (const c of this.opts.containers) {
            c.classList.add('cms-pagetree-dragging');
        }
        // Mark the source item so CSS can style it in place. Default
        // `cms-tree-dragging-item` matches the pagetree SCSS; the
        // structureboard adapter overrides to the legacy
        // `cms-draggable-is-dragging` class which the legacy SCSS
        // already styles.
        this.state.item.classList.add(
            this.opts.sourceClass ?? 'cms-tree-dragging-item',
        );
        document.body.style.userSelect = 'none';
    }

    private endDrag(): void {
        if (!this.state) return;
        const s = this.state as DragState & { cleanup?: () => void };
        s.cleanup?.();
        if (s.clone) s.clone.remove();
        if (s.marker) s.marker.remove();
        this.clearDropTargetHighlight();
        for (const c of this.opts.containers) {
            c.classList.remove('cms-pagetree-dragging');
        }
        this.state.item.classList.remove(
            this.opts.sourceClass ?? 'cms-tree-dragging-item',
        );
        document.body.style.userSelect = '';
        this.state = null;
    }

    // ────────────────────────────────────────────────────────────
    // Clone + marker elements
    // ────────────────────────────────────────────────────────────

    private buildClone(item: HTMLElement): HTMLElement {
        // If the caller provided a custom renderer (structureboard does),
        // use it. The renderer is responsible for setting position/
        // z-index/etc inline. Pagetree falls through to the default.
        if (this.opts.cloneRenderer) {
            return this.opts.cloneRenderer(item);
        }
        // Clone the visible row inside a minimal <ul class="cms-pagetree
        // -list"><li role="treeitem"> shell, so the scoped selectors
        // in the pagetree CSS (most rules are rooted at `.cms-pagetree
        // -list ...`) apply to the cloned row without any extra
        // overrides. Without the shell, the clone would appear
        // unstyled because `.cms-tree-row` alone matches nothing.
        const row = item.querySelector<HTMLElement>(this.opts.rowSelector);
        const shell = document.createElement('ul');
        shell.className = 'cms-pagetree-list cms-tree-drag-clone';
        shell.setAttribute('role', 'tree');
        shell.style.cssText = [
            'position: fixed',
            'pointer-events: none',
            'z-index: 9999',
            'opacity: 0.85',
            'margin: 0',
            'padding: 0',
            'list-style: none',
        ].join(';');
        if (row) {
            // Match the source row's rendered width so columns don't
            // reflow to content-intrinsic sizes.
            shell.style.width = `${row.getBoundingClientRect().width}px`;
            const li = document.createElement('li');
            li.setAttribute('role', 'treeitem');
            // Inherit the source's aria-level so any depth-based
            // styling (unlikely but possible) matches.
            const level = item.getAttribute('aria-level');
            if (level) li.setAttribute('aria-level', level);
            li.style.listStyle = 'none';
            li.appendChild(row.cloneNode(true));
            shell.appendChild(li);
        }
        return shell;
    }

    private buildMarker(): HTMLElement {
        const marker = document.createElement('div');
        marker.className = 'cms-tree-drop-marker';
        marker.setAttribute('aria-hidden', 'true');
        marker.style.cssText = [
            'position: absolute',
            'pointer-events: none',
            'z-index: 10',
            'display: none',
        ].join(';');
        return marker;
    }

    private updateClonePosition(e: PointerEvent): void {
        if (!this.state?.clone) return;
        // Offset slightly so the clone doesn't sit directly under the
        // cursor (the cursor would never hit any row for hit-testing).
        this.state.clone.style.left = `${e.clientX + 12}px`;
        this.state.clone.style.top = `${e.clientY + 12}px`;
    }

    // ────────────────────────────────────────────────────────────
    // Prospective drop computation
    // ────────────────────────────────────────────────────────────

    /**
     * Figure out where the dragged item would land if the user dropped
     * right now. Mutates `state.prospective`.
     *
     * Logic:
     *   1. Find the first visible row under cursor.y (NOT a descendant
     *      of the dragged item — you can't drop inside yourself).
     *   2. If cursor.y is in the MIDDLE 50% of that row → drop as child.
     *   3. Otherwise → drop as sibling. Anchor the sibling at the
     *      row above the cursor, then use cursor.x to pick depth: every
     *      full `depthPx` to the left of the anchor row outdents one
     *      level (the "deepest valid depth compatible with cursor X"
     *      rule).
     */
    private updateProspective(e: PointerEvent): void {
        if (!this.state) return;

        const item = this.state.item;
        // Gather rows from every participating container. Order
        // within each container is preserved; container order in the
        // page determines overall iteration order. For both pagetree
        // (one container) and the plugin tree (containers stacked
        // vertically inside `.cms-structure-content`), document order
        // matches visual order.
        const rows: HTMLElement[] = [];
        for (const c of this.opts.containers) {
            for (const row of c.querySelectorAll<HTMLElement>(this.opts.rowSelector)) {
                const li = row.closest<HTMLElement>(this.opts.itemSelector);
                if (!li) continue;
                if (li === item || item.contains(li)) continue;
                if (row.getBoundingClientRect().height <= 0) continue;
                rows.push(row);
            }
        }

        // Pass 1 — is the cursor inside the middle 50% of any row?
        // That's the classic "drop as child of this row" hit, rendered
        // as a row highlight.
        for (const row of rows) {
            const rect = row.getBoundingClientRect();
            const midTop = rect.top + rect.height * 0.25;
            const midBot = rect.bottom - rect.height * 0.25;
            if (e.clientY >= midTop && e.clientY <= midBot) {
                const li = row.closest<HTMLElement>(this.opts.itemSelector)!;
                if (
                    this.opts.canDropAsChild &&
                    !this.opts.canDropAsChild(li, item)
                ) {
                    this.state.prospective = null;
                    return;
                }
                this.state.prospective = {
                    kind: 'child',
                    reference: li,
                    anchor: li,
                    visualRef: row,
                    depth:
                        Number(li.getAttribute('aria-level') ?? '1') + 1,
                    visualMode: 'highlight',
                };
                return;
            }
        }

        // Pass 2 — sibling drop. Find the last row whose CENTER is at
        // or above cursor.y (the "above row" anchor), and the first
        // row whose center is below (the "below row").
        let aboveRow: HTMLElement | null = null;
        let belowRow: HTMLElement | null = null;
        for (const row of rows) {
            const rect = row.getBoundingClientRect();
            const centerY = rect.top + rect.height / 2;
            if (centerY <= e.clientY) {
                aboveRow = row;
            } else {
                belowRow = row;
                break;
            }
        }

        if (!aboveRow && !belowRow) {
            this.state.prospective = null;
            return;
        }

        if (!aboveRow && belowRow) {
            // Before the very first row — place before it at its depth.
            const li = belowRow.closest<HTMLElement>(this.opts.itemSelector)!;
            this.state.prospective = {
                kind: 'sibling-before',
                reference: li,
                anchor: li,
                visualRef: belowRow,
                depth: Number(li.getAttribute('aria-level') ?? '1'),
                visualMode: 'line-before',
            };
            return;
        }

        // aboveRow is present. Default: drop as sibling-after(aboveRow).
        // Cursor.x is the disambiguator:
        //   - right of aboveLeft + depthPx AND aboveLi accepts children
        //     → INDENT: become the first child of aboveLi (rendered as
        //     a line at aboveDepth + 1). Works whether aboveLi is a
        //     leaf, a collapsed parent, or an expanded parent with
        //     visible children — in all cases "indent past above.left"
        //     means "land inside above" on the way in.
        //   - at aboveLeft (±depthPx) → sibling-after aboveLi at aboveDepth.
        //   - left of aboveLeft → OUTDENT by one level per full depthPx
        //     step, walking the ancestor chain.
        const aboveLi = aboveRow!.closest<HTMLElement>(this.opts.itemSelector)!;
        const aboveDepth = Number(aboveLi.getAttribute('aria-level') ?? '1');
        const aboveLeft = aboveRow!.getBoundingClientRect().left;

        const canIndentToChild =
            !this.opts.canDropAsChild ||
            this.opts.canDropAsChild(aboveLi, item);
        if (
            canIndentToChild &&
            e.clientX >= aboveLeft + this.opts.depthPx
        ) {
            this.state.prospective = {
                kind: 'child',
                reference: aboveLi,
                anchor: aboveLi,
                visualRef: aboveRow!,
                depth: aboveDepth + 1,
                visualMode: 'line-after',
            };
            return;
        }

        // Outdent is bounded by the structural position. The user can
        // only outdent as far as an ancestor of aboveLi whose parent
        // container would logically contain the dragged item at this
        // cursor.y. Concretely: the minimum valid depth is the depth
        // of the NEXT visible row (belowRow) — you can't outdent past
        // where the tree is already going. If there is no below row,
        // the tree has ended at this point in visual order and any
        // depth from 1 (root) up to aboveDepth is valid.
        const minDepth = belowRow
            ? Number(
                belowRow
                    .closest<HTMLElement>(this.opts.itemSelector)
                    ?.getAttribute('aria-level') ?? '1',
            )
            : 1;

        const outdent = Math.max(
            0,
            Math.floor((aboveLeft - e.clientX) / this.opts.depthPx),
        );
        let desiredDepth = aboveDepth - outdent;
        if (desiredDepth < minDepth) desiredDepth = minDepth;
        if (desiredDepth > aboveDepth) desiredDepth = aboveDepth;

        // Walk up from aboveLi to the ancestor at desiredDepth.
        let anchor: HTMLElement | null = aboveLi;
        while (anchor) {
            const lvl = Number(anchor.getAttribute('aria-level') ?? '1');
            if (lvl === desiredDepth) break;
            const parent: HTMLElement | null = anchor.parentElement;
            anchor =
                parent?.closest<HTMLElement>(this.opts.itemSelector) ?? null;
        }
        if (!anchor) {
            this.state.prospective = null;
            return;
        }

        this.state.prospective = {
            kind: 'sibling-after',
            reference: aboveLi,
            anchor,
            visualRef: aboveRow!,
            depth: desiredDepth,
            visualMode: 'line-after',
        };
    }

    // ────────────────────────────────────────────────────────────
    // Marker rendering
    // ────────────────────────────────────────────────────────────

    private renderMarker(): void {
        if (!this.state?.marker) return;
        const p = this.state.prospective;
        this.clearDropTargetHighlight();

        if (!p) {
            this.state.marker.classList.remove('cms-tree-drop-marker--active');
            return;
        }

        if (p.visualMode === 'highlight') {
            // Row-highlight drop (cursor in middle 50% of a row).
            // The marker div is not used; instead a class on the row.
            this.state.marker.classList.remove('cms-tree-drop-marker--active');
            p.visualRef.classList.add('cms-tree-drop-target');
            return;
        }

        // Line marker — position relative to the marker's offset parent.
        //   Left = (depth - 1) * depthPx - triangle cap width
        //   Top  = below visualRef (line-after) or above (line-before)
        //
        // Must match the CSS triangle metrics in components/_tree-drag.scss:
        // the triangles use a 10px horizontal border, so we pull the
        // line start back by that so the leading cap sits in the
        // indent gutter. Line height is 4px.
        //
        // Width and indent reference is the *container that owns the
        // visualRef row* — for multi-container layouts (plugin tree)
        // each draggables list may have a different left edge.
        const TRIANGLE_PX = 10;
        const LINE_HEIGHT_PX = 4;
        const offsetHost = this.state.marker.offsetParent as HTMLElement | null;
        const hostRect = (offsetHost ?? this.host).getBoundingClientRect();
        const owningContainer =
            this.opts.containers.find((c) => c.contains(p.visualRef)) ??
            this.opts.containers[0]!;
        const treeRect = owningContainer.getBoundingClientRect();
        const rowRect = p.visualRef.getBoundingClientRect();
        // Left: tree's own left + depth offset - triangle width
        const leftOffset =
            treeRect.left - hostRect.left +
            (p.depth - 1) * this.opts.depthPx -
            TRIANGLE_PX;
        const baseY =
            p.visualMode === 'line-after' ? rowRect.bottom : rowRect.top;
        const top = baseY - hostRect.top - LINE_HEIGHT_PX / 2;

        const m = this.state.marker;
        m.classList.add('cms-tree-drop-marker--active');
        m.style.left = `${leftOffset}px`;
        m.style.width = `${treeRect.width - (p.depth - 1) * this.opts.depthPx + TRIANGLE_PX * 2}px`;
        m.style.right = '';
        m.style.top = `${top}px`;
        m.style.height = `${LINE_HEIGHT_PX}px`;
    }

    private clearDropTargetHighlight(): void {
        for (const c of this.opts.containers) {
            const highlighted = c.querySelectorAll<HTMLElement>('.cms-tree-drop-target');
            for (const el of Array.from(highlighted)) {
                el.classList.remove('cms-tree-drop-target');
            }
        }
    }

    // ────────────────────────────────────────────────────────────
    // Auto-scroll
    // ────────────────────────────────────────────────────────────

    private maybeAutoScroll(e: PointerEvent): void {
        // Find the nearest scroller for the container under the cursor
        // (or the first container as a fallback). For pagetree there's
        // only one container; for the plugin tree the scroller is
        // typically a shared ancestor and the first container's
        // findScrollParent walks up to it.
        const target = (e.target instanceof Element ? e.target : null) as Element | null;
        const containerUnderCursor =
            this.opts.containers.find((c) => target && c.contains(target)) ??
            this.opts.containers[0]!;
        const scroller = this.findScrollParent(containerUnderCursor);
        if (!scroller) return;
        const rect = scroller.getBoundingClientRect();
        const EDGE = 40;
        const SPEED = 10;

        if (e.clientY < rect.top + EDGE) {
            scroller.scrollBy({ top: -SPEED });
        } else if (e.clientY > rect.bottom - EDGE) {
            scroller.scrollBy({ top: SPEED });
        }
    }

    private findScrollParent(el: HTMLElement): HTMLElement | null {
        let cur: HTMLElement | null = el;
        while (cur && cur !== document.body) {
            const { overflowY } = getComputedStyle(cur);
            if (overflowY === 'auto' || overflowY === 'scroll') return cur;
            cur = cur.parentElement;
        }
        return document.scrollingElement as HTMLElement | null;
    }
}

