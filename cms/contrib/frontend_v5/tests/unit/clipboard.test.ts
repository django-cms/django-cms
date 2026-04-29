import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Clipboard } from '../../frontend/modules/clipboard/clipboard';
import { _resetForTest } from '../../frontend/modules/clipboard/sync';

interface CmsLike {
    config?: {
        csrf?: string;
        lang?: { cancel?: string };
        clipboard?: { url?: string };
    };
    settings?: Record<string, unknown>;
    API?: {
        Toolbar?: { openAjax: (opts: unknown) => Promise<unknown> };
    };
    Plugin?: unknown;
    _instances?: unknown[];
}

function setupDom(): void {
    document.body.innerHTML = `
        <div class="cms-toolbar-item-navigation">
            <ul>
                <li class="cms-clipboard-trigger">
                    <a href="#">Open</a>
                </li>
                <li class="cms-clipboard-empty">
                    <a href="#">Clear</a>
                </li>
            </ul>
        </div>
        <div class="cms-clipboard" data-title="Clipboard">
            <div class="cms-clipboard-containers">items</div>
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
        config: {
            csrf: 'token',
            lang: { cancel: 'Cancel' },
            clipboard: { url: '/clear/' },
        },
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
    _resetForTest();
    vi.restoreAllMocks();
});

describe('Clipboard — construction', () => {
    it('finds clipboard markup and triggers', () => {
        const c = new Clipboard();
        expect(c.ui.clipboard).not.toBeNull();
        expect(c.ui.triggers.length).toBe(1);
        expect(c.ui.triggerRemove.length).toBe(1);
    });

    it('initialises with empty currentClipboardData', () => {
        const c = new Clipboard();
        expect(c.currentClipboardData).toEqual({});
    });

    it('creates a Modal when markup is present', () => {
        const c = new Clipboard();
        expect(c.modal).not.toBeNull();
    });

    it('skips modal creation when .cms-modal is missing', () => {
        document.querySelector('.cms-modal')?.remove();
        const c = new Clipboard();
        expect(c.modal).toBeNull();
    });
});

describe('Clipboard — populate', () => {
    it('updates currentClipboardData and writes to localStorage', () => {
        const c = new Clipboard();
        c.populate('<div>x</div>', { plugin_id: 7 });
        expect(c.currentClipboardData.html).toBe('<div>x</div>');
        expect(c.currentClipboardData.data).toEqual({ plugin_id: 7 });
        const raw = localStorage.getItem('cms-clipboard');
        expect(raw).not.toBeNull();
        const parsed = JSON.parse(raw!);
        expect(parsed.data.plugin_id).toBe(7);
    });
});

describe('Clipboard — trigger click', () => {
    it('opens the modal when the trigger is clicked', () => {
        const c = new Clipboard();
        const open = vi.spyOn(c.modal!, 'open');
        c.ui.triggers[0]!.dispatchEvent(
            new MouseEvent('click', { bubbles: true }),
        );
        expect(open).toHaveBeenCalledTimes(1);
        const call = open.mock.calls[0]![0] as {
            html?: HTMLElement;
            title?: string;
        };
        expect(call.title).toBe('Clipboard');
    });

    it('disabled triggers do not open the modal', () => {
        const trigger = document.querySelector('.cms-clipboard-trigger')!;
        trigger.classList.add('cms-toolbar-item-navigation-disabled');
        const c = new Clipboard();
        const open = vi.spyOn(c.modal!, 'open');
        c.ui.triggers[0]!.dispatchEvent(
            new MouseEvent('click', { bubbles: true }),
        );
        expect(open).not.toHaveBeenCalled();
    });
});

describe('Clipboard — clear', () => {
    it('calls Toolbar.openAjax with the clipboard URL', () => {
        const openAjax = vi.fn().mockResolvedValue(undefined);
        (window as unknown as { CMS: CmsLike }).CMS!.API = {
            Toolbar: { openAjax },
        };
        const c = new Clipboard();
        c.clear();
        expect(openAjax).toHaveBeenCalled();
        const opts = openAjax.mock.calls[0]![0];
        expect(opts.url).toContain('/clear/');
    });

    it('falls back to populate("") when no Toolbar API is present', () => {
        (window as unknown as { CMS: CmsLike }).CMS!.API = {};
        const c = new Clipboard();
        c.populate('<x/>', { plugin_id: 1 });
        c.clear();
        expect(c.currentClipboardData.data).toEqual({});
        expect(c.currentClipboardData.html).toBe('');
    });

    it('calls supplied callback after fallback path', () => {
        (window as unknown as { CMS: CmsLike }).CMS!.API = {};
        const c = new Clipboard();
        const cb = vi.fn();
        c.clear(cb);
        expect(cb).toHaveBeenCalledOnce();
    });
});

describe('Clipboard — _toolbarEvents (re-bind)', () => {
    it('re-queries triggers after toolbar re-render', () => {
        const c = new Clipboard();
        // Simulate toolbar re-render: replace the triggers with new
        // anchor elements.
        document.querySelector('.cms-clipboard-trigger')!.innerHTML =
            '<a href="#">NEW</a>';
        c._toolbarEvents();
        const open = vi.spyOn(c.modal!, 'open');
        const newAnchor = document.querySelector<HTMLAnchorElement>(
            '.cms-clipboard-trigger a',
        )!;
        newAnchor.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(open).toHaveBeenCalledTimes(1);
    });
});

describe('Clipboard — cross-tab sync', () => {
    it('clears DOM state when external update has no plugin_id', () => {
        const c = new Clipboard();
        // Pre-set currentClipboardData with a plugin so the external
        // update is "newer".
        c.currentClipboardData = {
            data: { plugin_id: 1 },
            html: 'old',
            timestamp: 1,
        };
        // Disable triggers so we can verify cleanupDom flips them.
        c.ui.triggers[0]!.parentElement!.classList.remove(
            'cms-toolbar-item-navigation-disabled',
        );
        // Simulate a sibling tab clearing the clipboard.
        const evt = new StorageEvent('storage', {
            key: 'cms-clipboard',
            newValue: JSON.stringify({
                data: {},
                html: '',
                timestamp: 2,
            }),
        });
        window.dispatchEvent(evt);
        expect(
            c.ui.triggers[0]!.parentElement!.classList.contains(
                'cms-toolbar-item-navigation-disabled',
            ),
        ).toBe(true);
    });
});
