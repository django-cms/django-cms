/*
 * CMS.API.Helpers — cross-feature helpers exposed as a grab-bag object
 * on `window.CMS.API.Helpers`. Port of the legacy
 * `cms/static/cms/js/modules/cms.base.js`.
 *
 * This is the JQUERY GATEWAY module of the contrib app. Per CLAUDE.md
 * decision 7/7a, `admin.base.ts` (which imports this file) is the ONLY
 * internal TS file permitted to import jQuery. All the jQuery-flavored
 * primitives exported from here — `$window`, `$document`, the event
 * bus (`addEventListener`/`removeEventListener`/`dispatchEvent`), the
 * `csrf()` $.ajaxSetup wrapper, and the touch-scroll helpers with
 * namespaced events — keep jQuery semantics exactly on the first port
 * so downstream legacy modules (and third-party code hooking into
 * `$('#cms-top').on('cms-*', …)`) keep working.
 *
 * Decision 7a says we migrate the event bus to native CustomEvent at
 * the END of the migration, when every downstream bundle is ported
 * and we've audited third-party subscribers. Task #34 tracks that.
 *
 * Two intentional deviations from legacy:
 *
 *   1. The sync-ajax fallback in setSettings/getSettings is DROPPED.
 *      Legacy's `$.ajax({ async: false, … })` path for browsers
 *      without localStorage is removed — localStorage is universally
 *      available in 2026. If localStorage is unavailable at runtime,
 *      setSettings throws with a clear error instead of making a
 *      synchronous XHR. Matches the "strict improvement" spirit of
 *      the CSP refactor direction.
 *
 *   2. `onPluginSave` and `_pluginExists` are ported as pass-through
 *      stubs that safely no-op when `window.CMS.API.StructureBoard`
 *      and `window.CMS._instances` are absent. Legacy assumes
 *      cms.plugins / cms.structureboard have loaded before these
 *      methods fire — in the contrib app those bundles aren't ported
 *      yet, so the pass-through behavior lets us ship admin.base
 *      independently.
 */

import $ from 'jquery';
import { debounce, once, throttle } from 'lodash-es';

import { hideLoader, showLoader } from './loader';

// ────────────────────────────────────────────────────────────────────
// Internal helpers
// ────────────────────────────────────────────────────────────────────

/**
 * Prefix every event name in a space-separated list with `cms-`. Used
 * by the event bus to namespace pub/sub events on `#cms-top`.
 */
const nameSpaceEvent = (events: string): string =>
    events
        .split(/\s+/g)
        .map((eventName) => `cms-${eventName}`)
        .join(' ');

// ────────────────────────────────────────────────────────────────────
// Named exports consumed across the CMS codebase
// ────────────────────────────────────────────────────────────────────

/** Cached jQuery handles. Downstream modules expect JQuery, not plain window/document. */
export const $window: JQuery<Window & typeof globalThis> = $(window);
export const $document: JQuery<Document> = $(document);

/** Monotonic counter factory — returns 1, 2, 3, … across the process lifetime. */
export const uid: () => number = (() => {
    let i = 0;
    return () => ++i;
})();

/**
 * Check whether the settings blob was written by the currently-running
 * CMS version. Used to invalidate stale localStorage settings after a
 * CMS upgrade. `__CMS_VERSION__` is a webpack DefinePlugin constant
 * replaced at build time with the `cms/__init__.py` version.
 */
export const currentVersionMatches = ({ version }: { version?: string }): boolean =>
    version === __CMS_VERSION__;

// ────────────────────────────────────────────────────────────────────
// Helpers type + implementation
// ────────────────────────────────────────────────────────────────────

/**
 * Shape of the exported `Helpers` object. Downstream bundles import
 * `Helpers` and access its methods directly, so the interface reflects
 * the public API surface.
 *
 * NOTE on `this`: several methods rely on `this` being bound to the
 * Helpers object itself (e.g. `reloadBrowser` calls `this._getWindow`,
 * `updateUrlWithPath` calls `this.makeURL`, `toggleColorScheme` calls
 * `this.getColorScheme` + `this.setColorScheme`). Callers must invoke
 * these as methods: `Helpers.reloadBrowser(...)`, not via detached
 * references. This matches legacy behavior; breaking it would silently
 * fail at runtime.
 */
export interface HelpersType {
    /** Internal flag — see `reloadBrowser`. */
    _isReloading: boolean;

    /** Cached jQuery wrappers (re-exported for consumers that do `Helpers.$window`). */
    readonly $window: JQuery<Window & typeof globalThis>;
    readonly $document: JQuery<Document>;

    /** Monotonic counter — see top-level export. */
    readonly uid: () => number;

    /** Lodash re-exports. */
    readonly once: typeof once;
    readonly debounce: typeof debounce;
    readonly throttle: typeof throttle;

