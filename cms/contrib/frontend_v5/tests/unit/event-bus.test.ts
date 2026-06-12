import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { _resetEventBusForTest, cmsEvents } from '../../frontend/modules/core/event-bus';

describe('cmsEvents — native dispatch', () => {
    afterEach(() => {
        _resetEventBusForTest();
        delete (window as { jQuery?: unknown }).jQuery;
        if (window.CMS) delete window.CMS._eventRoot;
    });

    it('delivers detail to subscribers', () => {
        const seen: number[] = [];
        cmsEvents.on<number>('cms-test', (n) => seen.push(n));
        cmsEvents.emit('cms-test', 1);
        cmsEvents.emit('cms-test', 2);
        expect(seen).toEqual([1, 2]);
    });

    it('supports multiple subscribers on the same type', () => {
        const a: number[] = [];
        const b: number[] = [];
        cmsEvents.on<number>('cms-test', (n) => a.push(n));
        cmsEvents.on<number>('cms-test', (n) => b.push(n));
        cmsEvents.emit('cms-test', 7);
        expect(a).toEqual([7]);
        expect(b).toEqual([7]);
    });

    it('does not deliver to subscribers of other types', () => {
        const seen: string[] = [];
        cmsEvents.on<string>('cms-test', (s) => seen.push(s));
        cmsEvents.emit('cms-other', 'hello');
        expect(seen).toEqual([]);
    });

    it('returns an unsubscribe function', () => {
        const seen: number[] = [];
        const off = cmsEvents.on<number>('cms-test', (n) => seen.push(n));
        cmsEvents.emit('cms-test', 1);
        off();
        cmsEvents.emit('cms-test', 2);
        expect(seen).toEqual([1]);
    });

    it('unsubscribe is idempotent', () => {
        const off = cmsEvents.on('cms-test', () => undefined);
        expect(() => {
            off();
            off();
        }).not.toThrow();
    });

    it('handles missing detail (CustomEvent normalises to null per spec)', () => {
        let called = false;
        let receivedDetail: unknown = 'untouched';
        cmsEvents.on('cms-ping', (d) => {
            called = true;
            receivedDetail = d;
        });
        cmsEvents.emit('cms-ping');
        expect(called).toBe(true);
        // CustomEvent.detail defaults to null when not provided.
        expect(receivedDetail).toBeNull();
    });
});

describe('cmsEvents — jQuery bridge', () => {
    /*
     * Verifies the bidirectional bridge works when jQuery and
     * CMS._eventRoot are present, and that loops are prevented.
     */
    type Handler = (...args: unknown[]) => void;

    interface FakeJqRoot {
        handlers: Map<string, Set<Handler>>;
        on(type: string, h: Handler): void;
        trigger(type: string, args: unknown[]): void;
    }

    function installFakeJquery(): { root: FakeJqRoot; triggerSpy: ReturnType<typeof vi.fn> } {
        const root: FakeJqRoot = {
            handlers: new Map(),
            on(type: string, h: Handler) {
                let set = this.handlers.get(type);
                if (!set) this.handlers.set(type, (set = new Set()));
                set.add(h);
            },
            trigger(type: string, args: unknown[]) {
                this.handlers.get(type)?.forEach((h) => h({ type }, ...args));
            },
        };

        const triggerSpy = vi.fn((type: string, args: unknown[]) => root.trigger(type, args));
        const fake = ((target: unknown) => {
            // Always return a wrapper bound to our single fake root,
            // regardless of the argument — tests don't care which DOM
            // node legacy code passes here.
            void target;
            return {
                on: (type: string, h: Handler) => root.on(type, h),
                trigger: (type: string, args: unknown[]) => triggerSpy(type, args),
            };
        }) as unknown as JQueryStatic;

        (window as { jQuery?: unknown }).jQuery = fake;
        if (!window.CMS) window.CMS = {};
        window.CMS._eventRoot = {};
        return { root, triggerSpy };
    }

    beforeEach(() => {
        _resetEventBusForTest();
    });

    afterEach(() => {
        _resetEventBusForTest();
        delete (window as { jQuery?: unknown }).jQuery;
        if (window.CMS) delete window.CMS._eventRoot;
    });

    it('mirrors native emit → jQuery .trigger when jQuery is present', () => {
        const { triggerSpy } = installFakeJquery();
        cmsEvents.emit('cms-content-refresh', { foo: 1 });
        expect(triggerSpy).toHaveBeenCalledWith('cms-content-refresh', [{ foo: 1 }]);
    });

    it('does not mirror to jQuery when no event root is set', () => {
        const triggerSpy = vi.fn();
        const fake = ((_t: unknown) => ({ on: () => undefined, trigger: triggerSpy })) as unknown as JQueryStatic;
        (window as { jQuery?: unknown }).jQuery = fake;
        // No CMS._eventRoot.
        cmsEvents.emit('cms-test', 1);
        expect(triggerSpy).not.toHaveBeenCalled();
    });

    it('mirrors jQuery .trigger → native dispatch when subscribed first', () => {
        const { root } = installFakeJquery();
        const seen: unknown[] = [];
        cmsEvents.on('cms-from-legacy', (d) => seen.push(d));
        // Simulate legacy code firing on the jQuery bus.
        root.trigger('cms-from-legacy', [{ source: 'legacy' }]);
        expect(seen).toEqual([{ source: 'legacy' }]);
    });

    it('does not loop: native emit fires jQuery once and not back to native', () => {
        installFakeJquery();
        const seen: unknown[] = [];
        cmsEvents.on('cms-loop', (d) => seen.push(d));
        cmsEvents.emit('cms-loop', 'A');
        // Native subscriber should fire exactly once even though the
        // jQuery mirror would otherwise round-trip back into native.
        expect(seen).toEqual(['A']);
    });

    it('does not loop: jQuery trigger fires native once and not back to jQuery', () => {
        const { root, triggerSpy } = installFakeJquery();
        const seen: unknown[] = [];
        cmsEvents.on('cms-loop', (d) => seen.push(d));
        // Reset the spy so we only count what happens after this point.
        triggerSpy.mockClear();
        root.trigger('cms-loop', ['legacy']);
        expect(seen).toEqual(['legacy']);
        // Native dispatch should NOT have re-triggered the jQuery bus.
        expect(triggerSpy).not.toHaveBeenCalled();
    });

    it('survives a broken jQuery without throwing', () => {
        // Pass a jQuery whose `.trigger` throws — emit must not bubble.
        const fake = ((_t: unknown) => ({
            on: () => undefined,
            trigger: () => {
                throw new Error('bad jq');
            },
        })) as unknown as JQueryStatic;
        (window as { jQuery?: unknown }).jQuery = fake;
        if (!window.CMS) window.CMS = {};
        window.CMS._eventRoot = {};
        const seen: unknown[] = [];
        cmsEvents.on('cms-test', (d) => seen.push(d));
        expect(() => cmsEvents.emit('cms-test', 1)).not.toThrow();
        // Native side still got it.
        expect(seen).toEqual([1]);
    });
});
