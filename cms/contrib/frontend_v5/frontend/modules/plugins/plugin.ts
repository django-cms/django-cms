/*
 * The `Plugin` class — orchestrator for placeholder / plugin / generic
 * lifecycle.
 *
 * Constructor + lifecycle (`destroy`, `cleanup`) + the legacy method
 * shape that `cms.structureboard.js` and `cms.plugins.js::_refreshPlugins`
 * call into. Heavy lifting lives in `ui/` modules (per the data/UI
 * separation in the inventory). The class is intentionally thin — most
 * methods are one-line passthroughs.
 *
 * What's wired:
 *   - `_setupUI` → `ui/setup.ts::setupContainer`
 *   - `_ensureData` → `cms-data.ts::ensurePluginDataArray` (when applicable)
 *   - `_setPlaceholder` → `ui/placeholder.ts::setupPlaceholderEvents`
 *   - `_setPlugin` → calls `_setPluginContentEvents` (content path)
 *   - `_setPluginContentEvents` → `ui/content-events.ts::setupContentEvents`
 *   - `_setGeneric` → `ui/generic.ts::setupGenericEvents`
 *   - `_dblClickToEditHandler` → `ui/content-events.ts::dblClickToEdit`
 *   - `destroy` / `cleanup` — close modal, abort listeners, drop UI
 *
 * Method delegation map:
 *   - `_setupUI` → `ui/setup.ts::setupContainer`
 *   - `_ensureData` → `cms-data.ts::ensurePluginDataArray`
 *   - `_setPlaceholder` → `ui/placeholder.ts::setupPlaceholderEvents`
 *   - `_setPluginContentEvents` → `ui/content-events.ts::setupContentEvents`
 *   - `_setPluginStructureEvents` → inline + `ui/collapse.ts` + `ui/highlight.ts`
 *   - `_collapsables` → `ui/collapse.ts::setupCollapsable`
 *   - `_setGeneric` → `ui/generic.ts::setupGenericEvents`
 *   - `_dblClickToEditHandler` → `ui/content-events.ts::dblClickToEdit`
 *   - `_setSettingsMenu` → `ui/menu.ts::setupSettingsMenu`
 *   - `_setAddPluginModal` → `ui/picker.ts::setupAddPluginModal`
 *   - `_checkIfPasteAllowed` → inline (DOM + restriction check)
 *   - `addPlugin` / `editPlugin` / `copyPlugin` / `cutPlugin` /
 *     `pastePlugin` / `movePlugin` / `deletePlugin` / `editPluginPostAjax`
 *     → inline orchestrators on top of `api.ts` + `mutations.ts`
 *
 * Per-instance event tracking
 * ───────────────────────────
 * Every instance owns an `AbortController`; UI modules accept its
 * `signal` and use it for `addEventListener`. `destroy()` aborts the
 * controller, removing every listener wholesale. Replaces the legacy
 * jQuery-namespaced `.off('.uid')` bookkeeping with a single signal.
 */

import { Helpers, uid } from '../cms-base';
import {
    buildAddPluginUrl,
    requestCopyPlugin,
    requestCutPlugin,
    requestMovePlugin,
} from './api';
import {
    ensurePluginDataArray,
    getPlaceholderData,
    getPluginData,
    pushPluginData,
    setPlaceholderData,
    setPluginDataAt,
} from './cms-data';
import {
    getCmsConfig,
    getStructureBoard,
    isContentReady,
    isStructureReady,
} from './cms-globals';
import {
    broadcastInvalidate,
    constructModal,
    getClipboardDraggable,
    hideLoader,
    notifyError,
    notifySuccess,
    showLoader,
    withLock,
} from './mutations';
import {
    addInstance,
    findPluginById,
    getAllDescriptors,
    isPlaceholderDuplicate,
    isPluginDuplicate,
    markPlaceholderDuplicate,
    markPluginDuplicate,
    removeInstance,
    updatePluginPositions,
} from './registry';
import type { PluginInstance, PluginOptions, PluginType } from './types';
import {
    expandAll,
    collapseAll,
    setupCollapsable,
} from './ui/collapse';
import { dblClickToEdit, setupContentEvents } from './ui/content-events';
import { setupGenericEvents } from './ui/generic';
import { isExpandMode } from './ui/global-handlers';
import {
    highlightPluginContent,
    removeHighlightPluginContent,
} from './ui/highlight';
import { setupSettingsMenu } from './ui/menu';
import { setupAddPluginModal } from './ui/picker';
import { setupPlaceholderEvents, type PlaceholderUi } from './ui/placeholder';
import { setupContainer } from './ui/setup';

void Helpers; // keep the import side-effect-free; Helpers is consumed by callers.

const DEFAULT_OPTIONS: PluginOptions = {
    type: '',
    placeholder_id: null,
    plugin_type: '',
    plugin_id: null,
    plugin_parent: null,
    plugin_restriction: [],
    plugin_parent_restriction: [],
    urls: {
        add_plugin: '',
        edit_plugin: '',
        move_plugin: '',
        copy_plugin: '',
        delete_plugin: '',
    },
};

