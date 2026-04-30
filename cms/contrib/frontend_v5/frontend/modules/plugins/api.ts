/*
 * Plugin mutation HTTP API.
 *
 * Pure functions: build a payload, POST it, return the response. No
 * Modal/Messages/StructureBoard side effects, no `CMS.API.locked`
 * juggling — those are orchestration concerns the Plugin class
 * handles. This module is testable without window.CMS at all (beyond
 * a stub `CMS.config` for the language/csrf reads).
 *
 * Transport layer is `request.ts`, which already handles:
 *   - CSRF via `X-CSRFToken` header (sourced from `CMS.config.csrf`,
 *     since we updated request.ts in Phase 1)
 *   - Same-origin credentials
 *   - JSON-envelope error parsing for tree mutation endpoints
 *
 * Form-encoded payloads
 * ─────────────────────
 * Legacy uses `$.ajax({ data: {} })` which form-encodes by default,
 * because the django-cms placeholder admin views read `request.POST`
 * directly (form-encoded) — they don't decode JSON. So every payload
 * here is `URLSearchParams`. The browser sets the
 * `Content-Type: application/x-www-form-urlencoded` automatically.
 */

import { Helpers } from '../cms-base';
import { post } from '../request';
import { getCmsConfig } from './cms-globals';
import type { PluginOptions } from './types';

// ────────────────────────────────────────────────────────────────────
// Helpers
// ────────────────────────────────────────────────────────────────────

/**
 * Convert a flat record into a `URLSearchParams` body suitable for
 * Django POSTs. Nullish values are coerced to `''` so the field is
 * always present in the form (legacy behaviour — empty string
 * indicates "no parent" / "no plugin id" rather than "key absent").
 */
function toFormBody(values: Record<string, unknown>): URLSearchParams {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(values)) {
        if (value === undefined || value === null) {
            params.append(key, '');
        } else if (typeof value === 'boolean') {
            params.append(key, value ? 'true' : '');
        } else {
            params.append(key, String(value));
        }
    }
    return params;
}

function requireUrl(url: string | undefined, name: string): string {
    if (!url) {
        throw new Error(
            `[plugins/api] missing URL '${name}' on plugin options. ` +
                'The server must render this field — check the rendered ' +
                '<script data-cms-plugin> blob.',
        );
    }
    return Helpers.updateUrlWithPath(url);
}

function getRequestLanguage(): string {
    return getCmsConfig().request?.language ?? '';
}

// ────────────────────────────────────────────────────────────────────
// Copy
// ────────────────────────────────────────────────────────────────────

export interface CopyPluginInput {
    /** Source placeholder. */
    placeholder_id: number | string;
    /** Source plugin id (omit to copy the whole placeholder). */
    plugin_id?: number | string | null;
    /** Target plugin id (paste-as-child). */
    parent?: number | string | null;
    /** Target placeholder. Defaults to the clipboard placeholder. */
    target?: number | string | null;
    /** Action URLs. */
    urls: PluginOptions['urls'];
}

/** Server payload sent to the copy endpoint. Exposed for caller diagnostics. */
export interface CopyPluginPayload {
    source_placeholder_id: string;
    source_plugin_id: string;
    source_language: string;
    target_plugin_id: string;
    target_placeholder_id: string;
    target_language: string;
}

export interface CopyPluginResult<TResponse = unknown> {
    /** What was sent. */
    payload: CopyPluginPayload;
    /** Server response. */
    response: TResponse;
    /**
     * True when `sourceLanguage` was provided — the orchestrator
     * dispatches `PASTE` instead of `COPY` in that case. Mirrors
     * the legacy `copyingFromLanguage` branch.
     */
    copyingFromLanguage: boolean;
}

export async function requestCopyPlugin<TResponse = unknown>(
    opts: CopyPluginInput,
    sourceLanguage?: string,
): Promise<CopyPluginResult<TResponse>> {
    const config = getCmsConfig();
    const copyingFromLanguage = Boolean(sourceLanguage);

    let placeholder_id = opts.placeholder_id;
    let plugin_id: number | string | null | undefined = opts.plugin_id;
    let parent: number | string | null | undefined = opts.parent;
    let target: number | string | null | undefined = opts.target;
    let resolvedSourceLanguage = sourceLanguage;

    if (copyingFromLanguage) {
        // Cross-language copy: copy the *current* placeholder onto
        // itself, dropping plugin/parent ids.
        target = placeholder_id;
        plugin_id = '';
        parent = '';
    } else {
        resolvedSourceLanguage = config.request?.language;
    }

    const payload: CopyPluginPayload = {
        source_placeholder_id: String(placeholder_id ?? ''),
        source_plugin_id: String(plugin_id ?? ''),
        source_language: resolvedSourceLanguage ?? '',
        target_plugin_id: String(parent ?? ''),
        target_placeholder_id: String(target ?? config.clipboard?.id ?? ''),
        target_language: getRequestLanguage(),
    };

    const url = requireUrl(opts.urls?.copy_plugin, 'copy_plugin');
    const response = await post<TResponse>(url, toFormBody({ ...payload }));
    return { payload, response, copyingFromLanguage };
}

