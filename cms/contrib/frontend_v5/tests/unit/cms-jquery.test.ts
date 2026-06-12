import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    _resetCmsJqueryCache,
    getCmsJquery,
    loadCmsJquery,
} from '../../frontend/modules/core/cms-jquery';

/*
 * The lazy-load path uses a dynamic `import('jquery')`. Mock it here
 * so the unit tests don't pull the real ~85 KB jQuery into the test
 * environment, and so we can assert specific resolver behaviours
 * (memoisation, noConflict invocation, error handling).
 */
const noConflictSpy = vi.fn();
const lazyJq = { __source: 'lazy', noConflict: noConflictSpy } as unknown as JQueryStatic;

vi.mock('jquery', () => ({
    default: lazyJq,
}));

describe('getCmsJquery / loadCmsJquery', () => {
    type WindowWithJq = Window & {
        jQuery?: JQueryStatic;
        django?: { jQuery?: JQueryStatic };
    };
    const w = window as WindowWithJq;

    const fakeDjangoJq = { __source: 'django' } as unknown as JQueryStatic;

    let warnSpy: ReturnType<typeof vi.spyOn>;

    beforeEach(() => {
        _resetCmsJqueryCache();
        delete w.django;
        delete w.jQuery;
        noConflictSpy.mockClear();
        warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    });

    afterEach(() => {
        _resetCmsJqueryCache();
        delete w.django;
        delete w.jQuery;
        warnSpy.mockRestore();
    });

    describe('sync getCmsJquery', () => {
        it('returns undefined when nothing is resolved yet', () => {
            expect(getCmsJquery()).toBeUndefined();
        });

        it('resolves django.jQuery on first sync call', () => {
            w.django = { jQuery: fakeDjangoJq };
            expect(getCmsJquery()).toBe(fakeDjangoJq);
        });

        it('does NOT read window.jQuery (strategy forbids it)', () => {
            // Even with window.jQuery set, the resolver must ignore it.
            w.jQuery = { __source: 'forbidden' } as unknown as JQueryStatic;
            expect(getCmsJquery()).toBeUndefined();
        });

        it('memoises the resolved django instance', () => {
            w.django = { jQuery: fakeDjangoJq };
            expect(getCmsJquery()).toBe(fakeDjangoJq);
            // Even if django.jQuery disappears, the cached value sticks.
            delete w.django;
            expect(getCmsJquery()).toBe(fakeDjangoJq);
        });
    });

    describe('async loadCmsJquery', () => {
        it('uses django.jQuery when present (no lazy import)', async () => {
            w.django = { jQuery: fakeDjangoJq };
            const $ = await loadCmsJquery();
            expect($).toBe(fakeDjangoJq);
            // The lazy module's noConflict must NOT have been called —
            // we never loaded it.
            expect(noConflictSpy).not.toHaveBeenCalled();
            // No warning when django.jQuery is the source — that's the
            // expected fast path.
            expect(warnSpy).not.toHaveBeenCalled();
        });

        it('lazy-imports the bundled jquery when django is missing', async () => {
            const $ = await loadCmsJquery();
            expect($).toBe(lazyJq);
            // After lazy load, the sync accessor returns the same.
            expect(getCmsJquery()).toBe(lazyJq);
        });

        it('calls noConflict(true) on the lazy-loaded jquery', async () => {
            await loadCmsJquery();
            expect(noConflictSpy).toHaveBeenCalledTimes(1);
            expect(noConflictSpy).toHaveBeenCalledWith(true);
        });

        it('logs a console.warn when the lazy chunk loads', async () => {
            await loadCmsJquery();
            expect(warnSpy).toHaveBeenCalledTimes(1);
            const message = warnSpy.mock.calls[0]?.[0];
            expect(message).toMatch(/cms-jquery/);
            expect(message).toMatch(/lazy-loaded/);
        });

        it('logs the warning only once across concurrent + repeat calls', async () => {
            await Promise.all([loadCmsJquery(), loadCmsJquery()]);
            await loadCmsJquery();
            expect(warnSpy).toHaveBeenCalledTimes(1);
        });

        it('shares a single in-flight promise across concurrent callers', async () => {
            const a = loadCmsJquery();
            const b = loadCmsJquery();
            // Same promise object — concurrent callers don't trigger
            // a second dynamic import.
            expect(a).toBe(b);
            const [$a, $b] = await Promise.all([a, b]);
            expect($a).toBe(lazyJq);
            expect($b).toBe(lazyJq);
            // noConflict only fires once for the cached instance.
            expect(noConflictSpy).toHaveBeenCalledTimes(1);
        });

        it('resolves to the cached instance on later calls', async () => {
            const first = await loadCmsJquery();
            const second = await loadCmsJquery();
            expect(first).toBe(second);
            expect(noConflictSpy).toHaveBeenCalledTimes(1);
        });

        it('does NOT touch window.jQuery / window.$ when lazy-loading', async () => {
            await loadCmsJquery();
            expect(w.jQuery).toBeUndefined();
            expect((w as { $?: unknown }).$).toBeUndefined();
        });
    });

    describe('cache reset', () => {
        it('_resetCmsJqueryCache forces re-resolution', async () => {
            w.django = { jQuery: fakeDjangoJq };
            expect(await loadCmsJquery()).toBe(fakeDjangoJq);
            delete w.django;
            _resetCmsJqueryCache();
            // Now django is gone, so loadCmsJquery falls through to
            // the lazy import.
            expect(await loadCmsJquery()).toBe(lazyJq);
        });
    });
});
