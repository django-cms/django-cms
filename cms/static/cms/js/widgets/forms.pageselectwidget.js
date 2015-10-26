/*
 * Copyright https://github.com/divio/django-cms
 */

// #############################################################################
// NAMESPACES
var django = window.django || {};

// #############################################################################
// PAGE SELECT WIDGET
// cms/forms/widgets.py
(function ($) {
    'use strict';

    // shorthand for jQuery(document).ready();
    $(function () {

        var options = window._PageSelectWidget;
        var group0 = $('#id_' + options.name + '_0');
        var group1 = $('#id_' + options.name + '_1');
        var group2 = $('#id_' + options.name + '_2');
        var tmp;

        // handles the change event on the first select "site"
        // that controls the display of the second select "pagetree"
        group0.on('change', function () {
            tmp = $(this).children(':selected').text();

            group1.find('optgroup').remove();
            group1.append(
                group2.find('optgroup[label="' + tmp + '"]').clone()
            ).change();

            // refresh second select
            setTimeout(function () {
                group1.trigger('change');
            }, 0);
        }).trigger('change');

        // sets the correct value
        group1.on('change', function () {
            tmp = $(this).find('option:selected').val();

            if (tmp) {
                group2.find('option').attr('selected', false);
                group2.find('option[value="' + tmp + '"]').attr('selected', true);
            } else if (group2.length) {
                group2.find('option[value=""]').attr('selected', true);
            }
        });

        // don't allow to add another page from in here
        $('#add_id_' + options.name).hide();

    });
})(django.jQuery);
