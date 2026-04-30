import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Tooltip } from '../../frontend/modules/tooltip';

const liveTooltips: Tooltip[] = [];
function track(t: Tooltip): Tooltip {
    liveTooltips.push(t);
    return t;
}

function setupDom(): void {
    document.body.innerHTML = `
        <div class="cms-tooltip" style="display:none;visibility:hidden">
            <span></span>
        </div>
        <div class="cms-tooltip-touch" style="display:none;visibility:hidden">
            <span></span>
        </div>
        <div class="cms-plugin cms-plugin-7" id="plugin7"></div>
    `;
}

beforeEach(() => {
    setupDom();
});

afterEach(() => {
    while (liveTooltips.length > 0) liveTooltips.pop()!.destroy();
    document.body.innerHTML = '';
    vi.restoreAllMocks();
});

describe('Tooltip — construction', () => {
    it('picks .cms-tooltip in desktop mode and hides both candidates', () => {
        const t = track(new Tooltip());
        expect(t.isTouch).toBe(false);
        expect(t.domElem?.classList.contains('cms-tooltip')).toBe(true);
        const touchTooltip = document.querySelector<HTMLElement>(
            '.cms-tooltip-touch',
        )!;
        expect(touchTooltip.style.visibility).toBe('hidden');
    });

    it('flips to touch mode on the first touchstart', () => {
        const t = track(new Tooltip());
        document.body.dispatchEvent(new Event('touchstart'));
        expect(t.isTouch).toBe(true);
        expect(t.domElem?.classList.contains('cms-tooltip-touch')).toBe(true);
        t.destroy();
    });

    it('returns null domElem when no tooltip elements exist', () => {
        document.body.innerHTML = '';
        const t = track(new Tooltip());
        expect(t.domElem).toBeNull();
    });
});

describe('Tooltip — show()', () => {
    function makeMouseEvent(pageX: number, pageY: number): MouseEvent {
        const ev = new MouseEvent('mouseover', { bubbles: true });
        Object.defineProperty(ev, 'pageX', { value: pageX });
        Object.defineProperty(ev, 'pageY', { value: pageY });
        return ev;
    }

    it('makes the tooltip visible and writes the name into <span>', () => {
        const t = track(new Tooltip());
        t.show(makeMouseEvent(100, 100), 'My Plugin', 7);
        const tt = document.querySelector<HTMLElement>('.cms-tooltip')!;
        expect(tt.style.visibility).toBe('visible');
        expect(tt.classList.contains('cms-hidden')).toBe(false);
        expect(tt.querySelector('span')!.textContent).toBe('My Plugin');
        expect(tt.dataset.pluginId).toBe('7');
        t.destroy();
    });

    it('updates plugin id on subsequent shows', () => {
        const t = track(new Tooltip());
        t.show(makeMouseEvent(0, 0), 'A', 1);
        t.show(makeMouseEvent(0, 0), 'B', 2);
        const tt = document.querySelector<HTMLElement>('.cms-tooltip')!;
        expect(tt.dataset.pluginId).toBe('2');
        t.destroy();
    });

    it('clears plugin id when called without one', () => {
        const t = track(new Tooltip());
        t.show(makeMouseEvent(0, 0), 'A', 1);
        t.show(makeMouseEvent(0, 0), 'B');
        const tt = document.querySelector<HTMLElement>('.cms-tooltip')!;
        expect(tt.dataset.pluginId).toBeUndefined();
        t.destroy();
    });

    it('positions the tooltip relative to its offset parent', () => {
        const t = track(new Tooltip());
        t.show(makeMouseEvent(100, 100), 'P', 1);
        const tt = document.querySelector<HTMLElement>('.cms-tooltip')!;
        // jsdom doesn't compute offset/scroll, so we can only assert
        // the inline style was set.
        expect(tt.style.left).toMatch(/px$/);
        expect(tt.style.top).toMatch(/px$/);
        t.destroy();
    });

    it('rebinds mousemove on every show (no listener leak)', () => {
        const t = track(new Tooltip());
        t.show(makeMouseEvent(0, 0), 'A', 1);
        t.show(makeMouseEvent(0, 0), 'B', 2);
        // Now move — only the most recent listener should respond
        // (the position should update for B). Trivial smoke: no
        // exception.
        document.body.dispatchEvent(makeMouseEvent(50, 50));
        t.destroy();
    });

    it('does not bind mousemove in touch mode', () => {
        const t = track(new Tooltip());
        document.body.dispatchEvent(new Event('touchstart'));
        const spy = vi.spyOn(document.body, 'addEventListener');
        t.show(makeMouseEvent(0, 0), 'A', 1);
        const calls = spy.mock.calls.filter((c) => c[0] === 'mousemove');
        expect(calls.length).toBe(0);
        t.destroy();
    });
});

