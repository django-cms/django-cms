/*
 * Mutation orchestration helpers shared by the Plugin class's
 * mutation methods (`copyPlugin`, `cutPlugin`, `movePlugin`,
 * `addPlugin`, `editPlugin`, `deletePlugin`).
 *
 * Why this file exists
 * ────────────────────
 * The legacy methods all share four patterns:
 *   1. Lock state — `CMS.API.locked` flag prevents concurrent ops.
 *   2. Modal opening — defensive when `CMS.Modal` is absent.
 *   3. Success/error messaging — `CMS.API.Messages`, defensive.
 *   4. Structureboard invalidation — `CMS.API.StructureBoard.
 *      invalidateState`, defensive.
 *
 * Centralising these keeps the Plugin class methods short and gives
 * us one place to evolve the defensive fallbacks (e.g. when
 * `cms.modal` lands as a TS module the legacy bundle lookup goes
 * away here, not in five copies).
 */

import { hideLoader, showLoader } from '../loader';
import {
    getCmsConfig,
    getCmsLocked,
    getMessages,
    getModalConstructor,
    getStructureBoard,
    setCmsLocked,
} from './cms-globals';
import type { PluginMutationAction } from './types';

// ────────────────────────────────────────────────────────────────────
// Lock
// ────────────────────────────────────────────────────────────────────

/**
 * Acquire the global `CMS.API.locked` flag, run `fn`, release it.
 * The flag's purpose is to suppress double-fire on rapid clicks
 * (e.g. user double-clicks "cut" before the first request returns).
 *
 * Returns `undefined` when the lock is already held — callers treat
 * that as "request rejected, try again later". Mirrors the legacy
 * `if (CMS.API.locked) return false; CMS.API.locked = true; ...`
 * pattern exactly.
 */
export async function withLock<T>(fn: () => Promise<T>): Promise<T | undefined> {
    if (getCmsLocked()) return undefined;
    setCmsLocked(true);
    try {
        return await fn();
    } finally {
        setCmsLocked(false);
    }
}

// ────────────────────────────────────────────────────────────────────
// Modal
// ────────────────────────────────────────────────────────────────────

/**
 * Modal lifecycle handle that callers can hold onto until they're
 * done. `close()` + `off()` are called from Plugin.destroy.
 */
export interface ModalHandle {
    open?(opts: Record<string, unknown>): void;
    close?(): void;
    off?(): void;
    ui?: { modal?: { hide?(): void }; frame?: HTMLIFrameElement | unknown };
    [key: string]: unknown;
}

export interface ModalOpenOptions {
    url?: string;
    title?: string;
    breadcrumbs?: unknown[];
    width?: number;
    height?: number;
    html?: HTMLElement | string;
    [key: string]: unknown;
}

export interface OpenModalInput {
    /** Defensive — `onClose` is read off the plugin's options. */
    onClose?: unknown;
    /** Defensive — same. */
    redirectOnClose?: unknown;
}

/**
 * Construct a modal. Returns `null` when `CMS.Modal` isn't on the
 * page (contrib-only setup without the legacy bundle).
 */
export function constructModal(
    init: OpenModalInput = {},
): ModalHandle | null {
    const Modal = getModalConstructor();
    if (!Modal) return null;
    const params: Record<string, unknown> = {};
    if (init.onClose !== undefined) params.onClose = init.onClose;
    if (init.redirectOnClose !== undefined) {
        params.redirectOnClose = init.redirectOnClose;
    }
    return new Modal(params) as unknown as ModalHandle;
}

// ────────────────────────────────────────────────────────────────────
// Messages
// ────────────────────────────────────────────────────────────────────

/**
 * Open a localised success message via `CMS.API.Messages.open`. No-op
 * when Messages isn't on the page.
 */
export function notifySuccess(): void {
    const messages = getMessages();
    if (!messages) return;
    const message = getCmsConfig().lang?.success ?? 'Success';
    messages.open({ message });
}

/**
 * Open a localised error message. The legacy code concatenates
 * `lang.error + responseText` — we keep the same shape so the user
 * sees the server's error text after the localised prefix.
 */
export function notifyError(detail?: string): void {
    const messages = getMessages();
    if (!messages) return;
    const prefix = getCmsConfig().lang?.error ?? 'Error';
    messages.open({
        message: `${prefix}${detail ?? ''}`,
        error: true,
    });
}

// ────────────────────────────────────────────────────────────────────
// Structureboard invalidation
// ────────────────────────────────────────────────────────────────────

/**
 * Tell structureboard to recompute its tree state after a mutation.
 * No-op when structureboard isn't on the page (contrib-only setup).
 */
export function broadcastInvalidate(
    action: PluginMutationAction,
    data: unknown,
): void {
    getStructureBoard()?.invalidateState?.(action, data);
}

// ────────────────────────────────────────────────────────────────────
// Clipboard draggable
// ────────────────────────────────────────────────────────────────────

/**
 * The `<div class="cms-draggable-from-clipboard">` rendered by the
 * clipboard plugin (when something has been cut/copied). Read from
 * the DOM each time — legacy cached this in a module variable but
 * the cache went stale after structureboard re-renders.
 */
export function getClipboardDraggable(): HTMLElement | null {
    return document.querySelector<HTMLElement>('.cms-draggable-from-clipboard');
}

// ────────────────────────────────────────────────────────────────────
// Loader proxy (kept here so the Plugin class doesn't import loader directly)
// ────────────────────────────────────────────────────────────────────

export { hideLoader, showLoader };
