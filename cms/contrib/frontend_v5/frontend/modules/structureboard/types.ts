/*
 * Type definitions shared across the structureboard module.
 *
 * Mode names, the `invalidateState` action discriminators, and the
 * payload shapes the per-action handlers receive. Pure data — no
 * runtime code lives here.
 */

import type { PluginMutationAction, PluginOptions } from '../plugins/types';

/** Two-mode toggle: editing the page content vs editing the structure tree. */
export type ModeName = 'edit' | 'structure';

/**
 * Re-export the mutation discriminator so structureboard handlers
 * import from one place. `plugins/types.ts` is the source of truth.
 */
export type { PluginMutationAction };

/**
 * Server response payload after a plugin mutation. Loose because the
 * server adds situational fields (clipboard updates, sekizai blocks,
 * etc.). The handlers narrow what they read.
 */
export interface MutationData {
    /** Affected plugin descriptors — written into `CMS._plugins`. */
    plugins?: PluginOptions[];
    /** Re-rendered HTML for affected `.cms-plugin-<id>` containers. */
    content?: Array<{ pluginId: number | string; html: string }>;
    /** Sekizai (CSS / JS) block fragments to merge into head/body. */
    css?: string;
    js?: string;
    /** Source placeholder of a moved plugin. */
    placeholder_id?: number | string;
    /** Target placeholder. */
    target_placeholder_id?: number | string;
    /** New parent plugin id (or '' for placeholder root). */
    plugin_parent?: number | string | null;
    /** Position within the new parent. */
    target_position?: number;
    /** Cross-language paste flag. */
    move_a_copy?: boolean;
    /** When the action is CLEAR_PLACEHOLDER, the cleared id. */
    cleared_placeholder?: number | string;
    /** Loose escape hatch — server may add fields. */
    [key: string]: unknown;
}

/** Options for `invalidateState` — propagation is on by default. */
export interface InvalidateOptions {
    /**
     * When false, the localStorage cross-tab broadcast is skipped.
     * Set on the receiving side of `_handleExternalUpdate` so the
     * remote tab's invalidation doesn't bounce back through us.
     */
    propagate?: boolean;
}

/**
 * Latest-action stack entry. Used by `_handleExternalUpdate` to
 * de-dup an incoming storage event against an action we just
 * dispatched ourselves (the `storage` event fires in OTHER tabs but
 * not in the writer — our de-dup is more conservative than necessary
 * but matches legacy semantics).
 */
export type LatestAction = [PluginMutationAction, MutationData];

/**
 * The cross-tab payload pushed into `localStorage['cms-structure']`.
 * `pathname` scopes the broadcast: only tabs on the same path apply
 * the update.
 */
export type CrossTabPayload = [
    PluginMutationAction,
    MutationData,
    /* pathname */ string,
];
