/*
 * Fetch wrapper for the rewrite.
 *
 * Replaces the legacy `$.ajax({...})` calls scattered through cms.*.js.
 * The legacy stack had no canonical request helper — each module rolled
 * its own — so this module is designed for what callers actually need
 * rather than for legacy API parity.
 *
 * Design decisions:
 *
 *   1. CSRF goes in the `X-CSRFToken` header, read from a cookie
 *      (default name "csrftoken"). Django's middleware accepts both
 *      header and body; header is cleaner because callers don't need to
 *      merge a token field into the payload, and it works uniformly for
 *      JSON, FormData, and URLSearchParams.
 *
 *   2. Plain object bodies auto-serialise to JSON with the right
 *      Content-Type. FormData and URLSearchParams pass through unchanged
 *      so the browser sets the correct multipart boundary / form
 *      encoding. Strings pass through unchanged. The caller can also
 *      provide their own `Content-Type` header to override.
 *
 *   3. Errors throw a typed `RequestError` carrying `status`,
 *      `statusText`, `url`, and the parsed response body. Catchable and
 *      inspectable, unlike the legacy `error(jqXHR)` callback shape.
 *
 *   4. No global "locked" flag, no automatic loader UI. Those are UI
 *      concerns the legacy code mixed into the request layer. Callers
 *      that need a loader wrap the call themselves.
 */

export class RequestError extends Error {
    constructor(
        public readonly status: number,
        public readonly statusText: string,
        public readonly url: string,
        public readonly body: unknown,
    ) {
        super(`HTTP ${status} ${statusText} on ${url}`);
        this.name = 'RequestError';
    }
}

export interface RequestOptions {
    /**
     * Request body. Plain objects are JSON-stringified and sent with
     * `Content-Type: application/json`. FormData and URLSearchParams
     * pass through unchanged. Strings pass through unchanged. Use
     * `null`/`undefined` (or omit) for no body.
     */
    body?: unknown;
    /**
     * Extra headers merged onto the defaults. CSRF token is added
     * automatically for unsafe methods unless the caller already
     * provided an `X-CSRFToken`.
     */
    headers?: Record<string, string>;
    /** Abort signal forwarded to fetch. */
    signal?: AbortSignal;
    /** Cookie name for CSRF token lookup. Defaults to "csrftoken". */
    csrfCookieName?: string;
}

const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS', 'TRACE']);

/**
 * Read a cookie value by name. Returns the URL-decoded value, or null
 * if no cookie with that name is set. Exposed because the request
 * layer isn't the only place that sometimes needs cookie access.
 */
export function getCookie(name: string): string | null {
    if (typeof document === 'undefined' || !document.cookie) return null;
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
        const trimmed = cookie.trim();
        const eq = trimmed.indexOf('=');
        if (eq === -1) continue;
        const key = trimmed.substring(0, eq);
        if (key === name) {
            return decodeURIComponent(trimmed.substring(eq + 1));
        }
    }
    return null;
}

/**
 * Low-level request. Most callers should use the `get` / `post` / `put`
 * / `del` shortcuts below. The return type defaults to `unknown` so
 * callers can narrow it via the generic parameter.
 */
export async function request<T = unknown>(
    method: string,
    url: string,
    opts: RequestOptions = {},
): Promise<T> {
    const headers: Record<string, string> = {
        Accept: 'application/json',
        ...opts.headers,
    };

    let body: BodyInit | undefined;
    if (opts.body !== undefined && opts.body !== null) {
        if (opts.body instanceof FormData || opts.body instanceof URLSearchParams) {
            // Pass through; browser sets Content-Type with the correct boundary.
            body = opts.body;
        } else if (typeof opts.body === 'string') {
            body = opts.body;
        } else if (opts.body instanceof Blob || opts.body instanceof ArrayBuffer) {
            body = opts.body;
        } else {
            body = JSON.stringify(opts.body);
            if (!('Content-Type' in headers)) {
                headers['Content-Type'] = 'application/json';
            }
        }
    }

    const upperMethod = method.toUpperCase();
    if (!SAFE_METHODS.has(upperMethod) && !('X-CSRFToken' in headers)) {
        const cookieName = opts.csrfCookieName ?? 'csrftoken';
        const token = getCookie(cookieName);
        if (token) headers['X-CSRFToken'] = token;
    }

    // Build init incrementally so we never pass `body: undefined` or
    // `signal: undefined` — `exactOptionalPropertyTypes` rejects those.
    const init: RequestInit = {
        method: upperMethod,
        headers,
        credentials: 'same-origin',
    };
    if (body !== undefined) init.body = body;
    if (opts.signal !== undefined) init.signal = opts.signal;

    const response = await fetch(url, init);

    // Always parse the body — callers need it on both success and error
    // paths. Empty 204 responses are common; handle them as null.
    const parsed = await readBody(response);

    if (!response.ok) {
        throw new RequestError(response.status, response.statusText, url, parsed);
    }

    return parsed as T;
}

async function readBody(response: Response): Promise<unknown> {
    if (response.status === 204) return null;
    const contentType = response.headers.get('Content-Type') ?? '';
    if (contentType.includes('application/json')) {
        // Catch malformed JSON so the RequestError still carries useful info
        // instead of failing inside the parser.
        try {
            return await response.json();
        } catch {
            return null;
        }
    }
    return response.text();
}

export const get = <T = unknown>(url: string, opts?: RequestOptions): Promise<T> =>
    request<T>('GET', url, opts);

export const post = <T = unknown>(
    url: string,
    body?: unknown,
    opts?: RequestOptions,
): Promise<T> => request<T>('POST', url, { ...opts, body });

export const put = <T = unknown>(
    url: string,
    body?: unknown,
    opts?: RequestOptions,
): Promise<T> => request<T>('PUT', url, { ...opts, body });

export const del = <T = unknown>(url: string, opts?: RequestOptions): Promise<T> =>
    request<T>('DELETE', url, opts);
