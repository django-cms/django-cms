/*
 * Clipboard class — port of `cms.clipboard.js`. Manages the toolbar
 * clipboard modal and cross-tab sync for plugin copy/cut/paste.
 *
 * Public surface (read by the toolbar bundle, by plugins, and by
 * structureboard's `_refreshMarkup`):
 *
 *   class Clipboard {
 *       constructor()
 *       ui: { triggers, triggerRemove, ... }
 *       _toolbarEvents(): void          // re-bind after toolbar refresh
 *       clear(callback?): void
 *       populate(html, pluginData): void
 *   }
 *
 * The class re-binds toolbar listeners on demand (the toolbar may
 * re-render its markup, replacing the trigger anchors). Each call
 * detaches previous listeners first, so it's idempotent.
 *
 * Cross-tab sync goes through `clipboard/sync.ts` (native `storage`
 * events; replaces `local-storage` npm dep).
 */

import { Helpers } from '../cms-base';
import { Modal } from '../modal/modal';
import {
    getCmsConfig,
    getInstancesRegistry,
    getToolbar,
} from '../plugins/cms-globals';
import {
    listenForExternalUpdates,
    writeClipboard,
    type ClipboardData,
} from './sync';

const MIN_WIDTH = 400;
const MIN_HEIGHT = 117;

interface ClipboardUi {
    clipboard: HTMLElement | null;
    triggers: HTMLAnchorElement[];
    triggerRemove: HTMLAnchorElement[];
    pluginsList: HTMLElement | null;
}

interface PluginConstructor {
    new (
        identifier: string,
        options: ClipboardData['data'],
    ): { options: ClipboardData['data']; [key: string]: unknown };
    _removeAddPluginPlaceholder?(): void;
    _updateClipboard?(): void;
}

function getPluginConstructor(): PluginConstructor | undefined {
    return (window.CMS as { Plugin?: PluginConstructor } | undefined)?.Plugin;
}

export class Clipboard {
    public ui: ClipboardUi;
    public modal: Modal | null = null;
    public currentClipboardData: Partial<ClipboardData> = {};

    private toolbarCleanups: Array<() => void> = [];
    private modalListenerCleanups: Array<() => void> = [];
    private syncDetach: (() => void) | null = null;

    constructor() {
        this.ui = this.setupUi();
        this.bindEvents();
    }

    /**
     * Re-bind the toolbar trigger handlers. Called by the toolbar's
     * `_refreshMarkup` after a content swap (the trigger anchors
     * become stale references).
     */
    _toolbarEvents(): void {
        // Refresh trigger references from the live DOM.
        this.ui.triggers = Array.from(
            document.querySelectorAll<HTMLAnchorElement>(
                '.cms-clipboard-trigger a',
            ),
        );
        this.ui.triggerRemove = Array.from(
            document.querySelectorAll<HTMLAnchorElement>(
                '.cms-clipboard-empty a',
            ),
        );
        this.detachToolbar();
        this.bindToolbar();
    }

    /**
     * Server-side clear — dispatches a POST to the configured clear
     * URL and locally cleans up the DOM. Optional callback runs after
     * the AJAX completes (matches legacy semantics).
     */
    clear(callback?: () => void): void {
        const config = getCmsConfig() as {
            csrf?: string;
            clipboard?: { url?: string };
        };
        const url = config.clipboard?.url;
        if (!url) return;

        this.cleanupDom();

        const toolbar = getToolbar();
        const post = JSON.stringify({
            csrfmiddlewaretoken: config.csrf ?? '',
        });
        // The toolbar API.openAjax wraps the loader and error display.
        const openAjax = (
            toolbar as { openAjax?: (opts: unknown) => Promise<unknown> } | undefined
        )?.openAjax;
        if (!openAjax) {
            // Toolbar not available — best-effort: still populate empty.
            this.populate('', {});
            callback?.();
            return;
        }
        void openAjax({
            url: Helpers.updateUrlWithPath(url),
            post,
            callback: () => {
                this.populate('', {});
                callback?.();
            },
        });
    }

    /**
     * Update the clipboard with a copied plugin. Writes to
     * localStorage so sibling tabs receive the same payload.
     */
    populate(html: string, pluginData: ClipboardData['data']): void {
        this.currentClipboardData = {
            data: pluginData,
            timestamp: Date.now(),
            html,
        };
        writeClipboard(this.currentClipboardData as ClipboardData);
    }

