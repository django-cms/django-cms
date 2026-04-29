/*
 * Toolbar class — port of `cms.toolbar.js`. The thin shell wires
 * together the focused submodules (`menus`, `long-menus`,
 * `delegate`) and provides the public surface consumed by other
 * bundles (`window.CMS.API.Toolbar`).
 *
 * Public surface:
 *
 *   class Toolbar {
 *       constructor(options?)
 *       openAjax(opts): Promise
 *       showLoader(): void
 *       hideLoader(): void
 *       _show(opts?): void           // animates the toolbar in
 *       _refreshMarkup(newToolbar):  // re-render after content swap
 *       _delegate(anchor): boolean | void
 *   }
 *
 * Mode-switcher behaviour (Space-key toggle, hash-link resolution)
 * lives in `structureboard/ui/switcher.ts` — not duplicated here.
 *
 * The `_initialStates` bootstrap is intentionally tolerant: every
 * `CMS.API.X` lookup is defensive so a contrib-only page (without
 * the legacy bundle) doesn't throw if Sideframe / Clipboard /
 * Messages haven't been wired yet.
 */

import { throttle } from 'lodash-es';

import { Helpers } from '../cms-base';
import { hideLoader, showLoader } from '../loader';
import { getCmsConfig, getMessages } from '../plugins/cms-globals';
import {
    delegate,
    openAjax,
    type OpenAjaxOptions,
} from './delegate';
import {
    setupLongMenus,
    type LongMenusController,
} from './long-menus';
import { setupMenus, type MenusHandle } from './menus';

const TOOLBAR_OFFSCREEN_OFFSET = 10; // hides box-shadow during animate-in
const LONG_MENUS_THROTTLE_MS = 10;

export interface ToolbarOptions {
    /** Animation duration in ms — 0 disables. */
    toolbarDuration?: number;
}

interface ToolbarUi {
    container: HTMLElement | null;
    body: HTMLElement;
    toolbar: HTMLElement | null;
    navigations: NodeListOf<HTMLElement>;
    buttons: NodeListOf<HTMLElement>;
    messages: HTMLElement | null;
    structureBoard: HTMLElement | null;
    toolbarSwitcher: HTMLElement | null;
    revert: HTMLElement | null;
}

export class Toolbar {
    public readonly options: Required<ToolbarOptions>;
    public ui!: ToolbarUi;

    private menusHandle: MenusHandle | null = null;
    private longMenus: LongMenusController | null = null;
    private buttonCleanups: Array<() => void> = [];
    private windowCleanups: Array<() => void> = [];
    public lockToolbar = false;

    constructor(options: ToolbarOptions = {}) {
        this.options = {
            toolbarDuration: 200,
            ...options,
        };

        this.setupUi();

        if (!this.ui.toolbar) return;

        // Legacy gate: don't double-bind events on the same toolbar
        // instance. The marker is a `data-cms-ready` attribute on
        // `.cms-toolbar`, set the first time we wire up.
        if (this.ui.toolbar.dataset.cmsReady !== 'true') {
            this.bindEvents();
            this.ui.toolbar.dataset.cmsReady = 'true';
        }

        this.runInitialStates();
    }

    // ────────────────────────────────────────────────────────────
    // Public surface
    // ────────────────────────────────────────────────────────────

    openAjax(opts: OpenAjaxOptions): Promise<unknown | false> {
        return openAjax(opts);
    }

    showLoader(): void {
        showLoader();
    }

    hideLoader(): void {
        hideLoader();
    }

    /**
     * Slide the toolbar into view by animating `<html>`'s margin-top
     * to the toolbar height. Legacy used jQuery `.animate()`; we use
     * a CSS transition on the html element so the user-visible
     * outcome is identical and we drop a runtime dep.
     */
    _show(opts?: { duration?: number }): void {
        const speed = opts?.duration ?? this.options.toolbarDuration;
        if (!this.ui.toolbar) return;
        const toolbarHeight =
            this.ui.toolbar.getBoundingClientRect().height +
            TOOLBAR_OFFSCREEN_OFFSET;
        const target = toolbarHeight - TOOLBAR_OFFSCREEN_OFFSET;

        this.ui.body.classList.add('cms-toolbar-expanding');

        if (speed > 0) {
            this.ui.body.style.transition = `margin-top ${speed}ms linear`;
        } else {
            this.ui.body.style.transition = '';
        }
        this.ui.body.style.marginTop = `${target}px`;

        const onDone = (): void => {
            this.ui.body.classList.remove('cms-toolbar-expanding');
            this.ui.body.classList.add('cms-toolbar-expanded');
            this.ui.body.style.transition = '';
        };
        if (speed > 0) {
            window.setTimeout(onDone, speed);
        } else {
            onDone();
        }

        if (this.ui.messages) {
            this.ui.messages.style.top = `${target}px`;
        }
    }

