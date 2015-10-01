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
// Clipboard
(function ($) {
    'use strict';

    // shorthand for jQuery(document).ready();
    $(function () {
        /*!
         * Clipboard
         * Handles copy & paste
         */
        CMS.Clipboard = new CMS.Class({

            implement: [CMS.API.Helpers],

            options: {
                position: 220, // offset to top
                speed: 100,
                id: null,
                url: ''
            },

            initialize: function (options) {
                this.clipboard = $('.cms-clipboard');
                this.options = $.extend(true, {}, this.options, options);
                this.config = CMS.config;
                this.settings = CMS.settings;

                // elements
                this.containers = this.clipboard.find('.cms-clipboard-containers > .cms-draggable');
                this.triggers = $('.cms-clipboard-trigger a');
                this.triggerRemove = $('.cms-clipboard-empty a');

                // states
                this.click = 'click.cms.clipboard';

                // setup initial stuff
                this._setup();

                // setup events
                this._events();
            },

            // initial methods
            _setup: function () {
                var that = this;

                // FIXME kind of a magic number for 1 item in clipboard
                var minHeight = 117;
                var pluginsList = this.clipboard.find('.cms-clipboard-containers');
                var modal = new CMS.Modal({
                    minWidth: 400,
                    minHeight: minHeight,
                    minimizable: false,
                    maximizable: false,
                    resizable: false
                });

                modal.on('cms.modal.loaded cms.modal.closed', function removePlaceholder() {
                    $('.cms-add-plugin-placeholder').remove();
                }).on('cms.modal.closed cms.modal.load', function () {
                    pluginsList.prependTo(that.clipboard);
                }).ui.modal.on('cms.modal.load', function () {
                    pluginsList.prependTo(that.clipboard);
                });

                this.triggers.on(this.click, function (e) {
                    e.preventDefault();
                    if ($(this).parent().hasClass('cms-toolbar-item-navigation-disabled')) {
                        return false;
                    }

                    modal.open({
                        html: pluginsList,
                        title: that.clipboard.data('title'),
                        width: 400,
                        height: minHeight
                    });
                });
            },

            _events: function () {
                var that = this;

                // add remove event
                this.triggerRemove.on(this.click, function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    if ($(this).parent().hasClass('cms-toolbar-item-navigation-disabled')) {
                        return false;
                    }
                    that.clear(function () {
                        // remove element on success
                        that.clipboard.hide();
                        that.triggers.parent().addClass('cms-toolbar-item-navigation-disabled');
                        that.triggerRemove.parent().addClass('cms-toolbar-item-navigation-disabled');
                    });
                });
            },

            // public methods
            clear: function (callback) {
                // post needs to be a string, it will be converted using JSON.parse
                var post = '{ "csrfmiddlewaretoken": "' + this.config.csrf + '" }';
                // redirect to ajax
                CMS.API.Toolbar.openAjax({
                    url: this.config.clipboard.url,
                    post: post,
                    callback: callback
                });
            }

        });

    });
})(CMS.$);
