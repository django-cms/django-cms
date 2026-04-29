/*
 * Long-menus controller — when an opened submenu would extend past
 * the bottom of the viewport, "unstick" the toolbar (switch from
 * `position: fixed` to absolutely-positioned) so the user can scroll
 * the menu into view. Reverts to sticky once the menu fits or is
 * closed.
 *
 * Mirrors the logic in `cms.toolbar.js::_handleLongMenus`,
 * `_stickToolbar`, `_unstickToolbar`. Behaviour is observable via
 * the `cms-toolbar-non-sticky` class on the body, plus an inline
 * `top: <Npx> !important` on the toolbar.
 */

interface Position {
    top: number;
    stickyTop: number;
    isSticky: boolean;
}

export interface LongMenusOptions {
    /** The `<html>` element (legacy `this.ui.body = $('html')`). */
    body: HTMLElement;
    /** The `.cms-toolbar` element. */
    toolbar: HTMLElement;
    /** Window — overrideable for tests. */
    window?: Window;
}

export interface LongMenusController {
    /** Recompute sticky/unsticky based on current open menus. */
    recompute(): void;
    /** Force the toolbar back to its default sticky position. */
    stick(): void;
    /** Detach internal state (no listeners; included for symmetry). */
    destroy(): void;
}

export function setupLongMenus(opts: LongMenusOptions): LongMenusController {
    const win = opts.window ?? window;
    const position: Position = {
        top: 0,
        stickyTop: 0,
        isSticky: true,
    };

    function stick(): void {
        position.stickyTop = 0;
        position.isSticky = true;
        opts.body.classList.remove('cms-toolbar-non-sticky');
        opts.toolbar.style.top = '0';
    }

    function unstick(): void {
        position.stickyTop = position.top;
        opts.body.classList.add('cms-toolbar-non-sticky');
        // !important needed because the legacy debug-bar SCSS forces
        // a top value via specificity. setProperty with priority is
        // the only inline-style way to add !important.
        opts.toolbar.style.setProperty(
            'top',
            `${position.stickyTop}px`,
            'important',
        );
        position.isSticky = false;
    }

    function recompute(): void {
        const openMenus = Array.from(
            document.querySelectorAll<HTMLElement>(
                '.cms-toolbar-item-navigation-hover > ul',
            ),
        );
        if (openMenus.length === 0) {
            stick();
            return;
        }

        const positions = openMenus.map((el) => {
            const rect = el.getBoundingClientRect();
            // Mirror jQuery's `.position()` — top relative to offset
            // parent. For top-of-toolbar menus this is essentially
            // the rect top relative to the toolbar's offset parent;
            // legacy tested against `windowHeight` directly so we
            // approximate with `rect.bottom` (viewport-relative).
            return { top: rect.top, height: rect.height };
        });
        const windowHeight = win.innerHeight;

        position.top = win.scrollY;

        const overflows = positions.some(
            (item) => item.top + item.height > windowHeight,
        );

        if (overflows && position.top >= position.stickyTop) {
            if (position.isSticky) unstick();
        } else {
            stick();
        }
    }

    return {
        recompute,
        stick,
        destroy(): void {
            // No listeners owned here — the toolbar attaches its own
            // resize/scroll listeners and calls recompute().
        },
    };
}
