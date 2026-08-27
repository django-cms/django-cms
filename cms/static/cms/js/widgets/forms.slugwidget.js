/*
 * Copyright https://github.com/divio/django-cms
 */

// this essentially makes sure that dynamically required bundles are loaded
// from the same place
// eslint-disable-next-line
__webpack_public_path__ = require('../modules/get-dist-path')('bundle.forms.slugwidget');

/**
 * Finds the title field belonging to a slug field. Form fields can be prefixed
 * (``id_1-slug`` in the wizard, ``id_content__slug`` in grouper admins), so the
 * title is looked up by the slug's own id first and only then guessed.
 *
 * @function findTitle
 * @param {HTMLElement} slug slug input element
 * @returns {HTMLElement|null} matching title input element
 */
function findTitle(slug) {
    var derivedId = slug.id.replace(/slug$/, 'title');

    if (derivedId !== slug.id) {
        var derived = document.getElementById(derivedId);

        if (derived) {
            return derived;
        }
    }
    return document.querySelector('[id$=title]') || document.querySelector('[id*=title]');
}

require.ensure([], function (require) {
    var $ = require('jquery');
    var addSlugHandlers = require('../modules/slug').default;

    // init
    $(function () {
        // set local variables
        var slug = document.querySelector('[id$=slug]') || document.querySelector('[id*=slug]');

        if (!slug) {
            return;
        }

        addSlugHandlers($(findTitle(slug)), $(slug));
    });
}, 'admin.widget');
