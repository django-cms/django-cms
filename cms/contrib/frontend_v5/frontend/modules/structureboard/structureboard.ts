/*
 * StructureBoard class shell.
 *
 * Wires every prior sub-phase module into the legacy
 * `window.CMS.API.StructureBoard` surface. The class is intentionally
 * thin — almost every method delegates to a function in
 * `parsers/`, `network/`, `dom/`, `handlers/`, `ui/` etc. The class's
 * job is to:
 *
 *   - Stand up the live `ModeContext` (DOM refs + load callbacks)
 *   - Hold instance state (`dragging`, `latestAction`, the dnd /
 *     switcher / preload teardown handles)
 *   - Translate the legacy method-name surface into module calls
 *   - Wire the dispatcher's `onContentRefresh` / `onFullReload`
 *     callbacks to `refresh.ts` and `Helpers.reloadBrowser`
 *
 * The static helpers (`actualizePlaceholders`, `getPluginDataFromMarkup`)
 * are re-exposed on the class so legacy callers reading
 * `CMS.API.StructureBoard.actualizePlaceholders()` still work during
 * the strangler period.
 */

import { Helpers } from '../cms-base';
import {
    getCmsConfig,
    getInstancesRegistry,
} from '../plugins/cms-globals';
import {
    refreshPlugins,
} from '../plugins/tree';
import type { Plugin } from '../plugins/plugin';
import {
    actualizePlaceholders,
    actualizePluginCollapseStatus,
    actualizePluginsCollapsibleStatus,
    initializeDragItemsStates,
} from './dom/actualize';
import {
    incrementScriptCount,
    scriptLoaded,
    setRefreshCallback,
    triggerRefreshEvents,
} from './dom/body-swap';
import { invalidateState, type InvalidateOptions } from './invalidate';
import {
    invalidateModeCache,
    requestMode,
} from './network/fetch';
import {
    listenToExternalUpdates,
} from './network/propagate';
import {
    elementPresent,
    extractMessages,
    getPluginDataFromMarkup,
} from './parsers/markup';
import { getId, getIds } from './parsers/ids';
import { refreshContent, updateContent } from './refresh';
import type {
    MutationData,
    ModeName,
    PluginMutationAction,
} from './types';
import {
    hide,
    isCondensed,
    makeCondensed,
    makeFullWidth,
    show,
    type ModeContext,
} from './ui/mode';
import { setupModeSwitcher, type SwitcherHandle } from './ui/switcher';
import { setupOppositeModePreload, type PreloadHandle } from './ui/preload';
import {
    setupStructureBoardDnd,
    type StructureBoardDndHandle,
} from './ui/dnd';
import {
    highlightPluginFromUrl,
    showAndHighlightPlugin,
    type ShowAndHighlightOptions,
} from './ui/highlight';

// ────────────────────────────────────────────────────────────────────
// UI element bag — modeled after the legacy `this.ui.*`. Held by
// the class so consumers reading `instance.ui.X` keep working.
// ────────────────────────────────────────────────────────────────────

interface StructureBoardUi {
    container: HTMLElement | null;
    content: HTMLElement | null;
    toolbar: HTMLElement | null;
    toolbarModeSwitcher: HTMLElement | null;
    toolbarModeLinks: HTMLElement[];
    html: HTMLElement;
    win: Window;
}

function setupUi(): StructureBoardUi {
    const toolbar = document.querySelector<HTMLElement>('.cms-toolbar');
    const switcher = toolbar?.querySelector<HTMLElement>(
        '.cms-toolbar-item-cms-mode-switcher',
    ) ?? null;
    const links = switcher
        ? Array.from(switcher.querySelectorAll<HTMLElement>('a'))
        : [];

    const ui: StructureBoardUi = {
        container: document.querySelector<HTMLElement>('.cms-structure'),
        content: document.querySelector<HTMLElement>('.cms-structure-content'),
        toolbar: toolbar ?? null,
        toolbarModeSwitcher: switcher,
        toolbarModeLinks: links,
        html: document.documentElement,
        win: window,
    };
    if (ui.content) {
        // Initial touch-action — mirrors legacy `_setupUI`.
        ui.content.style.touchAction = 'pan-y';
    }
    return ui;
}

// ────────────────────────────────────────────────────────────────────
// Class
// ────────────────────────────────────────────────────────────────────

export class StructureBoard {
    public ui: StructureBoardUi;