    // ────────────────────────────────────────────────────────────
    // Internal
    // ────────────────────────────────────────────────────────────

    private setupUi(): ClipboardUi {
        const clipboard = document.querySelector<HTMLElement>('.cms-clipboard');
        return {
            clipboard,
            triggers: Array.from(
                document.querySelectorAll<HTMLAnchorElement>(
                    '.cms-clipboard-trigger a',
                ),
            ),
            triggerRemove: Array.from(
                document.querySelectorAll<HTMLAnchorElement>(
                    '.cms-clipboard-empty a',
                ),
            ),
            pluginsList:
                clipboard?.querySelector<HTMLElement>(
                    '.cms-clipboard-containers',
                ) ?? null,
        };
    }

    private bindEvents(): void {
        // Re-create the modal each time. The legacy code creates one
        // shared instance; we mirror that to keep parity with
        // `instance === this.modal` checks in the modal-* event
        // handlers.
        try {
            this.modal = new Modal({
                minWidth: MIN_WIDTH,
                minHeight: MIN_HEIGHT,
                minimizable: false,
                maximizable: false,
                resizable: false,
                closeOnEsc: false,
            });
        } catch {
            // No `.cms-modal` markup on the page — skip modal wiring
            // (defensive for contrib-only pages without the toolbar).
            this.modal = null;
        }

        this.detachModalListeners();
        const PluginCtor = getPluginConstructor();

        const onLoadOrClosed = (payload: unknown): void => {
            const instance = (payload as { instance?: Modal })?.instance;
            if (instance === this.modal) {
                PluginCtor?._removeAddPluginPlaceholder?.();
            }
        };
        const onClose = (payload: unknown): void => {
            const instance = (payload as { instance?: Modal })?.instance;
            if (instance === this.modal) this.repatriatePluginsList();
        };
        const onLoad = (payload: unknown): void => {
            const instance = (payload as { instance?: Modal })?.instance;
            // Always move the list back; if it's a different modal
            // instance also call _updateClipboard to refresh.
            this.repatriatePluginsList();
            if (instance !== this.modal) PluginCtor?._updateClipboard?.();
        };

        Helpers.addEventListener('modal-loaded', onLoadOrClosed);
        Helpers.addEventListener('modal-closed', onLoadOrClosed);
        Helpers.addEventListener('modal-close', onClose);
        Helpers.addEventListener('modal-load', onLoad);
        this.modalListenerCleanups.push(
            () => Helpers.removeEventListener('modal-loaded', onLoadOrClosed),
            () => Helpers.removeEventListener('modal-closed', onLoadOrClosed),
            () => Helpers.removeEventListener('modal-close', onClose),
            () => Helpers.removeEventListener('modal-load', onLoad),
        );

        // Cross-tab sync.
        this.syncDetach?.();
        this.syncDetach = listenForExternalUpdates((value) =>
            this.handleExternalUpdate(value),
        );

        this.bindToolbar();
    }

    private bindToolbar(): void {
        const onTrigger = (e: Event): void => {
            e.preventDefault();
            e.stopPropagation();
            const a = e.currentTarget as HTMLAnchorElement;
            if (
                a.parentElement?.classList.contains(
                    'cms-toolbar-item-navigation-disabled',
                )
            )
                return;
            if (!this.modal || !this.ui.pluginsList || !this.ui.clipboard)
                return;
            this.modal.open({
                html: this.ui.pluginsList,
                title: this.ui.clipboard.dataset.title,
                width: MIN_WIDTH,
                height: MIN_HEIGHT,
            });
            // Close the toolbar dropdown that contained the trigger.
            document.dispatchEvent(
                new MouseEvent('click', { bubbles: true }),
            );
        };
        const onClear = (e: Event): void => {
            e.preventDefault();
            e.stopPropagation();
            const a = e.currentTarget as HTMLAnchorElement;
            if (
                a.parentElement?.classList.contains(
                    'cms-toolbar-item-navigation-disabled',
                )
            )
                return;
            this.clear();
        };

        for (const a of this.ui.triggers) {
            a.addEventListener('click', onTrigger);
            this.toolbarCleanups.push(() =>
                a.removeEventListener('click', onTrigger),
            );
        }
        for (const a of this.ui.triggerRemove) {
            a.addEventListener('click', onClear);
            this.toolbarCleanups.push(() =>
                a.removeEventListener('click', onClear),
            );
        }
    }

