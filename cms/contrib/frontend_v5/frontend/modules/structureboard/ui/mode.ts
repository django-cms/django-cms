/*
 * Mode toggling — `show`, `hide`, `_toggleStructureBoard`, `_showBoard`,
 * `_hideBoard`, `_makeCondensed`, `_makeFullWidth`.
 *
 * Mirrors legacy `StructureBoard` instance methods of the same names.
 * Functional API so tests can drive the DOM transitions without
 * standing up the class shell (3i wires them onto the class).
 *
 * Three concerns split across the functions:
 *   - Settings + persistence (`CMS.settings.mode = 'structure' | 'edit'`)
 *   - Class flips (`cms-structure-mode-{structure,content}`,
 *     `cms-structure-condensed`, `cms-overflow`)
 *   - Container show/hide + scrollbar gap math
 *
 * The condensed/full-width state lives module-locally; the class shell
 * reads it via `isCondensed()` for the `resize` listener (3i).
 *
 * `show()` / `hide()` await `loadStructure` / `loadContent` callbacks
 * the caller provides — those fetch + apply the markup for the
 * mode being entered. They're injected (not imported) so this
 * module stays pure UI: refresh.ts owns content-mode loading; the
 * structure-mode loader (legacy `_loadStructure`) lands in 3i.
 */

import { getCmsConfig, getCmsSettings } from '../../plugins/cms-globals';

/** True when the structure board is in condensed (sidebar) layout. */
let condensed = false;

export function isCondensed(): boolean {
    return condensed;
}

/** Test/migration hook — reset module-level state. */
export function _resetForTest(): void {
    condensed = false;
}

export interface ModeContext {
    /** The structure board container (`.cms-structure`). */
    container: HTMLElement;
    /** The toolbar wrapper (`#cms-top` or `[data-cms]`). */
    toolbar: HTMLElement;
    /** The `<html>` element — for global mode classes + overflow control. */
    html: HTMLElement;
    /** The mode-toggle anchors (`<a>` per mode in the toolbar). */
    toolbarModeLinks: HTMLElement[];
    /** The window hosting the page — split out so tests can inject a stub. */
    win: Window;
    /** Read-only — set by structure-load pipeline (3i). */
    isLoadedStructure(): boolean;
    /** Read-only — set by `refresh.ts::contentLoaded`. */
    isLoadedContent(): boolean;
    /** Fetch + apply structure-mode markup. Resolves once visible. */
    loadStructure(): Promise<void>;
    /** Fetch + apply content-mode markup. Resolves once visible. */
    loadContent(): Promise<void>;
}

/**
 * Persist the current `CMS.settings` snapshot via the legacy
 * `Helpers.setSettings` path. Best-effort — localStorage failures
 * are swallowed (the mode flip is observable via DOM classes either
 * way).
 */
function persistSettings(): void {
    const cms = window.CMS as
        | { API?: { Helpers?: { setSettings?: (s: unknown) => void } } }
        | undefined;
    cms?.API?.Helpers?.setSettings?.(getCmsSettings());
}

function isLiveMode(): boolean {
    return getCmsConfig().mode === 'live';
}

/**
 * Width of the host's vertical scrollbar in pixels — reproduces the
 * legacy `measureScrollbar` utility. Returns 0 in environments where
 * the offset diff is undetectable (jsdom, mobile webkit overlay
 * scrollbars).
 */
function measureScrollbar(): number {
    const probe = document.createElement('div');
    probe.style.cssText =
        'position:absolute;top:-9999px;width:50px;height:50px;overflow:scroll';
    document.body.appendChild(probe);
    const width = probe.offsetWidth - probe.clientWidth;
    probe.remove();
    return width;
}

// ────────────────────────────────────────────────────────────────────
// show / hide
// ────────────────────────────────────────────────────────────────────

/**
 * Switch the page into structure mode. Mirrors legacy
 * `StructureBoard.show`. Resolves once the structure is rendered.
 *
 * `init: true` is passed on the very first show (page bootstrap) — it
 * compensates for the toolbar's scrollbar gap and skips the
 * condensed-layout flip (the bootstrap path may want full width).
 */
export async function show(
    ctx: ModeContext,
    options: { init?: boolean } = {},
): Promise<boolean> {
    if (isLiveMode()) return false;

    if (options.init) {
        // Toolbar position adjustment — keeps the toolbar in the same
        // visual spot regardless of whether the page had a scrollbar.
        const width = ctx.toolbar.getBoundingClientRect().width;
        let gap = ctx.win.innerWidth - width;
        if (!gap) gap = measureScrollbar();
        if (gap > 0) ctx.toolbar.style.right = `${gap}px`;
    }

    getCmsSettings().mode = 'structure';
    persistSettings();

    await ctx.loadStructure();
    showBoard(ctx, options.init ?? false);
    return true;
}

/**
 * Switch the page into content (edit) mode. Mirrors legacy
 * `StructureBoard.hide`.
 */
export async function hide(ctx: ModeContext): Promise<boolean> {
    if (isLiveMode()) return false;

    // Reset toolbar positioning + global overflow class.
    ctx.toolbar.style.right = '';
    ctx.html.classList.remove('cms-overflow');

    // Mode-link active state.
    for (const link of ctx.toolbarModeLinks) {
        link.classList.remove('cms-btn-active');
    }
    ctx.toolbarModeLinks[1]?.classList.add('cms-btn-active');

    ctx.html.classList.remove('cms-structure-mode-structure');
    ctx.html.classList.add('cms-structure-mode-content');

    getCmsSettings().mode = 'edit';
    persistSettings();

    await ctx.loadContent();
    hideBoard(ctx);
    return true;
}

