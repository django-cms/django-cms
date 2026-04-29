/*
 * Bundle entry for `bundle.toolbar.min.js` — the drop-in replacement
 * for the legacy toolbar bundle.
 *
 * Wires every ported module onto the `window.CMS` global in the same
 * boot order as the legacy `cms/static/cms/js/toolbar.js`:
 *
 *   1. Helpers + KEYS exposed via cms-base (eager, side-effect import)
 *   2. CMS.<Module> constructors registered for backwards compat
 *   3. On DOM-ready: instantiate API.{Clipboard, StructureBoard,
 *      Messages, Tooltip, Toolbar, Sideframe} in the same order as
 *      legacy, then call Plugin tree initialisation.
 *
 * `initializeTree` is the canonical add path for new Plugin
 * instances — see `frontend/modules/plugins/tree.ts`.
 *
 * IMPORTANT — drop-in contract
 * ────────────────────────────
 * This bundle SHADOWS the legacy `bundle.toolbar.min.js` once
 * `cms.contrib.frontend_v5` is listed before `cms` in INSTALLED_APPS.
 * That means EVERY consumer (toolbar plugin code, third-party
 * extensions, custom admin pages) reading `window.CMS.Modal`,
 * `window.CMS.API.Toolbar`, etc. lands on the TS port. Adding a new
 * top-level module here means: same name on `window.CMS`, same
 * lifecycle (lazy vs eager), same instantiation order — or be
 * prepared for the strangler pattern's regressions.
 */

// Side-effect import — Helpers self-installs `CMS._eventRoot`,
// preventSubmit, etc. on DOM-ready.
import { Helpers, KEYS } from '../modules/cms-base';

import { ChangeTracker } from '../modules/changetracker';
import { Clipboard } from '../modules/clipboard/clipboard';
import keyboard from '../modules/keyboard';
import { Messages } from '../modules/messages';
import { Modal } from '../modules/modal/modal';
import { Navigation } from '../modules/navigation';
import { Plugin } from '../modules/plugins/plugin';
import { initializeTree } from '../modules/plugins/tree';
import { Sideframe } from '../modules/sideframe';
import { StructureBoard } from '../modules/structureboard/structureboard';
import { Toolbar } from '../modules/toolbar/toolbar';
import { Tooltip } from '../modules/tooltip';
import { trap, untrap } from '../modules/trap';

// ────────────────────────────────────────────────────────────────────
// Expose globals — same shape as legacy `toolbar.js`.
// ────────────────────────────────────────────────────────────────────

interface ToolbarBundleGlobals {
    Messages: typeof Messages;
    ChangeTracker: typeof ChangeTracker;
    Modal: typeof Modal;
    Sideframe: typeof Sideframe;
    Clipboard: typeof Clipboard;
    Navigation: typeof Navigation;
    Plugin: typeof Plugin;
    StructureBoard: typeof StructureBoard;
    Toolbar: typeof Toolbar;
    Tooltip: typeof Tooltip;
    KEYS?: typeof KEYS;
    keyboard?: typeof keyboard;
    trap?: typeof trap;
    untrap?: typeof untrap;
    API?: Record<string, unknown>;
    _plugins?: unknown[];
}

const cms = (window.CMS = window.CMS ?? {}) as Record<string, unknown> &
    ToolbarBundleGlobals;

cms._plugins = cms._plugins ?? [];

cms.Messages = Messages;
cms.ChangeTracker = ChangeTracker;
cms.Modal = Modal;
cms.Sideframe = Sideframe;
cms.Clipboard = Clipboard;
cms.Navigation = Navigation;
cms.Plugin = Plugin;
cms.StructureBoard = StructureBoard;
cms.Toolbar = Toolbar;
cms.Tooltip = Tooltip;

cms.API = (cms.API ?? {}) as Record<string, unknown>;
(cms.API as { Helpers?: typeof Helpers }).Helpers = Helpers;
cms.KEYS = KEYS;
cms.keyboard = keyboard;

// Trap/untrap exposed for legacy plugins that still call them directly.
cms.trap = trap;
cms.untrap = untrap;

// ────────────────────────────────────────────────────────────────────
// Boot — instantiate APIs in the same order as legacy toolbar.js
// ────────────────────────────────────────────────────────────────────

let booted = false;

function boot(): void {
    // HMR or stray re-imports can re-evaluate the module — skipping
    // here prevents double-instantiation of API.{Toolbar,…} and the
    // duplicate DOM listener registrations that follow.
    if (booted) return;
    booted = true;

    const cmsAny = cms as Record<string, unknown> & {
        config?: Record<string, unknown>;
        settings?: Record<string, unknown>;
        API: Record<string, unknown>;
    };

    // Bootstrap config from the JSON-serialised <script id="cms-config-json">
    // tag. Defensive — pages without a CMS toolbar (e.g. raw admin
    // change-form views) won't have it.
    if (!cmsAny.config) {
        const tag = document.getElementById('cms-config-json');
        if (tag) {
            try {
                cmsAny.config = JSON.parse(tag.textContent ?? '{}');
            } catch {
                cmsAny.config = {};
            }
        } else {
            cmsAny.config = {};
        }
    }

    // Settings come from localStorage; Helpers seeds from config when
    // versions don't match.
    try {
        cmsAny.settings = Helpers.getSettings();
    } catch {
        // localStorage disabled — fall back to config defaults.
        cmsAny.settings = (cmsAny.config?.settings ?? {}) as Record<
            string,
            unknown
        >;
    }

    // Order matters: Clipboard's modal needs `.cms-modal` markup;
    // StructureBoard reads `.cms-toolbar`; Toolbar runs initial states
    // that may dispatch messages; Sideframe restores from settings.
    const api = cmsAny.API;

    api.Clipboard = safeInstantiate('Clipboard', () => new Clipboard());
    api.StructureBoard = safeInstantiate(
        'StructureBoard',
        () => new StructureBoard(),
    );
    api.Messages = safeInstantiate('Messages', () => new Messages());
    api.Tooltip = safeInstantiate('Tooltip', () => new Tooltip());
    api.Toolbar = safeInstantiate('Toolbar', () => new Toolbar());
    api.Sideframe = safeInstantiate('Sideframe', () => new Sideframe());

    // Plugin tree — scans for `<script data-cms-plugin>` blobs and
    // creates Plugin instances. Idempotent if no blobs are present.
    try {
        initializeTree();
    } catch (err) {
        // eslint-disable-next-line no-console
        console.error('[cms] Plugin tree initialisation failed', err);
    }
}

