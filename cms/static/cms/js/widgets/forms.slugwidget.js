/*
 * Copyright https://github.com/django-cms/django-cms
 */


import addSlugHandlers from '../modules/slug';

/**
 * Finds the title field belonging to a slug field. Form fields can be prefixed
 * (``id_1-slug`` in the wizard, ``id_content__slug`` in grouper admins), so the
 * title is looked up by the slug's own id first and only then guessed.
 */
function findTitle(slug) {
    const derivedId = slug.id.replace(/slug$/, 'title');

    if (derivedId !== slug.id) {
        const derived = document.getElementById(derivedId);

        if (derived) {
            return derived;
        }
    }
    return document.querySelector('[id$=title]') || document.querySelector('[id*=title]');
}

document.addEventListener('DOMContentLoaded', function () {
    // set local variables
    const slug = document.querySelector('[id$=slug]') || document.querySelector('[id*=slug]');

    if (!slug) {
        return;
    }

    addSlugHandlers(findTitle(slug), slug);
});
