import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Modal } from '../../frontend/modules/modal/modal';

interface CmsLike {
    config?: { lang?: { cancel?: string; confirmDirty?: string } };
    settings?: Record<string, unknown>;
    API?: {
        Tooltip?: { hide: () => void };
        Messages?: { open: (o: unknown) => void };
        locked?: boolean;
    };
}

function setupDom(): void {
    document.body.innerHTML = `
        <div class="cms">
            <div class="cms-toolbar"></div>
            <div class="cms-toolbar-left" style="width: 60px"></div>
        </div>
        <div class="cms-modal" style="display:none">
            <div class="cms-modal-shim"></div>
            <div class="cms-modal-resize"></div>
            <div class="cms-modal-minimize"></div>
            <div class="cms-modal-maximize"></div>
            <div class="cms-modal-title">
                <span class="cms-modal-title-prefix"></span>
                <span class="cms-modal-title-suffix"></span>
            </div>
            <div class="cms-modal-breadcrumb"></div>
            <div class="cms-modal-close"></div>
            <div class="cms-modal-cancel"></div>
            <div class="cms-modal-body">
                <div class="cms-modal-frame"></div>
            </div>
            <div class="cms-modal-buttons"></div>
        </div>
    `;
}

beforeEach(() => {
    setupDom();
    (window as unknown as { CMS: CmsLike }).CMS = {
        config: { lang: { cancel: 'Cancel', confirmDirty: 'Dirty?' } },
        settings: {},
        API: {},
    };
    vi.useFakeTimers();
});

afterEach(() => {
    vi.useRealTimers();
    document.body.innerHTML = '';
    delete (window as { CMS?: unknown }).CMS;
    document.documentElement.dataset.cmsKbContext = '';
});

describe('Modal — construction', () => {
    it('throws if .cms-modal is absent', () => {
        document.body.innerHTML = '';
        expect(() => new Modal()).toThrow(/Modal markup not found/);
    });

    it('default options can be overridden', () => {
        const m = new Modal({ minWidth: 200, modalDuration: 50 });
        expect(m.options.minWidth).toBe(200);
        expect(m.options.modalDuration).toBe(50);
    });
});

describe('Modal — open()', () => {
    it('throws when neither url nor html is provided', () => {
        const m = new Modal();
        expect(() =>
            m.open({} as unknown as Parameters<Modal['open']>[0]),
        ).toThrow(/were invalid/);
    });

    it('renders markup mode when given html', () => {
        const m = new Modal();
        m.open({ html: '<p>Hello</p>', title: 'Title' });
        const modal =
            document.querySelector<HTMLElement>('.cms-modal')!;
        expect(modal.classList.contains('cms-modal-markup')).toBe(true);
        expect(modal.classList.contains('cms-modal-iframe')).toBe(false);
        expect(
            modal.querySelector('.cms-modal-frame p')?.textContent,
        ).toBe('Hello');
        expect(
            modal.querySelector('.cms-modal-title-prefix')?.textContent,
        ).toBe('Title');
    });

    it('subtitle goes into title-suffix', () => {
        const m = new Modal();
        m.open({ html: '<p>x</p>', title: 'A', subtitle: 'B' });
        expect(
            document.querySelector('.cms-modal-title-suffix')?.textContent,
        ).toBe('B');
    });

    it('sets keyboard context to "modal" on open', () => {
        const m = new Modal();
        m.open({ html: '<p>x</p>' });
        expect(document.documentElement.dataset.cmsKbContext).toBe('modal');
    });

    it('toggles cms-modal-open class after a frame', () => {
        const m = new Modal();
        m.open({ html: '<p>x</p>' });
        const modal =
            document.querySelector<HTMLElement>('.cms-modal')!;
        expect(modal.classList.contains('cms-modal-open')).toBe(false);
        vi.advanceTimersByTime(10);
        expect(modal.classList.contains('cms-modal-open')).toBe(true);
    });
});

describe('Modal — close()', () => {
    it('hides the modal after the close animation', () => {
        const m = new Modal();
        m.open({ html: '<p>x</p>' });
        vi.advanceTimersByTime(10);
        m.close();
        const modal =
            document.querySelector<HTMLElement>('.cms-modal')!;
        // After modalDuration / 2 = 100ms, display is set to none.
        vi.advanceTimersByTime(100);
        expect(modal.style.display).toBe('none');
    });

    it('clears the iframe holder on close', () => {
        const m = new Modal();
        m.open({ html: '<div>content</div>' });
        const frame =
            document.querySelector<HTMLElement>('.cms-modal-frame')!;
        expect(frame.children.length).toBe(1);
        m.close();
        expect(frame.children.length).toBe(0);
    });
});

describe('Modal — minimize / maximize', () => {
    it('minimize toggles cms-modal-minimized on body', () => {
        const m = new Modal();
        m.open({ html: '<p>x</p>' });
        m.minimize();
        expect(
            document.documentElement.classList.contains(
                'cms-modal-minimized',
            ),
        ).toBe(true);
        m.minimize();
        expect(
            document.documentElement.classList.contains(
                'cms-modal-minimized',
            ),
        ).toBe(false);
    });

    it('maximize toggles cms-modal-maximized on body', () => {
        const m = new Modal();
        m.open({ html: '<p>x</p>' });
        m.maximize();
        expect(
            document.documentElement.classList.contains(
                'cms-modal-maximized',
            ),
        ).toBe(true);
        m.maximize();
        expect(
            document.documentElement.classList.contains(
                'cms-modal-maximized',
            ),
        ).toBe(false);
    });

    it('minimize is a no-op when maximized', () => {
        const m = new Modal();
        m.open({ html: '<p>x</p>' });
        m.maximize();
        const result = m.minimize();
        expect(result).toBe(false);
    });

    it('maximize is a no-op when minimized', () => {
        const m = new Modal();
        m.open({ html: '<p>x</p>' });
        m.minimize();
        const result = m.maximize();
        expect(result).toBe(false);
    });
});