/**
 * UI slot map. Loose typing because different plugin types populate
 * different slots, and downstream modules (structureboard) read this
 * by name. Tighten when each slot's owner is fully ported.
 */
export interface PluginUi extends Partial<PlaceholderUi> {
    /** Always set after `_setupUI`. */
    container?: Element[];
    /** Set by `_setPluginStructureEvents` (2f). */
    draggable?: HTMLElement | null;
    dragitem?: HTMLElement | null;
    /** Set by `_setSettingsMenu` (2d). */
    dropdown?: HTMLElement | null;
}

export class Plugin implements PluginInstance {
    options: PluginOptions;

    /** Unique-per-instance counter from `Helpers.uid()`. */
    readonly uid: number;

    /**
     * Modal handle set by `addPlugin` / `editPlugin` / `deletePlugin`.
     * Closed in `destroy()`. Loosely typed because the Modal API isn't
     * ported yet (legacy global).
     */
    modal: { close?: () => void; off?: () => void } | null = null;

    /** Resolved UI references — populated piecewise by `_set*` methods. */
    ui: PluginUi = {};

    /**
     * Set by close_frame.html before `Helpers.onPluginSave` fires.
     * Read by the orchestration code in 2g.
     */
    dataBridge?: PluginOptions;

    /**
     * Aborts every listener bound by this instance's UI modules. Wired
     * up at construction; `destroy()` calls `.abort()`.
     */
    private readonly abortController: AbortController;

    constructor(container: string, options: Partial<PluginOptions>) {
        this.options = mergeOptions(options);
        this.uid = uid();
        this.abortController = new AbortController();

        this._setupUI(container);
        this._ensureData();

        // Duplicate guards — when the same plugin id is rendered more
        // than once on a page, only the first call wires up; later
        // calls populate `ui.container` (already done above) and
        // `data('cms')` then early-return.
        const pluginId = this.options.plugin_id;
        const placeholderId = this.options.placeholder_id;

        if (
            this.options.type === 'plugin' &&
            pluginId !== undefined &&
            pluginId !== null &&
            isPluginDuplicate(pluginId)
        ) {
            return;
        }
        if (
            this.options.type === 'placeholder' &&
            placeholderId !== undefined &&
            placeholderId !== null &&
            isPlaceholderDuplicate(placeholderId)
        ) {
            return;
        }

        switch (this.options.type as PluginType | string) {
            case 'placeholder':
                if (placeholderId !== undefined && placeholderId !== null) {
                    markPlaceholderDuplicate(placeholderId);
                }
                if (this.ui.container?.[0]) {
                    setPlaceholderData(this.ui.container[0], this.options);
                }
                this._setPlaceholder();
                if (isStructureReady()) this._collapsables();
                break;
            case 'plugin':
                if (this.ui.container?.[0]) {
                    pushPluginData(this.ui.container[0], this.options);
                }
                if (pluginId !== undefined && pluginId !== null) {
                    markPluginDuplicate(pluginId);
                }
                this._setPlugin();
                if (isStructureReady()) this._collapsables();
                break;
            default: {
                // Generic — front-end editable fields, page menus, etc.
                if (this.ui.container?.[0]) {
                    pushPluginData(this.ui.container[0], this.options);
                }
                this._setGeneric();
            }
        }
    }

    // ────────────────────────────────────────────────────────────
    // Lifecycle hooks legacy structureboard / _refreshPlugins call
    // (CLAUDE.md decision 7: these names cannot change.)
    // ────────────────────────────────────────────────────────────

    _setupUI(container: string): void {
        const elements = setupContainer(container);
        this.ui.container = elements;
    }

    _ensureData(): void {
        // Generic + plugin descriptors carry an array; ensure it exists.
        // Placeholder descriptors are a single object — set in the
        // constructor's switch.
        if (this.options.type !== 'placeholder' && this.ui.container?.[0]) {
            ensurePluginDataArray(this.ui.container[0]);
        }
    }

    _setPlaceholder(): void {
        const ui = setupPlaceholderEvents(this, this.abortController.signal);
        this.ui.dragbar = ui.dragbar;
        this.ui.draggables = ui.draggables;
        this.ui.submenu = ui.submenu;
        this.ui.addSubmenu = ui.addSubmenu;
        // Settings menu + add-plugin modal land in 2d/2e — stub here.
        this._setSettingsMenu();
        this._setAddPluginModal();
        this._checkIfPasteAllowed();
    }

    _setPlugin(): void {
        if (isStructureReady()) this._setPluginStructureEvents();
        if (isContentReady()) this._setPluginContentEvents();
    }

    _setPluginContentEvents(): void {
        if (!this.ui.container) return;
        setupContentEvents(this, this.ui.container, this.abortController.signal);
    }

    _setGeneric(): void {
        if (!this.ui.container) return;
        setupGenericEvents(this, this.ui.container, this.abortController.signal);
    }

    /**
     * Legacy hook used by `_setPluginStructureEvents` and content-event
     * delegation. Forwards to the free function for symmetry with the
     * legacy method shape.
     */
    _dblClickToEditHandler(e: Event): void {
        dblClickToEdit(this, e);
    }