    /**
     * Replace the toolbar's rendered HTML with a fresh server render
     * (typically clipped from a content-mode response). Re-binds
     * every listener so the new markup is interactive. The mode
     * switcher node is preserved across the swap because it carries
     * structureboard state that must not reset.
     */
    _refreshMarkup(newToolbar: Element): void {
        if (!this.ui.toolbar) return;
        // Detach the live mode switcher so its event handlers persist.
        const switcher = this.ui.toolbarSwitcher;
        if (switcher && switcher.parentElement) {
            switcher.parentElement.removeChild(switcher);
        }

        // Replace the toolbar's children with the new render.
        this.ui.toolbar.replaceChildren(...Array.from(newToolbar.children));

        // Find the placeholder for the switcher in the new markup and
        // swap it back in.
        if (switcher) {
            const placeholder = this.ui.toolbar.querySelector<HTMLElement>(
                '.cms-toolbar-item-cms-mode-switcher',
            );
            if (placeholder && placeholder.parentElement) {
                placeholder.parentElement.replaceChild(switcher, placeholder);
            }
        }

        this.teardownEvents();
        this.setupUi();
        this.bindEvents();

        // Notify clipboard if it's around (legacy did this verbatim).
        const clipboard = (window.CMS?.API as { Clipboard?: unknown })
            ?.Clipboard;
        if (clipboard) {
            const cb = clipboard as {
                ui?: { triggers?: unknown; triggerRemove?: unknown };
                _toolbarEvents?: () => void;
            };
            if (cb.ui) {
                cb.ui.triggers = document.querySelectorAll(
                    '.cms-clipboard-trigger a',
                );
                cb.ui.triggerRemove = document.querySelectorAll(
                    '.cms-clipboard-empty a',
                );
            }
            cb._toolbarEvents?.();
        }
    }

    _delegate(anchor: HTMLAnchorElement): boolean | void {
        return delegate(anchor);
    }

    // ────────────────────────────────────────────────────────────
    // Internal wiring
    // ────────────────────────────────────────────────────────────

    private setupUi(): void {
        const container =
            document.querySelector<HTMLElement>('.cms') ?? null;
        this.ui = {
            container,
            body: document.documentElement,
            toolbar: container?.querySelector<HTMLElement>('.cms-toolbar') ?? null,
            navigations:
                container?.querySelectorAll<HTMLElement>(
                    '.cms-toolbar-item-navigation',
                ) ?? document.querySelectorAll<HTMLElement>('null'),
            buttons:
                container?.querySelectorAll<HTMLElement>(
                    '.cms-toolbar-item-buttons',
                ) ?? document.querySelectorAll<HTMLElement>('null'),
            messages:
                container?.querySelector<HTMLElement>('.cms-messages') ?? null,
            structureBoard:
                container?.querySelector<HTMLElement>('.cms-structure') ??
                null,
            toolbarSwitcher: document.querySelector<HTMLElement>(
                '.cms-toolbar-item-cms-mode-switcher',
            ),
            revert: document.querySelector<HTMLElement>('.cms-toolbar-revert'),
        };
    }

    private bindEvents(): void {
        if (!this.ui.toolbar) return;

        this.longMenus = setupLongMenus({
            body: this.ui.body,
            toolbar: this.ui.toolbar,
        });

        this.menusHandle = setupMenus({
            toolbar: this.ui.toolbar,
            structureBoard: this.ui.structureBoard ?? undefined,
            longMenus: this.longMenus,
            onTopLevelClick: (anchor) => this._delegate(anchor),
        });

        // Per-button click wiring (non-navigation toolbar items).
        for (const btn of Array.from(this.ui.buttons)) {
            const links = btn.querySelectorAll<HTMLAnchorElement>('a');
            for (const link of Array.from(links)) {
                if (
                    link.dataset.rel ||
                    link.classList.contains('cms-form-post-method')
                ) {
                    const handler = (e: Event): void => {
                        e.preventDefault();
                        this._delegate(link);
                    };
                    link.addEventListener('click', handler);
                    this.buttonCleanups.push(() =>
                        link.removeEventListener('click', handler),
                    );
                } else {
                    const handler = (e: Event): void => {
                        e.stopPropagation();
                    };
                    link.addEventListener('click', handler);
                    this.buttonCleanups.push(() =>
                        link.removeEventListener('click', handler),
                    );
                }
            }
        }

        // Window resize/scroll → recompute long-menus.
        const recompute = (): void => this.longMenus?.recompute();
        const throttled = throttle(recompute, LONG_MENUS_THROTTLE_MS);
        window.addEventListener('resize', throttled);
        window.addEventListener('scroll', throttled);
        this.windowCleanups.push(() => {
            window.removeEventListener('resize', throttled);
            window.removeEventListener('scroll', throttled);
            throttled.cancel();
        });
    }

