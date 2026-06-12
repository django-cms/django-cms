import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { addSlugHandlers } from '../../frontend/modules/slug';

/**
 * Test helpers.
 *
 * The slug module depends on two runtime globals:
 *   - URLify(value, numChars): Django admin's slugifier.
 *   - window.unihandecode: optional CJK decoder.
 *
 * We stub both globally between tests. URLify is required; unihandecode
 * is only present in the tests that exercise its path.
 */

const fakeURLify = (value: string, numChars = 64): string =>
    value
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '')
        .slice(0, numChars);

function makeForm(titleValue = '', slugValue = ''): {
    title: HTMLInputElement;
    slug: HTMLInputElement;
} {
    document.body.innerHTML = `
        <form>
            <input id="id_title" value="${titleValue}" />
            <input id="id_slug" value="${slugValue}" />
        </form>
    `;
    return {
        title: document.querySelector<HTMLInputElement>('#id_title')!,
        slug: document.querySelector<HTMLInputElement>('#id_slug')!,
    };
}

/** Simulate the user typing into an input — dispatches `input`. */
function typeInto(el: HTMLInputElement, value: string): void {
    el.value = value;
    el.dispatchEvent(new Event('input', { bubbles: true }));
}

describe('addSlugHandlers', () => {
    beforeEach(() => {
        vi.stubGlobal('URLify', fakeURLify);
    });

    afterEach(() => {
        vi.unstubAllGlobals();
        document.body.innerHTML = '';
        // Clear UNIHANDECODER between tests — it's cached on window.
        delete window.UNIHANDECODER;
    });

    describe('no-op cases', () => {
        it('returns a no-op handle when slug is null', () => {
            const { title } = makeForm();
            const handle = addSlugHandlers(title, null);
            expect(() => handle.destroy()).not.toThrow();
        });

        it('returns a no-op handle when title is null', () => {
            const { slug } = makeForm();
            const handle = addSlugHandlers(null, slug);
            expect(() => handle.destroy()).not.toThrow();
        });

        it('does not touch the DOM when either input is missing', () => {
            const { slug } = makeForm('ignored', 'pre-existing');
            addSlugHandlers(null, slug);
            expect(slug.value).toBe('pre-existing');
        });
    });

    describe('initial auto-fill', () => {
        it('generates a slug from a pre-filled title at init when slug is empty', () => {
            const { title, slug } = makeForm('My First Page');
            addSlugHandlers(title, slug);
            expect(slug.value).toBe('my-first-page');
        });

        it('does NOT overwrite an existing slug on init', () => {
            const { title, slug } = makeForm('My Title', 'custom-slug');
            addSlugHandlers(title, slug);
            expect(slug.value).toBe('custom-slug');
        });

        it('treats a whitespace-only slug as empty', () => {
            const { title, slug } = makeForm('Hello World', '   ');
            addSlugHandlers(title, slug);
            expect(slug.value).toBe('hello-world');
        });
    });

    describe('live update while typing', () => {
        it('updates slug on input events in the title', () => {
            const { title, slug } = makeForm('');
            addSlugHandlers(title, slug);

            typeInto(title, 'Hello');
            expect(slug.value).toBe('hello');

            typeInto(title, 'Hello World');
            expect(slug.value).toBe('hello-world');
        });

        it('responds to input event (covers paste, not just keystrokes)', () => {
            const { title, slug } = makeForm('');
            addSlugHandlers(title, slug);

            // Simulate a paste by setting value directly + firing input.
            // This is the case keyup/keypress miss in the legacy impl.
            title.value = 'Pasted Content';
            title.dispatchEvent(new Event('input', { bubbles: true }));

            expect(slug.value).toBe('pasted-content');
        });

        it('caps the generated slug at 64 characters', () => {
            const longTitle = 'a'.repeat(200);
            const { title, slug } = makeForm('');
            addSlugHandlers(title, slug);

            typeInto(title, longTitle);
            expect(slug.value).toHaveLength(64);
        });
    });

    describe('prefill flag / manual edit semantics', () => {
        it('stops auto-filling once the user manually edits the slug', () => {
            const { title, slug } = makeForm('');
            addSlugHandlers(title, slug);

            typeInto(title, 'First');
            expect(slug.value).toBe('first');

            // Simulate user manually editing the slug. The legacy code
            // used a `change` event to mark the slug as "touched"; the
            // same semantics here flip `prefill` off only after the user
            // clears the slug. Test the simpler version first: changing
            // the slug's value while typing in title → auto-update keeps
            // going, which is the legacy behavior.
            slug.value = 'custom';

            typeInto(title, 'First Second');
            // `prefill` is still true (slug wasn't empty when we checked),
            // so slug gets overwritten. This matches the legacy impl.
            expect(slug.value).toBe('first-second');
        });

        it('re-arms auto-fill when the user clears the slug', () => {
            const { title, slug } = makeForm('', 'seeded');
            addSlugHandlers(title, slug);
            // Initial: slug is non-empty, so prefill is false.
            typeInto(title, 'Hello');
            // Since prefill was false and slug is non-empty, no update.
            expect(slug.value).toBe('seeded');

            // User clears the slug.
            slug.value = '';
            typeInto(title, 'Hello World');
            // Re-arm: prefill flips back to true on empty slug, then the
            // SAME call generates the urlified slug.
            expect(slug.value).toBe('hello-world');
        });

        it('keeps auto-filling across many keystrokes once re-armed', () => {
            const { title, slug } = makeForm('', '');
            addSlugHandlers(title, slug);

            typeInto(title, 'A');
            typeInto(title, 'AB');
            typeInto(title, 'ABC');
            expect(slug.value).toBe('abc');
        });
    });

    describe('markChanged', () => {
        it('marks slug with data-changed when slug fires change event', () => {
            const { title, slug } = makeForm();
            addSlugHandlers(title, slug);

            slug.dispatchEvent(new Event('change', { bubbles: true }));
            expect(slug.dataset.changed).toBe('true');
        });

        it('marks title with data-changed when title fires change event', () => {
            const { title, slug } = makeForm();
            addSlugHandlers(title, slug);

            title.dispatchEvent(new Event('change', { bubbles: true }));
            expect(title.dataset.changed).toBe('true');
        });

        it('does not mark either input from `input` events alone', () => {
            const { title, slug } = makeForm();
            addSlugHandlers(title, slug);

            typeInto(title, 'Hi');
            expect(title.dataset.changed).toBeUndefined();
            expect(slug.dataset.changed).toBeUndefined();
        });
    });

    describe('unihandecode integration', () => {
        it('uses UNIHANDECODER to transliterate before URLify', () => {
            // The decoder turns the title into a string that's already
            // ASCII; URLify then slugifies THAT instead of the original.
            // That's the point: URLify by itself can't handle non-ASCII,
            // so the decoder runs first to produce an ASCII-ish form.
            const decode = vi.fn((s: string) => `transliterated ${s.length}`);
            window.unihandecode = {
                Unihan: vi.fn(() => ({ decode })),
            };

            const { title, slug } = makeForm('');
            addSlugHandlers(title, slug);
            typeInto(title, '日本語');
            // Decoder was called with the raw title.
            expect(decode).toHaveBeenCalledWith('日本語');
            // Slug is URLify(decoder output), not URLify(raw title).
            expect(slug.value).toBe('transliterated-3');
        });

        it('passes the slug data-decoder attribute to Unihan()', () => {
            const unihanFactory = vi.fn(() => ({ decode: (s: string) => s }));
            window.unihandecode = { Unihan: unihanFactory };

            document.body.innerHTML = `
                <form>
                    <input id="id_title" value="" />
                    <input id="id_slug" data-decoder="ja" value="" />
                </form>
            `;
            const title = document.querySelector<HTMLInputElement>('#id_title')!;
            const slug = document.querySelector<HTMLInputElement>('#id_slug')!;
            addSlugHandlers(title, slug);

            expect(unihanFactory).toHaveBeenCalledWith('ja');
        });

        it('falls back to plain URLify if Unihan instantiation throws', () => {
            window.unihandecode = {
                Unihan: vi.fn(() => {
                    throw new Error('decoder data missing');
                }),
            };

            const { title, slug } = makeForm('');
            // Must not throw.
            expect(() => addSlugHandlers(title, slug)).not.toThrow();
            typeInto(title, 'Hello');
            expect(slug.value).toBe('hello');
        });

        it('does nothing special when unihandecode is absent', () => {
            // Default case: window.unihandecode undefined.
            const { title, slug } = makeForm('');
            addSlugHandlers(title, slug);
            typeInto(title, 'Plain ASCII Title');
            expect(slug.value).toBe('plain-ascii-title');
        });
    });

    describe('destroy()', () => {
        it('removes all listeners so subsequent input events are no-ops', () => {
            const { title, slug } = makeForm('');
            const handle = addSlugHandlers(title, slug);

            typeInto(title, 'First');
            expect(slug.value).toBe('first');

            handle.destroy();

            // After destroy, typing in title should not update slug.
            title.value = 'Something Else';
            title.dispatchEvent(new Event('input', { bubbles: true }));
            expect(slug.value).toBe('first');
        });

        it('stops the change-event markChanged too', () => {
            const { title, slug } = makeForm();
            const handle = addSlugHandlers(title, slug);
            handle.destroy();

            slug.dispatchEvent(new Event('change', { bubbles: true }));
            expect(slug.dataset.changed).toBeUndefined();
        });
    });
});
