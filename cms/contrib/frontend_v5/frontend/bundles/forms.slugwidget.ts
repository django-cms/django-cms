/*
 * Entry point for the forms.slugwidget bundle.
 *
 * Drop-in replacement for the legacy bundle.forms.slugwidget.min.js.
 * Name and output path MUST match legacy exactly — see the contract
 * comment at the top of webpack.config.js and CLAUDE.md decision 1.
 *
 * The legacy bundle used a plain DOMContentLoaded listener to locate
 * the title + slug inputs by id-substring match. We preserve that
 * selector — it's part of the implicit contract between the JS and
 * Django's form-rendering conventions (page_form title/slug fields).
 */

import { addSlugHandlers } from '../modules/slug';

function init(): void {
    const title = document.querySelector<HTMLInputElement>('[id*=title]');
    const slug = document.querySelector<HTMLInputElement>('[id*=slug]');
    addSlugHandlers(title, slug);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
} else {
    init();
}
