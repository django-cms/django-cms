/*
 * Copyright https://github.com/divio/django-cms
 */

// this essentially makes sure that dynamically required bundles are loaded
// from the same place
// eslint-disable-next-line
__webpack_public_path__ = require('../modules/get-dist-path')('bundle.forms.slugwidget');

require.ensure([], function (require) {
    var $ = require('jquery');
    var addSlugHandlers = require('../modules/slug');

    // init
    $(function () {
        // set local variables
        var title = $('[id*=title]');
        var slug = $('[id*=slug]');

        addSlugHandlers(title, slug);
    });
}, 'admin.widget');
