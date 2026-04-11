/*
 * Auto-generate a URL slug from a title input.
 *
 * Port of the legacy `cms/static/cms/js/modules/slug.js`. Semantics are
 * preserved with two deliberate small upgrades:
 *
 *   1. Listens to the `input` event instead of `keyup`/`keypress`. The
 *      `input` event fires for paste, cut, drag-drop, IME compositions,
 *      autofill, and programmatic changes — all cases that keyup/keypress
 *      silently missed in the legacy implementation.
 *
 *   2. Unihandecode instantiation is guarded with a try/catch so a broken
 *      decoder (missing locale data, for example) doesn't prevent slug
 *      generation entirely — it just falls back to plain URLify.
 *
 * Semantics preserved from the legacy code:
 *
 *   - Only auto-fills while `prefill` is true. `prefill` starts true iff
 *     the slug was empty at init, goes false the first time the user
 *     manually edits the slug, and RE-ARMS if the user clears the slug
 *     back to empty while typing in the title.
 *   - Both title and slug get `data-changed="true"` on native `change`
 *     events — downstream code checks this to know the field was touched.
 *   - Auto-runs once on init so a server-rerendered form (e.g. validation
 *     error) gets the slug regenerated from a pre-filled title.
 *   - Slug is capped at 64 characters (Django's default `URLify` limit).
 */

const SLUG_MAX_CHARS = 64;

export interface SlugHandlerHandle {
    /** Remove all event listeners installed by `addSlugHandlers`. */
    destroy(): void;
}

/**
 * Wire up title → slug auto-generation on the given input pair. If
 * either input is null (common when the widget is rendered on a page
 * that has only one of the two), the function is a no-op.
 *
 * Returns a handle with a `destroy()` method so consumers that care
 * about teardown (SPAs, unit tests) can clean up listeners. The legacy
 * code leaked listeners; we don't need to match that.
 */
export function addSlugHandlers(
    title: HTMLInputElement | null,
    slug: HTMLInputElement | null,
): SlugHandlerHandle {
    // Both inputs required — no-op if either is missing. Legacy code
    // checked only `slug`, but a missing `title` is just as fatal.
    if (!title || !slug) {
        return { destroy() {} };
    }

    let prefill = slug.value.trim() === '';

    // Instantiate the optional unihandecoder exactly once, lazily. If
    // the locale data is broken, fall back to plain URLify — better to
    // produce an ASCII-approximation slug than to fail silently.
    if (window.unihandecode && !window.UNIHANDECODER) {
        try {
            const decoderName = slug.dataset.decoder;
            window.UNIHANDECODER = window.unihandecode.Unihan(decoderName);
        } catch {
            // Intentionally swallowed — degraded mode (plain URLify).
            // `delete` rather than `= undefined` to satisfy the strict
            // exactOptionalPropertyTypes rule.
            delete window.UNIHANDECODER;
        }
    }

    const updateSlug = (): void => {
        let value = title.value;
        if (window.UNIHANDECODER) {
            value = window.UNIHANDECODER.decode(value);
        }
        // Re-arm if the user cleared a previously-filled slug. This is
        // the subtle behavior that matters: editing-then-clearing returns
        // the field to auto-fill mode, matching the legacy logic exactly.
        if (!prefill && slug.value === '') {
            prefill = true;
        }
        const urlified = URLify(value, SLUG_MAX_CHARS);
        if (prefill) {
            slug.value = urlified;
        }
    };

    const markChanged = (event: Event): void => {
        const target = event.target;
        if (target instanceof HTMLElement) {
            target.dataset.changed = 'true';
        }
    };

    title.addEventListener('input', updateSlug);
    slug.addEventListener('change', markChanged);
    title.addEventListener('change', markChanged);

    // Auto-run once so a pre-filled title (e.g. after a server-side
    // validation error re-renders the form) populates the slug on load.
    updateSlug();

    return {
        destroy() {
            title.removeEventListener('input', updateSlug);
            slug.removeEventListener('change', markChanged);
            title.removeEventListener('change', markChanged);
        },
    };
}