    private teardownEvents(): void {
        this.menusHandle?.destroy();
        this.menusHandle = null;
        this.longMenus?.destroy();
        this.longMenus = null;
        for (const c of this.buttonCleanups) c();
        this.buttonCleanups = [];
        for (const c of this.windowCleanups) c();
        this.windowCleanups = [];
    }

    /**
     * The legacy `_initialStates` bootstrap. Tolerates missing
     * dependencies so the toolbar still constructs cleanly when
     * other CMS.API surfaces aren't available yet.
     */
    private runInitialStates(): void {
        // Hide publish button container (legacy only un-hides if a
        // sibling `.cms-btn-publish-active` exists).
        const publishBtn =
            document.querySelector<HTMLElement>('.cms-btn-publish');
        const publishHolder = publishBtn?.parentElement ?? null;

        this._show({ duration: 0 });

        if (publishHolder) {
            publishHolder.style.display = 'none';
            publishHolder.dataset.cmsHidden = 'true';
        }
        if (document.querySelector('.cms-btn-publish-active')) {
            if (publishHolder) {
                publishHolder.style.display = '';
                delete publishHolder.dataset.cmsHidden;
            }
            window.dispatchEvent(new Event('resize'));
        }
        if (publishHolder) hideDropdownIfRequired(publishHolder);

        const config = getCmsConfig();
        if ((config as { debug?: boolean }).debug) this.setupDebugBar();

        const messages = getMessages();
        const cfgMessage = (config as { messages?: string }).messages;
        const cfgError = (config as { error?: string }).error;
        const cfgPublisher = (config as { publisher?: string }).publisher;
        if (messages) {
            if (cfgMessage) messages.open({ message: cfgMessage });
            if (cfgError) messages.open({ message: cfgError, error: true });
            if (cfgPublisher)
                messages.open({
                    message: cfgPublisher,
                    delay: 3000,
                } as { message: string; delay?: number });
        }

        // Sideframe restore — defensive across the strangler period.
        this.maybeRestoreSideframe();

        // Color scheme — read theme from localStorage / config / 'auto'.
        try {
            const stored = localStorage.getItem('theme');
            const theme =
                stored ??
                (config as { color_scheme?: string }).color_scheme ??
                'auto';
            Helpers.setColorScheme(theme);
        } catch {
            /* no localStorage — accept the default */
        }

        this.ui.body.classList.add('cms-ready');
        Helpers.dispatchEvent('ready');
    }

    private setupDebugBar(): void {
        const lang = (getCmsConfig() as { lang?: { debug?: string } }).lang;
        if (!lang?.debug) return;
        const debug = this.ui.container?.querySelector<HTMLElement>(
            '.cms-debug-bar',
        );
        if (!debug) return;

        let timer: ReturnType<typeof setTimeout> | null = null;
        const onEnter = (): void => {
            if (timer !== null) clearTimeout(timer);
            timer = setTimeout(() => {
                getMessages()?.open({ message: lang.debug ?? '' });
            }, 1000);
        };
        const onLeave = (): void => {
            if (timer !== null) clearTimeout(timer);
            timer = null;
        };
        debug.addEventListener('mouseenter', onEnter);
        debug.addEventListener('mouseleave', onLeave);
        this.windowCleanups.push(() => {
            debug.removeEventListener('mouseenter', onEnter);
            debug.removeEventListener('mouseleave', onLeave);
            if (timer !== null) clearTimeout(timer);
        });
    }

    private maybeRestoreSideframe(): void {
        const settings = (window.CMS?.settings ?? {}) as {
            sideframe?: { url?: string };
            sideframe_enabled?: boolean;
        };
        const config = getCmsConfig() as { auth?: boolean };
        const enabled =
            typeof settings.sideframe_enabled === 'undefined' ||
            Boolean(settings.sideframe_enabled);
        if (
            !settings.sideframe?.url ||
            !config.auth ||
            !enabled
        ) {
            return;
        }
        const existing = (
            window.CMS?.API as { Sideframe?: { open(o: unknown): void } }
        )?.Sideframe;
        const Ctor = (
            window.CMS as {
                Sideframe?: new (
                    o?: Record<string, unknown>,
                ) => { open(o: unknown): void };
            }
        )?.Sideframe;
        const sideframe = existing ?? (Ctor ? new Ctor() : null);
        if (!sideframe) return;
        sideframe.open({
            url: settings.sideframe.url,
            animate: false,
        });
    }
}

function hideDropdownIfRequired(publishBtn: HTMLElement): void {
    const dropdown = publishBtn.closest<HTMLElement>('.cms-dropdown');
    if (!dropdown) return;
    const allItems = dropdown.querySelectorAll('li');
    const hidden = dropdown.querySelectorAll('li[data-cms-hidden]');
    if (allItems.length > 0 && allItems.length === hidden.length) {
        dropdown.style.display = 'none';
        dropdown.dataset.cmsHidden = 'true';
    }
}

export default Toolbar;
