/*
 * Cross-tab invalidation propagation.
 *
 * Two tabs editing the same page need to stay consistent: when one
 * tab dispatches `invalidateState('MOVE', data)`, the other tab
 * applies the same DOM mutations without re-broadcasting. Achieved
 * via `localStorage` write + `storage` event listen — the `storage`
 * event fires in OTHER same-origin tabs, never in the writer.
 *
 * Replaces the `local-storage` npm dep used by legacy. Native
 * `storage` events provide the same behaviour with less code and
 * one less dependency.
 *
 * Pathname scoping
 * ────────────────
 * The payload includes `window.location.pathname`. Tabs on different
 * paths ignore the broadcast. Query-string changes are intentionally
 * NOT a scoping factor — matches legacy behaviour (multiple tabs
 * editing the same page with different `?language=` are still seen
 * as the same page for invalidation purposes).
 *
 * De-duplication
 * ──────────────
 * The writer also remembers its `latestAction` so that if the storage
 * event somehow fires back at it (browser quirk on some legacy IE
 * versions), we don't re-apply.
 */

import type {
    CrossTabPayload,
    LatestAction,
    MutationData,
    PluginMutationAction,
} from '../types';

export const STORAGE_KEY = 'cms-structure';

let latestAction: LatestAction | null = null;
let listenerAttached = false;
let onUpdate: ((action: PluginMutationAction, data: MutationData) => void) | null = null;

/**
 * Write the current invalidation payload to localStorage. Same-origin
 * tabs on the same pathname will pick it up via their `storage`
 * listener.
 *
 * Idempotent if `localStorage` is unavailable (private browsing,
 * disabled storage) — the in-memory `latestAction` is still updated
 * so local de-dup works.
 */
export function propagateInvalidatedState(
    action: PluginMutationAction,
    data: MutationData,
): void {
    latestAction = [action, data];
    const payload: CrossTabPayload = [action, data, window.location.pathname];
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch {
        /* storage unavailable — local-only update */
    }
}

/**
 * Register a callback for storage events that match our key.
 * Idempotent — calling more than once replaces the callback.
 *
 * Returns a teardown that detaches the listener (used by
 * `_resetForTest`).
 */
export function listenToExternalUpdates(
    callback: (action: PluginMutationAction, data: MutationData) => void,
): () => void {
    onUpdate = callback;
    if (listenerAttached) return detach;
    if (!isStorageSupported()) return detach;
    window.addEventListener('storage', handleStorageEvent);
    listenerAttached = true;
    return detach;
}

function detach(): void {
    if (!listenerAttached) return;
    window.removeEventListener('storage', handleStorageEvent);
    listenerAttached = false;
    onUpdate = null;
}

function handleStorageEvent(event: StorageEvent): void {
    if (event.key !== STORAGE_KEY) return;
    handleExternalUpdate(event.newValue);
}

/**
 * Public for tests + the structureboard class to call directly when
 * synthesising a cross-tab dispatch (e.g. on first attach, replay
 * the last entry).
 *
 * Mirrors legacy `_handleExternalUpdate`: parses the JSON, scopes by
 * pathname, de-dups against `latestAction`, then dispatches.
 */
export function handleExternalUpdate(value: string | null): void {
    if (!value || !onUpdate) return;
    let parsed: CrossTabPayload;
    try {
        parsed = JSON.parse(value) as CrossTabPayload;
    } catch {
        return;
    }
    const [action, data, pathname] = parsed;
    if (pathname !== window.location.pathname) return;
    if (
        latestAction &&
        latestAction[0] === action &&
        deepEqual(latestAction[1], data)
    ) {
        return;
    }
    onUpdate(action, data);
}

/**
 * Lightweight deep-equality probe for the de-dup check. The data
 * payload is JSON-serialisable per `CrossTabPayload`, so a string
 * compare is fast and correct.
 */
function deepEqual(a: unknown, b: unknown): boolean {
    if (a === b) return true;
    try {
        return JSON.stringify(a) === JSON.stringify(b);
    } catch {
        return false;
    }
}

function isStorageSupported(): boolean {
    try {
        const probe = '__cms_structure_probe__';
        localStorage.setItem(probe, probe);
        localStorage.removeItem(probe);
        return true;
    } catch {
        return false;
    }
}

/**
 * Test/migration hook: detach + clear in-memory state. Used by
 * vitest between cases.
 */
export function _resetForTest(): void {
    detach();
    latestAction = null;
    try {
        localStorage.removeItem(STORAGE_KEY);
    } catch {
        /* unavailable */
    }
}
