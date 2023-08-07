var $ = require('jquery');

module.exports = function addSlugHandlers(title, slug) {
    if (!slug.length) {
        return;
    }

    // set local variables
    var prefill = false;

    // determine if slug is empty
    if (slug.val().trim() === '') {
        prefill = true;
    }
    if (window.unihandecode) {
        // eslint-disable-next-line new-cap
        window.UNIHANDECODER = window.unihandecode.Unihan(slug.data('decoder'));
    }

    // always bind the title > slug generation and do the validation inside for better ux
    title.on('keyup keypress', function() {
        var value = title.val();

        // international language handling
        if (window.UNIHANDECODER) {
            value = window.UNIHANDECODER.decode(value);
        }
        // if slug is empty, prefill again
        if (prefill === false && slug.val() === '') {
            prefill = true;
        }
        // urlify
        // eslint-disable-next-line
        var urlified = URLify(value, 64);
        if (prefill) {
            slug.val(urlified);
        }
    });
    // autocall
    title.trigger('keyup');

    // add changed data bindings to elements
    slug.add(title).bind('change', function() {
        $(this).data('changed', true);
    });
};
