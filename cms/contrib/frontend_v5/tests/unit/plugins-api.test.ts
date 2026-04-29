import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    _internals,
    buildAddPluginUrl,
    requestCopyPlugin,
    requestCutPlugin,
    requestMovePlugin,
} from '../../frontend/modules/plugins/api';

/**
 * Minimal Response stub — request.ts treats it as the fetch return.
 * Body is parsed JSON by default.
 */
function jsonResponse(body: unknown, status = 200): Response {
    const headers = new Headers();
    headers.set('Content-Type', 'application/json');
    return {
        ok: status >= 200 && status < 300,
        status,
        statusText: '',
        headers,
        json: async () => body,
        text: async () => JSON.stringify(body),
    } as unknown as Response;
}

/**
 * Read the body parameters out of the fetch init. Body is a
 * URLSearchParams; we re-parse from its string serialisation so tests
 * don't depend on URLSearchParams internals.
 */
function readFormBody(init: RequestInit | undefined): URLSearchParams {
    expect(init).toBeDefined();
    const body = init!.body;
    expect(body).toBeInstanceOf(URLSearchParams);
    return new URLSearchParams((body as URLSearchParams).toString());
}

describe('toFormBody (internal)', () => {
    it('coerces nullish values to empty string', () => {
        const body = _internals.toFormBody({ a: 'x', b: null, c: undefined });
        expect(body.get('a')).toBe('x');
        expect(body.get('b')).toBe('');
        expect(body.get('c')).toBe('');
    });

    it('coerces booleans to "true" / ""', () => {
        const body = _internals.toFormBody({ flag_on: true, flag_off: false });
        expect(body.get('flag_on')).toBe('true');
        expect(body.get('flag_off')).toBe('');
    });

    it('coerces numbers to strings', () => {
        const body = _internals.toFormBody({ id: 42 });
        expect(body.get('id')).toBe('42');
    });
});

