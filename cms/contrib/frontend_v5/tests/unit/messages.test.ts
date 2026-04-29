import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Messages } from '../../frontend/modules/messages';

interface CmsTestable {
    settings?: { toolbar?: string };
}

function setupCmsToolbar(toolbar?: 'collapsed'): void {
    (window as unknown as { CMS: CmsTestable }).CMS = toolbar
        ? { settings: { toolbar } }
        : {};
}

function setupDom(): void {
    document.body.innerHTML = `
        <div class="cms">
            <div class="cms-toolbar" style="height: 40px"></div>
            <div class="cms-messages" style="display: none">
                <div class="cms-messages-inner"></div>
                <div class="cms-messages-close"></div>
            </div>
        </div>
    `;
}

beforeEach(() => {
    setupDom();
    setupCmsToolbar();
});

afterEach(() => {
    document.body.innerHTML = '';
    delete (window as { CMS?: unknown }).CMS;
    vi.useRealTimers();
});

describe('Messages — open()', () => {
    it('throws when message is missing', () => {
        const m = new Messages();
        expect(() =>
            m.open(undefined as unknown as Parameters<Messages['open']>[0]),
        ).toThrow(/arguments passed to "open" were invalid/);
    });

    it('writes message HTML into .cms-messages-inner', () => {
        const m = new Messages();
        m.open({ message: '<p>Hello</p>' });
        const inner = document.querySelector('.cms-messages-inner')!;
        expect(inner.innerHTML).toBe('<p>Hello</p>');
    });

    it('shows the messages element (display unset)', () => {
        const m = new Messages();
        m.open({ message: 'hi' });
        const el = document.querySelector<HTMLElement>('.cms-messages')!;
        expect(el.style.display).not.toBe('none');
    });

    it('toggles cms-messages-error class based on the error flag', () => {
        const m = new Messages();
        m.open({ message: 'oops', error: true });
        const el = document.querySelector('.cms-messages')!;
        expect(el.classList.contains('cms-messages-error')).toBe(true);
        m.open({ message: 'ok' });
        expect(el.classList.contains('cms-messages-error')).toBe(false);
    });

    it('default (center) anchors at 50% with negative margin-left', () => {
        const m = new Messages();
        m.open({ message: 'centered' });
        const el = document.querySelector<HTMLElement>('.cms-messages')!;
        expect(el.style.left).toBe('50%');
        expect(el.style.marginLeft).toBe('-160px');
    });

    it('left direction slides in from the left edge', () => {
        const m = new Messages();
        m.open({ message: 'x', dir: 'left' });
        const el = document.querySelector<HTMLElement>('.cms-messages')!;
        // After the layout flush, left should be 0 (animation target).
        expect(el.style.left).toBe('0px');
        expect(el.style.right).toBe('auto');
    });

    it('right direction slides in from the right edge', () => {
        const m = new Messages();
        m.open({ message: 'x', dir: 'right' });
        const el = document.querySelector<HTMLElement>('.cms-messages')!;
        expect(el.style.right).toBe('0px');
        expect(el.style.left).toBe('auto');
    });

    it('delay > 0 schedules an auto-close', () => {
        vi.useFakeTimers();
        const m = new Messages();
        m.open({ message: 'fade', delay: 1000 });
        const el = document.querySelector<HTMLElement>('.cms-messages')!;
        expect(el.style.opacity).toBe('');
        vi.advanceTimersByTime(1000);
        expect(el.style.opacity).toBe('0');
    });

    it('delay = 0 disables auto-close and shows the close button', () => {
        vi.useFakeTimers();
        const m = new Messages();
        m.open({ message: 'sticky', delay: 0 });
        const closeBtn = document.querySelector<HTMLElement>(
            '.cms-messages-close',
        )!;
        expect(closeBtn.style.display).toBe('');
        // Run forward; nothing should auto-close.
        vi.advanceTimersByTime(10_000);
        const el = document.querySelector<HTMLElement>('.cms-messages')!;
        expect(el.style.opacity).toBe('');
    });

    it('long messages bypass auto-close and show the close button', () => {
        vi.useFakeTimers();
        const m = new Messages({ messageLength: 10 });
        m.open({ message: 'this message is too long' });
        const closeBtn = document.querySelector<HTMLElement>(
            '.cms-messages-close',
        )!;
        expect(closeBtn.style.display).toBe('');
        vi.advanceTimersByTime(10_000);
        const el = document.querySelector<HTMLElement>('.cms-messages')!;
        expect(el.style.opacity).toBe('');
    });

    it('uses top: 0 when toolbar is collapsed', () => {
        setupCmsToolbar('collapsed');
        const m = new Messages();
        m.open({ message: 'x' });
        const el = document.querySelector<HTMLElement>('.cms-messages')!;
        expect(el.style.top).toBe('0px');
    });

    it('clicking the close button closes the toast', () => {
        vi.useFakeTimers();
        const m = new Messages();
        m.open({ message: 'x', delay: 0 });
        const closeBtn = document.querySelector<HTMLElement>(
            '.cms-messages-close',
        )!;
        closeBtn.click();
        const el = document.querySelector<HTMLElement>('.cms-messages')!;
        expect(el.style.opacity).toBe('0');
    });

    it('open() after close() re-binds the close listener', () => {
        vi.useFakeTimers();
        const m = new Messages();
        m.open({ message: 'one', delay: 0 });
        m.close();
        m.open({ message: 'two', delay: 0 });
        const closeBtn = document.querySelector<HTMLElement>(
            '.cms-messages-close',
        )!;
        closeBtn.click();
        const el = document.querySelector<HTMLElement>('.cms-messages')!;
        expect(el.style.opacity).toBe('0');
    });

    it('successive opens reset the auto-close timer', () => {
        vi.useFakeTimers();
        const m = new Messages();
        m.open({ message: 'first', delay: 1000 });
        // Advance 500ms — timer would fire at 1000ms.
        vi.advanceTimersByTime(500);
        m.open({ message: 'second', delay: 2000 });
        // Advance another 500ms (total 1000ms from initial open). The
        // second open's timer hasn't fired yet (needs 2000ms from
        // its own start).
        vi.advanceTimersByTime(500);
        const el = document.querySelector<HTMLElement>('.cms-messages')!;
        expect(el.style.opacity).toBe('');
        // Now advance the rest of the second open's timer.
        vi.advanceTimersByTime(1500);
        expect(el.style.opacity).toBe('0');
    });
});