    // ────────────────────────────────────────────────────────────
    // Structure-mode wiring (called by legacy structureboard +
    // `_refreshPlugins`)
    // ────────────────────────────────────────────────────────────

    /**
     * Structure-mode wiring. Mirrors legacy
     * `_setPluginStructureEvents`. Resolves the `.cms-draggable` /
     * `.cms-dragitem` / `.cms-draggables` / `.cms-submenu` slots from
     * the live tree, mirrors the descriptor onto the draggable's
     * data store, wires dblclick-to-edit + shift-hover highlight, and
     * defers the menu / picker / paste-allowed wiring (2g) to
     * after the legacy `setTimeout(0)` to match render ordering.
     */
    _setPluginStructureEvents(): void {
        const pluginId = this.options.plugin_id;
        if (pluginId === undefined || pluginId === null) return;

        const draggable = document.querySelector<HTMLElement>(
            `.cms-draggable-${pluginId}`,
        );
        if (!draggable) return;
        const dragitem = draggable.querySelector<HTMLElement>(
            ':scope > .cms-dragitem',
        );
        const draggables = draggable.querySelector<HTMLElement>(
            ':scope > .cms-draggables',
        );
        const submenu = dragitem?.querySelector<HTMLElement>('.cms-submenu') ?? null;

        this.ui.draggable = draggable;
        this.ui.dragitem = dragitem;
        this.ui.draggables = draggables;
        this.ui.submenu = submenu;

        // Mirror the descriptor onto the draggable so structureboard
        // (still legacy) can keep doing `data('cms')` reads. Draggables
        // carry a single object (not the array shape that plugin
        // containers use).
        setPlaceholderData(draggable, this.options);

        const opts = { signal: this.abortController.signal };

        // dblclick on the dragitem text → edit (when this isn't a
        // slot wrapper).
        if (dragitem && !draggable.classList.contains('cms-slot')) {
            dragitem.addEventListener(
                'dblclick',
                (e) => this._dblClickToEditHandler(e),
                opts,
            );
        }

        // Drag controller fires `cms-plugins-update` on the draggable
        // when a drop commits — translate to a movePlugin call.
        draggable.addEventListener(
            'cms-plugins-update',
            (e) => {
                e.stopPropagation();
                const detail = (e as CustomEvent).detail;
                this.movePlugin(detail as PluginOptions | undefined);
            },
            opts,
        );

        // Paste flow: clipboard plugin clones itself + dispatches
        // `cms-paste-plugin-update`. We re-derive target placeholder /
        // parent from the live DOM, mark `move_a_copy`, and fire the
        // mutation. Mirrors legacy.
        draggable.addEventListener(
            'cms-paste-plugin-update',
            (e) => {
                e.stopPropagation();
                const detail = (e as CustomEvent<{ id?: number | string }>).detail;
                const pastedId = detail?.id;
                if (pastedId === undefined || pastedId === null) return;
                const matches = document.querySelectorAll<HTMLElement>(
                    `.cms-draggable-${pastedId}`,
                );
                const pasted = matches[matches.length - 1];
                if (!pasted) return;
                const newPlaceholderId = resolveNewPlaceholderId(pasted);
                if (newPlaceholderId === undefined) return;
                const parentDraggable = pasted.parentElement?.closest<HTMLElement>(
                    '.cms-draggable',
                );
                const parentId =
                    parentDraggable !== null && parentDraggable !== undefined
                        ? parseDraggableId(parentDraggable)
                        : undefined;

                // Update the data-mirror so `data('cms')` reads see the
                // new placement. Draggable mirror shape = single object.
                const data = { ...this.options } as PluginOptions & {
                    target?: number | string;
                    parent?: number | string;
                    move_a_copy?: boolean;
                };
                data.target = newPlaceholderId;
                if (parentId !== undefined) data.parent = parentId;
                data.move_a_copy = true;
                setPlaceholderData(pasted, data);

                // Persist the parent's expanded state (legacy did this).
                const settings = getCmsConfig().settings as
                    | { states?: Array<number | string> }
                    | undefined;
                if (settings && parentId !== undefined) {
                    if (!Array.isArray(settings.states)) settings.states = [];
                    settings.states.push(parentId);
                    try {
                        Helpers.setSettings(settings as Record<string, unknown>);
                    } catch {
                        /* localStorage unavailable */
                    }
                }

                this.movePlugin(data);
            },
            opts,
        );

        // Shift-hover preview: when expandmode is on AND the structure
        // tree is in condensed view AND no drag in progress, highlight
        // the matching content node. Mouseleave clears it.
        dragitem?.addEventListener(
            'mouseenter',
            (e) => {
                e.stopPropagation();
                if (!isExpandMode()) return;
                if (
                    draggable.querySelector(
                        ':scope > .cms-dragitem > .cms-plugin-disabled',
                    )
                ) {
                    return;
                }
                const sb = getStructureBoard();
                if (!sb?.ui?.container?.hasClass('cms-structure-condensed')) return;
                if (sb.dragging) return;
                highlightPluginContent(pluginId, {
                    successTimeout: 0,
                    seeThrough: true,
                });
            },
            opts,
        );
        dragitem?.addEventListener(
            'mouseleave',
            (e) => {
                const sb = getStructureBoard();
                if (!sb?.ui?.container?.hasClass('cms-structure-condensed')) return;
                e.stopPropagation();
                removeHighlightPluginContent(pluginId);
            },
            opts,
        );

        // Settings menu, add-plugin trigger, and paste-allowed check
        // run after the current task — legacy used setTimeout(0) here
        // so the DOM has settled when these wire up.
        setTimeout(() => {
            this._setSettingsMenu(submenu);
            const addBtn = dragitem?.querySelector<HTMLElement>(
                '.cms-submenu-add',
            );
            this._setAddPluginModal(addBtn ?? null);
            this._checkIfPasteAllowed();
        }, 0);

        // Dragbar title click → expand-all / collapse-all. Wired
        // here (placeholder path) because legacy attached this in
        // `_setPlaceholder` via `Plugin.expandToggle`. Placeholder
        // path also calls _setPlaceholder which runs earlier; this
        // is here in case a plugin's structure events run first.
        const dragbarTitle = draggable
            .closest<HTMLElement>('.cms-dragarea')
            ?.querySelector<HTMLElement>('.cms-dragbar-title');
        dragbarTitle?.addEventListener(
            'click',
            (e) => {
                e.preventDefault();
                if (dragbarTitle.classList.contains('cms-dragbar-title-expanded')) {
                    collapseAll(this, dragbarTitle);
                } else {
                    expandAll(this, dragbarTitle);
                }
            },
            opts,
        );
    }