    /**
     * True while a drag is in progress. Read by `plugins/plugin.ts`
     * mouseenter handlers to suppress the shift-hover preview.
     */
    public dragging = false;

    /** Cross-tab dedup state — set by `invalidateState`. */
    public latestAction: [PluginMutationAction, MutationData] | [] = [];

    /** True after the structure-mode markup has been loaded. */
    public _loadedStructure = false;

    /**
     * True after the content-mode markup has been loaded. Synced from
     * `refresh.ts::getContentLoaded()` after `loadContent`.
     */
    public _loadedContent = false;

    private modeCtx: ModeContext;
    private dnd: StructureBoardDndHandle | null = null;
    private switcher: SwitcherHandle | null = null;
    private preload: PreloadHandle | null = null;
    private detachExternalUpdates: (() => void) | null = null;

    constructor() {
        this.ui = setupUi();
        this.modeCtx = this.buildModeContext();

        // Ditch any stale cross-tab payload from a prior session.
        try {
            localStorage.removeItem('cms-structure');
        } catch {
            /* private browsing — ignore */
        }

        // Wire the body-swap pipeline's "all scripts loaded" callback
        // into our refresh-events. The dom/body-swap module owns the
        // refcount; we own the post-swap signal.
        setRefreshCallback(() => {
            // No-op: triggerRefreshEvents already dispatches the
            // window-scoped events. Hook left wired so future signal
            // additions land in one place.
        });

        const setupResult = this._setup();
        if (setupResult === false) return;

        if (getCmsConfig().mode === 'draft') {
            this.preload = setupOppositeModePreload({
                isLoadedStructure: () => this._loadedStructure,
            });
        }

        this.switcher = setupModeSwitcher(this.modeCtx, {
            modeLinks: this.ui.toolbarModeLinks,
            ...(this.ui.toolbarModeSwitcher
                ? { switcher: this.ui.toolbarModeSwitcher }
                : {}),
            onShowAndHighlight: (timeout) =>
                showAndHighlightPlugin(this.modeCtx, {
                    ...(timeout !== undefined ? { successTimeout: timeout } : {}),
                }),
        });

        this._events();
        actualizePlaceholders();

        // URL-hash highlight — defer one tick so the toolbar+messages
        // module (legacy) can register first.
        setTimeout(() => highlightPluginFromUrl(), 0);

        this.detachExternalUpdates = listenToExternalUpdates((action, data) => {
            this.invalidateState(action, data as MutationData, {
                propagate: false,
            });
        });
    }

    // ────────────────────────────────────────────────────────────
    // Setup helpers
    // ────────────────────────────────────────────────────────────

    private buildModeContext(): ModeContext {
        return {
            container: this.ui.container ?? document.body,
            toolbar: this.ui.toolbar ?? document.body,
            html: this.ui.html,
            toolbarModeLinks: this.ui.toolbarModeLinks,
            win: this.ui.win,
            isLoadedStructure: () => this._loadedStructure,
            isLoadedContent: () => this._loadedContent,
            loadStructure: () => this._loadStructure(),
            loadContent: () => this._loadContent(),
        };
    }

    /**
     * Initial mode setup. Returns false to bail when no mode-switcher
     * is present (legacy `_setup`).
     */
    private _setup(): boolean | undefined {
        if (!this.ui.toolbarModeSwitcher) return false;

        const settings = getCmsConfig().settings ?? {};
        if (settings.mode === 'structure') {
            void this.show({ init: true });
            this._loadedStructure = true;
            initializeDragItemsStates();
        } else {
            void this.hide();
            this._loadedContent = true;
        }

        if (settings.legacy_mode) {
            this._loadedStructure = true;
            this._loadedContent = true;
        }

        // Enable mode-switcher buttons when there's at least one
        // (non-clipboard) dragarea or placeholder on the page.
        const hasDragareas = document.querySelectorAll(
            '.cms-dragarea:not(.cms-clipboard .cms-dragarea)',
        ).length;
        const hasPlaceholders = document.querySelectorAll('.cms-placeholder').length;
        if (hasDragareas || hasPlaceholders) {
            this.ui.toolbarModeSwitcher
                ?.querySelectorAll<HTMLElement>('.cms-btn')
                .forEach((btn) => btn.classList.remove('cms-btn-disabled'));
        }

        return undefined;
    }