// ────────────────────────────────────────────────────────────────────
// showBoard / hideBoard — the visible-DOM half of show/hide.
// ────────────────────────────────────────────────────────────────────

/**
 * Apply the structure-mode CSS classes + show the container. Mirrors
 * legacy `_showBoard`. Splits from `show` so 3i can call it without
 * paying the load round-trip when structure is already loaded.
 */
export function showBoard(ctx: ModeContext, init: boolean): void {
    for (const link of ctx.toolbarModeLinks) {
        link.classList.remove('cms-btn-active');
    }
    ctx.toolbarModeLinks[0]?.classList.add('cms-btn-active');

    ctx.html.classList.remove('cms-structure-mode-content');
    ctx.html.classList.add('cms-structure-mode-structure');

    ctx.container.style.display = '';

    if (!init) {
        makeCondensed(ctx);
    }
    if (init && !ctx.isLoadedContent()) {
        makeFullWidth(ctx);
    }

    ctx.win.dispatchEvent(new Event('resize'));
}

/** Hide the structure container + trigger a window resize. */
export function hideBoard(ctx: ModeContext): void {
    ctx.container.style.display = 'none';
    ctx.win.dispatchEvent(new Event('resize'));
}

// ────────────────────────────────────────────────────────────────────
// makeCondensed / makeFullWidth — sidebar vs full-width layout.
// ────────────────────────────────────────────────────────────────────

/**
 * Switch the structure container to the condensed sidebar layout.
 * Mirrors legacy `_makeCondensed`. When the toolbar is in structure
 * mode, also rewrites the URL so a refresh in condensed view loads
 * the edit URL (the visible content is content-mode, just with the
 * sidebar overlaid).
 */
export function makeCondensed(ctx: ModeContext): void {
    condensed = true;
    ctx.container.classList.add('cms-structure-condensed');

    if (getCmsSettings().mode === 'structure') {
        const editUrl = getCmsConfig().settings?.edit;
        if (editUrl !== undefined) {
            try {
                history.replaceState({}, '', editUrl);
            } catch {
                /* security exceptions in cross-origin iframes — ignore */
            }
        }
    }

    const toolbarWidth = ctx.toolbar.getBoundingClientRect().width;
    let gap = ctx.win.innerWidth - toolbarWidth;
    if (!gap) gap = measureScrollbar();

    ctx.html.classList.remove('cms-overflow');
    if (gap > 0) ctx.container.style.right = `${-gap}px`;
}

/**
 * Switch the structure container to the full-width layout. Mirrors
 * legacy `_makeFullWidth`. URL is rewritten back to the structure
 * URL when the toolbar is in structure mode.
 */
export function makeFullWidth(ctx: ModeContext): void {
    condensed = false;
    ctx.container.classList.remove('cms-structure-condensed');

    if (getCmsSettings().mode === 'structure') {
        const structureUrl = getCmsConfig().settings?.structure;
        if (structureUrl !== undefined) {
            try {
                history.replaceState({}, '', structureUrl);
            } catch {
                /* ignore — see makeCondensed */
            }
        }
        if (ctx.html.classList.contains('cms-structure-mode-structure')) {
            ctx.html.classList.add('cms-overflow');
        }
    }

    ctx.container.style.right = '0';
}

// ────────────────────────────────────────────────────────────────────
// toggleStructureBoard — flip mode based on current setting.
// ────────────────────────────────────────────────────────────────────

export interface ToggleOptions {
    /**
     * When true and the user is currently in edit mode, show the
     * board AND highlight the plugin under the cursor. Used by the
     * shift+space keybind. The actual highlight-on-show logic lives
     * in `ui/highlight.ts` (3i wires it).
     */
    useHoveredPlugin?: boolean;
    /**
     * Forwarded to the highlight pipeline — controls how long the
     * "successfully showed plugin X" indicator stays up.
     */
    successTimeout?: number;
    /**
     * Called when `useHoveredPlugin` is true and the toolbar is in
     * edit mode. The structureboard class shell wires this to the
     * `_showAndHighlightPlugin` method (3i).
     */
    onShowAndHighlight?(successTimeout?: number): Promise<unknown> | unknown;
}

/**
 * Flip the structure board mode based on the current `CMS.settings.mode`.
 * Mirrors legacy `_toggleStructureBoard`.
 */
export function toggleStructureBoard(
    ctx: ModeContext,
    options: ToggleOptions = {},
): void {
    const mode = getCmsSettings().mode;
    if (options.useHoveredPlugin && mode !== 'structure') {
        // Defer to the highlight pipeline — the caller provides it.
        const handler = options.onShowAndHighlight;
        if (handler) {
            const result = handler(options.successTimeout);
            if (result && typeof (result as Promise<unknown>).then === 'function') {
                (result as Promise<unknown>).then(
                    () => undefined,
                    () => undefined,
                );
            }
        }
        return;
    }
    if (options.useHoveredPlugin) return;

    if (mode === 'structure') {
        void hide(ctx);
    } else if (mode === 'edit') {
        void show(ctx);
    }
}