    /** Payload set by close_frame.html before `onPluginSave` fires. */
    dataBridge?: {
        action?: string;
        plugin_id?: string | number;
        [key: string]: unknown;
    };

    reloadBrowser(url?: string | null, timeout?: number): void;
    onPluginSave(): void;
    _pluginExists(pluginId: string | number): boolean;
    preventSubmit(): void;
    csrf(csrfToken: string): void;
    setSettings(newSettings: Record<string, unknown>): Record<string, unknown>;
    getSettings(): Record<string, unknown>;
    makeURL(url: string, params?: Array<[string, string]>): string;
    secureConfirm(message: string): boolean;
    readonly _isStorageSupported: boolean;
    addEventListener(eventName: string, fn: (...args: unknown[]) => void): unknown;
    removeEventListener(
        eventName: string,
        fn?: (...args: unknown[]) => void,
    ): unknown;
    dispatchEvent(eventName: string, payload?: unknown): unknown;
    preventTouchScrolling(element: JQuery, namespace: string): void;
    allowTouchScrolling(element: JQuery, namespace: string): void;
    _getWindow(): Window & typeof globalThis;
    updateUrlWithPath(url: string): string;
    getColorScheme(): string;
    setColorScheme(mode: string): void;
    toggleColorScheme(): void;
}

/**
 * Is localStorage usable? Cached at module-load time. Returns false
 * if localStorage throws on write — happens in private-browsing mode
 * on some legacy browsers, or when the user has disabled storage.
 */
const _isStorageSupported: boolean = (() => {
    const probe = 'cms_storage_probe';
    try {
        localStorage.setItem(probe, probe);
        localStorage.removeItem(probe);
        return true;
    } catch {
        /* istanbul ignore next */
        return false;
    }
})();

