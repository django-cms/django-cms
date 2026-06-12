/*
 * Type definitions shared across the plugins module.
 *
 * Source of truth for the legacy `cms.plugins.js` data shapes. When the
 * server changes the rendered `<script data-cms-plugin>` payload, this
 * file is the place to widen the types — every other module in
 * `plugins/` consumes them.
 */

/**
 * Discriminator for a plugin descriptor. The legacy code's switch
 * statement covers three values: 'placeholder', 'plugin', and
 * everything else (treated as 'generic'). We keep the explicit set so
 * narrowing works.
 */
export type PluginType = 'placeholder' | 'plugin' | 'generic';

/**
 * URLs the server renders alongside each plugin descriptor. Every
 * field is optional because not every action is available on every
 * plugin (e.g. placeholders don't have an edit URL).
 */
export interface PluginUrls {
    add_plugin?: string;
    edit_plugin?: string;
    move_plugin?: string;
    copy_plugin?: string;
    delete_plugin?: string;
}

/**
 * The descriptor object the server renders into the
 * `<script data-cms-plugin>` (and `data-cms-placeholder` /
 * `data-cms-general`) blobs. Stored on the wrapping DOM element via
 * `cms-data.ts` and read by every consumer.
 *
 * Loose by design — the legacy server adds situational fields
 * (breadcrumb data, position, language, etc.) and we don't want to
 * fight the type checker every time a new key shows up. Add narrow
 * fields here as the port matures.
 */
export interface PluginOptions {
    type: PluginType | string;

    // Identifiers
    placeholder_id?: number | string | null;
    plugin_type?: string;
    plugin_id?: number | string | null;
    plugin_parent?: number | string | null;

    // Restrictions (allowed child / parent plugin types)
    plugin_restriction?: string[];
    plugin_parent_restriction?: string[];

    // Action URLs
    urls?: PluginUrls;

    // Server-rendered position within the parent placeholder.
    position?: number;

    // Display name — used in modals, breadcrumbs, tooltips.
    name?: string;

    // Language code — lifted from `CMS.config.request.language` if
    // absent, but the server may pre-render it.
    language?: string;

    /**
     * Catch-all so the type doesn't fight new server-rendered fields.
     * Prefer adding named fields above when a new key becomes
     * load-bearing in TS code.
     */
    [key: string]: unknown;
}

/**
 * Minimum surface a registry consumer needs from a Plugin instance.
 * The actual `Plugin` class implements this; using the interface in
 * `registry.ts` lets the registry stay independent of the class
 * definition (and avoids a circular import).
 */
export interface PluginInstance {
    options: PluginOptions;
}

/**
 * Entry shape for `CMS._plugins` — `[scriptId, options]` tuples
 * preserved from the legacy `_initializeTree` flow.
 */
export type PluginDescriptor = [string, PluginOptions];

/**
 * The action discriminator passed to
 * `StructureBoard.invalidateState(action, data)` and
 * `Plugin._recalculatePluginPositions`.
 */
export type PluginMutationAction =
    | 'ADD'
    | 'EDIT'
    | 'CHANGE'
    | 'DELETE'
    | 'MOVE'
    | 'COPY'
    | 'CUT'
    | 'PASTE'
    | 'CLEAR_PLACEHOLDER';
