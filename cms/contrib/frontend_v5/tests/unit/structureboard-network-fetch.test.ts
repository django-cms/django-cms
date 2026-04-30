import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    _resetCacheForTest,
    invalidateModeCache,
    loadToolbar,
    requestMode,
} from '../../frontend/modules/structureboard/network/fetch';

interface CmsTestable {
    config?: Record<string, unknown>;
    settings?: Record<string, unknown>;
    _instances?: unknown[];
    _plugins?: unknown[];
}

function setupCms(extras: Record<string, unknown> = {}): void {
    (window as unknown as { CMS: CmsTestable }).CMS = {
        config: {
            settings: {
                structure: '/cms/structure/',
                edit: '/cms/edit/',
            },
            request: {
                toolbar: '/cms/toolbar/',
                pk: 42,
                model: 'cms.page',
                language: 'en',
            },
            ...((extras.config as Record<string, unknown>) ?? {}),
        },
        settings: {},
        _instances: [],
        _plugins: [],
        ...extras,
    };
}

describe('network/fetch — requestMode', () => {
    beforeEach(() => {
        setupCms();
        _resetCacheForTest();
    });
    afterEach(() => {
        _resetCacheForTest();
        delete (window as { CMS?: unknown }).CMS;
        vi.restoreAllMocks();
    });

    it('GETs the structure URL and returns markup', async () => {
        const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(
            new Response('<html>structure</html>', { status: 200 }),
        );
        const markup = await requestMode('structure');
        expect(markup).toBe('<html>structure</html>');
        expect(fetchSpy).toHaveBeenCalledWith(
            '/cms/structure/',
            expect.objectContaining({ method: 'GET', credentials: 'same-origin' }),
        );
    });

    it('GETs the content URL when mode=content', async () => {
        const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(
            new Response('<html>content</html>', { status: 200 }),
        );
        await requestMode('content');
        expect(fetchSpy.mock.calls[0]?.[0]).toBe('/cms/edit/');
    });

    it('memoises concurrent calls — single fetch for parallel requests', async () => {
        const fetchSpy = vi.spyOn(global, 'fetch').mockImplementation(() =>
            Promise.resolve(new Response('html', { status: 200 })),
        );
        const [a, b] = await Promise.all([
            requestMode('structure'),
            requestMode('structure'),
        ]);
        expect(a).toBe(b);
        expect(fetchSpy).toHaveBeenCalledOnce();
    });

    it('re-fetches when force: true is passed', async () => {
        const fetchSpy = vi.spyOn(global, 'fetch').mockImplementation(() =>
            Promise.resolve(new Response('html', { status: 200 })),
        );
        await requestMode('structure');
        await requestMode('structure', { force: true });
        expect(fetchSpy).toHaveBeenCalledTimes(2);
    });

    it('invalidateModeCache clears a single mode', async () => {
        const fetchSpy = vi.spyOn(global, 'fetch').mockImplementation(() =>
            Promise.resolve(new Response('html', { status: 200 })),
        );
        await requestMode('structure');
        invalidateModeCache('structure');
        await requestMode('structure');
        expect(fetchSpy).toHaveBeenCalledTimes(2);
    });

    it('rejects when CMS.config.settings.structure is missing', async () => {
        setupCms({ config: { settings: {} } });
        _resetCacheForTest();
        await expect(requestMode('structure')).rejects.toThrow(
            /missing CMS.config.settings.structure URL/,
        );
    });

    it('rejects on non-2xx response', async () => {
        vi.spyOn(global, 'fetch').mockResolvedValue(
            new Response('Not found', { status: 404, statusText: 'Not Found' }),
        );
        await expect(requestMode('structure')).rejects.toThrow(/404 Not Found/);
    });
});

describe('network/fetch — loadToolbar', () => {
    beforeEach(() => {
        setupCms();
        _resetCacheForTest();
    });
    afterEach(() => {
        _resetCacheForTest();
        delete (window as { CMS?: unknown }).CMS;
        vi.restoreAllMocks();
    });

    it('builds query string from CMS._plugins placeholder ids + obj_id/obj_type/language', async () => {
        // Drop in a plugin descriptor list with two placeholders.
        const cms = (window as unknown as { CMS: CmsTestable }).CMS;
        cms._plugins = [
            ['cms-placeholder-7', { type: 'placeholder', placeholder_id: 7 }],
            ['cms-placeholder-9', { type: 'placeholder', placeholder_id: 9 }],
            ['cms-plugin-3', { type: 'plugin', plugin_id: 3 }],
        ];
        const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(
            new Response('<div>toolbar</div>', { status: 200 }),
        );
        const html = await loadToolbar();
        expect(html).toBe('<div>toolbar</div>');
        const url = fetchSpy.mock.calls[0]?.[0] as string;
        expect(url).toContain('/cms/toolbar/');
        expect(url).toContain('placeholders%5B%5D=7');
        expect(url).toContain('placeholders%5B%5D=9');
        expect(url).toContain('obj_id=42');
        expect(url).toContain('obj_type=cms.page');
        expect(url).toContain('language=en');
    });

    it('rejects when CMS.config.request.toolbar is missing', async () => {
        setupCms({ config: { request: {} } });
        _resetCacheForTest();
        await expect(loadToolbar()).rejects.toThrow(
            /missing CMS.config.request.toolbar URL/,
        );
    });
});