export const Helpers: HelpersType = {
    _isReloading: false,

    $window,
    $document,

    uid,
    once,
    debounce,
    throttle,

    _isStorageSupported,

    // ────────────────────────────────────────────────────────────
    // Navigation / page reload
    // ────────────────────────────────────────────────────────────

    reloadBrowser(url, timeout) {
        const win = this._getWindow();
        const parent = win.parent ?? win;
        this._isReloading = true;

        parent.setTimeout(() => {
            if (url === 'REFRESH_PAGE' || !url || url === parent.location.href) {
                parent.location.reload();
            } else {
                parent.location.href = url;
            }
        }, timeout ?? 0);
    },

    // ────────────────────────────────────────────────────────────
    // Plugin save glue — pass-through stubs
    // ────────────────────────────────────────────────────────────

    onPluginSave() {
        const data = this.dataBridge ?? {};
        const action = data.action ? data.action.toUpperCase() : null;

        // Resolve at call time — StructureBoard isn't ported yet, so
        // the global may be undefined on a fresh contrib-only page.
        // When the legacy structureboard is present (dual-stack
        // scenario during migration), it hooks into the same
        // `window.CMS.API.StructureBoard` reference and things work.
        const structureBoard = window.CMS?.API?.StructureBoard;

        switch (action) {
            case 'CHANGE':
            case 'EDIT':
                if (this._pluginExists(data.plugin_id ?? '')) {
                    structureBoard?.invalidateState?.('EDIT', data);
                } else {
                    structureBoard?.invalidateState?.('ADD', data);
                }
                return;
            case 'ADD':
            case 'DELETE':
            case 'CLEAR_PLACEHOLDER':
                structureBoard?.invalidateState?.(action, data);
                return;
            default:
                break;
        }

        if (!this._isReloading) {
            this.reloadBrowser(null, 300);
        }
    },

    _pluginExists(pluginId) {
        const instances = window.CMS?._instances;
        if (!instances) return false;
        return instances.some(
            (plugin) =>
                Number(plugin.options.plugin_id) === Number(pluginId) &&
                plugin.options.type === 'plugin',
        );
    },

    // ────────────────────────────────────────────────────────────
    // Form submit guard (toolbar forms)
    // ────────────────────────────────────────────────────────────

    preventSubmit() {
        const forms = $('.cms-toolbar').find('form');
        const SUBMITTED_OPACITY = 0.5;

        // Using `.submit` (jQuery shortcut) + `.on('click', …)` matches
        // the legacy semantics: after the first submit, subsequent
        // button clicks preventDefault and the submit buttons become
        // translucent as a visual lock. Kept as jQuery because this
        // method runs on the toolbar which is still legacy.
        forms.on('submit', () => {
            showLoader();
            $('input[type="submit"]')
                .on('click', (e) => {
                    e.preventDefault();
                })
                .css('opacity', SUBMITTED_OPACITY);
        });
    },

    // ────────────────────────────────────────────────────────────
    // Legacy jQuery AJAX CSRF setup
    // ────────────────────────────────────────────────────────────

    csrf(csrfToken) {
        // Attach CSRF header to every subsequent jQuery ajax call.
        // Our `request.ts` wrapper doesn't need this (it handles CSRF
        // per-call), but legacy bundles still use `$.ajax` and require
        // the header. Keep this live until all legacy ajax calls are
        // ported.
        $.ajaxSetup({
            beforeSend(xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrfToken);
            },
        });
    },

    // ────────────────────────────────────────────────────────────
    // Settings persistence (localStorage only — sync-ajax fallback dropped)
    // ────────────────────────────────────────────────────────────

    setSettings(newSettings) {
        if (!this._isStorageSupported) {
            throw new Error(
                'CMS settings persistence requires localStorage. The legacy ' +
                    'synchronous-ajax fallback has been dropped in the frontend_v5 ' +
                    'rewrite. Enable localStorage (it is disabled in some private- ' +
                    'browsing modes and by some privacy extensions).',
            );
        }

        const merged = { ...(window.CMS?.config?.settings ?? {}), ...newSettings };
        const serialized = JSON.stringify(merged);
        localStorage.setItem('cms_cookie', serialized);

        if (window.CMS) {
            window.CMS.settings = merged;
        }
        return merged;
    },

    getSettings() {
        if (!this._isStorageSupported) {
            throw new Error(
                'CMS settings persistence requires localStorage. The legacy ' +
                    'synchronous-ajax fallback has been dropped in the frontend_v5 ' +
                    'rewrite.',
            );
        }

        let settings: Record<string, unknown> | null = null;
        try {
            const raw = localStorage.getItem('cms_cookie');
            settings = raw ? (JSON.parse(raw) as Record<string, unknown>) : null;
        } catch {
            settings = null;
        }

        // If the stored settings don't match the current CMS version,
        // re-seed from `window.CMS.config.settings` (server-rendered
        // defaults) via setSettings, which also persists.
        if (!settings || !currentVersionMatches(settings as { version?: string })) {
            settings = this.setSettings(window.CMS?.config?.settings ?? {});
        }

        if (window.CMS) {
            window.CMS.settings = settings;
        }
        return settings;
    },

    // ────────────────────────────────────────────────────────────
    // URL manipulation
    // ────────────────────────────────────────────────────────────

    makeURL(url, params) {
        const urlParams = params ?? [];
        // Decode + normalise &amp; → & (see #3404).
        const decodedUrl = decodeURIComponent(url.replace(/&amp;/g, '&'));
        const hadLeadingSlash = decodedUrl.startsWith('/');

        let parsed: URL;
        let isAbsolute = false;
        try {
            parsed = new URL(decodedUrl);
            isAbsolute = true;
        } catch {
            parsed = new URL(decodedUrl, window.location.origin);
        }

        for (const [key, value] of urlParams) {
            parsed.searchParams.delete(key);
            parsed.searchParams.set(key, value);
        }

        if (isAbsolute) return parsed.toString();

        let result = parsed.pathname + parsed.search + parsed.hash;
        if (!hadLeadingSlash && result.startsWith('/')) {
            result = result.substring(1);
        }
        return result;
    },

    updateUrlWithPath(url) {
        const win = this._getWindow();
        const path = win.location.pathname + win.location.search;
        return this.makeURL(url, [['cms_path', path]]);
    },

    // ────────────────────────────────────────────────────────────
    // Confirm wrapper — timing-based fallback for "prevent this page from creating additional dialogs"
    // ────────────────────────────────────────────────────────────

    secureConfirm(message) {
        // Browsers let users tick a "Prevent this page from creating
        // additional dialogs" checkbox. When that's checked, subsequent
        // `confirm()` calls return instantly without showing a dialog.
        // We detect this by measuring wall-clock duration of the call:
        // if it returned in under 10ms, assume the user never saw a
        // dialog and treat the result as "confirmed" (i.e. allow the
        // action rather than silently cancel).
        const MINIMUM_DELAY = 10;
        const start = Date.now();
        // eslint-disable-next-line no-alert
        const result = confirm(message);
        const end = Date.now();
        return end < start + MINIMUM_DELAY || result === true;
    },

    // ────────────────────────────────────────────────────────────
    // Event bus (Option B — jQuery preserved per decision 7a)
    // ────────────────────────────────────────────────────────────

    addEventListener(eventName, fn) {
        // `window.CMS._eventRoot` is set by the module initializer
        // below to $('#cms-top'). Loosely typed in CmsGlobal — we know
        // it's a JQuery at runtime.
        const root = window.CMS?._eventRoot as JQuery | undefined;
        return root?.on(nameSpaceEvent(eventName), fn as JQuery.EventHandlerBase<unknown, JQuery.Event>);
    },

    removeEventListener(eventName, fn) {
        const root = window.CMS?._eventRoot as JQuery | undefined;
        if (fn) {
            return root?.off(nameSpaceEvent(eventName), fn as JQuery.EventHandlerBase<unknown, JQuery.Event>);
        }
        return root?.off(nameSpaceEvent(eventName));
    },

    dispatchEvent(eventName, payload) {
        const root = window.CMS?._eventRoot as JQuery | undefined;
        if (!root) return undefined;
        const event = $.Event(nameSpaceEvent(eventName));
        root.trigger(event, [payload]);
        return event;
    },

    // ────────────────────────────────────────────────────────────
    // Touch scroll helpers (jQuery namespaced events preserved)
    // ────────────────────────────────────────────────────────────

    preventTouchScrolling(element, namespace) {
        element.on(`touchmove.cms.preventscroll.${namespace}`, (e) => {
            e.preventDefault();
        });
    },

    allowTouchScrolling(element, namespace) {
        element.off(`touchmove.cms.preventscroll.${namespace}`);
    },

    // ────────────────────────────────────────────────────────────
    // Window accessor (exists so reloadBrowser can be tested with a stub)
    // ────────────────────────────────────────────────────────────

    _getWindow() {
        return window;
    },

    // ────────────────────────────────────────────────────────────
    // Color scheme (light / dark / auto)
    // ────────────────────────────────────────────────────────────

    getColorScheme() {
        let state = $('html').attr('data-theme');
        if (!state) {
            state =
                localStorage.getItem('theme') ??
                (window.CMS?.config?.color_scheme as string | undefined) ??
                'auto';
        }
        return state;
    },

    setColorScheme(mode) {
        const body = $('html');
        const scheme = mode !== 'light' && mode !== 'dark' ? 'auto' : mode;

        // Only set localStorage if it was already set OR if scheme
        // differs from the server-side preset. Avoids locking the user
        // to the preset even after the preset changes server-side.
        const configScheme = window.CMS?.config?.color_scheme as string | undefined;
        if (localStorage.getItem('theme') || configScheme !== scheme) {
            localStorage.setItem('theme', scheme);
        }

        body.attr('data-theme', scheme);
        body.find('div.cms iframe').each(function setFrameColorScheme(
            _i: number,
            el: HTMLElement,
        ) {
            const e = el as HTMLIFrameElement;
            if (e.contentDocument) {
                e.contentDocument.documentElement.dataset.theme = scheme;
                $(e.contentDocument).find('iframe').each(setFrameColorScheme);
            }
        });
    },

    toggleColorScheme() {
        const currentTheme = this.getColorScheme();
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        if (prefersDark) {
            // Auto (effectively dark) → Light → Dark → Auto
            if (currentTheme === 'auto') this.setColorScheme('light');
            else if (currentTheme === 'light') this.setColorScheme('dark');
            else this.setColorScheme('auto');
        } else {
            // Auto (effectively light) → Dark → Light → Auto
            if (currentTheme === 'auto') this.setColorScheme('dark');
            else if (currentTheme === 'dark') this.setColorScheme('light');
            else this.setColorScheme('auto');
        }
    },
};

