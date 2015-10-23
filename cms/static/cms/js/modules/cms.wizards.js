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

            _choice: function initialize(options) {
                // set active element when making a choice
                var choices = $('.choice');
                choices.on('click', function (e) {
                    choices.removeClass('active')
                        .eq(choices.index(e.currentTarget))
                        .addClass('active');
                });

                // focus window so hitting "enter" doesnt trigger a refresh
                $(window).focus();
            },

            _pageTypeSelect: function () {
                var pageTypeField = $('.form-row.page_type select');
                var contentGroup = $('.form-row.content');
                var contentField = contentGroup.find('textarea');

                pageTypeField.on('change', function () {
                    if ($(this).val()) {
                        contentGroup.hide();
                        contentField.prop('disabled', true);
                    } else {
                        contentGroup.show();
                        contentField.prop('disabled', false);
                    }
                });
            }

        };

        // directly initialize required methods
        if ($('.choice').length) {
            CMS.Wizards._choice();
        }
        if ($('.form-row.page_type select').length) {
            CMS.Wizards._pageTypeSelect();
        }

    });
})(CMS.$);
