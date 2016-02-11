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
        /**
         * Handles copy & paste in the structureboard.
         *
         * @class Clipboard
         * @namespace CMS
         * @uses CMS.API.Helpers
         */
        CMS.Clipboard = new CMS.Class({

            implement: [CMS.API.Helpers],

            initialize: function () {
                this._setupUI();

                // states
                this.click = 'click.cms.clipboard';

                // setup events
                this._events();
            },

            /**
             * Caches all the jQuery element queries.
             *
             * @method _setupUI
             * @private
             */
            _setupUI: function _setupUI() {
                var clipboard = $('.cms-clipboard');
                this.ui = {
                    clipboard: clipboard,
                    triggers: $('.cms-clipboard-trigger a'),
                    triggerRemove: $('.cms-clipboard-empty a'),
                    pluginsList: clipboard.find('.cms-clipboard-containers'),
                    document: $(document)
                };
            },

            /**
             * Sets up event handlers for clipboard ui.
             *
             * @method _events
             * @private
             */
            _events: function () {
                var that = this;

                var MIN_WIDTH = 400;
                // FIXME kind of a magic number for 1 item in clipboard
                var MIN_HEIGHT = 117;

                that.modal = new CMS.Modal({
                    minWidth: MIN_WIDTH,
                    minHeight: MIN_HEIGHT,
                    minimizable: false,
                    maximizable: false,
                    resizable: false
                });

                that.modal.on('cms.modal.loaded cms.modal.closed', function removePlaceholder() {
                    // cannot be cached
                    $('.cms-add-plugin-placeholder').remove();
                }).on('cms.modal.closed cms.modal.load', function () {
                    that.ui.pluginsList.prependTo(that.ui.clipboard);
                }).ui.modal.on('cms.modal.load', function () {
                    that.ui.pluginsList.prependTo(that.ui.clipboard);
                });

                that.ui.triggers.on(that.click, function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    if ($(this).parent().hasClass('cms-toolbar-item-navigation-disabled')) {
                        return false;
                    }

                    that.modal.open({
                        html: that.ui.pluginsList,
                        title: that.ui.clipboard.data('title'),
                        width: MIN_WIDTH,
                        height: MIN_HEIGHT
                    });
                    that.ui.document.trigger('click.cms.toolbar');
                });

                // add remove event
                that.ui.triggerRemove.on(that.click, function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    if ($(this).parent().hasClass('cms-toolbar-item-navigation-disabled')) {
                        return false;
                    }
                    that.clear(function () {
                        // remove element on success
                        that.modal.close();
                        that.ui.triggers.parent().addClass('cms-toolbar-item-navigation-disabled');
                        that.ui.triggerRemove.parent().addClass('cms-toolbar-item-navigation-disabled');
                        that.ui.document.trigger('click.cms.toolbar');
                    });
                });
            },

            /**
             * Clears the clipboard by quering the server.
             * Callback is optional, but if provided - it's called
             * no matter what outcome was of the ajax call.
             *
             * @method clear
             * @param {Function} [callback]
             */
            clear: function (callback) {
                // post needs to be a string, it will be converted using JSON.parse
                var post = '{ "csrfmiddlewaretoken": "' + CMS.config.csrf + '" }';
                var pasteItems = $('.cms-submenu-item [data-rel=paste]').parent().
                    addClass('cms-submenu-item-disabled');
                pasteItems.find('.cms-submenu-item-paste-tooltip').css('display', 'none');
                pasteItems.find('.cms-submenu-item-paste-tooltip-empty').css('display', 'block');

                // redirect to ajax
                CMS.API.Toolbar.openAjax({
                    url: CMS.config.clipboard.url,
                    post: post,
                    callback: callback
                });
            }

        });

    });
})(CMS.$);
