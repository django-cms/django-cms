/*
 * Typed boundary for every `window.CMS.X` access made by the plugins
 * module.
 *
 * Why this file exists (CLAUDE.md decision 7)
 * ───────────────────────────────────────────
 * The legacy bundle (`cms.modal`, `cms.structureboard`, `cms.messages`,
 * `cms.tooltip`, `cms.toolbar`, `cms.clipboard`) is still the runtime
 * source for those globals on this branch. The plugins module talks
 * to them defensively — methods no-op when a global is absent so a
 * contrib-only page (which lacks the legacy bundle) still works.
 *
 * Every `window.CMS.X` lookup goes through an accessor here. When the
 * legacy bundle is dropped (Phase 4 — assemble `bundle.toolbar.min.js`),
 * THIS is the single file that changes: each accessor swaps from
 * "read window.CMS.X with defensive defaults" to "import the ported
 * module directly."
 *
 * Accessors return `undefined` (or sentinel empty values) when the
 * global isn't set up yet. Callers narrow with `if (api)` before use.
 */

import type {
    PluginDescriptor,
    PluginInstance,
    PluginMutationAction,
} from './types';

// ────────────────────────────────────────────────────────────────────
// Type-level shapes for the legacy globals we touch
// ────────────────────────────────────────────────────────────────────

/** Subset of `window.CMS.config` the plugins module reads. */
export interface PluginsCmsConfig {
    csrf?: string;
    lang?: Record<string, string>;
    request?: { language?: string; toolbar?: string; pk?: number | string; model?: string };
    clipboard?: { id?: number | string };
    /**
     * Top-level mode flag — `'draft'` for editable pages, `'live'` for
     * read-only views. Distinct from `settings.mode` which toggles
     * between `'structure'` and `'edit'` views of the same draft page.
     */
    mode?: string;
    settings?: {
        mode?: string;
        legacy_mode?: boolean;
        /** URL the structureboard fetches for structure-mode rendering. */
        structure?: string;
        /** URL the structureboard fetches for edit-mode rendering. */
        edit?: string;
    };
    [key: string]: unknown;
}

/** Subset of `window.CMS.settings` the plugins module reads/mutates. */
export interface PluginsCmsSettings {
    mode?: string;
    states?: Array<number | string>;
    dragbars?: Array<number | string>;
    [key: string]: unknown;
}

/**
 * Surface of `window.CMS.API.StructureBoard` consumed by plugins.
 * Loose because StructureBoard isn't ported yet — narrow these
 * fields in Phase 3 when the port lands.
 */
export interface StructureBoardApi {
    _loadedStructure?: boolean;
    _loadedContent?: boolean;
    dragging?: boolean;
    ui?: { container?: { hasClass(className: string): boolean } };
    invalidateState?(action: PluginMutationAction, data: unknown): void;
    _showAndHighlightPlugin?(timeout: number, ignoreErrors: boolean): unknown;
    getId?(el: unknown): number | string | undefined;
    getIds?(els: unknown): Array<number | string>;
    actualizePluginCollapseStatus?(pluginId: number | string): void;
    [key: string]: unknown;
}

/** Surface of `window.CMS.Modal` (constructor). */
export type ModalConstructor = new (options?: Record<string, unknown>) => unknown;

/** Surface of `window.CMS.API.Messages.open` / `.close`. */
export interface MessagesApi {
    open(options: { message: string; error?: boolean; delay?: number }): void;
    close?(): void;
}

/** Surface of `window.CMS.API.Tooltip` consumed by plugins. */
export interface TooltipApi {
    displayToggle(
        show: boolean,
        target?: HTMLElement | null,
        name?: string,
        pluginId?: number | string,
    ): void;
}

/** Surface of `window.CMS.API.Clipboard` consumed by plugins. */
export interface ClipboardApi {
    populate(html: string, pluginData: unknown): void;
}

/** Surface of `window.CMS.API.Toolbar` consumed by plugins (loose). */
export interface ToolbarApi {
    /**
     * Replace the toolbar's rendered markup with a fresh version
     * (typically clipped from the content-mode response). Called by
     * structureboard's `refreshContent` after a content swap so the
     * toolbar reflects the updated state.
     */
    _refreshMarkup?(newToolbar: Element): void;
    [key: string]: unknown;
}

// ────────────────────────────────────────────────────────────────────
// Accessors — every `window.CMS.X` read funnels through here
// ────────────────────────────────────────────────────────────────────

