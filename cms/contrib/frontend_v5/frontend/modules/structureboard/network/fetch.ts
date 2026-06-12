/*
 * GET endpoints structureboard hits during mode-switching and
 * post-mutation toolbar refresh.
 *
 *   - `requestMode('structure'|'content')` — fetches the rendered
 *     page in the opposite mode, used by `_loadStructure`/`_loadContent`.
 *     Cached per mode (legacy memoised on `this._requeststructure` /
 *     `this._requestcontent` to avoid duplicate prefetch).
 *   - `loadToolbar()` — fetches a toolbar HTML fragment with
 *     placeholder ids and obj_id / obj_type / language query params.
 *
 * Native fetch (text response). Caller decides how to consume —
 * structureboard's `_loadContent` regexes the HTML, our content
 * pipeline (3g) DiffDOM-applies it.
 *
 * Cache invalidation: the per-mode promise can be cleared by passing
 * `force: true` so a re-fetch happens. Legacy used per-instance state;
 * we own the cache here.
 */

import { Helpers } from '../../cms-base';
import { getCmsConfig, getPluginsRegistry } from '../../plugins/cms-globals';
import { preloadImagesFromMarkup } from './images';

const cache: Partial<Record<'structure' | 'content', Promise<string>>> = {};

/**
 * Fetch the page in the opposite mode (structure/content). Memoised
 * per mode — concurrent calls share the in-flight promise. Side
 * effect: triggers `preloadImagesFromMarkup` on the response so
 * structure-mode hover-previews don't pop in.
 *
 * Mirrors legacy `_requestMode`. The URLs come from
 * `CMS.config.settings.{structure,edit}` — server-rendered.
 */
export function requestMode(
    mode: 'structure' | 'content',
    opts: { force?: boolean } = {},
): Promise<string> {
    if (!opts.force && cache[mode]) {
        return cache[mode] as Promise<string>;
    }
    const settings = getCmsConfig().settings ?? {};
    const url =
        mode === 'structure'
            ? (settings.structure as string | undefined)
            : (settings.edit as string | undefined);
    if (!url) {
        return Promise.reject(
            new Error(
                `[structureboard/network] missing CMS.config.settings.${mode === 'structure' ? 'structure' : 'edit'} URL`,
            ),
        );
    }

    const promise = fetch(url, {
        method: 'GET',
        credentials: 'same-origin',
        headers: { Accept: 'text/html' },
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error(
                    `[structureboard/network] ${mode} fetch failed: ${response.status} ${response.statusText}`,
                );
            }
            return response.text();
        })
        .then((markup) => {
            preloadImagesFromMarkup(markup);
            return markup;
        });

    cache[mode] = promise;
    return promise;
}

/**
 * Drop the cached promise for a mode so the next `requestMode` call
 * re-fetches. Called by content-refresh after a mutation lands.
 */
export function invalidateModeCache(mode?: 'structure' | 'content'): void {
    if (mode) {
        delete cache[mode];
    } else {
        delete cache.structure;
        delete cache.content;
    }
}

/**
 * GET the toolbar fragment for the current page. Query params:
 *   - `placeholders[]=<id>` for every placeholder on the page
 *   - `obj_id=<pk>`, `obj_type=<model>`, `language=<lang>`
 *
 * Mirrors legacy `_loadToolbar`. The response is HTML which the
 * legacy toolbar bundle's `_refreshMarkup` renders into the toolbar
 * container.
 */
export function loadToolbar(): Promise<string> {
    const config = getCmsConfig();
    const request = (config.request ?? {}) as {
        toolbar?: string;
        pk?: number | string;
        model?: string;
        language?: string;
    };
    if (!request.toolbar) {
        return Promise.reject(
            new Error('[structureboard/network] missing CMS.config.request.toolbar URL'),
        );
    }

    const placeholders = getPlaceholderIds(getPluginsRegistry());
    const params = new URLSearchParams();
    for (const id of placeholders) params.append('placeholders[]', String(id));
    params.append('obj_id', String(request.pk ?? ''));
    params.append('obj_type', String(request.model ?? ''));
    params.append('language', String(request.language ?? ''));

    const url = Helpers.updateUrlWithPath(
        `${request.toolbar}?${params.toString()}`,
    );

    return fetch(url, {
        method: 'GET',
        credentials: 'same-origin',
        headers: { Accept: 'text/html' },
    }).then((response) => {
        if (!response.ok) {
            throw new Error(
                `[structureboard/network] toolbar fetch failed: ${response.status} ${response.statusText}`,
            );
        }
        return response.text();
    });
}

/**
 * Distinct placeholder ids in `CMS._plugins`. Equivalent to legacy
 * `getPlaceholderIds` from `cms.toolbar.js`. Lives here so 3b doesn't
 * have to wait on the toolbar port.
 */
function getPlaceholderIds(
    plugins: ReadonlyArray<readonly [string, unknown]>,
): Array<number | string> {
    const ids = new Set<number | string>();
    for (const entry of plugins) {
        const opts = entry[1] as
            | { type?: string; placeholder_id?: number | string | null }
            | null;
        if (
            opts &&
            opts.type === 'placeholder' &&
            opts.placeholder_id !== undefined &&
            opts.placeholder_id !== null
        ) {
            ids.add(opts.placeholder_id);
        }
    }
    return Array.from(ids);
}

/** Test/migration hook: clear the per-mode cache between tests. */
export function _resetCacheForTest(): void {
    delete cache.structure;
    delete cache.content;
}