// ────────────────────────────────────────────────────────────────────
// Cut (move-to-clipboard)
// ────────────────────────────────────────────────────────────────────

export interface CutPluginInput {
    plugin_id: number | string;
    urls: PluginOptions['urls'];
}

export interface CutPluginPayload {
    placeholder_id: string;
    plugin_id: string;
    plugin_parent: string;
    target_language: string;
}

export interface CutPluginResult<TResponse = unknown> {
    payload: CutPluginPayload;
    response: TResponse;
}

export async function requestCutPlugin<TResponse = unknown>(
    opts: CutPluginInput,
): Promise<CutPluginResult<TResponse>> {
    const config = getCmsConfig();
    const payload: CutPluginPayload = {
        placeholder_id: String(config.clipboard?.id ?? ''),
        plugin_id: String(opts.plugin_id),
        plugin_parent: '',
        target_language: getRequestLanguage(),
    };
    const url = requireUrl(opts.urls?.move_plugin, 'move_plugin');
    const response = await post<TResponse>(url, toFormBody({ ...payload }));
    return { payload, response };
}

// ────────────────────────────────────────────────────────────────────
// Move (drag commit / ordering / paste)
// ────────────────────────────────────────────────────────────────────

export interface MovePluginInput {
    plugin_id: number | string;
    /** Empty string when moving to the placeholder root. */
    plugin_parent?: number | string | null;
    /** When set, the server records this as a "move-a-copy" paste. */
    move_a_copy?: boolean;
    /** New placeholder id when crossing placeholder boundaries. */
    placeholder_id?: number | string | null;
    /** 1-based position within the new parent. */
    target_position?: number;
    urls: PluginOptions['urls'];
}

export interface MovePluginPayload {
    plugin_id: string;
    plugin_parent: string;
    target_language: string;
    move_a_copy: string;
    target_position: string;
    /** Only present when crossing placeholder boundaries. */
    placeholder_id?: string;
}

export interface MovePluginResult<TResponse = unknown> {
    payload: MovePluginPayload;
    response: TResponse;
}

export async function requestMovePlugin<TResponse = unknown>(
    opts: MovePluginInput,
): Promise<MovePluginResult<TResponse>> {
    const payload: MovePluginPayload = {
        plugin_id: String(opts.plugin_id),
        plugin_parent: opts.plugin_parent === undefined || opts.plugin_parent === null
            ? ''
            : String(opts.plugin_parent),
        target_language: getRequestLanguage(),
        move_a_copy: opts.move_a_copy ? 'true' : '',
        target_position: opts.target_position !== undefined ? String(opts.target_position) : '',
    };
    if (opts.placeholder_id !== undefined && opts.placeholder_id !== null) {
        payload.placeholder_id = String(opts.placeholder_id);
    }
    const url = requireUrl(opts.urls?.move_plugin, 'move_plugin');
    const response = await post<TResponse>(url, toFormBody({ ...payload }));
    return { payload, response };
}

// ────────────────────────────────────────────────────────────────────
// URL builders (modal-opening methods don't POST themselves)
// ────────────────────────────────────────────────────────────────────

export interface BuildAddPluginUrlInput {
    /** From `this.options.urls.add_plugin`. */
    addPluginUrl: string;
    /** Containing placeholder id. */
    placeholder_id: number | string;
    /** Plugin type slug (e.g. 'TextPlugin'). */
    plugin_type: string;
    /** Optional parent plugin id when adding as a child. */
    plugin_parent?: number | string | null;
    /** 1-based insertion position. */
    plugin_position: number;
    /**
     * The original page path the toolbar opened on. Defaults to
     * `window.location.pathname + window.location.search`.
     */
    cms_path?: string;
}

/**
 * Build the URL for opening the add-plugin modal. Equivalent to the
 * legacy:
 *
 *   url = this.options.urls.add_plugin + '?' + $.param(params);
 *
 * Pulled out as a pure function so the Plugin class's `addPlugin`
 * method only has to coordinate the modal — URL construction is
 * tested here in isolation.
 */
export function buildAddPluginUrl(opts: BuildAddPluginUrlInput): string {
    const config = getCmsConfig();
    const language = config.request?.language ?? '';
    const cmsPath = opts.cms_path ?? `${window.location.pathname}${window.location.search}`;

    const params = new URLSearchParams({
        placeholder_id: String(opts.placeholder_id),
        plugin_type: opts.plugin_type,
        cms_path: cmsPath,
        plugin_language: language,
        plugin_position: String(opts.plugin_position),
    });
    if (opts.plugin_parent !== undefined && opts.plugin_parent !== null && opts.plugin_parent !== '') {
        params.append('plugin_parent', String(opts.plugin_parent));
    }
    const sep = opts.addPluginUrl.includes('?') ? '&' : '?';
    return `${opts.addPluginUrl}${sep}${params.toString()}`;
}

// Test/migration hook for diagnosing payload construction without
// hitting the network.
export const _internals = { toFormBody, requireUrl };
