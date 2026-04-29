import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Toolbar } from '../../frontend/modules/toolbar/toolbar';

interface CmsLike {
    config?: Record<string, unknown>;
    settings?: Record<string, unknown>;
    API?: {
        Messages?: { open: (opts: { message: string }) => void };
        Sideframe?: { open: (opts: unknown) => void };
        Helpers?: unknown;
    };
}

function setupDom(): void {
    document.body.innerHTML = `
        <div class="cms">
            <div class="cms-toolbar">
                <div class="cms-toolbar-item-buttons">
                    <a href="/x/" data-rel="message" data-text="hi">Click</a>
                    <a href="/y/">Plain</a>
                </div>
                <div class="cms-toolbar-item-cms-mode-switcher">switcher</div>
                <div class="cms-btn-publish"></div>
                <div class="cms-messages"></div>
            </div>
        </div>
    `;
}

function setCMS(cms: CmsLike): void {
    (window as unknown as { CMS: CmsLike }).CMS = cms;
}

beforeEach(() => {
    setupDom();
    setCMS({ config: {}, settings: {}, API: {} });
    vi.stubGlobal(
        'matchMedia',
        vi.fn().mockReturnValue({ matches: false }),
    );
});

afterEach(() => {
    document.body.innerHTML = '';
    delete (window as { CMS?: unknown }).CMS;
    document.documentElement.style.marginTop = '';
    document.documentElement.classList.remove(
        'cms-toolbar-expanded',
        'cms-toolbar-expanding',
        'cms-ready',
    );
    vi.restoreAllMocks();
});

describe('Toolbar — construction', () => {
    it('marks toolbar as ready', () => {
        new Toolbar();
        const toolbar =
            document.querySelector<HTMLElement>('.cms-toolbar')!;
        expect(toolbar.dataset.cmsReady).toBe('true');
    });

    it('adds cms-ready class to <html>', () => {
        new Toolbar();
        expect(document.documentElement.classList.contains('cms-ready')).toBe(
            true,
        );
    });

    it('hides the publish button container by default', () => {
        new Toolbar();
        const publish = document.querySelector<HTMLElement>(
            '.cms-btn-publish',
        )!;
        const holder = publish.parentElement!;
        expect(holder.style.display).toBe('none');
        expect(holder.dataset.cmsHidden).toBe('true');
    });

    it('does NOT bind events twice when constructed against a marked toolbar', () => {
        const t1 = new Toolbar();
        // Stub _delegate on second instance to ensure the FIRST
        // toolbar still owns the click wiring.
        const delegateSpy = vi.spyOn(t1, '_delegate');
        new Toolbar();
        const link = document.querySelector<HTMLAnchorElement>(
            'a[data-rel="message"]',
        )!;
        link.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        // Only one toolbar should have wired the click handler. We
        // expect exactly one call from the first instance.
        expect(delegateSpy).toHaveBeenCalledTimes(1);
    });
});

describe('Toolbar — button click delegation', () => {
    it('clicking a data-rel button invokes _delegate', () => {
        const t = new Toolbar();
        const delegateSpy = vi.spyOn(t, '_delegate');
        const link = document.querySelector<HTMLAnchorElement>(
            'a[data-rel="message"]',
        )!;
        link.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(delegateSpy).toHaveBeenCalledWith(link);
    });

    it('plain links do NOT invoke _delegate', () => {
        const t = new Toolbar();
        const delegateSpy = vi.spyOn(t, '_delegate');
        const plain = document.querySelector<HTMLAnchorElement>(
            '.cms-toolbar-item-buttons a[href="/y/"]',
        )!;
        // Override navigation to avoid jsdom warnings.
        plain.addEventListener('click', (e) => e.preventDefault(), true);
        plain.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(delegateSpy).not.toHaveBeenCalled();
    });
});

describe('Toolbar — _show', () => {
    it('sets margin-top on <html> based on toolbar height', () => {
        const toolbar = document.querySelector<HTMLElement>(
            '.cms-toolbar',
        )!;
        Object.defineProperty(toolbar, 'getBoundingClientRect', {
            value: () => ({
                height: 50,
                width: 0,
                top: 0,
                bottom: 50,
                left: 0,
                right: 0,
                x: 0,
                y: 0,
                toJSON: () => ({}),
            }),
        });
        const t = new Toolbar();
        t._show({ duration: 0 });
        // 50 + 10 - 10 = 50px
        expect(document.documentElement.style.marginTop).toBe('50px');
        expect(
            document.documentElement.classList.contains(
                'cms-toolbar-expanded',
            ),
        ).toBe(true);
    });
});

describe('Toolbar — initial states with messages', () => {
    it('opens config.messages when present', () => {
        const open = vi.fn();
        setCMS({
            config: { messages: 'hello' },
            settings: {},
            API: { Messages: { open } },
        });
        new Toolbar();
        expect(open).toHaveBeenCalledWith({ message: 'hello' });
    });

    it('opens config.error with error: true', () => {
        const open = vi.fn();
        setCMS({
            config: { error: 'oops' },
            settings: {},
            API: { Messages: { open } },
        });
        new Toolbar();
        expect(open).toHaveBeenCalledWith({
            message: 'oops',
            error: true,
        });
    });
});

describe('Toolbar — _refreshMarkup', () => {
    it('replaces toolbar children but preserves the mode switcher', () => {
        const t = new Toolbar();
        const fresh = document.createElement('div');
        fresh.innerHTML = `
            <div class="cms-toolbar-item-fresh">FRESH</div>
            <div class="cms-toolbar-item-cms-mode-switcher">placeholder</div>
        `;
        t._refreshMarkup(fresh);
        const toolbar =
            document.querySelector<HTMLElement>('.cms-toolbar')!;
        expect(toolbar.querySelector('.cms-toolbar-item-fresh')).not.toBeNull();
        // The placeholder should have been replaced by the original
        // switcher (whose textContent is "switcher" from setupDom).
        const switcher = toolbar.querySelector<HTMLElement>(
            '.cms-toolbar-item-cms-mode-switcher',
        )!;
        expect(switcher.textContent?.trim()).toBe('switcher');
    });
});
