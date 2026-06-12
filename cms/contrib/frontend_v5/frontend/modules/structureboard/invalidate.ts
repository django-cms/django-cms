/*
 * `invalidateState` — top-level dispatcher for plugin mutations.
 *
 * Mirrors legacy `StructureBoard.invalidateState`. Routes the mutation
 * action to its handler, recalculates plugin positions, and (unless
 * `propagate: false` is passed) broadcasts the action over the
 * cross-tab `storage` event so other open tabs apply the same
 * mutation locally.
 *
 * Content refresh (the legacy `_updateContentFromDataBridge` step) is
 * NOT done here — it's the structureboard class shell's responsibility
 * (3i) and uses `refresh.ts` (3g) once those land. The dispatcher
 * exposes an `onContentRefresh` hook so the shell can wire it.
 *
 * Receiving side
 * ──────────────
 * `network/propagate.ts::listenToExternalUpdates` fires when another
 * tab broadcasts. The shell-side wiring (3i) calls
 * `invalidateState(action, data, { propagate: false })` so the local
 * apply doesn't bounce back through `propagate.ts`.
 */

import { recalculatePluginPositions } from '../plugins/registry';
import { propagateInvalidatedState } from './network/propagate';
import { handleAddPlugin } from './handlers/add';
import { handleClearPlaceholder } from './handlers/clear';
import { handleCopyPlugin } from './handlers/copy';
import { handleCutPlugin } from './handlers/cut';
import { handleDeletePlugin } from './handlers/delete';
import { handleEditPlugin } from './handlers/edit';
import { handleMovePlugin } from './handlers/move';
import type { MutationData, PluginMutationAction } from './types';

export interface InvalidateOptions {
    /**
     * When false, the cross-tab broadcast is skipped. Used by the
     * `storage`-event receiving side so a remote-originated update
     * doesn't echo back through us.
     */
    propagate?: boolean;
    /**
     * Called when the action is undefined / null / empty string —
     * the legacy fallback was `Helpers.reloadBrowser()`. The shell
     * (3i) wires the real reload; tests pass a spy.
     */
    onFullReload?: () => void;
    /**
     * Called after the handler runs (and BEFORE propagation) for
     * actions that require visible-content refresh — i.e. every
     * action except COPY. The shell wires this to `refresh.ts`
     * (3g). Defaults to a no-op.
     */
    onContentRefresh?: (
        action: PluginMutationAction,
        data: MutationData,
    ) => void;
}

/** Actions where COPY is the only one whose page content does NOT change. */
const SKIPS_CONTENT_REFRESH: ReadonlySet<PluginMutationAction> = new Set([
    'COPY',
]);

export function invalidateState(
    action: PluginMutationAction | undefined | null | '',
    data: MutationData,
    opts: InvalidateOptions = {},
): void {
    switch (action) {
        case 'COPY':
            handleCopyPlugin(data);
            break;
        case 'ADD':
            handleAddPlugin(data);
            break;
        case 'EDIT':
            handleEditPlugin(data);
            break;
        case 'CHANGE':
            // Legacy treats CHANGE as EDIT. Same payload shape.
            handleEditPlugin(data);
            break;
        case 'DELETE':
            handleDeletePlugin(data);
            break;
        case 'CLEAR_PLACEHOLDER':
            handleClearPlaceholder(data);
            break;
        case 'PASTE':
        case 'MOVE':
            handleMovePlugin(data);
            break;
        case 'CUT':
            handleCutPlugin(data);
            break;
        case undefined:
        case null:
        case '':
            opts.onFullReload?.();
            return;
        default:
            // Unknown action — fall through. Legacy: silent no-op.
            return;
    }

    recalculatePluginPositions(action, data);

    if (!SKIPS_CONTENT_REFRESH.has(action)) {
        opts.onContentRefresh?.(action, data);
    }

    if (opts.propagate !== false) {
        propagateInvalidatedState(action, data);
    }
}
