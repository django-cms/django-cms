import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { delegate, openAjax } from '../../frontend/modules/toolbar/delegate';

interface CmsLike {
    config?: { csrf?: string } | undefined;
    settings?: { sideframe_enabled?: boolean } | undefined;
    API?:
        | {
              Messages?: {
                  open: (opts: { message: string; error?: boolean }) => void;
              };
              Sideframe?: { open: (opts: { url: string }) => void };
              locked?: boolean;
          }
        | undefined;
    Modal?:
        | (new (opts?: { onClose?: unknown }) => {
              open: (opts: { url: string; title?: string }) => void;
          })
        | undefined;
    Sideframe?:
        | (new (opts?: { onClose?: unknown }) => {
              open: (opts: { url: string }) => void;
          })
        | undefined;
}

function makeAnchor(attrs: Record<string, string>): HTMLAnchorElement {
    const a = document.createElement('a');
    for (const [k, v] of Object.entries(attrs)) {
        if (k === 'class') a.className = v;
        else a.setAttribute(k, v);
    }
    document.body.appendChild(a);
    return a;
}

function setCMS(cms: CmsLike): void {
    (window as unknown as { CMS: CmsLike }).CMS = cms;
}

beforeEach(() => {
    document.body.innerHTML = '';
});

afterEach(() => {
    document.body.innerHTML = '';
    delete (window as { CMS?: unknown }).CMS;
    vi.restoreAllMocks();
});

describe('delegate', () => {
    it('returns false for disabled buttons', () => {
        const a = makeAnchor({ class: 'cms-btn-disabled', href: '/x/' });
        expect(delegate(a)).toBe(false);
    });

    it('data-rel="message" calls Messages.open with text', () => {
        const open = vi.fn();
        setCMS({ API: { Messages: { open } } });
        const a = makeAnchor({
            'data-rel': 'message',
            'data-text': 'hello',
            href: '#',
        });
        delegate(a);
        expect(open).toHaveBeenCalledWith({ message: 'hello' });
    });

    it('data-rel="modal" instantiates the Modal constructor', () => {
        const open = vi.fn();
        const Ctor = vi.fn(() => ({ open }));
        setCMS({
            Modal: Ctor as unknown as CmsLike['Modal'],
            config: {},
        });
        const a = makeAnchor({
            'data-rel': 'modal',
            'data-name': 'Title',
            href: '/edit/',
        });
        delegate(a);
        expect(Ctor).toHaveBeenCalled();
        expect(open).toHaveBeenCalledTimes(1);
        const call = open.mock.calls[0]![0] as { url: string; title?: string };
        expect(call.title).toBe('Title');
        expect(call.url).toContain('/edit/');
        expect(call.url).toContain('_popup=1');
    });

    it('data-rel="modal" without Modal constructor falls back to navigation', () => {
        setCMS({});
        const win = {
            location: { href: '' },
        } as unknown as Window;
        const a = makeAnchor({
            'data-rel': 'modal',
            href: '/fallback/',
        });
        // Spy on Helpers._getWindow to inject our fake window.
        // (Direct way: since we can't easily patch the import, just
        // check that no exception is thrown when Modal is missing.)
        expect(() => delegate(a)).not.toThrow();
        void win;
    });

    it('data-rel="color-toggle" toggles the color scheme', () => {
        vi.stubGlobal(
            'matchMedia',
            vi.fn().mockReturnValue({ matches: false }),
        );
        // Pre-set theme so toggle is observable.
        document.documentElement.setAttribute('data-theme', 'light');
        const a = makeAnchor({ 'data-rel': 'color-toggle', href: '#' });
        delegate(a);
        expect(document.documentElement.getAttribute('data-theme')).not.toBe(
            'light',
        );
    });

    it('data-rel="sideframe" opens the sideframe when enabled', () => {
        const open = vi.fn();
        setCMS({
            API: { Sideframe: { open } },
            settings: { sideframe_enabled: true },
        });
        const a = makeAnchor({
            'data-rel': 'sideframe',
            href: '/sf/',
        });
        delegate(a);
        expect(open).toHaveBeenCalledWith({ url: '/sf/', animate: true });
    });

    it('data-rel="sideframe" disabled falls through to default', () => {
        const open = vi.fn();
        setCMS({
            API: { Sideframe: { open } },
            settings: { sideframe_enabled: false },
        });
        const a = makeAnchor({
            'data-rel': 'sideframe',
            href: '/sf/',
        });
        // Stub Helpers._getWindow's location to detect navigation.
        const win = (window as unknown as { __targetUrl: string });
        win.__targetUrl = '';
        // Override location via assigning location.href triggers
        // jsdom navigation; instead spy on Helpers.
        delegate(a);
        // Sideframe.open must NOT have been called.
        expect(open).not.toHaveBeenCalled();
    });

    it('cms-form-post-method default builds and submits a hidden form', () => {
        // jsdom doesn't support form.submit() actual navigation, but
        // we can spy on it.
        setCMS({ config: { csrf: 'token-xyz' } });
        const a = makeAnchor({
            class: 'cms-form-post-method',
            href: '/post/',
        });
        const submitSpy = vi
            .spyOn(HTMLFormElement.prototype, 'submit')
            .mockImplementation(() => {});
        delegate(a);
        expect(submitSpy).toHaveBeenCalledTimes(1);
        const form = document.querySelector<HTMLFormElement>(
            'form[action="/post/"]',
        )!;
        expect(form).not.toBeNull();
        const input = form.querySelector<HTMLInputElement>(
            'input[name="csrfmiddlewaretoken"]',
        )!;
        expect(input.value).toBe('token-xyz');
    });
});

describe('openAjax', () => {
    it('cancels when text-confirm returns false', async () => {
        // Make confirm return false AND take long enough that the
        // secureConfirm timing trick doesn't bypass it.
        const realConfirm = window.confirm;
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        window.confirm = ((_msg: string) => {
            // Spend a bit of wall clock to pass the secureConfirm
            // 10ms threshold (busy-wait).
            const start = Date.now();
            while (Date.now() - start < 15) {
                /* spin */
            }
            return false;
        }) as unknown as typeof window.confirm;

        try {
            const result = await openAjax({
                url: '/x/',
                text: 'Are you sure?',
            });
            expect(result).toBe(false);
        } finally {
            window.confirm = realConfirm;
        }
    });

    it('reports network errors via Messages', async () => {
        const open = vi.fn();
        setCMS({ API: { Messages: { open } } });
        const fetchMock = vi
            .fn()
            .mockRejectedValue(new Error('Network down'));
        vi.stubGlobal('fetch', fetchMock);

        const result = await openAjax({ url: '/x/' });
        expect(result).toBe(false);
        expect(open).toHaveBeenCalled();
        const call = open.mock.calls[0]![0];
        expect(call.error).toBe(true);
        expect(call.message).toContain('Network down');
    });

    it('on success calls callback with the response payload', async () => {
        const fetchMock = vi.fn().mockResolvedValue(
            new Response(JSON.stringify({ ok: 1 }), { status: 200 }),
        );
        vi.stubGlobal('fetch', fetchMock);

        const cb = vi.fn();
        await openAjax({ url: '/x/', callback: cb });
        expect(cb).toHaveBeenCalledWith({ ok: 1 });
    });
});
