//##############################################################################
// PAGE TYPE WIDGET

/* global CMS */
(function ($) {
    'use strict';
    // CMS.$ will be passed for $
    $(function () {

        var pageTypeField = $('.form-row.page_type select'),
            contentGroup = $('.form-row.content'),
            contentField = contentGroup.find('textarea');

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