    /**
     * Layout-related window listener. Mirrors legacy `_events`. The
     * resize listener flips between condensed and full layouts at
     * the 1024px breakpoint (only when content has finished loading
     * and the page is in draft mode).
     */
    private _events(): void {
        const BREAKPOINT = 1024;
        this.ui.win.addEventListener('resize', () => {
            if (!this._loadedContent) return;
            if (getCmsConfig().mode !== 'draft') return;
            const width = this.ui.win.innerWidth;
            if (width > BREAKPOINT && !isCondensed()) {
                makeCondensed(this.modeCtx);
            }
            if (width <= BREAKPOINT && isCondensed()) {
                makeFullWidth(this.modeCtx);
            }
        });
    }

    // ────────────────────────────────────────────────────────────
    // Public mode API — thin wrappers over `ui/mode.ts`.
    // ────────────────────────────────────────────────────────────

    show(options: { init?: boolean } = {}): Promise<boolean> {
        return show(this.modeCtx, options);
    }

    hide(): Promise<boolean> {
        return hide(this.modeCtx);
    }

    showAndHighlightPlugin(
        successTimeout?: number,
        seeThrough?: boolean,
    ): Promise<boolean> {
        const opts: ShowAndHighlightOptions = {};
        if (successTimeout !== undefined) opts.successTimeout = successTimeout;
        if (seeThrough !== undefined) opts.seeThrough = seeThrough;
        return showAndHighlightPlugin(this.modeCtx, opts);
    }

    highlightPluginFromUrl(): void {
        highlightPluginFromUrl();
    }

    // ────────────────────────────────────────────────────────────
    // Public mutation API.
    // ────────────────────────────────────────────────────────────

    invalidateState(
        action: PluginMutationAction | undefined | null | '',
        data: MutationData,
        opts: InvalidateOptions = {},
    ): void {
        if (action) {
            this.latestAction = [action, data];
        }
        invalidateState(action, data, {
            ...opts,
            onFullReload:
                opts.onFullReload ??
                ((): void => {
                    Helpers.reloadBrowser();
                }),
            onContentRefresh:
                opts.onContentRefresh ??
                ((_action, _data): void => {
                    invalidateModeCache('content');
                    void updateContent().catch(() => Helpers.reloadBrowser());
                }),
        });
        // After every successful mutation, refresh the dnd container
        // set — handlers may have inserted new placeholders.
        this.dnd?.refresh();
    }

    // ────────────────────────────────────────────────────────────
    // Loading pipelines.
    // ────────────────────────────────────────────────────────────

    /**
     * Fetch + apply structure-mode markup. Mirrors legacy
     * `_loadStructure`. Skipped when already loaded.
     *
     * The strategy is: fetch the structure URL, parse the body, copy
     * the `.cms-structure-content` HTML in, refresh the toolbar,
     * append cms scripts, then re-bind plugin instances + drag.
     */
    async _loadStructure(): Promise<void> {
        if (this._loadedStructure) return;
        const settings = getCmsConfig().settings ?? {};
        if (settings.mode === 'structure') {
            // Page was rendered server-side in structure mode — nothing
            // to fetch. Mark loaded and bail.
            this._loadedStructure = true;
            return;
        }

        let markup: string;
        try {
            markup = await requestMode('structure');
        } catch {
            // Fallback to a hard navigation — matches legacy.
            const url = settings.structure;
            if (url) window.location.href = url;
            return;
        }

        // Parse via DOMParser (legacy used a regex; DOMParser is
        // robust and we need full element access anyway).
        const doc = new DOMParser().parseFromString(markup, 'text/html');

        // Pull updated descriptor scripts in for `updateRegistry`.
        const draggables = Array.from(
            doc.body.querySelectorAll<HTMLElement>('.cms-draggable'),
        );
        const ids = getIds(draggables);
        const pluginData = getPluginDataFromMarkup(doc.body, ids);
        if (pluginData.length > 0) {
            const { updateRegistry } = await import('../plugins/tree');
            updateRegistry(pluginData);
        }

        // Refresh toolbar markup against the freshly-rendered toolbar.
        const newToolbar = doc.body.querySelector<HTMLElement>('.cms-toolbar');
        if (newToolbar) {
            const cms = window.CMS as
                | { API?: { Toolbar?: { _refreshMarkup?: (el: Element) => void } } }
                | undefined;
            cms?.API?.Toolbar?._refreshMarkup?.(newToolbar);
        }

        // Append cms scripts that came in the response (legacy
        // `[type="text/cms-template"]`). They're inert script tags but
        // some plugins read them via id.
        const cmsScripts = Array.from(
            doc.body.querySelectorAll<HTMLScriptElement>('[type="text/cms-template"]'),
        );
        for (const s of cmsScripts) document.body.appendChild(s);

        // Swap in the structure tree HTML.
        const newStructure = doc.body.querySelector<HTMLElement>(
            '.cms-structure-content',
        );
        if (this.ui.content && newStructure) {
            this.ui.content.innerHTML = newStructure.innerHTML;
        }

        // Re-bind structure-mode events. Mirrors legacy `_loadStructure`:
        // we DON'T call `refreshPlugins()` here because that wires
        // *content* events for plugins; structure mode needs each
        // plugin's `_setPluginStructureEvents` (drag handle, dropdown
        // wiring, add-plugin trigger) plus `_collapsables`. Placeholders
        // re-run their `_setPlaceholder` setup so the placeholder-level
        // submenu re-binds.
        actualizePlaceholders();
        const instances = getInstancesRegistry();
        for (const instance of instances) {
            if (instance.options.type !== 'placeholder') continue;
            (instance as Plugin)._setPlaceholder();
        }
        for (const instance of instances) {
            if (instance.options.type !== 'plugin') continue;
            const plugin = instance as Plugin;
            plugin._setPluginStructureEvents();
            plugin._collapsables();
        }
        initializeDragItemsStates();
        // Mount the drag clone + drop marker on the shared
        // `.cms-structure-content` scroller. Without an explicit host,
        // TreeDrag falls back to `containers[0].parentElement`, which is
        // the FIRST `.cms-dragarea` placeholder — the marker is then
        // clipped/mispositioned for any drop in the other placeholders.
        this.dnd = setupStructureBoardDnd(
            this.ui.content ? { host: this.ui.content } : {},
        );

        this._loadedStructure = true;
        this.ui.win.dispatchEvent(new Event('resize'));
    }