describe('requireUrl (internal)', () => {
    afterEach(() => {
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('throws a clear error when the URL is missing', () => {
        expect(() => _internals.requireUrl(undefined, 'copy_plugin')).toThrow(/copy_plugin/);
    });

    it('passes the URL through Helpers.updateUrlWithPath (cms_path appended)', () => {
        // Helpers.updateUrlWithPath uses window.location.pathname + search.
        const out = _internals.requireUrl('/admin/plugins/copy/', 'copy_plugin');
        expect(out).toContain('/admin/plugins/copy/');
        expect(out).toContain('cms_path=');
    });
});

describe('buildAddPluginUrl', () => {
    afterEach(() => {
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('builds a URL with required params', () => {
        window.CMS = { config: { request: { language: 'en' } } } as CmsGlobal;
        const url = buildAddPluginUrl({
            addPluginUrl: '/admin/cms/page/add-plugin/',
            placeholder_id: 7,
            plugin_type: 'TextPlugin',
            plugin_position: 3,
            cms_path: '/page/',
        });
        const params = new URL(url, 'http://x').searchParams;
        expect(params.get('placeholder_id')).toBe('7');
        expect(params.get('plugin_type')).toBe('TextPlugin');
        expect(params.get('plugin_language')).toBe('en');
        expect(params.get('plugin_position')).toBe('3');
        expect(params.get('cms_path')).toBe('/page/');
        expect(params.has('plugin_parent')).toBe(false);
    });

    it('includes plugin_parent when provided', () => {
        const url = buildAddPluginUrl({
            addPluginUrl: '/admin/cms/page/add-plugin/',
            placeholder_id: 1,
            plugin_type: 'Image',
            plugin_position: 1,
            plugin_parent: 99,
            cms_path: '/',
        });
        const params = new URL(url, 'http://x').searchParams;
        expect(params.get('plugin_parent')).toBe('99');
    });

    it('omits plugin_parent for empty string / null / unset', () => {
        // null
        let url = buildAddPluginUrl({
            addPluginUrl: '/x/',
            placeholder_id: 1,
            plugin_type: 'T',
            plugin_position: 1,
            plugin_parent: null,
            cms_path: '/',
        });
        expect(new URL(url, 'http://x').searchParams.has('plugin_parent')).toBe(false);

        // empty string
        url = buildAddPluginUrl({
            addPluginUrl: '/x/',
            placeholder_id: 1,
            plugin_type: 'T',
            plugin_position: 1,
            plugin_parent: '',
            cms_path: '/',
        });
        expect(new URL(url, 'http://x').searchParams.has('plugin_parent')).toBe(false);

        // unset (key omitted from input — `exactOptionalPropertyTypes: true`
        // forbids passing explicit undefined)
        url = buildAddPluginUrl({
            addPluginUrl: '/x/',
            placeholder_id: 1,
            plugin_type: 'T',
            plugin_position: 1,
            cms_path: '/',
        });
        expect(new URL(url, 'http://x').searchParams.has('plugin_parent')).toBe(false);
    });

    it('uses & if the base URL already has a query string', () => {
        const url = buildAddPluginUrl({
            addPluginUrl: '/admin/?prefilled=1',
            placeholder_id: 1,
            plugin_type: 'T',
            plugin_position: 1,
            cms_path: '/',
        });
        // Either ?...&... or ?...&placeholder_id — count of '?' must be 1
        expect((url.match(/\?/g) ?? []).length).toBe(1);
    });

    it('falls back to window.location for cms_path when omitted', () => {
        const url = buildAddPluginUrl({
            addPluginUrl: '/admin/',
            placeholder_id: 1,
            plugin_type: 'T',
            plugin_position: 1,
        });
        const cmsPath = new URL(url, 'http://x').searchParams.get('cms_path');
        expect(cmsPath).toBeTruthy();
    });
});

describe('requestCopyPlugin', () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        fetchMock = vi.fn();
        vi.stubGlobal('fetch', fetchMock);
        window.CMS = {
            config: {
                csrf: 'tok',
                request: { language: 'en' },
                clipboard: { id: 99 },
            },
        } as CmsGlobal;
    });

    afterEach(() => {
        vi.unstubAllGlobals();
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('builds the same-language copy payload (defaults target to clipboard)', async () => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ ok: 1 }));
        const result = await requestCopyPlugin({
            placeholder_id: 5,
            plugin_id: 17,
            urls: { copy_plugin: '/admin/copy/' },
        });
        expect(result.copyingFromLanguage).toBe(false);
        const body = readFormBody(fetchMock.mock.calls[0]![1]);
        expect(body.get('source_placeholder_id')).toBe('5');
        expect(body.get('source_plugin_id')).toBe('17');
        expect(body.get('source_language')).toBe('en');
        expect(body.get('target_plugin_id')).toBe(''); // no parent
        expect(body.get('target_placeholder_id')).toBe('99'); // clipboard fallback
        expect(body.get('target_language')).toBe('en');
    });

    it('cross-language copy: rewrites target to the source placeholder, clears plugin/parent', async () => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ ok: 1 }));
        const result = await requestCopyPlugin(
            {
                placeholder_id: 5,
                plugin_id: 17,
                parent: 4,
                urls: { copy_plugin: '/admin/copy/' },
            },
            'de',
        );
        expect(result.copyingFromLanguage).toBe(true);
        const body = readFormBody(fetchMock.mock.calls[0]![1]);
        expect(body.get('source_placeholder_id')).toBe('5');
        expect(body.get('source_plugin_id')).toBe('');
        expect(body.get('source_language')).toBe('de');
        expect(body.get('target_plugin_id')).toBe('');
        expect(body.get('target_placeholder_id')).toBe('5'); // == source placeholder
        expect(body.get('target_language')).toBe('en');
    });

    it('uses the given target placeholder when set', async () => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ ok: 1 }));
        await requestCopyPlugin({
            placeholder_id: 5,
            plugin_id: 17,
            target: 42,
            urls: { copy_plugin: '/admin/copy/' },
        });
        const body = readFormBody(fetchMock.mock.calls[0]![1]);
        expect(body.get('target_placeholder_id')).toBe('42');
    });

    it('throws when copy_plugin URL is missing', async () => {
        await expect(
            requestCopyPlugin({ placeholder_id: 1, plugin_id: 1, urls: {} }),
        ).rejects.toThrow(/copy_plugin/);
    });

    it('returns the parsed response from the server', async () => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ status: 'ok', new_id: 7 }));
        const result = await requestCopyPlugin({
            placeholder_id: 1,
            plugin_id: 1,
            urls: { copy_plugin: '/admin/copy/' },
        });
        expect(result.response).toEqual({ status: 'ok', new_id: 7 });
    });
});

