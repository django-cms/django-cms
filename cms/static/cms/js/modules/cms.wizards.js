//##############################################################################
// WIZARDS

/* global CMS */
(function ($) {
    'use strict';
    // CMS.$ will be passed for $
    $(function () {
        // set active element when making a choice
        var choices = $('.choice');
        choices.on('click', function (e) {
            choices.removeClass('active')
                .eq(choices.index(e.currentTarget))
                .addClass('active');
        });

        // focus window so hitting "enter" doesnt trigger a refresh
        $(window).focus();
    });
})(CMS.$);
