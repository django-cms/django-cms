import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Sideframe } from '../../frontend/modules/sideframe';

interface CmsLike {
    config?: { csrf?: string; debug?: boolean };
    settings?: Record<string, unknown>;
    API?: { Messages?: { open: (o: unknown) => void } };
}

function setupDom(): void {
    document.body.innerHTML = `
        <div class="cms-sideframe" style="display:none">
            <div class="cms-sideframe-dimmer"></div>
            <div class="cms-sideframe-close"></div>
            <div class="cms-sideframe-frame"></div>
            <div class="cms-sideframe-shim"></div>
            <div class="cms-sideframe-history">
                <span class="cms-icon-arrow-back cms-icon-disabled"></span>
                <span class="cms-icon-arrow-forward cms-icon-disabled"></span>
            </div>
        </div>
    `;
}

beforeEach(() => {
    setupDom();
    (window as unknown as { CMS: CmsLike }).CMS = {
        config: {},
        settings: {},
        API: {},
    };
    vi.useFakeTimers();
});

afterEach(() => {
    vi.useRealTimers();
    document.body.innerHTML = '';
    delete (window as { CMS?: unknown }).CMS;
    document.documentElement.classList.remove('cms-prevent-scrolling');
});

describe('Sideframe — construction', () => {
    it('throws if .cms-sideframe is absent', () => {
        document.body.innerHTML = '';
        expect(() => new Sideframe()).toThrow(/Sideframe markup not found/);
    });

    it('default options can be overridden', () => {
        const s = new Sideframe({ sideframeDuration: 100 });
        expect(s.options.sideframeDuration).toBe(100);
    });
});

describe('Sideframe — open()', () => {
    it('throws when no url', () => {
        const s = new Sideframe();
        expect(() =>
            s.open({} as unknown as Parameters<Sideframe['open']>[0]),
        ).toThrow(/were invalid/);
    });

    it('returns false when sideframe is disabled', () => {
        (window as unknown as { CMS: CmsLike }).CMS!.settings = {
            sideframe_enabled: false,
        };
        const s = new Sideframe();
        const result = s.open({ url: '/x/' });
        expect(result).toBe(false);
    });

    it('shows the sideframe and injects an iframe', () => {
        const s = new Sideframe();
        s.open({ url: '/x/' });
        expect(s.ui.sideframe.style.width).toBe('95%');
        const iframe =
            s.ui.frame.querySelector<HTMLIFrameElement>('iframe')!;
        expect(iframe.src).toContain('/x/');
    });

    it('persists sideframe URL in CMS.settings', () => {
        const s = new Sideframe();
        s.open({ url: '/admin/foo/' });
        const settings = (window.CMS!.settings ?? {}) as {
            sideframe?: { url?: string };
        };
        expect(settings.sideframe?.url).toContain('/admin/foo/');
    });

    it('animated open applies a transition', () => {
        const s = new Sideframe({ sideframeDuration: 100 });
        s.open({ url: '/x/', animate: true });
        expect(s.ui.sideframe.style.transition).toContain('width 100ms');
    });
});

describe('Sideframe — close()', () => {
    it('marks sideframe as hidden in settings', () => {
        const s = new Sideframe({ sideframeDuration: 50 });
        s.open({ url: '/x/' });
        s.close();
        const settings = (window.CMS!.settings ?? {}) as {
            sideframe?: { hidden?: boolean };
        };
        expect(settings.sideframe?.hidden).toBe(true);
    });

    it('hides the sideframe element after the duration', () => {
        const s = new Sideframe({ sideframeDuration: 50 });
        s.open({ url: '/x/' });
        s.close();
        // close uses duration / 2 = 25
        vi.advanceTimersByTime(30);
        expect(s.ui.sideframe.classList.contains('cms-sideframe--open')).toBe(false);
    });

    it('clicking the close button closes the sideframe', () => {
        const s = new Sideframe();
        s.open({ url: '/x/' });
        const closeBtn = s.ui.close!;
        const spy = vi.spyOn(s, 'close');
        closeBtn.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(spy).toHaveBeenCalled();
    });

    it('clicking the dimmer closes the sideframe', () => {
        const s = new Sideframe();
        s.open({ url: '/x/' });
        const dimmer = s.ui.dimmer!;
        const spy = vi.spyOn(s, 'close');
        dimmer.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(spy).toHaveBeenCalled();
    });
});

describe('Sideframe — history', () => {
    it('back/forward buttons are disabled with empty history', () => {
        const s = new Sideframe();
        s.open({ url: '/x/' });
        expect(
            s.ui.historyBack?.classList.contains('cms-icon-disabled'),
        ).toBe(true);
        expect(
            s.ui.historyForward?.classList.contains('cms-icon-disabled'),
        ).toBe(true);
    });

    it('back button enables after multiple history entries', () => {
        const s = new Sideframe();
        s.open({ url: '/x/' });
        // Manually add to history (load events don't fire in jsdom).
        s.history.back.push('/a/');
        s.history.back.push('/b/');
        // Trigger update via private method through any cast.
        (s as unknown as {
            updateHistoryButtons(): void;
        }).updateHistoryButtons();
        expect(
            s.ui.historyBack?.classList.contains('cms-icon-disabled'),
        ).toBe(false);
    });

    it('forward button enables when forward stack has entries', () => {
        const s = new Sideframe();
        s.open({ url: '/x/' });
        s.history.forward.push('/x/');
        (s as unknown as {
            updateHistoryButtons(): void;
        }).updateHistoryButtons();
        expect(
            s.ui.historyForward?.classList.contains('cms-icon-disabled'),
        ).toBe(false);
    });
});