describe('requestCutPlugin', () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        fetchMock = vi.fn();
        vi.stubGlobal('fetch', fetchMock);
        window.CMS = {
            config: {
                csrf: 'tok',
                request: { language: 'en' },
                clipboard: { id: 99 },
            },
        } as CmsGlobal;
    });

    afterEach(() => {
        vi.unstubAllGlobals();
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('moves the plugin to the clipboard placeholder', async () => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ ok: 1 }));
        await requestCutPlugin({
            plugin_id: 17,
            urls: { move_plugin: '/admin/move/' },
        });
        const body = readFormBody(fetchMock.mock.calls[0]![1]);
        expect(body.get('placeholder_id')).toBe('99'); // clipboard
        expect(body.get('plugin_id')).toBe('17');
        expect(body.get('plugin_parent')).toBe('');
        expect(body.get('target_language')).toBe('en');
    });
});

describe('requestMovePlugin', () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        fetchMock = vi.fn();
        vi.stubGlobal('fetch', fetchMock);
        window.CMS = {
            config: { csrf: 'tok', request: { language: 'fr' } },
        } as CmsGlobal;
    });

    afterEach(() => {
        vi.unstubAllGlobals();
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('omits placeholder_id when not crossing placeholders', async () => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ ok: 1 }));
        await requestMovePlugin({
            plugin_id: 5,
            target_position: 3,
            urls: { move_plugin: '/admin/move/' },
        });
        const body = readFormBody(fetchMock.mock.calls[0]![1]);
        expect(body.has('placeholder_id')).toBe(false);
        expect(body.get('plugin_id')).toBe('5');
        expect(body.get('target_position')).toBe('3');
        expect(body.get('plugin_parent')).toBe('');
        expect(body.get('move_a_copy')).toBe('');
    });

    it('includes placeholder_id when crossing placeholders', async () => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ ok: 1 }));
        await requestMovePlugin({
            plugin_id: 5,
            placeholder_id: 42,
            target_position: 1,
            urls: { move_plugin: '/admin/move/' },
        });
        const body = readFormBody(fetchMock.mock.calls[0]![1]);
        expect(body.get('placeholder_id')).toBe('42');
    });

    it('serialises move_a_copy as "true" when set', async () => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ ok: 1 }));
        await requestMovePlugin({
            plugin_id: 5,
            move_a_copy: true,
            target_position: 1,
            urls: { move_plugin: '/admin/move/' },
        });
        const body = readFormBody(fetchMock.mock.calls[0]![1]);
        expect(body.get('move_a_copy')).toBe('true');
    });

    it('serialises plugin_parent as "" when null/undefined', async () => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ ok: 1 }));
        await requestMovePlugin({
            plugin_id: 5,
            plugin_parent: null,
            target_position: 1,
            urls: { move_plugin: '/admin/move/' },
        });
        const body = readFormBody(fetchMock.mock.calls[0]![1]);
        expect(body.get('plugin_parent')).toBe('');
    });

    it('serialises plugin_parent when set', async () => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ ok: 1 }));
        await requestMovePlugin({
            plugin_id: 5,
            plugin_parent: 99,
            target_position: 1,
            urls: { move_plugin: '/admin/move/' },
        });
        const body = readFormBody(fetchMock.mock.calls[0]![1]);
        expect(body.get('plugin_parent')).toBe('99');
    });

    it('uses CMS.config.request.language for target_language', async () => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ ok: 1 }));
        await requestMovePlugin({
            plugin_id: 5,
            target_position: 1,
            urls: { move_plugin: '/admin/move/' },
        });
        const body = readFormBody(fetchMock.mock.calls[0]![1]);
        expect(body.get('target_language')).toBe('fr');
    });
});
