/*
 * Copyright https://github.com/divio/django-cms
 */

// #############################################################################
// NAMESPACES
/**
 * @module CMS
 */
var CMS = window.CMS || {};

// #############################################################################
// MODAL
(function ($) {
    'use strict';

    // shorthand for jQuery(document).ready();
    $(function () {
        /**
         * Adds internal methods for the creation wizard.
         *
         * @class Wizards
         * @namespace CMS
         */
        CMS.Wizards = {

            _choice: function initialize() {
                // set active element when making a choice
                var form = $('form');
                var choices = $('.choice');
                choices.on('click', function (e) {
                    choices.removeClass('active')
                        .eq(choices.index(e.currentTarget))
                        .addClass('active');
                });
                // submit the form on double click
                choices.on('dblclick', function () {
                    form.submit();
                });

                // focus window so hitting "enter" doesnt trigger a refresh
                $(window).focus();
            }

        };

        // directly initialize required methods
        if ($('.choice').length) {
            CMS.Wizards._choice();
        }

    });
})(CMS.$);
