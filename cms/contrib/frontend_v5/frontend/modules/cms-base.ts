/*
 * CMS.API.Helpers — cross-feature helpers exposed as a grab-bag object
 * on `window.CMS.API.Helpers`. Port of the legacy
 * `cms/static/cms/js/modules/cms.base.js`.
 *
 * jQuery decoupling (Phase 1 of the migration plan)
 * ─────────────────────────────────────────────────
 * This module USED to be the JQUERY GATEWAY: it imported jQuery at
 * module-load time, exported pre-wrapped `$window` / `$document`, and
 * ran `$(callback)` for DOM-ready wiring. All of that is gone — jQuery
 * is now strictly opt-in via `core/cms-jquery.ts`. The only Helpers
 * method that still needs jQuery is `csrf()`, which lazy-loads it via
 * `loadCmsJquery()` because it has to call `$.ajaxSetup` for legacy
 * callers that still issue jQuery-style ajax requests.
 *
 * Where the legacy module used jQuery:
 *
 *   - `$window` / `$document` exports — DROPPED (no remaining
 *     consumers in the v5 modules; toolbar bundle code that needed
 *     them isn't ported on this branch).
 *   - `$(callback)` DOM-ready — replaced with native
 *     `DOMContentLoaded` + `document.readyState` check.
 *   - `preventSubmit` (form submit guard) — native DOM equivalent.
 *   - `csrf` ($.ajaxSetup) — async, lazy-loads jQuery.
 *   - `addEventListener` / `removeEventListener` / `dispatchEvent`
 *     (legacy event bus on `#cms-top`) — delegate to `cmsEvents`,
 *     which has its own jQuery bridge so legacy `.trigger/.on` calls
 *     interop transparently.
 *   - `preventTouchScrolling` / `allowTouchScrolling` — native
 *     pointer/touch listeners + a WeakMap for namespace tracking.
 *   - `getColorScheme` / `setColorScheme` — native DOM (`html`
 *     element + `dataset.theme`, native iframe walk).
 *   - `_eventRoot` — set to the raw `#cms-top` HTMLElement; the
 *     `cmsEvents` jQuery bridge wraps it on demand if jQuery is
 *     loaded.
 *
 * Two intentional deviations from legacy:
 *
 *   1. The sync-ajax fallback in setSettings/getSettings is DROPPED.
 *      Legacy's `$.ajax({ async: false, … })` path for browsers
 *      without localStorage is removed — localStorage is universally
 *      available in 2026. If localStorage is unavailable at runtime,
 *      setSettings throws with a clear error instead of making a
 *      synchronous XHR.
 *
 *   2. `onPluginSave` and `_pluginExists` are ported as pass-through
 *      stubs that safely no-op when `window.CMS.API.StructureBoard`
 *      and `window.CMS._instances` are absent. Legacy assumes
 *      cms.plugins / cms.structureboard have loaded before these
 *      methods fire — in the contrib app those bundles aren't ported
 *      yet, so the pass-through behavior lets us ship admin.base
 *      independently.
 */

import { debounce, once, throttle } from 'lodash-es';

import { loadCmsJquery } from './core/cms-jquery';
import { cmsEvents } from './core/event-bus';
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

/**
 * Run `cb` once the DOM is ready. Replaces the legacy `$(cb)` shortcut
 * with native semantics: fires immediately if the document has already
 * passed the `loading` state, otherwise waits for `DOMContentLoaded`.
 */
const onDomReady = (cb: () => void): void => {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', cb, { once: true });
    } else {
        cb();
    }
};

// ────────────────────────────────────────────────────────────────────
// Named exports consumed across the CMS codebase
// ────────────────────────────────────────────────────────────────────

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
    /**
     * Lazy-loads jQuery on first call so legacy `$.ajax` consumers
     * have CSRF wired up. Async because the load may take a network
     * round-trip on first use.
     */
    csrf(csrfToken: string): Promise<void>;
    setSettings(newSettings: Record<string, unknown>): Record<string, unknown>;
    getSettings(): Record<string, unknown>;
    makeURL(url: string, params?: Array<[string, string]>): string;
    secureConfirm(message: string): boolean;
    readonly _isStorageSupported: boolean;
    /** Subscribe to a `cms-`-namespaced event on the shared bus. */
    addEventListener(eventName: string, fn: (payload?: unknown) => void): void;
    /**
     * Unsubscribe a previously-registered handler. Per-handler removal
     * requires the same function reference that was passed to
     * `addEventListener`.
     */
    removeEventListener(eventName: string, fn?: (payload?: unknown) => void): void;
    dispatchEvent(eventName: string, payload?: unknown): void;
    preventTouchScrolling(element: HTMLElement, namespace: string): void;
    allowTouchScrolling(element: HTMLElement, namespace: string): void;
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

/**
 * Map of (eventName + namespace) → registered native handler, used by
 * `preventTouchScrolling` / `allowTouchScrolling` to support the
 * legacy "namespaced unbind" semantics on plain DOM elements.
 */
const TOUCH_HANDLERS = new WeakMap<HTMLElement, Map<string, EventListener>>();

/**
 * Map of original add-event-listener handler → cmsEvents unsubscribe
 * function. `removeEventListener(name, fn)` looks up the dispose to
 * call. Stores per (eventName, fn) pair.
 */
const EVENT_DISPOSERS = new WeakMap<
    (...args: never[]) => unknown,
    Map<string, () => void>
>();

