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
         * This script adds internal methods for various UI components to the
         * wizard through the "Create" button on the toolbar.
         *
         * @class Wizards
         * @namespace CMS
         */
        CMS.Wizards = {

            _choice: function initialize() {
                // set active element when making a choice
                var choices = $('.choice');
                choices.on('click', function (e) {
                    choices.removeClass('active')
                        .eq(choices.index(e.currentTarget))
                        .addClass('active');
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