    _collapsables(): void {
        setupCollapsable(this, this.abortController.signal);
    }

    _setSettingsMenu(nav?: HTMLElement | null): void {
        // Resolve the trigger from `ui.submenu` (placeholder path) or
        // `ui.dragitem`'s nested `.cms-submenu` (plugin path) when the
        // caller doesn't pass one explicitly.
        const trigger =
            nav ??
            (this.ui.submenu instanceof HTMLElement ? this.ui.submenu : null);
        if (!trigger) return;
        const dropdown = setupSettingsMenu(this, trigger, this.abortController.signal);
        this.ui.dropdown = dropdown;
    }

    _setAddPluginModal(nav?: HTMLElement | null): void {
        const trigger =
            nav ??
            (this.ui.addSubmenu instanceof HTMLElement ? this.ui.addSubmenu : null);
        if (!trigger) return;
        setupAddPluginModal(this, trigger, this.abortController.signal);
    }

    /**
     * Inspect the dropdown's "paste" item and disable / enable it
     * based on the current clipboard contents and the plugin's
     * `plugin_restriction` rules. Returns true when paste is allowed.
     *
     * Mirrors legacy `_checkIfPasteAllowed`. Pure DOM manipulation —
     * the actual paste happens later via `pastePlugin`.
     */
    _checkIfPasteAllowed(): boolean {
        const dropdown = this.ui.dropdown;
        if (!dropdown) return false;
        const pasteButton = dropdown.querySelector<HTMLElement>(
            '[data-rel=paste]',
        );
        const pasteItem = pasteButton?.parentElement ?? null;
        if (!pasteItem) return false;

        const clipboard = getClipboardDraggable();
        if (!clipboard) {
            disablePaste(pasteItem, '.cms-submenu-item-paste-tooltip-empty');
            return false;
        }
        if (this.ui.draggable?.classList.contains('cms-draggable-disabled')) {
            disablePaste(pasteItem, '.cms-submenu-item-paste-tooltip-disabled');
            return false;
        }

        // Clipboard draggables carry the placeholder shape (single
        // object), written via setPlaceholderData in
        // _setPluginStructureEvents. Read with the matching helper.
        const clipboardData = getPlaceholderData(clipboard);
        if (!clipboardData) return false;

        const bounds = this.options.plugin_restriction ?? [];
        const parentBounds = (
            clipboardData.plugin_parent_restriction ?? []
        ).filter((restriction) => restriction !== '0');
        const clipboardType = clipboardData.plugin_type ?? '';
        const currentType = this.options.plugin_type ?? '';

        if (
            (bounds.length > 0 && !bounds.includes(clipboardType)) ||
            (parentBounds.length > 0 && !parentBounds.includes(currentType))
        ) {
            disablePaste(pasteItem, '.cms-submenu-item-paste-tooltip-restricted');
            return false;
        }

        // Allowed: clear disabled state.
        pasteItem.classList.remove('cms-submenu-item-disabled');
        pasteItem.querySelectorAll<HTMLAnchorElement>('a').forEach((a) => {
            a.removeAttribute('tabindex');
            a.removeAttribute('aria-disabled');
        });
        return true;
    }

    // ────────────────────────────────────────────────────────────
    // Mutation API (sub-phase 2g)
    // ────────────────────────────────────────────────────────────