// ────────────────────────────────────────────────────────────────────
// Keyboard constants
// ────────────────────────────────────────────────────────────────────

/**
 * Key code lookup. Legacy API — modern code should prefer
 * `event.key === 'Enter'` string comparisons. Kept here for
 * backwards compatibility with downstream bundles that do
 * `e.keyCode === CMS.KEYS.ENTER`.
 */
export const KEYS = {
    SHIFT: 16,
    TAB: 9,
    UP: 38,
    DOWN: 40,
    ENTER: 13,
    SPACE: 32,
    ESC: 27,
    CMD_LEFT: 91,
    CMD_RIGHT: 93,
    CMD_FIREFOX: 224,
    CTRL: 17,
} as const;

// ────────────────────────────────────────────────────────────────────
// Module initializer — runs at DOM-ready time
// ────────────────────────────────────────────────────────────────────

/**
 * Legacy does this with `$(function() { ... })`. We use jQuery's ready
 * shortcut directly so the semantics match exactly (including the
 * "run immediately if DOM is already ready" behavior).
 */
$(() => {
    // The event bus root. Every addEventListener / dispatchEvent call
    // hooks .on()/.trigger() on this element. The element comes from
    // the template (admin bundles include `<div id="cms-top">`).
    if (window.CMS) {
        window.CMS._eventRoot = $('#cms-top');
    }
    Helpers.preventSubmit();
});

// ────────────────────────────────────────────────────────────────────
// Legacy default export (for tests / consumers that import the whole module)
// ────────────────────────────────────────────────────────────────────

const _CMS = {
    API: { Helpers },
    KEYS,
};
export default _CMS;
