import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { initChangeForm } from '../../frontend/modules/changeform';

/**
 * Test strategy.
 *
 * The module's slug integration is already covered by `slug.test.ts`,
 * so we don't retest slug behavior here — just confirm init wires the
 * title/slug element pair. Everything else (lazy-load, row hiding,
 * language tabs, changeLanguage API) gets its own test block.
 *
 * `window.location.href` is a pain to mock in jsdom because jsdom's
 * Location implementation attempts real navigation on assignment. We
 * replace the whole `window.location` with a plain object for the
 * duration of each test via `Object.defineProperty`, then restore.
 */

const originalLocation = window.location;

function stubLocation(): { href: string } {
    const stub = { href: '' };
    Object.defineProperty(window, 'location', {
        configurable: true,
        writable: true,
        value: stub,
    });
    return stub;
}

function restoreLocation(): void {
    Object.defineProperty(window, 'location', {
        configurable: true,
        writable: true,
        value: originalLocation,
    });
}

/** Required shim for URLify — the slug module calls it unconditionally. */
function installURLifyStub(): void {
    vi.stubGlobal('URLify', (v: string, n = 64) =>
        v
            .toLowerCase()
            .trim()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-|-$/g, '')
            .slice(0, n),
    );
}

function basicForm(titleValue = '', slugValue = ''): void {
    document.body.innerHTML = `
        <form>
            <input id="id_title" value="${titleValue}" />
            <input id="id_slug" value="${slugValue}" />
        </form>
    `;
}