    /**
     * Fetch + apply content-mode markup. Thin wrapper over
     * `refresh.ts::updateContent`. Skipped when already loaded.
     *
     * Mirrors legacy `_loadContent` — but the body-swap path is the
     * one used by every mutation refresh too (refreshContent), so we
     * simply re-route here. Differences from the legacy path that
     * mattered (HTML attribute merge, unhandled-plugins detection)
     * land as follow-ups when we hit a regression in 3j Playwright.
     */
    async _loadContent(): Promise<void> {
        if (this._loadedContent) return;
        const settings = getCmsConfig().settings ?? {};
        if (settings.mode === 'edit') {
            this._loadedContent = true;
            return;
        }
        try {
            await updateContent();
            this._loadedContent = true;
        } catch {
            const url = settings.edit;
            if (url) window.location.href = url;
        }
    }

    // ────────────────────────────────────────────────────────────
    // Class-static helpers — mirror legacy `StructureBoard.X` surface.
    // ────────────────────────────────────────────────────────────

    /** Class-side `getId`. Legacy: `instance.getId(el)`. */
    getId(el: Element | null | undefined): number | undefined {
        return getId(el);
    }

    /** Class-side `getIds`. Legacy: `instance.getIds(els)`. */
    getIds(els: Iterable<Element>): number[] {
        return getIds(els);
    }

    /**
     * Test/migration teardown — release every listener bound by the
     * constructor. Vitest needs it; legacy never tore the class down.
     */
    destroy(): void {
        this.dnd?.destroy();
        this.switcher?.destroy();
        this.preload?.destroy();
        this.detachExternalUpdates?.();
        setRefreshCallback(null);
    }

    // ────────────────────────────────────────────────────────────
    // Static hooks — re-exposed for legacy `CMS.API.StructureBoard.X`.
    // ────────────────────────────────────────────────────────────

    static actualizePlaceholders = actualizePlaceholders;
    static actualizePluginCollapseStatus = actualizePluginCollapseStatus;
    static actualizePluginsCollapsibleStatus = actualizePluginsCollapsibleStatus;
    static _initializeDragItemsStates = initializeDragItemsStates;
    static _getPluginDataFromMarkup = getPluginDataFromMarkup;
    static _elementPresent = elementPresent;
    static _extractMessages = extractMessages;
    static _triggerRefreshEvents = triggerRefreshEvents;
    static refreshContent = refreshContent;

    // Internal hooks for legacy callers that participate in the
    // body-swap script refcount (sekizai 3g, etc.).
    static incrementScriptCount = incrementScriptCount;
    static scriptLoaded = scriptLoaded;
}

export type { ModeName, PluginMutationAction };
