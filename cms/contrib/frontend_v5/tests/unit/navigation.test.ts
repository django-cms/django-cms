import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Navigation } from '../../frontend/modules/navigation';

const liveNavs: Navigation[] = [];
function track(n: Navigation): Navigation {
    liveNavs.push(n);
    return n;
}

function setupDom(leftCount = 4, rightCount = 2): void {
    const leftItems = Array.from({ length: leftCount }, (_, i) =>
        `<li><a href="#" data-id="L${i}">L${i}</a><ul></ul></li>`,
    ).join('');
    const rightItems = Array.from({ length: rightCount }, (_, i) =>
        `<div class="cms-toolbar-item" data-id="R${i}">R${i}</div>`,
    ).join('');
    document.body.innerHTML = `
        <div class="cms">
            <div class="cms-toolbar-trigger"></div>
            <div class="cms-toolbar-item-logo" style="margin-left:0;margin-right:0;"></div>
            <div class="cms-toolbar-left">
                <ul class="cms-toolbar-item-navigation">
                    ${leftItems}
                    <li class="cms-toolbar-more">
                        <ul></ul>
                    </li>
                </ul>
            </div>
            <div class="cms-toolbar-right" style="padding-inline-end:0;">
                ${rightItems}
            </div>
        </div>
    `;
}

function stubItemWidth(el: HTMLElement, width: number): void {
    Object.defineProperty(el, 'getBoundingClientRect', {
        configurable: true,
        value: () => ({
            width,
            height: 30,
            top: 0,
            left: 0,
            right: width,
            bottom: 30,
            x: 0,
            y: 0,
            toJSON: () => ({}),
        }),
    });
}

function stubFloat(): void {
    // jsdom's getComputedStyle returns float as `none` by default;
    // override so handleResize's CSS-loaded probe passes.
    const original = window.getComputedStyle;
    window.getComputedStyle = ((el: Element, pseudo?: string | null) => {
        const cs = original.call(window, el as Element, pseudo);
        return new Proxy(cs, {
            get(target, prop) {
                if (prop === 'cssFloat') return 'left';
                if (prop === 'paddingInlineEnd') return '0px';
                if (prop === 'marginLeft') return '0px';
                if (prop === 'marginRight') return '0px';
                return Reflect.get(target, prop) as unknown;
            },
        });
    }) as typeof window.getComputedStyle;
}

beforeEach(() => {
    setupDom();
    stubFloat();
});

afterEach(() => {
    while (liveNavs.length > 0) liveNavs.pop()!.destroy();
    document.body.innerHTML = '';
    vi.restoreAllMocks();
});

describe('Navigation — construction', () => {
    it('initialises with empty items and no measured widths', () => {
        const n = track(new Navigation());
        expect(n.items.left).toEqual([]);
        expect(n.items.right).toEqual([]);
        expect(n.rightMostItemIndex).toBe(-1);
        expect(n.leftMostItemIndex).toBe(0);
    });

    it('finds toolbar-left and toolbar-right', () => {
        const n = track(new Navigation());
        expect(n.ui.toolbarLeftPart).not.toBeNull();
        expect(n.ui.toolbarRightPart).not.toBeNull();
        expect(n.ui.trigger).not.toBeNull();
    });
});

describe('Navigation — overflow handling', () => {
    it('shows all items when viewport is wide', () => {
        // Each left item 100px, right items 50px → total 4*100+2*50=500
        document
            .querySelectorAll<HTMLElement>(
                '.cms-toolbar-left .cms-toolbar-item-navigation > li:not(.cms-toolbar-more)',
            )
            .forEach((el) => stubItemWidth(el, 100));
        document
            .querySelectorAll<HTMLElement>(
                '.cms-toolbar-right > .cms-toolbar-item',
            )
            .forEach((el) => stubItemWidth(el, 50));
        stubItemWidth(
            document.querySelector('.cms-toolbar-more')!,
            40,
        );
        Object.defineProperty(window, 'innerWidth', {
            configurable: true,
            value: 1000,
        });
        const n = track(new Navigation());
        window.dispatchEvent(new Event('resize'));
        // Throttled — flush via timer.
        vi.useFakeTimers();
        vi.advanceTimersByTime(60);
        vi.useRealTimers();
        // Trigger should be hidden when everything fits.
        expect(
            n.ui.trigger?.classList.contains('cms-toolbar-more--visible'),
        ).toBe(false);
    });

    it('moves rightmost left items to dropdown when too narrow', () => {
        document
            .querySelectorAll<HTMLElement>(
                '.cms-toolbar-left .cms-toolbar-item-navigation > li:not(.cms-toolbar-more)',
            )
            .forEach((el) => stubItemWidth(el, 100));
        document
            .querySelectorAll<HTMLElement>(
                '.cms-toolbar-right > .cms-toolbar-item',
            )
            .forEach((el) => stubItemWidth(el, 50));
        stubItemWidth(
            document.querySelector('.cms-toolbar-more')!,
            40,
        );
        // Tight viewport: total left=400, right=100, more=40 → 540 doesn't fit in 300
        Object.defineProperty(window, 'innerWidth', {
            configurable: true,
            value: 300,
        });
        const n = track(new Navigation());
        // Manually call resize handler since throttle requires timers.
        // Force the lazy-measure pass.
        (n as unknown as { handleResize(): void }).handleResize();
        // At least one left item should have moved into the dropdown.
        const dropdown = document.querySelector<HTMLElement>(
            '.cms-toolbar-more > ul',
        )!;
        expect(dropdown.children.length).toBeGreaterThan(0);
        // Trigger should be visible.
        expect(
            n.ui.trigger?.classList.contains('cms-toolbar-more--visible'),
        ).toBe(true);
    });
});

describe('Navigation — destroy', () => {
    it('removes window listeners', () => {
        const n = track(new Navigation());
        const removeSpy = vi.spyOn(window, 'removeEventListener');
        n.destroy();
        // Should have removed at least resize/load/orientationchange.
        const events = removeSpy.mock.calls.map((c) => c[0]);
        expect(events).toContain('resize');
        expect(events).toContain('load');
        expect(events).toContain('orientationchange');
        // Avoid double-destroy in afterEach.
        liveNavs.length = 0;
    });
});
