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
// CMS_FRAME
(function ($) {
    'use strict';

    // shorthand for jQuery(document).ready();
    $(function () {
        /**
         * The cms_frame is triggered via API calls from the backend either
         * through the toolbar navigation or from plugins. The APIs only allow
         * to open a url within the cms_frame.
         *
         * @class CMSFrame
         * @namespace CMS
         * @uses CMS.API.Helpers
         */
        CMS.CMSFrame = new CMS.Class({

            implement: [CMS.API.Helpers],

            options: {
            },

            initialize: function initialize(options) {
                this.options = $.extend(true, {}, this.options, options);
            },

            /**
             * Opens a given url within a new, named tab (hopefully).
             *
             * @method open
             * @chainable
             * @param opts
             * @param opts.url {String} url to render in the new window/tab
             */
            open: function open(opts) {
                if (!(opts && opts.url)) {
                    throw new Error('The CMSFrame.open method requires a url.');
                }

                var url = opts.url;

                var win = window.open(url, 'cms_frame');
                win.focus();
                return this;
            }
        });
    });
})(CMS.$);