    /**
     * Open the add-plugin modal at the URL the server constructs from
     * `urls.add_plugin` plus the placeholder / type / position params.
     * `showAddForm=false` skips the type-picker iframe and submits the
     * empty form directly (used from the toolbar's quick-add).
     */
    addPlugin(
        type: string,
        name: string,
        parent?: number | string | null,
        showAddForm: boolean = true,
        position?: number,
    ): void {
        const placeholderId = this.options.placeholder_id;
        if (placeholderId === undefined || placeholderId === null) return;
        const addUrl = this.options.urls?.add_plugin;
        if (!addUrl) return;

        const url = buildAddPluginUrl({
            addPluginUrl: addUrl,
            placeholder_id: placeholderId,
            plugin_type: type,
            plugin_position: position ?? this._getPluginAddPosition(),
            ...(parent !== undefined && parent !== null
                ? { plugin_parent: parent }
                : {}),
        });

        const modal = constructModal({
            onClose: this.options.onClose,
            redirectOnClose: this.options.redirectOnClose,
        });
        if (!modal) return;
        this.modal = modal;

        if (showAddForm) {
            modal.open?.({ url, title: name });
        } else {
            // Open empty modal then auto-submit a hidden form to skip
            // the picker UI. Mirrors legacy direct-add path.
            modal.open?.({ url: '#', title: name });
            modal.ui?.modal?.hide?.();
            const csrf = getCmsConfig().csrf ?? '';
            const frame = modal.ui?.frame;
            const iframe =
                frame instanceof HTMLIFrameElement
                    ? frame
                    : (frame as { querySelector?: (s: string) => unknown })
                          ?.querySelector?.('iframe');
            const body =
                iframe instanceof HTMLIFrameElement
                    ? iframe.contentDocument?.body
                    : null;
            if (body) {
                const form = document.createElement('form');
                form.method = 'post';
                form.action = url;
                form.style.display = 'none';
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = csrf;
                form.appendChild(csrfInput);
                body.appendChild(form);
                form.submit();
            }
        }
    }

    /**
     * Compute the 1-based slot the new plugin should land in. For a
     * placeholder: append to the bottom (count of draggables + 1).
     * For a plugin: position immediately after the last child if any,
     * otherwise immediately after self.
     *
     * Mirrors legacy `_getPluginAddPosition` exactly.
     */
    _getPluginAddPosition(): number {
        if (this.options.type === 'placeholder') {
            const placeholderId = this.options.placeholder_id;
            const count = document.querySelectorAll(
                `.cms-dragarea-${placeholderId} .cms-draggable`,
            ).length;
            return count + 1;
        }
        const draggable = this.ui.draggable;
        if (draggable) {
            const children = draggable.querySelectorAll<HTMLElement>(
                '.cms-draggable',
            );
            const lastChild = children[children.length - 1];
            if (lastChild) {
                const childId = parseDraggableId(lastChild);
                if (childId !== undefined) {
                    const childInstance = findPluginById(childId);
                    const childPos = childInstance?.options.position;
                    if (typeof childPos === 'number') return childPos + 1;
                }
            }
        }
        return (this.options.position ?? 0) + 1;
    }

    /**
     * Open the edit-plugin modal. URL + breadcrumb come from the
     * caller (the menu module computed the breadcrumb via
     * `_getPluginBreadcrumbs`).
     */
    editPlugin(url: string, name?: string, breadcrumb?: unknown[]): void {
        const modal = constructModal({
            onClose: this.options.onClose,
            redirectOnClose: this.options.redirectOnClose,
        });
        if (!modal) return;
        this.modal = modal;
        modal.open?.({
            url,
            title: name ?? '',
            breadcrumbs: breadcrumb ?? [],
            width: 850,
        });
    }

    /**
     * Open the delete-plugin confirmation modal. Same shape as
     * `editPlugin`, narrower default width.
     */
    deletePlugin(url: string, name?: string, breadcrumb?: unknown[]): void {
        const modal = constructModal({
            onClose: this.options.onClose,
            redirectOnClose: this.options.redirectOnClose,
        });
        if (!modal) return;
        this.modal = modal;
        modal.open?.({
            url,
            title: name ?? '',
            breadcrumbs: breadcrumb ?? [],
        });
    }

    /**
     * POST a copy request. With `sourceLanguage` this is a "copy
     * from another language" — the server pastes the source-language
     * placeholder onto this one. Without, it copies onto the
     * clipboard placeholder.
     *
     * Mirrors legacy `copyPlugin` including the lock and the
     * COPY/PASTE invalidate-state branch.
     */
    async copyPlugin(
        opts?: PluginOptions,
        sourceLanguage?: string,
    ): Promise<void> {
        await withLock(async () => {
            const options = { ...(opts ?? this.options) };
            try {
                const copyInput: Parameters<typeof requestCopyPlugin>[0] = {
                    placeholder_id: options.placeholder_id ?? '',
                    urls: options.urls,
                };
                if (options.plugin_id !== undefined) copyInput.plugin_id = options.plugin_id;
                if (options.parent !== undefined) {
                    copyInput.parent = options.parent as number | string | null;
                }
                if (options.target !== undefined) {
                    copyInput.target = options.target as number | string | null;
                }
                const { payload, response, copyingFromLanguage } =
                    await requestCopyPlugin(copyInput, sourceLanguage);
                notifySuccess();
                if (copyingFromLanguage) {
                    broadcastInvalidate('PASTE', {
                        ...payload,
                        ...(typeof response === 'object' && response !== null
                            ? (response as Record<string, unknown>)
                            : {}),
                    });
                } else {
                    broadcastInvalidate('COPY', response);
                }
            } catch (err) {
                notifyError((err as Error).message);
            } finally {
                hideLoader();
            }
        });
    }

