/*
 * Copyright https://github.com/django-cms/django-cms
 */


import addSlugHandlers from '../modules/slug';

document.addEventListener('DOMContentLoaded', function () {
    // set local variables
    const title = document.querySelector('[id*=title]');
    const slug = document.querySelector('[id*=slug]');

    addSlugHandlers(title, slug);
});