    private detachToolbar(): void {
        for (const c of this.toolbarCleanups) c();
        this.toolbarCleanups = [];
    }

    private detachModalListeners(): void {
        for (const c of this.modalListenerCleanups) c();
        this.modalListenerCleanups = [];
    }

    /**
     * Move the live `.cms-clipboard-containers` element back to its
     * original parent. The modal opens with `html: this.ui.pluginsList`
     * which reparents the live node into the modal frame; closing the
     * modal needs to put it back so subsequent opens see the latest
     * state.
     */
    private repatriatePluginsList(): void {
        const list = this.ui.pluginsList;
        const home = this.ui.clipboard;
        if (!list || !home) return;
        if (list.parentElement === home) return;
        home.insertBefore(list, home.firstChild);
    }

    private handleExternalUpdate(payload: ClipboardData): void {
        const current = this.currentClipboardData;
        const sameOrOlder =
            (current.timestamp !== undefined &&
                payload.timestamp < current.timestamp) ||
            (current.data?.plugin_id !== undefined &&
                current.data.plugin_id === payload.data.plugin_id);
        if (sameOrOlder) {
            this.currentClipboardData = payload;
            return;
        }

        if (!payload.data.plugin_id) {
            this.cleanupDom();
            this.currentClipboardData = payload;
            return;
        }

        if (!current.data?.plugin_id) this.enableTriggers();

        if (this.ui.pluginsList) {
            this.ui.pluginsList.innerHTML = payload.html;
        }
        const PluginCtor = getPluginConstructor();
        PluginCtor?._updateClipboard?.();
        if (PluginCtor) {
            const instances = getInstancesRegistry();
            instances.push(
                new PluginCtor(
                    `cms-plugin-${payload.data.plugin_id}`,
                    payload.data,
                ) as unknown as ReturnType<
                    typeof getInstancesRegistry
                >[number],
            );
        }

        this.currentClipboardData = payload;
    }

    private isClipboardModalOpen(): boolean {
        const body = this.modal?.ui.modalBody;
        if (!body) return false;
        return body.querySelectorAll('.cms-clipboard-containers').length > 0;
    }

    private cleanupDom(): void {
        const pasteAnchors = document.querySelectorAll<HTMLElement>(
            '.cms-submenu-item [data-rel=paste]',
        );
        pasteAnchors.forEach((el) => {
            el.tabIndex = -1;
            const li = el.parentElement;
            if (!li) return;
            li.classList.add('cms-submenu-item-disabled');
            li.querySelectorAll<HTMLAnchorElement>('a').forEach((a) =>
                a.setAttribute('aria-disabled', 'true'),
            );
            li.querySelectorAll<HTMLElement>(
                '.cms-submenu-item-paste-tooltip',
            ).forEach((t) => {
                t.style.display = 'none';
            });
            li.querySelectorAll<HTMLElement>(
                '.cms-submenu-item-paste-tooltip-empty',
            ).forEach((t) => {
                t.style.display = 'block';
            });
        });

        if (this.isClipboardModalOpen()) this.modal?.close();

        this.disableTriggers();
        document.dispatchEvent(
            new MouseEvent('click', { bubbles: true }),
        );
    }

    private enableTriggers(): void {
        for (const a of this.ui.triggers) {
            a.parentElement?.classList.remove(
                'cms-toolbar-item-navigation-disabled',
            );
        }
        for (const a of this.ui.triggerRemove) {
            a.parentElement?.classList.remove(
                'cms-toolbar-item-navigation-disabled',
            );
        }
    }

    private disableTriggers(): void {
        for (const a of this.ui.triggers) {
            a.parentElement?.classList.add(
                'cms-toolbar-item-navigation-disabled',
            );
        }
        for (const a of this.ui.triggerRemove) {
            a.parentElement?.classList.add(
                'cms-toolbar-item-navigation-disabled',
            );
        }
    }
}

export default Clipboard;