    /**
     * POST a cut request — moves the plugin to the clipboard
     * placeholder via the same `move_plugin` endpoint copy/paste use.
     */
    async cutPlugin(): Promise<void> {
        await withLock(async () => {
            const pluginId = this.options.plugin_id;
            if (pluginId === undefined || pluginId === null) return;
            try {
                const { payload, response } = await requestCutPlugin({
                    plugin_id: pluginId,
                    urls: this.options.urls,
                });
                notifySuccess();
                broadcastInvalidate('CUT', {
                    ...payload,
                    ...(typeof response === 'object' && response !== null
                        ? (response as Record<string, unknown>)
                        : {}),
                });
            } catch (err) {
                notifyError((err as Error).message);
            } finally {
                hideLoader();
            }
        });
    }

    /**
     * Insert a clone of the clipboard draggable into this plugin's
     * `.cms-draggables` container, then call the *source* (clipboard)
     * plugin's `movePlugin` with `move_a_copy=true`.
     *
     * Legacy used jQuery `.clone(true, true)` to copy the source's
     * `cms-paste-plugin-update` listener onto the clone, then
     * dispatched the event on the clone — `that` inside the listener
     * was always the source plugin instance. Native `cloneNode(true)`
     * doesn't carry listeners, so we look up the source instance
     * directly and call `movePlugin` ourselves. Same semantics, no
     * intermediate event.
     */
    pastePlugin(): void {
        const clipboard = getClipboardDraggable();
        const draggables = this.ui.draggables;
        if (!clipboard || !draggables) return;
        const id = parseDraggableId(clipboard);
        if (id === undefined) return;
        const sourceInstance = findPluginById(id) as Plugin | undefined;
        if (!sourceInstance) return;

        const clone = clipboard.cloneNode(true) as HTMLElement;
        draggables.appendChild(clone);

        // Mirror the source's options onto the clone's data store so
        // that consumers reading `data('cms')` see the correct
        // descriptor on the new node.
        setPlaceholderData(clone, sourceInstance.options);

        const sb = getStructureBoard();
        if (this.options.plugin_id !== undefined && this.options.plugin_id !== null) {
            sb?.actualizePluginCollapseStatus?.(this.options.plugin_id);
        }
        // Notify structureboard that DOM changed (legacy hook).
        draggables.dispatchEvent(
            new CustomEvent('cms-structure-update', {
                detail: { id },
                bubbles: true,
            }),
        );

        // Re-derive new placement from the live DOM and call
        // movePlugin on the *source* instance.
        const newPlaceholderId = parseDragareaId(
            clone.closest<HTMLElement>('.cms-dragarea'),
        );
        if (newPlaceholderId === undefined) return;
        const parentDraggable = clone.parentElement?.closest<HTMLElement>(
            '.cms-draggable',
        );
        const parentId =
            parentDraggable !== null && parentDraggable !== undefined
                ? parseDraggableId(parentDraggable)
                : undefined;

        const data: PluginOptions & {
            target?: number | string;
            parent?: number | string;
            move_a_copy?: boolean;
        } = {
            ...sourceInstance.options,
            target: newPlaceholderId,
            move_a_copy: true,
        };
        if (parentId !== undefined) data.parent = parentId;

        // Persist the new parent's expanded state (legacy did this).
        const settings = getCmsConfig().settings as
            | { states?: Array<number | string> }
            | undefined;
        if (settings && parentId !== undefined) {
            if (!Array.isArray(settings.states)) settings.states = [];
            settings.states.push(parentId);
            try {
                Helpers.setSettings(settings as Record<string, unknown>);
            } catch {
                /* localStorage unavailable */
            }
        }

        void sourceInstance.movePlugin(data);
    }

