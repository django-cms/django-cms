/*
 * Copyright https://github.com/divio/django-cms
 */

import Modal from './cms.modal';
import $ from 'jquery';
import { Helpers } from './cms.base';
import Plugin from './cms.plugins';
import ls from 'local-storage';
var storageKey = 'cms-clipboard';

var MIN_WIDTH = 400;
// magic number for 1 item in clipboard
var MIN_HEIGHT = 117;

/**
 * Handles copy & paste in the structureboard.
 *
 * @class Clipboard
 * @namespace CMS
 * @uses CMS.API.Helpers
 */
class Clipboard {
    constructor() {
        this._setupUI();

        // setup events
        this._events();
        this.currentClipboardData = {};
    }

    /**
     * Caches all the jQuery element queries.
     *
     * @method _setupUI
     * @private
     */
    _setupUI() {
        var clipboard = $('.cms-clipboard');

        this.ui = {
            clipboard: clipboard,
            triggers: $('.cms-clipboard-trigger a'),
            triggerRemove: $('.cms-clipboard-empty a'),
            pluginsList: clipboard.find('.cms-clipboard-containers'),
            document: $(document)
        };
    }

    /**
     * Sets up event handlers for clipboard ui.
     *
     * @method _events
     * @private
     */
    _events() {
        var that = this;

        that.modal = new Modal({
            minWidth: MIN_WIDTH,
            minHeight: MIN_HEIGHT,
            minimizable: false,
            maximizable: false,
            resizable: false,
            closeOnEsc: false
        });

        Helpers.removeEventListener(
            'modal-loaded.clipboard modal-closed.clipboard modal-close.clipboard modal-load.clipboard'
        );

        Helpers.addEventListener('modal-loaded.clipboard modal-closed.clipboard', (e, { instance }) => {
            if (instance === this.modal) {
                Plugin._removeAddPluginPlaceholder();
            }
        });

        Helpers.addEventListener('modal-close.clipboard', (e, { instance }) => {
            if (instance === this.modal) {
                this.ui.pluginsList.prependTo(that.ui.clipboard);
                Plugin._updateClipboard();
            }
        });
        Helpers.addEventListener('modal-load.clipboard', (e, { instance }) => {
            if (instance === this.modal) {
                this.ui.pluginsList.prependTo(that.ui.clipboard);
            } else {
                this.ui.pluginsList.prependTo(that.ui.clipboard);
                Plugin._updateClipboard();
            }
        });

        try {
            ls.off(storageKey);
        } catch (e) {}
        ls.on(storageKey, value => this._handleExternalUpdate(value));

        this._toolbarEvents();
    }

    _toolbarEvents() {
        var that = this;

        that.ui.triggers.off(Clipboard.click).on(Clipboard.click, function(e) {
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
        that.ui.triggerRemove.off(Clipboard.click).on(Clipboard.click, function(e) {
            e.preventDefault();
            e.stopPropagation();
            if ($(this).parent().hasClass('cms-toolbar-item-navigation-disabled')) {
                return false;
            }
            that.clear();
        });
    }

    /**
     * _handleExternalUpdate
     *
     * @private
     * @param {String} value event new value
     */
    _handleExternalUpdate(value) {
        var that = this;
        var clipboardData = JSON.parse(value);

        if (
            clipboardData.timestamp < that.currentClipboardData.timestamp ||
            (that.currentClipboardData.data &&
                that.currentClipboardData.data.plugin_id === clipboardData.data.plugin_id)
        ) {
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
        CMS._instances.push(new Plugin(`cms-plugin-${clipboardData.data.plugin_id}`, clipboardData.data));

        that.currentClipboardData = clipboardData;
    }

    /**
     * @method _isClipboardModalOpen
     * @private
     * @returns {Boolean}
     */
    _isClipboardModalOpen() {
        return !!this.modal.ui.modalBody.find('.cms-clipboard-containers').length;
    }

    /**
     * Cleans up DOM state when clipboard is cleared
     *
     * @method _cleanupDOM
     * @private
     */
    _cleanupDOM() {
        var that = this;
        var pasteItems = $('.cms-submenu-item [data-rel=paste]')
            .attr('tabindex', '-1')
            .parent()
            .addClass('cms-submenu-item-disabled');

        pasteItems.find('> a').attr('aria-disabled', 'true');
        pasteItems.find('.cms-submenu-item-paste-tooltip').css('display', 'none');
        pasteItems.find('.cms-submenu-item-paste-tooltip-empty').css('display', 'block');

        if (that._isClipboardModalOpen()) {
            that.modal.close();
        }

        that._disableTriggers();
        that.ui.document.trigger('click.cms.toolbar');
    }

    /**
     * @method _enableTriggers
     * @private
     */
    _enableTriggers() {
        this.ui.triggers.parent().removeClass('cms-toolbar-item-navigation-disabled');
        this.ui.triggerRemove.parent().removeClass('cms-toolbar-item-navigation-disabled');
    }

    /**
     * @method _disableTriggers
     * @private
     */
    _disableTriggers() {
        this.ui.triggers.parent().addClass('cms-toolbar-item-navigation-disabled');
        this.ui.triggerRemove.parent().addClass('cms-toolbar-item-navigation-disabled');
    }

    /**
     * Clears the clipboard by quering the server.
     * Callback is optional, but if provided - it's called
     * no matter what outcome was of the ajax call.
     *
     * @method clear
     * @param {Function} [callback]
     */
    clear(callback) {
        var that = this;
        // post needs to be a string, it will be converted using JSON.parse
        var post = '{ "csrfmiddlewaretoken": "' + CMS.config.csrf + '" }';

        that._cleanupDOM();

        // redirect to ajax
        CMS.API.Toolbar.openAjax({
            url: Helpers.updateUrlWithPath(CMS.config.clipboard.url),
            post: post,
            callback: function() {
                var args = Array.prototype.slice.call(arguments);

                that.populate('', {});
                // istanbul ignore next
                if (callback) {
                    callback.apply(this, args);
                }
            }
        });
    }

    /**
     * populate
     *
     * @public
     * @param {String} html markup of the clipboard draggable
     * @param {Object} pluginData data of the plugin in the clipboard
     */
    populate(html, pluginData) {
        this.currentClipboardData = {
            data: pluginData,
            timestamp: Date.now(),
            html: html
        };

        ls.set(storageKey, JSON.stringify(this.currentClipboardData));
    }
}

Clipboard.click = 'click.cms.clipboard';

export default Clipboard;
