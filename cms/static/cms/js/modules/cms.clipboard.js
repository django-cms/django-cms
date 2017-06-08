/*
 * Copyright https://github.com/divio/django-cms
 */

import Modal from './cms.modal';
var $ = require('jquery');
var Class = require('classjs');
var Helpers = require('./cms.base').default.API.Helpers;
var storageKey = 'cms.clipboard';
var Plugin = require('./cms.plugins').default;

var MIN_WIDTH = 400;
// FIXME kind of a magic number for 1 item in clipboard
var MIN_HEIGHT = 117;


/**
 * Handles copy & paste in the structureboard.
 *
 * @class Clipboard
 * @namespace CMS
 * @uses CMS.API.Helpers
 */
var Clipboard = new Class({

    implement: [Helpers],

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

        that.modal = new Modal({
            minWidth: MIN_WIDTH,
            minHeight: MIN_HEIGHT,
            minimizable: false,
            maximizable: false,
            resizable: false,
            closeOnEsc: false
        });

        that.modal.on('cms.modal.loaded cms.modal.closed', function removePlaceholder() {
            // cannot be cached
            $('.cms-add-plugin-placeholder').remove();
        }).on('cms.modal.closed cms.modal.load', function () {
            that.ui.pluginsList.prependTo(that.ui.clipboard);
        }).ui.modal.on('cms.modal.load', function () {
            that.ui.pluginsList.prependTo(that.ui.clipboard);
        });

        Helpers._getWindow().addEventListener('storage', function (e) {
            if (e.key === storageKey) {
                that._handleExternalUpdate(e);
            }
        });

        this._toolbarEvents();
    },

    _toolbarEvents() {
        var that = this;

        that.ui.triggers.off(that.click).on(that.click, function (e) {
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
        that.ui.triggerRemove.off(that.click).on(that.click, function (e) {
            e.preventDefault();
            e.stopPropagation();
            if ($(this).parent().hasClass('cms-toolbar-item-navigation-disabled')) {
                return false;
            }
            that.clear();
        });

    },

    /**
     * _handleExternalUpdate
     *
     * @private
     * @param {StorageEvent} e event
     */
    _handleExternalUpdate: function _handleExternalUpdate(e) {
        var that = this;
        var clipboardData = JSON.parse(e.newValue);

        if (clipboardData.timestamp < that.currentClipboardData.timestamp ||
            that.currentClipboardData.data.plugin_id === clipboardData.data.plugin_id) {
            that.currentClipboardData = clipboardData;
            return;
        }

        if (!clipboardData.data.plugin_id) {
            that._cleanupDOM();
            that.currentClipboardData = clipboardData;
            return;
        }

        if (!that.currentClipboardData.data.plugin_id) {
            that._enableTriggers();
        }

        that.ui.pluginsList.html(clipboardData.html);
        Plugin._updateClipboard();
        new Plugin('cms-plugin-' + clipboardData.data.plugin_id, clipboardData.data);

        that.currentClipboardData = clipboardData;
    },

    /**
     * @method _isClipboardModalOpen
     * @private
     * @returns {Boolean}
     */
    _isClipboardModalOpen: function _isClipboardModalOpen() {
        return !!this.modal.ui.modalBody.find('.cms-clipboard-containers').length;
    },

    /**
     * Cleans up DOM state when clipboard is cleared
     *
     * @method _cleanupDOM
     * @private
     */
    _cleanupDOM: function _cleanupDOM() {
        var that = this;
        var pasteItems = $('.cms-submenu-item [data-rel=paste]').attr('tabindex', '-1').parent()
            .addClass('cms-submenu-item-disabled');

        pasteItems.find('> a').attr('aria-disabled', 'true');
        pasteItems.find('.cms-submenu-item-paste-tooltip').css('display', 'none');
        pasteItems.find('.cms-submenu-item-paste-tooltip-empty').css('display', 'block');

        if (that._isClipboardModalOpen()) {
            that.modal.close();
        }

        that._disableTriggers();
        that.ui.document.trigger('click.cms.toolbar');
    },

    /**
     * @method _enableTriggers
     * @private
     */
    _enableTriggers: function _enableTriggers() {
        this.ui.triggers.parent().removeClass('cms-toolbar-item-navigation-disabled');
        this.ui.triggerRemove.parent().removeClass('cms-toolbar-item-navigation-disabled');
    },

    /**
     * @method _disableTriggers
     * @private
     */
    _disableTriggers: function _disableTriggers() {
        this.ui.triggers.parent().addClass('cms-toolbar-item-navigation-disabled');
        this.ui.triggerRemove.parent().addClass('cms-toolbar-item-navigation-disabled');
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
        var that = this;
        // post needs to be a string, it will be converted using JSON.parse
        var post = '{ "csrfmiddlewaretoken": "' + CMS.config.csrf + '" }';

        that._cleanupDOM();

        // redirect to ajax
        CMS.API.Toolbar.openAjax({
            url: Helpers.updateUrlWithPath(CMS.config.clipboard.url),
            post: post,
            callback: function () {
                var args = Array.prototype.slice.call(arguments);

                that.populate('', {});
                // istanbul ignore next
                if (callback) {
                    callback.apply(this, args);
                }
            }
        });
    },

    /**
     * populate
     *
     * @public
     * @param {String} html markup of the clipboard draggable
     * @param {Object} pluginData data of the plugin in the clipboard
     */
    populate: function (html, pluginData) {
        this.currentClipboardData = {
            data: pluginData,
            timestamp: Date.now(),
            html: html
        };

        if (Helpers._isStorageSupported) {
            localStorage.setItem(storageKey, JSON.stringify(this.currentClipboardData));
        }
    }
});

export default Clipboard;
