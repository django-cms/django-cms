import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    _resetForTest as _resetRefreshForTest,
    getContentLoaded,
    refreshContent,
    updateContent,
} from '../../frontend/modules/structureboard/refresh';
import {
    _resetCacheForTest,
    invalidateModeCache,
} from '../../frontend/modules/structureboard/network/fetch';
import { _resetForTest as _resetBodySwapForTest } from '../../frontend/modules/structureboard/dom/body-swap';

interface CmsTestable {
    config?: Record<string, unknown>;
    settings?: Record<string, unknown>;
    _instances?: unknown[];
    _plugins?: unknown[];
    API?: {
        Toolbar?: { _refreshMarkup?: ReturnType<typeof vi.fn> };
        Messages?: { open?: ReturnType<typeof vi.fn>; close?: ReturnType<typeof vi.fn> };
    };
}

function setupCms(extras: Partial<CmsTestable['API']> = {}): void {
    (window as unknown as { CMS: CmsTestable }).CMS = {
        config: {
            settings: {
                structure: '/cms/structure/',
                edit: '/cms/edit/',
            },
        },
        settings: {},
        _instances: [],
        _plugins: [],
        API: {
            Toolbar: { _refreshMarkup: vi.fn() },
            Messages: { open: vi.fn(), close: vi.fn() },
            ...extras,
        },
    };
}

beforeEach(() => {
    document.body.innerHTML = '';
    document.head.innerHTML = '';
    setupCms();
    _resetRefreshForTest();
    _resetCacheForTest();
    _resetBodySwapForTest();
});

afterEach(() => {
    document.body.innerHTML = '';
    document.head.innerHTML = '';
    delete (window as { CMS?: unknown }).CMS;
    _resetRefreshForTest();
    _resetCacheForTest();
    _resetBodySwapForTest();
    vi.useRealTimers();
    vi.restoreAllMocks();
});

// ────────────────────────────────────────────────────────────────────
// refreshContent
// ────────────────────────────────────────────────────────────────────

describe('refresh — refreshContent', () => {
    it('replaces document.body with the new doc body', () => {
        document.body.innerHTML = '<p>before</p>';
        refreshContent('<html><body><p>after</p></body></html>');
        expect(document.body.innerHTML).toContain('after');
        expect(document.body.innerHTML).not.toContain('before');
    });

    it('preserves the live toolbar wrapper across the body swap', () => {
        document.body.innerHTML = `
            <div id="cms-top">live toolbar</div>
            <p>page content</p>
        `;
        const liveToolbar = document.getElementById('cms-top')!;
        // Attach a property that can't survive innerHTML round-trip
        (liveToolbar as HTMLElement & { _live?: boolean })._live = true;

        refreshContent(`
            <html>
                <body>
                    <div id="cms-top">stale toolbar</div>
                    <p>new content</p>
                </body>
            </html>
        `);

        const after = document.getElementById('cms-top')!;
        // Same DOM node — live property still attached
        expect((after as HTMLElement & { _live?: boolean })._live).toBe(true);
    });

    it('strips toolbar markup from the new doc (no duplicate toolbars)', () => {
        document.body.innerHTML = `
            <div id="cms-top">live</div>
            <p>old</p>
        `;
        refreshContent(`
            <html><body>
                <div id="cms-top">stale</div>
                <p>new</p>
            </body></html>
        `);
        // Only one #cms-top (the live one preserved)
        expect(document.querySelectorAll('#cms-top').length).toBe(1);
        expect(document.getElementById('cms-top')!.textContent).toContain('live');
    });

    it('calls Toolbar._refreshMarkup with the new toolbar markup', () => {
        const refresh = vi.fn();
        setupCms({ Toolbar: { _refreshMarkup: refresh } });
        refreshContent(`
            <html><body>
                <div class="cms-toolbar">fresh toolbar</div>
            </body></html>
        `);
        expect(refresh).toHaveBeenCalledOnce();
        const arg = refresh.mock.calls[0]![0];
        expect((arg as Element).classList.contains('cms-toolbar')).toBe(true);
    });

    it('opens server messages from the new doc on a microtask', () => {
        vi.useFakeTimers();
        const open = vi.fn();
        setupCms({ Messages: { open, close: vi.fn() } });
        refreshContent(`
            <html><body>
                <ul class="messagelist">
                    <li>welcome</li>
                </ul>
                <p>x</p>
            </body></html>
        `);
        expect(open).not.toHaveBeenCalled(); // deferred
        vi.runAllTimers();
        expect(open).toHaveBeenCalledOnce();
        expect(open.mock.calls[0]![0].message).toBe('welcome');
    });

    it('sets contentLoaded = true after a successful refresh', () => {
        expect(getContentLoaded()).toBe(false);
        refreshContent('<html><body><p>x</p></body></html>');
        expect(getContentLoaded()).toBe(true);
    });

    it('restores .cms-structure-content scrollTop across the swap', () => {
        document.body.innerHTML = `
            <div class="cms-structure-content" style="height:100px;overflow:auto" id="sc">
                <div style="height:1000px"></div>
            </div>
            <p>x</p>
        `;
        const scroller = document.getElementById('sc')!;
        // jsdom doesn't actually do layout, but it does record scrollTop writes
        scroller.scrollTop = 250;
        refreshContent(`
            <html><body>
                <div class="cms-structure-content" id="sc"><div></div></div>
                <p>new</p>
            </body></html>
        `);
        const after = document.getElementById('sc')!;
        expect(after.scrollTop).toBe(250);
    });

    it('applies head changes (DiffDOM) — adds new <link> tags', () => {
        document.head.innerHTML = '<title>old</title>';
        refreshContent(`
            <html>
                <head>
                    <title>new</title>
                    <link rel="stylesheet" href="/fresh.css">
                </head>
                <body><p>x</p></body>
            </html>
        `);
        // After diff apply, head should reflect new tags
        expect(document.head.querySelector('link[href="/fresh.css"]')).not.toBeNull();
    });
});

