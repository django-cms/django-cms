//##############################################################################
// PAGE WIZARD

/* global CMS */
(function ($) {
    'use strict';
    // CMS.$ will be passed for $
    $(document).ready(function () {

        var pageTypeField = $('.form-row.page_type select'),
            contentGroup = $('.form-row.content'),
            contentField = contentGroup.find('textarea');

        // Show it if we change to an app_hook that requires a namespace
        pageTypeField.on('change', function () {
            if ($(this).val()){
                contentGroup.hide();
                contentField.prop('disabled', true);
            }
            else {
                contentGroup.show();
                contentField.removeProp('disabled');
            }
        });
    });
})(CMS.$);
