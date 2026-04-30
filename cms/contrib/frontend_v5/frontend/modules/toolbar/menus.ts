/*
 * Toolbar navigation menus — port of the per-navigation event wiring
 * from `cms.toolbar.js::_events`. Each `.cms-toolbar-item-navigation`
 * gets its own state machine (open/cmdPressed/isTouchingTopLevelMenu)
 * because the menus are independent — closing one shouldn't close
 * another, and click-outside should reset every open menu.
 *
 * The state machine handles three input modalities:
 *   - Mouse — click to open, hover to switch siblings, click outside
 *     to close.
 *   - Touch — tap to open; mouseover events fired by touch are
 *     ignored (they fire on touch devices and would close the menu
 *     prematurely).
 *   - Keyboard — Tab to advance focus and reset; Esc to close;
 *     Enter to open submenu when a parent item is hovered.
 *
 * The CMD/CTRL-click escape hatch opens the link in a new tab — the
 * legacy code calls `window.open(href, '_blank')` rather than relying
 * on the browser's default ctrl-click behaviour because the click is
 * intercepted before the default would fire.
 *
 * Layout overflow handling is delegated to `LongMenusController`
 * (see `long-menus.ts`) — the menus module just calls its
 * `recompute()` whenever a submenu opens/closes.
 */

import { KEYS } from '../cms-base';
import type { LongMenusController } from './long-menus';

export interface MenusOptions {
    /** Click-outside catchment area. The legacy code listens on
     * `document` for clicks. Tests can override with a constrained
     * element. */
    document?: Document | undefined;
    /** Window — for `keyup` (Esc/Tab) and resize-throttled menu reset. */
    window?: Window | undefined;
    /** Toolbar root for click-self-to-reset behaviour. */
    toolbar: HTMLElement;
    /** Structureboard catchment — clicking inside also resets. */
    structureBoard?: HTMLElement | undefined;
    /** Long-menus controller invoked after each menu state change. */
    longMenus?: LongMenusController | undefined;
    /** Click handler for top-level link entries. Receives the anchor. */
    onTopLevelClick: (anchor: HTMLAnchorElement) => void;
}

export interface MenusHandle {
    /** Release every listener bound by `setupMenus`. */
    destroy(): void;
}

const ROOT_CLASS = 'cms-toolbar-item-navigation';
const HOVER_CLASS = 'cms-toolbar-item-navigation-hover';
const DISABLED_CLASS = 'cms-toolbar-item-navigation-disabled';
const CHILDREN_CLASS = 'cms-toolbar-item-navigation-children';

/**
 * Wire up every `.cms-toolbar-item-navigation` inside `toolbar`. Each
 * gets its own state machine; they share the click-outside + window
 * handlers via the returned `destroy()` aggregating cleanup.
 */
export function setupMenus(opts: MenusOptions): MenusHandle {
    const doc = opts.document ?? document;
    const win = opts.window ?? window;

    const navigations = Array.from(
        opts.toolbar.querySelectorAll<HTMLElement>(
            `.${ROOT_CLASS}`,
        ),
    );

    const handles: MenusHandle[] = [];
    for (const nav of navigations) {
        handles.push(setupSingleNav(nav, opts, doc, win));
    }

    return {
        destroy(): void {
            for (const h of handles) h.destroy();
        },
    };
}

// ────────────────────────────────────────────────────────────────────
// Single-navigation state machine
// ────────────────────────────────────────────────────────────────────

