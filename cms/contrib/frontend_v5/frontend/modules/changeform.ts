/*
 * Page change-form enhancements.
 *
 * Port of the legacy `cms/static/cms/js/modules/cms.changeform.js`.
 * Wires five behaviors on Django's admin "change page" form:
 *
 *   1. Title → slug auto-fill (delegates to the ported `slug` module).
 *   2. Lazy-load `<div class="loading" rel="…">` partials via fetch +
 *      DOMParser. Used for the Permissions and Page States sections,
 *      which the form renders as empty stubs and fills async.
 *   3. Hide `.form-row` elements that contain only a hidden input.
 *   4. Wire click handlers on the language tab buttons to call the
 *      `CMS.API.changeLanguage()` public API.
 *   5. Expose `CMS.API.changeLanguage()` on `window.CMS.API`. This is
 *      a public API — the inline script in
 *      `admin/cms/page/change_form.html` calls it directly.
 *
 * Semantics preserved exactly from the legacy implementation. The only
 * changes are:
 *   - Legacy's `textContent = ''; while (firstChild) appendChild()`
 *     lazy-load dance is replaced with the modern one-liner
 *     `replaceChildren(…)`. Same effect.
 *   - Fetch errors no longer fail silently into a dead stub — they're
 *     caught so the rest of init continues. Legacy would leave a
 *     hanging unresolved promise on network failure; ours just logs
 *     to console and moves on.
 *   - A `destroy()` handle is returned so tests (and any future SPA
 *     teardown path) can cleanly unwind listeners.
 */

import { addSlugHandlers, type SlugHandlerHandle } from './slug';

export interface ChangeFormHandle {
    destroy(): void;
}

export function initChangeForm(): ChangeFormHandle {
    const title = document.getElementById('id_title') as HTMLInputElement | null;
    const slug = document.getElementById('id_slug') as HTMLInputElement | null;

    const slugHandle: SlugHandlerHandle = addSlugHandlers(title, slug);

    // ---- Lazy-load permissions / page-state partials ----
    // Each `<div class="loading" rel="/some/url">` gets its body replaced
    // with the HTML returned by fetching the URL. Errors are swallowed
    // (console.error) so a single broken partial doesn't break the form.
    for (const div of Array.from(document.querySelectorAll<HTMLElement>('div.loading'))) {
        const rel = div.getAttribute('rel');
        if (!rel) continue;
        fetch(rel)
            .then((response) => response.text())
            .then((html) => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                div.replaceChildren(...Array.from(doc.body.childNodes));
            })
            .catch((err) => {
                // eslint-disable-next-line no-console
                console.error('changeform: failed to lazy-load partial', rel, err);
            });
    }

    // ---- Hide form rows wrapping dynamically-hidden fields ----
    // This step is NOT about hiding already-invisible `<input type="hidden">`
    // elements — those are invisible by definition. It's about hiding the
    // `<div class="form-row">` WRAPPER around them.
    //
    // Normal Django admin handles hidden fields correctly: fields declared
    // with `widget=HiddenInput` from the start are rendered via
    // `form.hidden_fields()` outside the fieldset iteration, without a
    // `.form-row` wrapper, so no visual row appears.
    //
    // BUT the CMS grouper admin in `cms/admin/utils.py` swaps certain
    // grouping fields (typically `language`, possibly `site`) to
    // `HiddenInput` *after* the form class is built — see
    // `GrouperAdminMixin.get_form`, around the `extra_grouping_fields`
    // loop. Those fields stay in the visible fieldset spec, so Django
    // wraps them in `.form-row` during iteration without knowing the
    // widget is now hidden. The result: empty rows with vertical
    // spacing where the grouper fields "should be".
    //
    // This loop hides those empty rows at DOMContentLoaded. It's a
    // workaround for the post-hoc widget swap, not a general feature;
    // the proper fix would be to declare the grouper fields as hidden
    // from the start (Python side) so Django's standard handling kicks
    // in. Until that's done, this JS cleanup is load-bearing — removing
    // it produces visible layout gaps on the advanced settings form.
    for (const input of Array.from(
        document.querySelectorAll<HTMLInputElement>('input[type="hidden"]'),
    )) {
        const row = input.closest<HTMLElement>('.form-row');
        if (row) row.style.display = 'none';
    }

    // ---- Language tab click handlers ----
    // Each button's `data-admin-url` carries the URL for that language.
    // We route the click through `CMS.API.changeLanguage` (which we
    // define below) so the dirty-state check runs uniformly whether
    // the user clicked a tab or called the API directly.
    const languageButtonTeardowns: Array<() => void> = [];
    for (const btn of Array.from(
        document.querySelectorAll<HTMLElement>('#page_form_lang_tabs .language_button'),
    )) {
        const handler = (): void => {
            const url = btn.dataset.adminUrl;
            if (url) {
                window.CMS?.API?.changeLanguage?.(url);
            }
        };
        btn.addEventListener('click', handler);
        languageButtonTeardowns.push(() => btn.removeEventListener('click', handler));
    }

    // ---- Public API: CMS.API.changeLanguage ----
    // Closes over the title/slug elements found at init time. Matches
    // the legacy closure behavior exactly: if the form's title/slug
    // elements are later replaced (they aren't in practice, but in
    // principle), the closure keeps referencing the originals.
    const changeLanguage = (url: string): void => {
        let changed = false;
        if (slug) {
            const slugDirty = slug.dataset.changed === 'true';
            const titleDirty = title?.dataset.changed === 'true';
            if (slugDirty || titleDirty) changed = true;
        }

        let answer = true;
        if (changed) {
            const fallback =
                'Are you sure you want to change tabs without saving the page first?';
            const question = typeof gettext === 'function' ? gettext(fallback) : fallback;
            // eslint-disable-next-line no-alert
            answer = confirm(question);
        }

        if (answer) {
            window.location.href = url;
        }
    };

    // Attach to window.CMS.API without clobbering anything else that
    // may have attached methods earlier (e.g. if admin.base loaded
    // first and set up its own API surface). Preserves existing keys.
    window.CMS = window.CMS ?? {};
    window.CMS.API = window.CMS.API ?? {};
    window.CMS.API.changeLanguage = changeLanguage;

    return {
        destroy() {
            slugHandle.destroy();
            for (const teardown of languageButtonTeardowns) {
                teardown();
            }
            // Leave CMS.API.changeLanguage in place — third-party code
            // may still hold a reference to it. Removing it on destroy
            // would be a surprising regression vs the legacy code,
            // which never cleaned up at all.
        },
    };
}