    /**
     * POST a move request. Reads the new placeholder + parent from
     * the live DOM (the drag controller has already moved the
     * draggable into its new position), recomputes positions, and
     * dispatches MOVE / PASTE on success.
     */
    async movePlugin(opts?: PluginOptions): Promise<void> {
        await withLock(async () => {
            const options = opts ?? this.options;
            const pluginId = options.plugin_id;
            if (pluginId === undefined || pluginId === null) return;

            // Find the current DOM position. Multiple draggables can
            // share the id while a paste is in progress — pick the
            // last one (matches legacy `:last`).
            const matches = document.querySelectorAll<HTMLElement>(
                `.cms-draggable-${pluginId}`,
            );
            const dragitem = matches[matches.length - 1];
            if (!dragitem) return;

            // Resolve new placeholder by walking up to the OUTERMOST
            // `.cms-draggables` ancestor and reading the dragbar that
            // immediately precedes it. Mirrors legacy
            // `dragitem.parents('.cms-draggables').last().prevAll('.cms-dragbar').first()`.
            // This is more robust than `closest('.cms-dragarea')` for
            // mid-transit nodes whose nearest `.cms-dragarea` is stale.
            const newPlaceholderId = resolveNewPlaceholderId(dragitem);
            if (newPlaceholderId === undefined) return;

            // Resolve new parent by walking up to the closest
            // ancestor draggable.
            const parentDraggable = dragitem.parentElement?.closest<HTMLElement>(
                '.cms-draggable',
            );
            const parentId =
                parentDraggable !== null && parentDraggable !== undefined
                    ? parseDraggableId(parentDraggable)
                    : undefined;

            const moveACopy = options.move_a_copy === true;
            const samePlaceholder =
                Number(newPlaceholderId) === Number(options.placeholder_id);

            if (samePlaceholder) {
                if (options.placeholder_id !== undefined && options.placeholder_id !== null) {
                    updatePluginPositions(options.placeholder_id);
                }
            } else {
                updatePluginPositions(newPlaceholderId);
                if (options.placeholder_id !== undefined && options.placeholder_id !== null) {
                    updatePluginPositions(options.placeholder_id);
                }
            }

            // Position must come from the live DOM after
            // `updatePluginPositions` refresh — find the moving
            // instance and read its updated `options.position`. For
            // paste flows where `opts !== this.options`, this reaches
            // the *source* instance whose options we just refreshed.
            const updatedInstance = findPluginById(pluginId);
            const targetPosition = updatedInstance?.options.position;

            showLoader();
            try {
                const moveInput: Parameters<typeof requestMovePlugin>[0] = {
                    plugin_id: pluginId,
                    move_a_copy: moveACopy,
                    placeholder_id: samePlaceholder ? null : newPlaceholderId,
                    urls: options.urls,
                };
                if (parentId !== undefined) moveInput.plugin_parent = parentId;
                if (targetPosition !== undefined) {
                    moveInput.target_position = targetPosition;
                }
                const { payload, response } = await requestMovePlugin(moveInput);
                broadcastInvalidate(moveACopy ? 'PASTE' : 'MOVE', {
                    ...payload,
                    placeholder_id: newPlaceholderId,
                    ...(typeof response === 'object' && response !== null
                        ? (response as Record<string, unknown>)
                        : {}),
                });
            } catch (err) {
                notifyError((err as Error).message);
            } finally {
                hideLoader();
            }
        });
    }

    /**
     * Called after a plugin form has been saved via the toolbar's
     * ajax flow. Re-opens the edit modal so the user can review.
     */
    editPluginPostAjax(_toolbar: unknown, response: unknown): void {
        if (!response || typeof response !== 'object') return;
        const r = response as { url?: string; breadcrumb?: unknown[] };
        if (!r.url) return;
        this.editPlugin(
            Helpers.updateUrlWithPath(r.url),
            this.options.plugin_name as string | undefined,
            r.breadcrumb,
        );
    }

    /**
     * Merge `newSettings` into `oldSettings` and write the result
     * back to:
     *   - `this.options` (instance state)
     *   - the plugin container's data array (matching descriptor)
     *   - the draggable's single-object data (mirror)
     *
     * Mirrors legacy `_setSettings`. Used after an edit modal closes
     * with the new descriptor.
     */
    _setSettings(
        oldSettings: PluginOptions,
        newSettings: Partial<PluginOptions>,
    ): void {
        const merged: PluginOptions = {
            ...oldSettings,
            ...newSettings,
            urls: { ...(oldSettings.urls ?? {}), ...(newSettings.urls ?? {}) },
        };
        this.options = merged;

        const id = merged.plugin_id;
        if (id === undefined || id === null) return;

        document
            .querySelectorAll<HTMLElement>(`.cms-plugin-${id}`)
            .forEach((el) => {
                const arr = getPluginData(el);
                if (!arr) return;
                const idx = arr.findIndex(
                    (d) => Number(d.plugin_id) === Number(merged.plugin_id),
                );
                if (idx >= 0) setPluginDataAt(el, idx, merged);
            });

        const draggable = document.querySelector<HTMLElement>(
            `.cms-draggable-${id}`,
        );
        if (draggable) setPlaceholderData(draggable, merged);
    }