describe('Messages — close()', () => {
    it('hides the messages element after the duration elapses', () => {
        vi.useFakeTimers();
        const m = new Messages({ messageDuration: 100 });
        m.open({ message: 'x', delay: 0 });
        m.close();
        const el = document.querySelector<HTMLElement>('.cms-messages')!;
        expect(el.style.opacity).toBe('0');
        vi.advanceTimersByTime(100);
        expect(el.style.display).toBe('none');
    });

    it('is safe to call when no message is open', () => {
        const m = new Messages();
        expect(() => m.close()).not.toThrow();
    });

    it('does not throw when the .cms-messages element is gone', () => {
        const m = new Messages();
        document.body.innerHTML = ''; // wipe before close
        expect(() => m.close()).not.toThrow();
    });
});

describe('Messages — open() resilience', () => {
    it('returns silently when the .cms-messages element is missing', () => {
        document.body.innerHTML = ''; // no .cms wrapper
        const m = new Messages();
        expect(() => m.open({ message: 'x' })).not.toThrow();
    });

    it('re-queries the toolbar markup on every open() (post-refresh)', () => {
        const m = new Messages();
        m.open({ message: 'first' });
        // Simulate structureboard's content refresh — body swap.
        setupDom();
        m.open({ message: 'second' });
        const inner = document.querySelector('.cms-messages-inner')!;
        expect(inner.innerHTML).toBe('second');
    });
});