describe('initChangeForm', () => {
    beforeEach(() => {
        installURLifyStub();
        document.body.innerHTML = '';
        // Reset CMS between tests so API attachments don't leak.
        delete (window as { CMS?: unknown }).CMS;
    });

    afterEach(() => {
        vi.unstubAllGlobals();
        restoreLocation();
    });

    describe('slug wiring', () => {
        it('generates a slug from the title on page load', () => {
            basicForm('Hello World');
            initChangeForm();
            const slug = document.querySelector<HTMLInputElement>('#id_slug')!;
            expect(slug.value).toBe('hello-world');
        });

        it('is a no-op when title or slug input is missing', () => {
            document.body.innerHTML = '<form><input id="id_title" /></form>';
            expect(() => initChangeForm()).not.toThrow();
        });
    });

    describe('lazy-load of div.loading[rel] partials', () => {
        it('fetches the rel URL and replaces the div contents with the parsed body', async () => {
            basicForm();
            document.body.insertAdjacentHTML(
                'beforeend',
                '<div class="loading" rel="/permissions/">loading...</div>',
            );
            const fetchMock = vi.fn().mockResolvedValue({
                text: async () => '<p class="perm">granted</p>',
            });
            vi.stubGlobal('fetch', fetchMock);

            initChangeForm();
            // Allow the fetch promise chain to settle.
            await new Promise((resolve) => setTimeout(resolve, 0));
            await new Promise((resolve) => setTimeout(resolve, 0));

            expect(fetchMock).toHaveBeenCalledWith('/permissions/');
            const div = document.querySelector('div.loading')!;
            expect(div.querySelector('p.perm')?.textContent).toBe('granted');
            expect(div.textContent).not.toContain('loading...');
        });

        it('skips div.loading elements with no rel attribute', () => {
            basicForm();
            document.body.insertAdjacentHTML(
                'beforeend',
                '<div class="loading">nothing here</div>',
            );
            const fetchMock = vi.fn();
            vi.stubGlobal('fetch', fetchMock);

            initChangeForm();
            expect(fetchMock).not.toHaveBeenCalled();
        });

        it('swallows fetch errors without crashing init', async () => {
            basicForm();
            document.body.insertAdjacentHTML(
                'beforeend',
                '<div class="loading" rel="/boom/">x</div>',
            );
            vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network down')));
            // Silence console.error for the expected log.
            const errSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

            expect(() => initChangeForm()).not.toThrow();
            // Let the rejection propagate through the catch handler.
            await new Promise((resolve) => setTimeout(resolve, 0));
            await new Promise((resolve) => setTimeout(resolve, 0));
            expect(errSpy).toHaveBeenCalled();
            errSpy.mockRestore();
        });
    });

    describe('hidden-input row hiding', () => {
        it('hides .form-row elements containing a hidden input', () => {
            basicForm();
            document.body.insertAdjacentHTML(
                'beforeend',
                `
                <div class="form-row visible-row">
                    <input type="text" name="visible" />
                </div>
                <div class="form-row hidden-row">
                    <input type="hidden" name="hidden" />
                </div>
                `,
            );

            initChangeForm();

            const visibleRow = document.querySelector<HTMLElement>('.visible-row')!;
            const hiddenRow = document.querySelector<HTMLElement>('.hidden-row')!;
            expect(visibleRow.style.display).toBe('');
            expect(hiddenRow.style.display).toBe('none');
        });

        it('does not crash on a hidden input without a .form-row ancestor', () => {
            basicForm();
            document.body.insertAdjacentHTML(
                'beforeend',
                '<input type="hidden" name="naked" />',
            );
            expect(() => initChangeForm()).not.toThrow();
        });
    });

    describe('language tab clicks', () => {
        it('calls CMS.API.changeLanguage with the button\'s data-admin-url', () => {
            basicForm();
            document.body.insertAdjacentHTML(
                'beforeend',
                `
                <div id="page_form_lang_tabs">
                    <button class="language_button" data-admin-url="/de/edit/">DE</button>
                </div>
                `,
            );
            stubLocation();
            initChangeForm();

            // changeLanguage is installed on window.CMS.API — spy through it.
            const api = window.CMS!.API as { changeLanguage: (url: string) => void };
            const spy = vi.spyOn(api, 'changeLanguage');

            document.querySelector<HTMLButtonElement>('.language_button')!.click();
            expect(spy).toHaveBeenCalledWith('/de/edit/');
        });

        it('ignores a language button without data-admin-url', () => {
            basicForm();
            document.body.insertAdjacentHTML(
                'beforeend',
                `
                <div id="page_form_lang_tabs">
                    <button class="language_button">DE</button>
                </div>
                `,
            );
            stubLocation();
            initChangeForm();

            const api = window.CMS!.API as { changeLanguage: (url: string) => void };
            const spy = vi.spyOn(api, 'changeLanguage');
            document.querySelector<HTMLButtonElement>('.language_button')!.click();
            expect(spy).not.toHaveBeenCalled();
        });
    });

    describe('CMS.API.changeLanguage', () => {
        it('is exposed on window.CMS.API after init', () => {
            basicForm();
            initChangeForm();
            expect(typeof window.CMS?.API?.changeLanguage).toBe('function');
        });

        it('creates window.CMS and window.CMS.API if absent', () => {
            basicForm();
            initChangeForm();
            expect(window.CMS).toBeTypeOf('object');
            expect(window.CMS!.API).toBeTypeOf('object');
        });

        it('preserves existing keys on window.CMS.API', () => {
            basicForm();
            window.CMS = { API: { preExisting: 'kept' } };
            initChangeForm();
            expect(window.CMS.API!.preExisting).toBe('kept');
            expect(typeof window.CMS.API!.changeLanguage).toBe('function');
        });

        it('navigates directly when nothing is dirty', () => {
            basicForm();
            const location = stubLocation();
            initChangeForm();

            window.CMS!.API!.changeLanguage!('/target/');
            expect(location.href).toBe('/target/');
        });

        it('confirms and navigates when title is dirty', () => {
            basicForm('Hello', 'custom');
            const location = stubLocation();
            const confirmSpy = vi.fn().mockReturnValue(true);
            vi.stubGlobal('confirm', confirmSpy);
            initChangeForm();

            // Mark the title as dirty (what slug.ts's markChanged does).
            document.querySelector<HTMLInputElement>('#id_title')!.dataset.changed = 'true';

            window.CMS!.API!.changeLanguage!('/de/');
            expect(confirmSpy).toHaveBeenCalledOnce();
            expect(location.href).toBe('/de/');
        });

        it('confirms and navigates when slug is dirty', () => {
            basicForm('Hello', 'custom');
            const location = stubLocation();
            const confirmSpy = vi.fn().mockReturnValue(true);
            vi.stubGlobal('confirm', confirmSpy);
            initChangeForm();

            document.querySelector<HTMLInputElement>('#id_slug')!.dataset.changed = 'true';

            window.CMS!.API!.changeLanguage!('/fr/');
            expect(confirmSpy).toHaveBeenCalledOnce();
            expect(location.href).toBe('/fr/');
        });

        it('aborts navigation when the user cancels the confirm', () => {
            basicForm('Hello', 'custom');
            const location = stubLocation();
            vi.stubGlobal('confirm', vi.fn().mockReturnValue(false));
            initChangeForm();

            document.querySelector<HTMLInputElement>('#id_slug')!.dataset.changed = 'true';

            window.CMS!.API!.changeLanguage!('/fr/');
            expect(location.href).toBe('');
        });

        it('uses gettext for the confirm message when available', () => {
            basicForm('Hello', 'custom');
            stubLocation();
            const gettextFn = vi.fn((msg: string) => `[translated] ${msg}`);
            vi.stubGlobal('gettext', gettextFn);
            const confirmSpy = vi.fn().mockReturnValue(true);
            vi.stubGlobal('confirm', confirmSpy);
            initChangeForm();

            document.querySelector<HTMLInputElement>('#id_slug')!.dataset.changed = 'true';
            window.CMS!.API!.changeLanguage!('/fr/');

            expect(gettextFn).toHaveBeenCalledWith(
                'Are you sure you want to change tabs without saving the page first?',
            );
            expect(confirmSpy.mock.calls[0]![0]).toMatch(/^\[translated\]/);
        });

        it('falls back to plain English when gettext is undefined', () => {
            basicForm('Hello', 'custom');
            stubLocation();
            const confirmSpy = vi.fn().mockReturnValue(true);
            vi.stubGlobal('confirm', confirmSpy);
            // Explicitly ensure gettext is not installed.
            initChangeForm();

            document.querySelector<HTMLInputElement>('#id_slug')!.dataset.changed = 'true';
            window.CMS!.API!.changeLanguage!('/fr/');

            expect(confirmSpy.mock.calls[0]![0]).toBe(
                'Are you sure you want to change tabs without saving the page first?',
            );
        });
    });

    describe('destroy', () => {
        it('removes language button click listeners', () => {
            basicForm();
            document.body.insertAdjacentHTML(
                'beforeend',
                `
                <div id="page_form_lang_tabs">
                    <button class="language_button" data-admin-url="/x/">X</button>
                </div>
                `,
            );
            stubLocation();
            const handle = initChangeForm();
            const api = window.CMS!.API as { changeLanguage: (url: string) => void };
            const spy = vi.spyOn(api, 'changeLanguage');

            handle.destroy();
            document.querySelector<HTMLButtonElement>('.language_button')!.click();
            expect(spy).not.toHaveBeenCalled();
        });
    });
});
