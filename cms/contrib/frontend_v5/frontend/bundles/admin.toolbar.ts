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
 * `_initializeTree` is the canonical add path for new Plugin
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
}

const cms = (window.CMS = window.CMS ?? {}) as Record<string, unknown> &
    ToolbarBundleGlobals & {
        API?: Record<string, unknown>;
        KEYS?: typeof KEYS;
        keyboard?: typeof keyboard;
        _plugins?: unknown[];
    };

cms._plugins = (cms._plugins ?? []) as unknown[];

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
(cms as unknown as { trap?: typeof trap; untrap?: typeof untrap }).trap = trap;
(
    cms as unknown as { trap?: typeof trap; untrap?: typeof untrap }
).untrap = untrap;

// ────────────────────────────────────────────────────────────────────
// Boot — instantiate APIs in the same order as legacy toolbar.js
// ────────────────────────────────────────────────────────────────────

function boot(): void {
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

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
} else {
    boot();
}

export default cms;