function setupSingleNav(
    nav: HTMLElement,
    opts: MenusOptions,
    doc: Document,
    win: Window,
): MenusHandle {
    const lists = Array.from(nav.querySelectorAll<HTMLElement>('li'));
    let isTouchingTopLevelMenu = false;
    let open = false;
    let cmdPressed = false;
    const cleanups: Array<() => void> = [];

    function reset(): void {
        open = false;
        cmdPressed = false;
        for (const li of lists) li.classList.remove(HOVER_CLASS);
        // Mirror legacy `lists.find('ul ul').hide()` — jQuery's `.find()`
        // scopes descendant combinators to the search root, so the outer
        // `ul` of `ul ul` must itself be inside an `<li>` of `lists`.
        // Without that scoping, `nav.querySelectorAll('ul ul')` matches
        // the top-level dropdown UL too (its `<ul>` ancestor is the nav
        // root UL) and stamps `display: none` onto it.
        nav.querySelectorAll<HTMLElement>('li ul ul').forEach((ul) => {
            ul.style.display = 'none';
        });
        nav.querySelectorAll<HTMLLIElement>(':scope > li').forEach(
            (topLi) => {
                if (topMouseEnterHandlers.has(topLi)) {
                    const fn = topMouseEnterHandlers.get(topLi)!;
                    topLi.removeEventListener('mouseenter', fn);
                    topMouseEnterHandlers.delete(topLi);
                }
            },
        );
        doc.removeEventListener('click', reset);
        opts.toolbar.removeEventListener('click', reset);
        opts.structureBoard?.removeEventListener('click', reset);
        win.removeEventListener('resize', resetThrottled);
        opts.longMenus?.recompute();
    }

    let resetThrottled: EventListener = (): void => reset();

    // ── Window keyup: Esc closes
    const onWinKeyup = (e: KeyboardEvent): void => {
        if (e.keyCode === KEYS.ESC) reset();
    };
    win.addEventListener('keyup', onWinKeyup);
    cleanups.push(() => win.removeEventListener('keyup', onWinKeyup));

    // ── Top-level + sibling Tab-out reset
    const tabResetTargets = collectTabResetTargets(nav, opts.toolbar);
    const onTabReset = (e: KeyboardEvent): void => {
        if (e.keyCode === KEYS.TAB) reset();
    };
    for (const el of tabResetTargets) {
        el.addEventListener('keyup', onTabReset);
        cleanups.push(() =>
            el.removeEventListener('keyup', onTabReset),
        );
    }

    // ── Per-anchor click + key (CMD detection + delegate)
    const anchors = Array.from(nav.querySelectorAll<HTMLAnchorElement>('a'));
    const onAnchorEvent = (e: Event): void => {
        const ev = e as MouseEvent | KeyboardEvent;
        const anchor = ev.currentTarget as HTMLAnchorElement;
        const ke = ev as KeyboardEvent;
        if (
            ke.keyCode === KEYS.CMD_LEFT ||
            ke.keyCode === KEYS.CMD_RIGHT ||
            ke.keyCode === KEYS.CMD_FIREFOX ||
            ke.keyCode === KEYS.SHIFT ||
            ke.keyCode === KEYS.CTRL
        ) {
            cmdPressed = true;
        }
        if (ev.type === 'keyup') cmdPressed = false;

        const href = anchor.getAttribute('href');
        const parent = anchor.parentElement;
        const isDisabled =
            parent !== null && parent.classList.contains(DISABLED_CLASS);

        if (href && href !== '' && href !== '#' && !isDisabled) {
            if (cmdPressed && ev.type === 'click') {
                win.open(href, '_blank');
            } else if (ev.type === 'click') {
                opts.onTopLevelClick(anchor);
            } else {
                return; // tabbing through
            }
            reset();
            ev.preventDefault();
            ev.stopPropagation();
        }
    };
    const onAnchorTouchStart = (): void => {
        isTouchingTopLevelMenu = true;
    };
    for (const a of anchors) {
        a.addEventListener('click', onAnchorEvent);
        a.addEventListener('keydown', onAnchorEvent);
        a.addEventListener('keyup', onAnchorEvent);
        a.addEventListener('touchstart', onAnchorTouchStart);
        cleanups.push(() => {
            a.removeEventListener('click', onAnchorEvent);
            a.removeEventListener('keydown', onAnchorEvent);
            a.removeEventListener('keyup', onAnchorEvent);
            a.removeEventListener('touchstart', onAnchorTouchStart);
        });
    }

    // ── Per-li click (open / close menu)
    // Tracks per-top-level-li mouseenter handlers so we can unbind on reset.
    const topMouseEnterHandlers = new WeakMap<HTMLElement, EventListener>();
    const onLiClick = (e: Event): void => {
        e.preventDefault();
        e.stopPropagation();
        const li = e.currentTarget as HTMLElement;
        const liParent = li.parentElement;
        const isRoot =
            liParent !== null && liParent.classList.contains(ROOT_CLASS);

        if (isRoot && open) {
            reset();
            return;
        }

        if (!li.classList.contains(CHILDREN_CLASS)) {
            reset();
        }

        if (
            (isRoot && li.classList.contains(HOVER_CLASS)) ||
            (li.classList.contains(DISABLED_CLASS) && !isRoot)
        ) {
            return;
        }

        li.classList.add(HOVER_CLASS);
        // Show direct-child <ul> (submenu)
        const directChildUl = li.querySelector<HTMLUListElement>(':scope > ul');
        if (directChildUl) directChildUl.style.display = '';
        opts.longMenus?.recompute();

        if (!isTouchingTopLevelMenu) {
            // Bind mouseenter on every direct top-level li so hovering
            // an adjacent menu opens it without an extra click.
            const topLis = Array.from(
                nav.querySelectorAll<HTMLLIElement>(':scope > li'),
            );
            for (const topLi of topLis) {
                const handler = (): void => {
                    if (topLi.classList.contains(HOVER_CLASS)) return;
                    open = false;
                    topLi.dispatchEvent(
                        new MouseEvent('click', { bubbles: true }),
                    );
                };
                topLi.addEventListener('mouseenter', handler);
                topMouseEnterHandlers.set(topLi, handler);
            }
        }

        isTouchingTopLevelMenu = false;
        // Click-outside catchment — install on document, structureboard,
        // toolbar (so clicking the toolbar background also closes).
        doc.addEventListener('click', reset);
        opts.structureBoard?.addEventListener('click', reset);
        opts.toolbar.addEventListener('click', reset);
        // Throttle window resize → reset (legacy uses 1s throttle).
        win.addEventListener('resize', resetThrottled);
        open = true;
    };
    for (const li of lists) {
        li.addEventListener('click', onLiClick);
        cleanups.push(() => li.removeEventListener('click', onLiClick));
    }

    // ── Per-li hover/keyup (submenu reveal + sibling switch)
    const onLiPointerOrKey = (e: Event): void => {
        const ev = e as PointerEvent | KeyboardEvent;
        const target = ev.target as Element | null;
        // Find the closest <li> within this nav
        const li = target?.closest<HTMLElement>('li');
        if (!li || !nav.contains(li)) return;
        // Match legacy `lists.on(event, 'li', …)` delegated semantics:
        // jQuery's `'li'` selector filters to DESCENDANT lis, so the
        // handler never fires on a top-level menu item — that prevents
        // hovering a top-level menu from opening it without a click.
        // Once a dropdown is open the hover handler runs against its
        // nested lis (which all have an `<li>` ancestor) and switches
        // sub-menu state to follow the cursor.
        if (!li.parentElement?.closest('li')) return;

        const parents = closestAndAncestors(
            li,
            `.${CHILDREN_CLASS}`,
        );
        const hasChildren =
            li.classList.contains(CHILDREN_CLASS) || parents.length > 0;

        if (li.classList.contains(DISABLED_CLASS)) {
            ev.stopPropagation();
            return;
        }
        if (
            li.classList.contains(HOVER_CLASS) &&
            ev.type !== 'keyup'
        ) {
            return;
        }
        // Mirror legacy `lists.find('li').removeClass(hover)` — that
        // jQuery call only matches `<li>` *descendants* of an `<li>` in
        // `lists`, i.e. nested submenu items. Top-level `<li>`s keep
        // their hover state, so the dropdown's cascade rule
        // (`.cms-toolbar-item-navigation-hover ul { display: block }`)
        // doesn't briefly flip to `display: none` between the wipe and
        // the parents-add below — that transition was the cause of the
        // dropdown disappearing as the cursor entered it.
        for (const nested of nav.querySelectorAll<HTMLElement>('li li')) {
            nested.classList.remove(HOVER_CLASS);
        }
        li.classList.add(HOVER_CLASS);

        const isKeyup = ev.type === 'keyup';
        const isEnter =
            isKeyup && (ev as KeyboardEvent).keyCode === KEYS.ENTER;

        if (
            (hasChildren && !isKeyup) ||
            (hasChildren && isEnter)
        ) {
            const sub = li.querySelector<HTMLUListElement>(':scope > ul');
            if (sub) sub.style.display = '';
            for (const p of parents) p.classList.add(HOVER_CLASS);
            opts.longMenus?.recompute();
        } else if (!isKeyup) {
            // See `reset()` — `'li ul ul'` mirrors jQuery's scoped
            // `lists.find('ul ul')`, excluding the top-level dropdown
            // UL whose only `<ul>` ancestor is the nav root.
            nav.querySelectorAll<HTMLElement>('li ul ul').forEach((ul) => {
                ul.style.display = 'none';
            });
            opts.longMenus?.recompute();
        }
        // Hide stale submenus on siblings.
        const siblings = Array.from(
            (li.parentElement?.children ?? []) as HTMLCollectionOf<HTMLElement>,
        );
        for (const sib of siblings) {
            if (sib === li) continue;
            sib.querySelectorAll<HTMLElement>(':scope > ul').forEach((ul) => {
                ul.style.display = 'none';
            });
        }
    };
    for (const li of lists) {
        li.addEventListener('pointerover', onLiPointerOrKey);
        li.addEventListener('pointerout', onLiPointerOrKey);
        li.addEventListener('keyup', onLiPointerOrKey);
        cleanups.push(() => {
            li.removeEventListener('pointerover', onLiPointerOrKey);
            li.removeEventListener('pointerout', onLiPointerOrKey);
            li.removeEventListener('keyup', onLiPointerOrKey);
        });
    }

    // ── Pointer-leave on submenus → unhover NESTED lis only.
    // Legacy `lists.find('li').removeClass(hover)` matches only LIs
    // *nested inside* another LI, so leaving the dropdown collapses
    // inner submenu state but the top-level item keeps HOVER and the
    // dropdown stays open. Wiping every LI here would close the
    // dropdown the moment the cursor crosses the UL boundary.
    const submenuUls = Array.from(
        nav.querySelectorAll<HTMLUListElement>('li > ul'),
    );
    const onPointerLeave = (): void => {
        for (const nested of nav.querySelectorAll<HTMLElement>('li li')) {
            nested.classList.remove(HOVER_CLASS);
        }
    };
    for (const ul of submenuUls) {
        ul.addEventListener('pointerleave', onPointerLeave);
        cleanups.push(() =>
            ul.removeEventListener('pointerleave', onPointerLeave),
        );
    }

    return {
        destroy(): void {
            reset();
            for (const c of cleanups) c();
        },
    };
}

// ────────────────────────────────────────────────────────────────────
// Helpers
// ────────────────────────────────────────────────────────────────────

/**
 * Collect the elements that should reset the menu when Tab leaves
 * them: the top-level nav anchors plus other (non-navigation) toolbar
 * items.
 */
function collectTabResetTargets(
    nav: HTMLElement,
    toolbar: HTMLElement,
): HTMLElement[] {
    const fromNav = Array.from(
        nav.querySelectorAll<HTMLElement>(':scope > li > a'),
    );
    const fromToolbar = Array.from(
        toolbar.querySelectorAll<HTMLElement>(
            `.cms-toolbar-item:not(.${ROOT_CLASS}) > a`,
        ),
    );
    return [...fromNav, ...fromToolbar];
}

/**
 * Find the closest ancestor matching `selector`, plus every further
 * ancestor that also matches. Mirrors the legacy
 * `el.closest(...).add(el.parents(...))` pattern.
 */
function closestAndAncestors(
    el: HTMLElement,
    selector: string,
): HTMLElement[] {
    const out: HTMLElement[] = [];
    let cur: HTMLElement | null = el;
    while (cur) {
        if (cur.matches(selector)) out.push(cur);
        cur = cur.parentElement;
    }
    return out;
}