describe('Tooltip — hide()', () => {
    it('hides the active tooltip', () => {
        const t = track(new Tooltip());
        t.show(new MouseEvent('mouseover'), 'P', 1);
        t.hide();
        const tt = document.querySelector<HTMLElement>('.cms-tooltip')!;
        expect(tt.style.visibility).toBe('hidden');
        expect(tt.classList.contains('cms-hidden')).toBe(true);
    });

    it('detaches the mousemove listener', () => {
        const t = track(new Tooltip());
        const ev = new MouseEvent('mouseover');
        Object.defineProperty(ev, 'pageX', { value: 0 });
        Object.defineProperty(ev, 'pageY', { value: 0 });
        t.show(ev, 'P', 1);
        const tt = document.querySelector<HTMLElement>('.cms-tooltip')!;
        t.hide();
        // Style was cleared but moving the mouse should NOT re-show.
        document.body.dispatchEvent(new MouseEvent('mousemove'));
        expect(tt.style.visibility).toBe('hidden');
        t.destroy();
    });

    it('is safe to call when never shown', () => {
        const t = track(new Tooltip());
        expect(() => t.hide()).not.toThrow();
    });

    it('is safe to call with no domElem', () => {
        document.body.innerHTML = '';
        const t = track(new Tooltip());
        expect(() => t.hide()).not.toThrow();
    });
});

describe('Tooltip — displayToggle()', () => {
    it('show=true with event delegates to show()', () => {
        const t = track(new Tooltip());
        const ev = new MouseEvent('mouseover');
        Object.defineProperty(ev, 'pageX', { value: 10 });
        Object.defineProperty(ev, 'pageY', { value: 10 });
        t.displayToggle(true, ev, 'P', 1);
        const tt = document.querySelector<HTMLElement>('.cms-tooltip')!;
        expect(tt.style.visibility).toBe('visible');
        t.destroy();
    });

    it('show=false delegates to hide()', () => {
        const t = track(new Tooltip());
        const ev = new MouseEvent('mouseover');
        Object.defineProperty(ev, 'pageX', { value: 10 });
        Object.defineProperty(ev, 'pageY', { value: 10 });
        t.show(ev, 'P', 1);
        t.displayToggle(false);
        const tt = document.querySelector<HTMLElement>('.cms-tooltip')!;
        expect(tt.style.visibility).toBe('hidden');
        t.destroy();
    });

    it('show=true with no event is a no-op (defensive)', () => {
        const t = track(new Tooltip());
        expect(() => t.displayToggle(true)).not.toThrow();
        // Tooltip remains hidden
        const tt = document.querySelector<HTMLElement>('.cms-tooltip')!;
        expect(tt.style.visibility).toBe('hidden');
        t.destroy();
    });
});

describe('Tooltip — touch tap dispatches dblclick on matching plugin', () => {
    it('dispatches dblclick on .cms-plugin-<id> when tapped', () => {
        const t = track(new Tooltip());
        document.body.dispatchEvent(new Event('touchstart'));
        // Now in touch mode; tooltip is the touch one.
        const tooltipEl = t.domElem!;
        tooltipEl.dataset.pluginId = '7';
        const dblclick = vi.fn();
        document
            .getElementById('plugin7')!
            .addEventListener('dblclick', dblclick);
        tooltipEl.dispatchEvent(new Event('touchstart'));
        expect(dblclick).toHaveBeenCalledOnce();
        t.destroy();
    });

    it('falls back to a generic .cms-plugin-cms-X-<id> match', () => {
        document.body.innerHTML = `
            <div class="cms-tooltip"></div>
            <div class="cms-tooltip-touch"></div>
            <div class="cms-plugin cms-plugin-cms-page-changelist-42" id="generic42"></div>
        `;
        const t = track(new Tooltip());
        document.body.dispatchEvent(new Event('touchstart'));
        const tooltipEl = t.domElem!;
        tooltipEl.dataset.pluginId = '42';
        const dblclick = vi.fn();
        document
            .getElementById('generic42')!
            .addEventListener('dblclick', dblclick);
        tooltipEl.dispatchEvent(new Event('touchstart'));
        expect(dblclick).toHaveBeenCalledOnce();
        t.destroy();
    });

    it('no-ops when no plugin id is set', () => {
        const t = track(new Tooltip());
        document.body.dispatchEvent(new Event('touchstart'));
        // No throw, no dblclick anywhere.
        const dblclick = vi.fn();
        document
            .getElementById('plugin7')!
            .addEventListener('dblclick', dblclick);
        t.domElem!.dispatchEvent(new Event('touchstart'));
        expect(dblclick).not.toHaveBeenCalled();
        t.destroy();
    });
});
