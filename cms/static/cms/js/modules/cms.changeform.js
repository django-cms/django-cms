/* global CMS, gettext */
import $ from 'jquery';
import addSlugHandlers from './slug';

$(function() {
    // set local variables
    var title = $('#id_title');
    var slug = $('#id_slug');

    addSlugHandlers(title, slug);

    // all permissions and page states loader
    $('div.loading').each(function() {
        $(this).load($(this).attr('rel'));
    });

    // hide rows when hidden input fields are added
    $('input[type="hidden"]').each(function() {
        $(this).parent('.form-row').hide();
    });

    // public api for changing the language tabs
    // used in admin/cms/page/change_form.html
    window.CMS.API.changeLanguage = function(url) {
        // also make sure that we will display the confirm dialog
        // in case users switch tabs while editing plugins
        var answer = true;
        var changed = false;

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