// ────────────────────────────────────────────────────────────────────
// updateContent
// ────────────────────────────────────────────────────────────────────

describe('refresh — updateContent', () => {
    it('GETs content mode markup and applies it', async () => {
        const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(
            new Response(
                '<html><body><p>fetched</p></body></html>',
                { status: 200 },
            ),
        );
        await updateContent();
        expect(fetchSpy).toHaveBeenCalledWith(
            '/cms/edit/',
            expect.objectContaining({ method: 'GET' }),
        );
        expect(document.body.innerHTML).toContain('fetched');
    });

    it('bypasses the per-mode memo cache (force fresh fetch)', async () => {
        const fetchSpy = vi.spyOn(global, 'fetch').mockImplementation(() =>
            Promise.resolve(new Response('html', { status: 200 })),
        );
        await updateContent();
        await updateContent();
        // Both calls fetch (cache invalidated each time)
        expect(fetchSpy).toHaveBeenCalledTimes(2);
    });

    it('propagates fetch errors so the caller can fallback to reload', async () => {
        vi.spyOn(global, 'fetch').mockResolvedValue(
            new Response('boom', { status: 500, statusText: 'Internal Error' }),
        );
        await expect(updateContent()).rejects.toThrow();
    });

    it('does not double-set contentLoaded if previously set', async () => {
        // Fresh Response per call so the body isn't reused.
        vi.spyOn(global, 'fetch').mockImplementation(() =>
            Promise.resolve(
                new Response('<html><body></body></html>', { status: 200 }),
            ),
        );
        await updateContent();
        expect(getContentLoaded()).toBe(true);
        await updateContent();
        expect(getContentLoaded()).toBe(true);
    });

    it('cooperates with invalidateModeCache (caller can pre-clear)', async () => {
        const fetchSpy = vi.spyOn(global, 'fetch').mockImplementation(() =>
            Promise.resolve(new Response('html', { status: 200 })),
        );
        invalidateModeCache('content');
        await updateContent();
        expect(fetchSpy).toHaveBeenCalled();
    });
});
