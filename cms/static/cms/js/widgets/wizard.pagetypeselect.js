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
// PAGE TYPE SELECT
(function ($) {
    'use strict';

    // shorthand for jQuery(document).ready();
    $(function () {

        var pageTypeField = $('.form-row.source select');
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

    });
})(CMS.$);