    /**
     * Walk up the descriptor registry from this plugin's parent,
     * accumulating `{ url, title }` pairs for the breadcrumb display.
     * Returns the breadcrumb in root-first order, with this plugin
     * appended last.
     */
    _getPluginBreadcrumbs(): Array<{ url: string; title: string }> {
        const breadcrumbs: Array<{ url: string; title: string }> = [];
        breadcrumbs.unshift({
            title: (this.options.plugin_name as string | undefined) ?? '',
            url: this.options.urls?.edit_plugin ?? '',
        });

        const descriptors = getAllDescriptors();
        const findParent = (id: number | string) =>
            descriptors.find(([key]) => key === `cms-plugin-${id}`);

        let current: number | string | null | undefined =
            this.options.plugin_parent;
        while (current !== undefined && current !== null && current !== 'None') {
            const data = findParent(current);
            if (!data) break;
            breadcrumbs.unshift({
                title: (data[1].plugin_name as string | undefined) ?? '',
                url: data[1].urls?.edit_plugin ?? '',
            });
            current = data[1].plugin_parent;
        }
        return breadcrumbs;
    }

    // ────────────────────────────────────────────────────────────
    // Teardown
    // ────────────────────────────────────────────────────────────

    destroy(options: { mustCleanup?: boolean } = {}): void {
        if (this.modal) {
            this.modal.close?.();
            this.modal.off?.();
        }
        if (options.mustCleanup) this.cleanup();
        // Abort every listener wired by UI modules using our signal.
        this.abortController.abort();
        removeInstance(this);
    }

    cleanup(): void {
        // Remove every UI element the instance owns. Legacy used
        // `Object.keys(this.ui).forEach(el => this.ui[el].remove())`;
        // we mirror it but only call .remove() on real Elements.
        for (const value of Object.values(this.ui)) {
            if (Array.isArray(value)) {
                for (const el of value) {
                    if (el instanceof Element) el.remove();
                }
            } else if (value instanceof Element) {
                value.remove();
            }
        }
    }
}

// ────────────────────────────────────────────────────────────────────
// Helpers
// ────────────────────────────────────────────────────────────────────

function parseDraggableId(el: Element | null): number | undefined {
    if (!el) return undefined;
    for (const cls of Array.from(el.classList)) {
        const match = /^cms-draggable-(\d+)$/.exec(cls);
        if (match && match[1]) return Number(match[1]);
    }
    return undefined;
}

/**
 * Resolve the placeholder id for a moved/pasted draggable by walking
 * up to the outermost `.cms-draggables` ancestor and reading the
 * dragbar that immediately precedes it. Mirrors legacy
 * `dragitem.parents('.cms-draggables').last().prevAll('.cms-dragbar').first()`.
 *
 * The closest ancestor `.cms-dragarea` may be stale during a
 * mid-transit move — this walk follows the path the drag controller
 * actually established.
 */
function resolveNewPlaceholderId(dragitem: HTMLElement): number | undefined {
    let outermost: HTMLElement | null = null;
    let walker: HTMLElement | null = dragitem.parentElement;
    while (walker) {
        if (walker.classList.contains('cms-draggables')) {
            outermost = walker;
        }
        walker = walker.parentElement;
    }
    if (!outermost) return undefined;
    let prev = outermost.previousElementSibling;
    while (prev) {
        if (prev.classList.contains('cms-dragbar')) {
            return parsePlaceholderId(prev);
        }
        prev = prev.previousElementSibling;
    }
    // Fallback: parse from the surrounding cms-dragarea.
    return parseDragareaId(outermost.closest('.cms-dragarea'));
}

function parsePlaceholderId(el: Element | null): number | undefined {
    if (!el) return undefined;
    for (const cls of Array.from(el.classList)) {
        const match = /^cms-(?:dragbar|dragarea)-(\d+)$/.exec(cls);
        if (match && match[1]) return Number(match[1]);
    }
    return undefined;
}

function parseDragareaId(el: Element | null): number | undefined {
    if (!el) return undefined;
    for (const cls of Array.from(el.classList)) {
        const match = /^cms-dragarea-(\d+)$/.exec(cls);
        if (match && match[1]) return Number(match[1]);
    }
    return undefined;
}

function disablePaste(item: HTMLElement, tooltipSelector: string): void {
    item.classList.add('cms-submenu-item-disabled');
    item.querySelectorAll<HTMLAnchorElement>('a').forEach((a) => {
        a.setAttribute('tabindex', '-1');
        a.setAttribute('aria-disabled', 'true');
    });
    const tooltip = item.querySelector<HTMLElement>(tooltipSelector);
    if (tooltip) tooltip.style.display = 'block';
}

function mergeOptions(input: Partial<PluginOptions>): PluginOptions {
    // Deep-ish merge for the `urls` sub-object, shallow for the rest.
    // Matches the legacy `$.extend(true, {}, defaults, input)` shape
    // closely enough — none of the other keys are nested objects.
    const merged: PluginOptions = { ...DEFAULT_OPTIONS, ...input };
    merged.urls = { ...DEFAULT_OPTIONS.urls, ...input.urls };
    return merged;
}

/**
 * Test/migration hook: register a freshly-constructed Plugin in the
 * shared registry. The constructor doesn't auto-add because legacy
 * `Plugin._initializeTree` is the canonical add path — adding via
 * the constructor would double-register when the tree initializer
 * runs. Tests that drive the constructor directly call this.
 */
export function _registerForTest(instance: Plugin): void {
    addInstance(instance);
}

export default Plugin;
