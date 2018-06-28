/*
 * Copyright (c) 2013, Divio AG
 */

// #############################################################################
// NAMESPACES
/**
 * @module Cl
 */
var Cl = window.Cl || {};

(function ($) {
    'use strict';

    Cl.Back = new Class({
        options: {
            linkClass: '.js-back-link',
            originalDomain: ''
        },

        initialize: function (options) {
            this.options = $.extend({}, this.options, options);

            this._bindEvents();
        },

        _bindEvents: function () {
            var that = this;

            $(document).on('click', this.options.linkClass, function (e) {
                e.preventDefault();
                that._historyBack($(this));
            });
        },

        _historyBack: function (link) {
            if (window.history.length > 1 && document.referrer.indexOf(this.options.originalDomain) !== -1) {
                window.history.back();
            } else {
                window.location.href = link.data('default');
            }
        }
    });
})(jQuery);
