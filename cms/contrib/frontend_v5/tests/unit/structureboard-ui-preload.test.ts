import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { setupOppositeModePreload } from '../../frontend/modules/structureboard/ui/preload';
import { _resetCacheForTest } from '../../frontend/modules/structureboard/network/fetch';

interface CmsTestable {
    config?: {
        settings?: {
            structure?: string;
            edit?: string;
            legacy_mode?: boolean;
        };
    };
}

function setupCms(extras: Partial<CmsTestable['config']> = {}): void {
    (window as unknown as { CMS: CmsTestable }).CMS = {
        config: {
            settings: {
                structure: '/cms/structure/',
                edit: '/cms/edit/',
            },
            ...extras,
        },
    };
}

beforeEach(() => {
    setupCms();
    _resetCacheForTest();
});

afterEach(() => {
    delete (window as { CMS?: unknown }).CMS;
    _resetCacheForTest();
    vi.useRealTimers();
    vi.restoreAllMocks();
});

describe('preload — setupOppositeModePreload', () => {
    it('returns a no-op handle when legacy_mode is on', () => {
        setupCms({ settings: { legacy_mode: true } });
        const handle = setupOppositeModePreload({
            isLoadedStructure: () => false,
        });
        expect(typeof handle.destroy).toBe('function');
        // Destroy should not throw
        handle.destroy();
    });

    it('preloads structure when content is currently loaded', async () => {
        vi.useFakeTimers();
        const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(
            new Response('html', { status: 200 }),
        );
        setupOppositeModePreload({
            isLoadedStructure: () => false,
            delayMs: 0,
        });
        window.dispatchEvent(new Event('load'));
        await vi.runAllTimersAsync();
        expect(fetchSpy).toHaveBeenCalledWith(
            '/cms/structure/',
            expect.any(Object),
        );
    });

    it('preloads content when structure is currently loaded', async () => {
        vi.useFakeTimers();
        const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(
            new Response('html', { status: 200 }),
        );
        setupOppositeModePreload({
            isLoadedStructure: () => true,
            delayMs: 0,
        });
        window.dispatchEvent(new Event('load'));
        await vi.runAllTimersAsync();
        expect(fetchSpy).toHaveBeenCalledWith('/cms/edit/', expect.any(Object));
    });

    it('uses the configured delay before fetching', async () => {
        vi.useFakeTimers();
        const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(
            new Response('html', { status: 200 }),
        );
        setupOppositeModePreload({
            isLoadedStructure: () => false,
            delayMs: 1500,
        });
        window.dispatchEvent(new Event('load'));
        await vi.advanceTimersByTimeAsync(1499);
        expect(fetchSpy).not.toHaveBeenCalled();
        await vi.advanceTimersByTimeAsync(1);
        expect(fetchSpy).toHaveBeenCalledOnce();
    });

    it('cancels a pending preload when destroy() is called', async () => {
        vi.useFakeTimers();
        const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(
            new Response('html', { status: 200 }),
        );
        const handle = setupOppositeModePreload({
            isLoadedStructure: () => false,
            delayMs: 100,
        });
        window.dispatchEvent(new Event('load'));
        handle.destroy();
        await vi.runAllTimersAsync();
        expect(fetchSpy).not.toHaveBeenCalled();
    });

    it('detaches the load listener on destroy() (no late triggers)', async () => {
        vi.useFakeTimers();
        const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(
            new Response('html', { status: 200 }),
        );
        const handle = setupOppositeModePreload({
            isLoadedStructure: () => false,
            delayMs: 0,
        });
        handle.destroy();
        window.dispatchEvent(new Event('load'));
        await vi.runAllTimersAsync();
        expect(fetchSpy).not.toHaveBeenCalled();
    });

    it('swallows preload errors (no unhandled rejections)', async () => {
        vi.useFakeTimers();
        vi.spyOn(global, 'fetch').mockRejectedValue(new Error('network'));
        setupOppositeModePreload({
            isLoadedStructure: () => false,
            delayMs: 0,
        });
        window.dispatchEvent(new Event('load'));
        await vi.runAllTimersAsync();
        // No assertion — completes without throwing
    });
});
