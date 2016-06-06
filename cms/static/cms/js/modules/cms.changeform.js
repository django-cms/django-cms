/* global CMS, URLify, gettext */
var $ = require('jquery');

$(function () {

    // set local variables
    var title = $('#id_title');
    var slug = $('#id_slug');
    var changed = false;
    var prefill = false;

    // hide rows when hidden input fields are added
    $('input[type="hidden"]').each(function () {
        $(this).parent('.form-row').hide();
    });

    // determine if slug is empty
    if (slug.val() === '') {
        prefill = true;
    }

    // always bind the title > slug generation and do the validation inside for better ux
    title.bind('keyup', function () {
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

    // set focus to title
    title.focus();

    // all permissions and page states loader
    $('div.loading').each(function () {
        $(this).load($(this).attr('rel'));
    });

    // add changed data bindings to elements
    slug.add(title).bind('change', function () {
        $(this).data('changed', true);
    });

    // public api for changing the language tabs
    // used in admin/cms/page/change_form.html
    window.CMS.API.changeLanguage = function (url) {
        // also make sure that we will display the confirm dialog
        // in case users switch tabs while editing plugins
        var answer = true;

        if (slug.length) {
            // check if the slug has the changed attribute
            if (slug.data('changed') || title.data('changed')) {
                changed = true;
            }
        }

        if (changed) {
            var question = gettext('Are you sure you want to change tabs without saving the page first?');

            // eslint-disable-next-line no-alert
            answer = confirm(question);
        }
        if (answer) {
            window.location.href = url;
        }
    };

});