/**
 * Instantiate a module, swallow construction errors. The legacy
 * bundle hard-fails on any one module — that's a footgun on
 * contrib-only pages where some markup might be absent. We keep the
 * console.error so problems are still observable.
 */
function safeInstantiate<T>(name: string, factory: () => T): T | undefined {
    try {
        return factory();
    } catch (err) {
        // eslint-disable-next-line no-console
        console.error(`[cms] Failed to instantiate ${name}`, err);
        return undefined;
    }
}

/**
 * Inject `cms.toolbar.css` next to whichever script loaded us. Drop-in
 * mode means the legacy bundle path `…/cms/js/dist/<version>/bundle.
 * toolbar.min.js` hosts us; the CSS sibling lives at `…/cms/css/<
 * version>/cms.toolbar.css`.
 *
 * URL resolution (most precise first):
 *   1. `document.currentScript.src` — the exact script that's running
 *      this code right now, even when multiple `bundle.toolbar*.js`
 *      tags coexist (e.g. legacy + contrib during deployment).
 *   2. `__webpack_public_path__` — the path webpack hard-codes at
 *      build time (`/static/cms/js/dist/<CMS_VERSION>/`). Always
 *      defined, so this is the reliable fallback even on pages that
 *      load the bundle dynamically (no matching `<script>`).
 *   3. As a last resort, scan `<script[src]>` for a matching tag.
 *
 * Idempotent — early-out on `data-cms-toolbar-css` to survive double-
 * load (the toolbar bundle is included on most admin pages).
 */
function ensureToolbarStylesheet(): void {
    if (document.querySelector('link[data-cms-toolbar-css]')) return;

    const cssHref = resolveToolbarCssHref();
    if (!cssHref) {
        // eslint-disable-next-line no-console
        console.warn(
            '[cms] Could not resolve cms.toolbar.css URL — drag visuals on ' +
                'the structureboard may not render.',
        );
        return;
    }

    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = cssHref;
    link.dataset.cmsToolbarCss = '';
    link.addEventListener('error', () => {
        // eslint-disable-next-line no-console
        console.warn(
            `[cms] Failed to load ${cssHref} — drag visuals on the ` +
                'structureboard may not render. Check STATIC_URL and the ' +
                "contrib app's static files.",
        );
    });
    document.head.appendChild(link);
}

const TOOLBAR_BUNDLE_RE = /\/cms\/js\/dist\/([^/]+)\/bundle\.toolbar(?:\.min)?\.js/;

function resolveToolbarCssHref(): string | null {
    // (1) document.currentScript — only set during initial classic-script
    // execution (i.e. exactly when this module runs). For module/async
    // loads it's null, so we fall through.
    const current = document.currentScript as HTMLScriptElement | null;
    if (current?.src && TOOLBAR_BUNDLE_RE.test(current.src)) {
        return toolbarCssFromScriptSrc(current.src);
    }

    // (2) __webpack_public_path__ — webpack inlines the configured
    // publicPath at build time. Format: `/static/cms/js/dist/<v>/`.
    // The `declare` keeps this typesafe without polluting the global
    // scope; webpack rewrites the symbol on bundle.
    const publicPath: string | undefined =
        typeof __webpack_public_path__ === 'string'
            ? __webpack_public_path__
            : undefined;
    if (publicPath) {
        const match = /\/cms\/js\/dist\/([^/]+)\/?$/.exec(publicPath);
        if (match) return `${publicPath.replace(/\/cms\/js\/dist\/.*$/, '')}/cms/css/${match[1]}/cms.toolbar.css`;
    }

    // (3) Last-resort scan. Picks the first matching script — only
    // hit if (1) and (2) both miss, which in practice means a hand-
    // rolled embed.
    for (const s of Array.from(document.querySelectorAll('script[src]'))) {
        const src = (s as HTMLScriptElement).src;
        if (TOOLBAR_BUNDLE_RE.test(src)) return toolbarCssFromScriptSrc(src);
    }
    return null;
}

function toolbarCssFromScriptSrc(src: string): string {
    return src.replace(
        /\/cms\/js\/dist\/([^/]+)\/bundle\.toolbar(?:\.min)?\.js.*$/,
        '/cms/css/$1/cms.toolbar.css',
    );
}

declare const __webpack_public_path__: string;

ensureToolbarStylesheet();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
} else {
    boot();
}

export default cms;