export const Helpers: HelpersType = {
    _isReloading: false,

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
    // Form submit guard (toolbar forms) — native DOM
    // ────────────────────────────────────────────────────────────

    preventSubmit() {
        const SUBMITTED_OPACITY = '0.5';
        // Bind once to every toolbar form. Legacy used jQuery
        // delegation but the toolbar markup is static after page-ready,
        // so a one-shot scan is sufficient.
        const forms = document.querySelectorAll<HTMLFormElement>(
            '.cms-toolbar form',
        );
        forms.forEach((form) => {
            form.addEventListener('submit', () => {
                showLoader();
                document
                    .querySelectorAll<HTMLInputElement>('input[type="submit"]')
                    .forEach((input) => {
                        input.addEventListener('click', (e) => {
                            e.preventDefault();
                        });
                        input.style.opacity = SUBMITTED_OPACITY;
                    });
            });
        });
    },

    // ────────────────────────────────────────────────────────────
    // Legacy jQuery AJAX CSRF setup (lazy)
    // ────────────────────────────────────────────────────────────

    async csrf(csrfToken) {
        // Loaded lazily because this is the only Helpers method that
        // needs jQuery on a contrib-only page; pulling it in eagerly
        // would defeat the lazy-load contract for `CMS.$`.
        const $ = await loadCmsJquery();
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
    // Event bus — delegates to cmsEvents
    // ────────────────────────────────────────────────────────────

    addEventListener(eventName, fn) {
        const namespaced = nameSpaceEvent(eventName);
        const types = namespaced.split(/\s+/g);
        // Track every dispose so removeEventListener(name, fn) can find
        // them later. Same fn registered against multiple type-names
        // (legacy supports space-separated `'foo bar'`) gets one entry
        // per type.
        let perFn = EVENT_DISPOSERS.get(fn as (...args: never[]) => unknown);
        if (!perFn) {
            perFn = new Map();
            EVENT_DISPOSERS.set(fn as (...args: never[]) => unknown, perFn);
        }
        for (const type of types) {
            const dispose = cmsEvents.on(type, fn);
            perFn.set(type, dispose);
        }
    },

    removeEventListener(eventName, fn) {
        const types = nameSpaceEvent(eventName).split(/\s+/g);
        if (fn) {
            const perFn = EVENT_DISPOSERS.get(fn as (...args: never[]) => unknown);
            if (!perFn) return;
            for (const type of types) {
                perFn.get(type)?.();
                perFn.delete(type);
            }
            return;
        }
        // No fn → drop every disposer that matches one of the types.
        // We can't enumerate WeakMap keys, so without a fn parameter
        // there's nothing reliable to do; this matches the documented
        // contract that fn-less unbind is best-effort.
    },

    dispatchEvent(eventName, payload) {
        const types = nameSpaceEvent(eventName).split(/\s+/g);
        for (const type of types) {
            cmsEvents.emit(type, payload);
        }
    },

    // ────────────────────────────────────────────────────────────
    // Touch scroll helpers — native, namespaced via WeakMap
    // ────────────────────────────────────────────────────────────

    preventTouchScrolling(element, namespace) {
        let map = TOUCH_HANDLERS.get(element);
        if (!map) {
            map = new Map();
            TOUCH_HANDLERS.set(element, map);
        }
        const key = `touchmove.cms.preventscroll.${namespace}`;
        if (map.has(key)) return;
        const handler: EventListener = (e) => e.preventDefault();
        element.addEventListener('touchmove', handler, { passive: false });
        map.set(key, handler);
    },

    allowTouchScrolling(element, namespace) {
        const map = TOUCH_HANDLERS.get(element);
        if (!map) return;
        const key = `touchmove.cms.preventscroll.${namespace}`;
        const handler = map.get(key);
        if (!handler) return;
        element.removeEventListener('touchmove', handler);
        map.delete(key);
    },

    // ────────────────────────────────────────────────────────────
    // Window accessor (exists so reloadBrowser can be tested with a stub)
    // ────────────────────────────────────────────────────────────

    _getWindow() {
        return window;
    },

    // ────────────────────────────────────────────────────────────
    // Color scheme (light / dark / auto) — native DOM
    // ────────────────────────────────────────────────────────────

    getColorScheme() {
        const html = document.documentElement;
        const state = html.getAttribute('data-theme');
        if (state) return state;
        return (
            localStorage.getItem('theme') ??
            (window.CMS?.config?.color_scheme as string | undefined) ??
            'auto'
        );
    },

    setColorScheme(mode) {
        const html = document.documentElement;
        const scheme = mode !== 'light' && mode !== 'dark' ? 'auto' : mode;

        // Only set localStorage if it was already set OR if scheme
        // differs from the server-side preset. Avoids locking the user
        // to the preset even after the preset changes server-side.
        const configScheme = window.CMS?.config?.color_scheme as string | undefined;
        if (localStorage.getItem('theme') || configScheme !== scheme) {
            localStorage.setItem('theme', scheme);
        }

        html.setAttribute('data-theme', scheme);
        // Recursively apply to every iframe nested inside `div.cms`.
        const applyToFrames = (root: Document | HTMLIFrameElement['contentDocument']) => {
            if (!root) return;
            const frames = root.querySelectorAll<HTMLIFrameElement>(
                'div.cms iframe',
            );
            frames.forEach((frame) => {
                const inner = frame.contentDocument;
                if (!inner) return;
                inner.documentElement.dataset.theme = scheme;
                applyToFrames(inner);
            });
        };
        applyToFrames(document);
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

onDomReady(() => {
    // The event bus root. Legacy code listens via
    // `$('#cms-top').on('cms-…', …)`; the cmsEvents jQuery bridge
    // wraps this element on demand if jQuery is loaded, so storing
    // the raw HTMLElement keeps both new and legacy paths happy.
    if (window.CMS) {
        window.CMS._eventRoot = document.getElementById('cms-top');
    }
    Helpers.preventSubmit();
});
