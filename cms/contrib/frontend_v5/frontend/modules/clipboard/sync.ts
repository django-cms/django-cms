/*
 * Cross-tab clipboard sync — when the user copies/cuts a plugin in
 * one tab, every other same-origin tab should see the same clipboard
 * state without a page refresh. Replaces the `local-storage` npm dep
 * used by legacy with native `storage` events. Same pattern as
 * structureboard's `network/propagate.ts`.
 *
 * Storage key: `cms-clipboard`. Writers serialize the full clipboard
 * blob (`{ data, html, timestamp }`); readers deserialise and notify
 * via the registered callback.
 */

const STORAGE_KEY = 'cms-clipboard';

export interface ClipboardData {
    /** The plugin descriptor (loose — passes straight to Plugin ctor). */
    data: { plugin_id?: number | string; [key: string]: unknown };
    /** Pre-rendered HTML for the clipboard list item. */
    html: string;
    /** Date.now() at write time — used for cross-tab tie-breaking. */
    timestamp: number;
}

let listenerAttached = false;
let onUpdate: ((value: ClipboardData) => void) | null = null;

/**
 * Write the clipboard blob. Same-origin tabs receive it via their
 * `storage` listener. Idempotent when storage is unavailable.
 */
export function writeClipboard(value: ClipboardData): void {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
    } catch {
        /* storage unavailable — local-only update */
    }
}

/**
 * Subscribe to clipboard updates from sibling tabs. Calling more
 * than once replaces the callback. Returns a teardown for tests.
 */
export function listenForExternalUpdates(
    callback: (value: ClipboardData) => void,
): () => void {
    onUpdate = callback;
    if (listenerAttached) return detach;
    if (!isStorageSupported()) return detach;
    window.addEventListener('storage', handleStorageEvent);
    listenerAttached = true;
    return detach;
}

function handleStorageEvent(e: StorageEvent): void {
    if (e.key !== STORAGE_KEY || !e.newValue) return;
    try {
        const parsed = JSON.parse(e.newValue) as ClipboardData;
        onUpdate?.(parsed);
    } catch {
        /* malformed payload — ignore */
    }
}

function detach(): void {
    if (!listenerAttached) return;
    window.removeEventListener('storage', handleStorageEvent);
    listenerAttached = false;
    onUpdate = null;
}

function isStorageSupported(): boolean {
    try {
        const probe = '__cms_clipboard_probe';
        localStorage.setItem(probe, probe);
        localStorage.removeItem(probe);
        return true;
    } catch {
        return false;
    }
}

/** Test helper — reset module-level state. */
export function _resetForTest(): void {
    detach();
}
