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
// PAGE SMART LINK WIDGET
// cms/forms/widgets.py used for redirects in admin/cms/page/advanced-settings
(function ($) {
    'use strict';

    // shorthand for jQuery(document).ready();
    $(function () {
        /**
         * Creates a select field using jquery.select2 to filter through
         * available pages or set a custom url.
         *
         * @class PageSmartLinkWidget
         * @namespace CMS
         */
        CMS.PageSmartLinkWidget = new CMS.Class({

            initialize: function initialize(options) {
                this.options = $.extend(true, {}, this.options, options);
                // load functionality
                this._setup(options);
            },

            /**
             * Setup internal functions and events.
             *
             * @private
             * @method _setup
             */
            _setup: function _setup(options) {
                $('#' + options.id).select2({
                    placeholder: options.text,
                    allowClear: true,
                    multiple: false,
                    ajax: {
                        url: options.url,
                        dataType: 'json',
                        data: function (term) {
                            return {
                                q: term,
                                language_code: options.lang
                            };
                        },
                        // default search output, will be overridden if no results map
                        results: function (data) {
                            return {
                                more: false,
                                results: $.map(data, function (item) {
                                    return {
                                        id: item.redirect_url,
                                        text: item.title + ' (/' + item.path + ')'
                                    };
                                })
                            };
                        }
                    },
                    // create fallback entry if no choices are found
                    createSearchChoice: function (term, data) {
                        if ($(data).filter(
                            function () {
                                return this.text.localeCompare(term) === 0;
                            }).length === 0
                        ) {
                            return {
                                id: term,
                                text: term
                            };
                        }
                    },
                    // ensures initial selection is loaded
                    initSelection: function (element, callback) {
                        callback({
                            id: element.val(),
                            text: element.val()
                        });
                    }
                });
            }
        });

    });
})(CMS.$);