/** The `window.CMS` namespace, or undefined if the bundle hasn't run. */
export function getCmsNamespace(): CmsGlobal | undefined {
    return window.CMS;
}

export function getCmsConfig(): PluginsCmsConfig {
    return (window.CMS?.config ?? {}) as PluginsCmsConfig;
}

export function getCmsSettings(): PluginsCmsSettings {
    if (!window.CMS) return {};
    if (!window.CMS.settings) window.CMS.settings = {};
    return window.CMS.settings as PluginsCmsSettings;
}

export function getCmsLocked(): boolean {
    return Boolean(window.CMS?.API?.locked);
}

export function setCmsLocked(value: boolean): void {
    const api = ensureCmsApi();
    api.locked = value;
}

export function getStructureBoard(): StructureBoardApi | undefined {
    return window.CMS?.API?.StructureBoard as StructureBoardApi | undefined;
}

export function getMessages(): MessagesApi | undefined {
    return window.CMS?.API?.Messages as MessagesApi | undefined;
}

export function getTooltip(): TooltipApi | undefined {
    return window.CMS?.API?.Tooltip as TooltipApi | undefined;
}

export function getClipboard(): ClipboardApi | undefined {
    return window.CMS?.API?.Clipboard as ClipboardApi | undefined;
}

export function getToolbar(): ToolbarApi | undefined {
    return window.CMS?.API?.Toolbar as ToolbarApi | undefined;
}

/** Modal constructor. Undefined if the legacy bundle hasn't run. */
export function getModalConstructor(): ModalConstructor | undefined {
    const cms = window.CMS as { Modal?: ModalConstructor } | undefined;
    return cms?.Modal;
}

// ────────────────────────────────────────────────────────────────────
// Plugin registries (live on `window.CMS` so legacy + structureboard
// see the same instances during the strangler period).
// ────────────────────────────────────────────────────────────────────

/**
 * The shared `CMS._instances` array — Plugin instances created from
 * the rendered descriptor blobs. Auto-creates the array if missing
 * so callers can `push` without further checks.
 */
export function getInstancesRegistry(): PluginInstance[] {
    const cms = ensureCmsNamespace();
    const existing = cms._instances as unknown as PluginInstance[] | undefined;
    if (existing) return existing;
    const fresh: PluginInstance[] = [];
    (cms as unknown as { _instances: PluginInstance[] })._instances = fresh;
    return fresh;
}

/**
 * The shared `CMS._plugins` array — `[scriptId, options]` tuples read
 * from `<script data-cms-plugin>` blobs by `_initializeTree`. Auto-
 * creates the array if missing.
 */
export function getPluginsRegistry(): PluginDescriptor[] {
    const cms = ensureCmsNamespace();
    const existing = cms._plugins as PluginDescriptor[] | undefined;
    if (existing) return existing;
    const fresh: PluginDescriptor[] = [];
    (cms as { _plugins: PluginDescriptor[] })._plugins = fresh;
    return fresh;
}

// ────────────────────────────────────────────────────────────────────
// Derived predicates
// ────────────────────────────────────────────────────────────────────

/**
 * Reproduces the legacy `isStructureReady` check. True when:
 *   - settings.mode is 'structure', OR
 *   - settings.legacy_mode is on, OR
 *   - StructureBoard has finished loading the structure.
 */
export function isStructureReady(): boolean {
    const settings = getCmsConfig().settings ?? {};
    if (settings.mode === 'structure') return true;
    if (settings.legacy_mode) return true;
    const sb = getStructureBoard();
    return Boolean(sb?._loadedStructure);
}

/**
 * Reproduces the legacy `isContentReady` check. True when:
 *   - settings.mode is NOT 'structure', OR
 *   - settings.legacy_mode is on, OR
 *   - StructureBoard has finished loading the content.
 */
export function isContentReady(): boolean {
    const settings = getCmsConfig().settings ?? {};
    if (settings.mode !== 'structure') return true;
    if (settings.legacy_mode) return true;
    const sb = getStructureBoard();
    return Boolean(sb?._loadedContent);
}

// ────────────────────────────────────────────────────────────────────
// Internal helpers
// ────────────────────────────────────────────────────────────────────

function ensureCmsNamespace(): CmsGlobal {
    if (!window.CMS) window.CMS = {};
    return window.CMS;
}

function ensureCmsApi(): CmsApi {
    const cms = ensureCmsNamespace();
    if (!cms.API) cms.API = {};
    return cms.API;
}
