/*
 * Mode-switcher event wiring.
 *
 * Mirrors legacy `StructureBoard._setupModeSwitcher`. Three concerns:
 *
 *   1. Track Cmd/Ctrl/Shift held state on the window so a click while
 *      a modifier is down opens the mode link in a new tab (legacy
 *      behaviour — preserves "open in new tab" semantics for the
 *      structure/content URL).
 *
 *   2. Bind a click handler on the mode toggle anchors. Click → flip
 *      to the other mode via `show()` / `hide()`. Modifier-down click
 *      bypasses to `window.open`.
 *
 *   3. Bind Space / Shift+Space keyboard shortcuts to toggle the
 *      structure board (the legacy keyboard module's "cms" context).
 *      For the strangler period we use a plain `keydown` listener with
 *      modifier checks — the dedicated keyboard module ports later.
 *
 * Returns a teardown handle so 3i can release listeners on unload (the
 * legacy class never tore them down — single-page session lifetime).
 */

import { hide, show, toggleStructureBoard, type ModeContext, type ToggleOptions } from './mode';

export interface SwitcherOptions {
    /**
     * The mode-toggle anchors. Click handler is delegated; modifier-
     * down clicks open in a new tab (`href` of the first link).
     */
    modeLinks: HTMLElement[];
    /**
     * The mode-switcher wrapper (`.cms-toolbar-item-cms-mode-switcher`).
     * If absent or its `.cms-btn` is disabled, keyboard shortcuts
     * are not bound. Mirrors legacy guard.
     */
    switcher?: HTMLElement | null;
    /** Forwarded to `toggleStructureBoard` for shift+space. */
    onShowAndHighlight?: ToggleOptions['onShowAndHighlight'];
}

export interface SwitcherHandle {
    destroy(): void;
}

/**
 * Wire the click + keyboard handlers. The returned handle's
 * `destroy()` removes both, so the structureboard class shell can
 * cleanly tear down on unload (legacy never did, but vitest does).
 */
export function setupModeSwitcher(
    ctx: ModeContext,
    options: SwitcherOptions,
): SwitcherHandle {
    const controller = new AbortController();
    const opts = { signal: controller.signal };

    // (1) Modifier-key tracking — both keydown + keyup so we know
    //     state at click time.
    let modifierDown = false;
    const onKey = (e: KeyboardEvent): void => {
        if (
            e.type === 'keydown' &&
            (e.metaKey || e.ctrlKey || e.shiftKey)
        ) {
            modifierDown = true;
        }
        if (e.type === 'keyup') modifierDown = false;
    };
    ctx.win.addEventListener('keydown', onKey, opts);
    ctx.win.addEventListener('keyup', onKey, opts);
    ctx.win.addEventListener(
        'blur',
        () => {
            modifierDown = false;
        },
        opts,
    );

    // (2) Click handler on each mode link.
    const onLinkClick = (e: Event): void => {
        e.preventDefault();
        e.stopImmediatePropagation();

        const allDisabled = options.modeLinks.every((el) =>
            el.classList.contains('cms-btn-disabled'),
        );
        if (allDisabled) return;

        // Modifier-down → open the link's target in a new tab.
        if (modifierDown && e.type === 'click') {
            const href = options.modeLinks[0]?.getAttribute('href');
            if (href) ctx.win.open(href, '_blank');
            return;
        }

        const cms = window.CMS as { settings?: { mode?: string } } | undefined;
        if (cms?.settings?.mode === 'edit') {
            void show(ctx);
        } else {
            void hide(ctx);
        }
    };
    for (const link of options.modeLinks) {
        link.addEventListener('click', onLinkClick, opts);
    }

    // (3) Keyboard shortcuts — Space / Shift+Space.
    const switcherDisabled = !options.switcher
        ? true
        : Array.from(
              options.switcher.querySelectorAll<HTMLElement>('.cms-btn'),
          ).every((el) => el.classList.contains('cms-btn-disabled'));

    if (!switcherDisabled) {
        const onKeyboardShortcut = (e: KeyboardEvent): void => {
            // Don't trigger inside text inputs / contentEditable.
            const target = e.target as HTMLElement | null;
            if (target && isTextInputTarget(target)) return;
            if (e.key !== ' ' && e.code !== 'Space') return;
            e.preventDefault();
            const toggleOpts: ToggleOptions = {};
            if (e.shiftKey) toggleOpts.useHoveredPlugin = true;
            if (options.onShowAndHighlight) {
                toggleOpts.onShowAndHighlight = options.onShowAndHighlight;
            }
            toggleStructureBoard(ctx, toggleOpts);
        };
        ctx.win.addEventListener('keydown', onKeyboardShortcut, opts);
    }

    return {
        destroy(): void {
            controller.abort();
        },
    };
}

function isTextInputTarget(el: HTMLElement): boolean {
    if (el.isContentEditable) return true;
    const tag = el.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true;
    return false;
}
