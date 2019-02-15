/*
 * Copyright https://github.com/divio/django-cms
 */
import Modal from './cms.modal';
import StructureBoard from './cms.structureboard';
import $ from 'jquery';
import '../polyfills/array.prototype.findindex';
import nextUntil from './nextuntil';

import { toPairs, isNaN, debounce, findIndex, find, every, uniqWith, once, difference, isEqual } from 'lodash';

import Class from 'classjs';
import { Helpers, KEYS, $window, $document, uid } from './cms.base';
import { showLoader, hideLoader } from './loader';
import { filter as fuzzyFilter } from 'fuzzaldrin';

var clipboardDraggable;
var path = window.location.pathname + window.location.search;

var pluginUsageMap = Helpers._isStorageSupported ? JSON.parse(localStorage.getItem('cms-plugin-usage') || '{}') : {};

const isStructureReady = () =>
    CMS.config.settings.mode === 'structure' ||
    CMS.config.settings.legacy_mode ||
    CMS.API.StructureBoard._loadedStructure;
const isContentReady = () =>
    CMS.config.settings.mode !== 'structure' ||
    CMS.config.settings.legacy_mode ||
    CMS.API.StructureBoard._loadedContent;

/**
 * Class for handling Plugins / Placeholders or Generics.
 * Handles adding / moving / copying / pasting / menus etc
 * in structureboard.
 *
 * @class Plugin
 * @namespace CMS
 * @uses CMS.API.Helpers
 */
var Plugin = new Class({
    implement: [Helpers],

    options: {
        type: '', // bar, plugin or generic
        placeholder_id: null,
        plugin_type: '',
        plugin_id: null,
        plugin_parent: null,
        plugin_order: null,
        plugin_restriction: [],
        plugin_parent_restriction: [],
        urls: {
            add_plugin: '',
            edit_plugin: '',
            move_plugin: '',
            copy_plugin: '',
            delete_plugin: ''
        }
    },

    // these properties will be filled later
    modal: null,

    initialize: function initialize(container, options) {
        this.options = $.extend(true, {}, this.options, options);

        // create an unique for this component to use it internally
        this.uid = uid();

        this._setupUI(container);
        this._ensureData();

        if (this.options.type === 'plugin' && Plugin.aliasPluginDuplicatesMap[this.options.plugin_id]) {
            return;
        }
        if (this.options.type === 'placeholder' && Plugin.staticPlaceholderDuplicatesMap[this.options.placeholder_id]) {
            return;
        }

        // determine type of plugin
        switch (this.options.type) {
            case 'placeholder': // handler for placeholder bars
                Plugin.staticPlaceholderDuplicatesMap[this.options.placeholder_id] = true;
                this.ui.container.data('cms', this.options);
                this._setPlaceholder();
                if (isStructureReady()) {
                    this._collapsables();
                }
                break;
            case 'plugin': // handler for all plugins
                this.ui.container.data('cms').push(this.options);
                Plugin.aliasPluginDuplicatesMap[this.options.plugin_id] = true;
                this._setPlugin();
                if (isStructureReady()) {
                    this._collapsables();
                }
                break;
            default:
                // handler for static content
                this.ui.container.data('cms').push(this.options);
                this._setGeneric();
        }
    },

    _ensureData: function _ensureData() {
        // bind data element to the container (mutating!)
        if (!this.ui.container.data('cms')) {
            this.ui.container.data('cms', []);
        }
    },

    /**
     * Caches some jQuery references and sets up structure for
     * further initialisation.
     *
     * @method _setupUI
     * @private
     * @param {String} container `cms-plugin-${id}`
     */
    _setupUI: function setupUI(container) {
        var wrapper = $(`.${container}`);
        var contents;

        // have to check for cms-plugin, there can be a case when there are multiple
        // static placeholders or plugins rendered twice, there could be multiple wrappers on same page
        if (wrapper.length > 1 && container.match(/cms-plugin/)) {
            // so it's possible that multiple plugins (more often generics) are rendered
            // in different places. e.g. page menu in the header and in the footer
            // so first, we find all the template tags, then put them in a structure like this:
            // [[start, end], [start, end]...]
            //
            // in case of plugins it means that it's aliased plugin or a plugin in a duplicated
            // static placeholder (for whatever reason)
            var contentWrappers = wrapper.toArray().reduce((wrappers, elem, index) => {
                if (index === 0) {
                    wrappers[0].push(elem);
                    return wrappers;
                }

                var lastWrapper = wrappers[wrappers.length - 1];
                var lastItemInWrapper = lastWrapper[lastWrapper.length - 1];

                if ($(lastItemInWrapper).is('.cms-plugin-end')) {
                    wrappers.push([elem]);
                } else {
                    lastWrapper.push(elem);
                }

                return wrappers;
            }, [[]]);

            // then we map that structure into an array of jquery collections
            // from which we filter out empty ones
            contents = contentWrappers
                .map(items => {
                    var templateStart = $(items[0]);
                    var className = templateStart.attr('class').replace('cms-plugin-start', '');

                    var itemContents = $(nextUntil(templateStart[0], container));

                    $(items).filter('template').remove();

                    itemContents.each((index, el) => {
                        // if it's a non-space top-level text node - wrap it in `cms-plugin`
                        if (el.nodeType === Node.TEXT_NODE && !el.textContent.match(/^\s*$/)) {
                            var element = $(el);

                            element.wrap('<cms-plugin class="cms-plugin-text-node"></cms-plugin>');
                            itemContents[index] = element.parent()[0];
                        }
                    });

                    // otherwise we don't really need text nodes or comment nodes or empty text nodes
                    itemContents = itemContents.filter(function() {
                        return this.nodeType !== Node.TEXT_NODE && this.nodeType !== Node.COMMENT_NODE;
                    });

                    itemContents.addClass(`cms-plugin ${className}`);

                    return itemContents;
                })
                .filter(v => v.length);

            if (contents.length) {
                // and then reduce it to one big collection
                contents = contents.reduce((collection, items) => collection.add(items), $());
            }
        } else {
            contents = wrapper;
        }

        // in clipboard can be non-existent
        if (!contents.length) {
            contents = $('<div></div>');
        }

        this.ui = this.ui || {};
        this.ui.container = contents;
    },

    /**
     * Sets up behaviours and ui for placeholder.
     *
     * @method _setPlaceholder
     * @private
     */
    _setPlaceholder: function() {
        var that = this;

        this.ui.dragbar = $('.cms-dragbar-' + this.options.placeholder_id);
        this.ui.draggables = this.ui.dragbar.closest('.cms-dragarea').find('> .cms-draggables');
        this.ui.submenu = this.ui.dragbar.find('.cms-submenu-settings');
        var title = this.ui.dragbar.find('.cms-dragbar-title');
        var togglerLinks = this.ui.dragbar.find('.cms-dragbar-toggler a');
        var expanded = 'cms-dragbar-title-expanded';

        // register the subnav on the placeholder
        this._setSettingsMenu(this.ui.submenu);
        this._setAddPluginModal(this.ui.dragbar.find('.cms-submenu-add'));

        // istanbul ignore next
        CMS.settings.dragbars = CMS.settings.dragbars || []; // expanded dragbars array

        // enable expanding/collapsing globally within the placeholder
        togglerLinks.off(Plugin.click).on(Plugin.click, function(e) {
            e.preventDefault();
            if (title.hasClass(expanded)) {
                that._collapseAll(title);
            } else {
                that._expandAll(title);
            }
        });

        if ($.inArray(this.options.placeholder_id, CMS.settings.dragbars) !== -1) {
            title.addClass(expanded);
        }

        this._checkIfPasteAllowed();
    },

    /**
     * Sets up behaviours and ui for plugin.
     *
     * @method _setPlugin
     * @private
     */
    _setPlugin: function() {
        if (isStructureReady()) {
            this._setPluginStructureEvents();
        }
        if (isContentReady()) {
            this._setPluginContentEvents();
        }
    },

    _setPluginStructureEvents: function _setPluginStructureEvents() {
        var that = this;

        // filling up ui object
        this.ui.draggable = $('.cms-draggable-' + this.options.plugin_id);
        this.ui.dragitem = this.ui.draggable.find('> .cms-dragitem');
        this.ui.draggables = this.ui.draggable.find('> .cms-draggables');
        this.ui.submenu = this.ui.dragitem.find('.cms-submenu');

        this.ui.draggable.data('cms', this.options);

        this.ui.dragitem.on(Plugin.doubleClick, this._dblClickToEditHandler.bind(this));

        // adds listener for all plugin updates
        this.ui.draggable.off('cms-plugins-update').on('cms-plugins-update', function(e, eventData) {
            e.stopPropagation();
            that.movePlugin(null, eventData);
        });

        // adds listener for copy/paste updates
        this.ui.draggable.off('cms-paste-plugin-update').on('cms-paste-plugin-update', function(e, eventData) {
            e.stopPropagation();

            var dragitem = $(`.cms-draggable-${eventData.id}:last`);

            // find out new placeholder id
            var placeholder_id = that._getId(dragitem.closest('.cms-dragarea'));

            // if placeholder_id is empty, cancel
            if (!placeholder_id) {
                return false;
            }

            var data = dragitem.data('cms');

            data.target = placeholder_id;
            data.parent = that._getId(dragitem.parent().closest('.cms-draggable'));
            data.move_a_copy = true;

            // expand the plugin we paste to
            CMS.settings.states.push(data.parent);
            Helpers.setSettings(CMS.settings);

            that.movePlugin(data);
        });

        setTimeout(() => {
            this.ui.dragitem
                .on('mouseenter', e => {
                    e.stopPropagation();
                    if (!$document.data('expandmode')) {
                        return;
                    }
                    if (this.ui.draggable.find('> .cms-dragitem > .cms-plugin-disabled').length) {
                        return;
                    }
                    if (!CMS.API.StructureBoard.ui.container.hasClass('cms-structure-condensed')) {
                        return;
                    }
                    if (CMS.API.StructureBoard.dragging) {
                        return;
                    }
                    // eslint-disable-next-line no-magic-numbers
                    Plugin._highlightPluginContent(this.options.plugin_id, { successTimeout: 0, seeThrough: true });
                })
                .on('mouseleave', e => {
                    if (!CMS.API.StructureBoard.ui.container.hasClass('cms-structure-condensed')) {
                        return;
                    }
                    e.stopPropagation();
                    // eslint-disable-next-line no-magic-numbers
                    Plugin._removeHighlightPluginContent(this.options.plugin_id);
                });
            // attach event to the plugin menu
            this._setSettingsMenu(this.ui.submenu);

            // attach events for the "Add plugin" modal
            this._setAddPluginModal(this.ui.dragitem.find('.cms-submenu-add'));

            // clickability of "Paste" menu item
            this._checkIfPasteAllowed();
        });
    },

    _dblClickToEditHandler: function _dblClickToEditHandler(e) {
        var that = this;

        e.preventDefault();
        e.stopPropagation();

        that.editPlugin(
            Helpers.updateUrlWithPath(that.options.urls.edit_plugin),
            that.options.plugin_name,
            that._getPluginBreadcrumbs()
        );
    },

    _setPluginContentEvents: function _setPluginContentEvents() {
        const pluginDoubleClickEvent = this._getNamepacedEvent(Plugin.doubleClick);

        this.ui.container
            .off('mouseover.cms.plugins')
            .on('mouseover.cms.plugins', e => {
                if (!$document.data('expandmode')) {
                    return;
                }
                if (CMS.settings.mode !== 'structure') {
                    return;
                }
                e.stopPropagation();
                $('.cms-dragitem-success').remove();
                $('.cms-draggable-success').removeClass('cms-draggable-success');
                CMS.API.StructureBoard._showAndHighlightPlugin(0, true); // eslint-disable-line no-magic-numbers
            })
            .off('mouseout.cms.plugins')
            .on('mouseout.cms.plugins', e => {
                if (CMS.settings.mode !== 'structure') {
                    return;
                }
                e.stopPropagation();
                if (this.ui.draggable && this.ui.draggable.length) {
                    this.ui.draggable.find('.cms-dragitem-success').remove();
                    this.ui.draggable.removeClass('cms-draggable-success');
                }
                // Plugin._removeHighlightPluginContent(this.options.plugin_id);
            });

        if (!Plugin._isContainingMultiplePlugins(this.ui.container)) {
            $document
                .off(pluginDoubleClickEvent, `.cms-plugin-${this.options.plugin_id}`)
                .on(
                    pluginDoubleClickEvent,
                    `.cms-plugin-${this.options.plugin_id}`,
                    this._dblClickToEditHandler.bind(this)
                );
        }
    },

    /**
     * Sets up behaviours and ui for generics.
     * Generics do not show up in structure board.
     *
     * @method _setGeneric
     * @private
     */
    _setGeneric: function() {
        var that = this;

        // adds double click to edit
        this.ui.container.off(Plugin.doubleClick).on(Plugin.doubleClick, function(e) {
            e.preventDefault();
            e.stopPropagation();
            that.editPlugin(Helpers.updateUrlWithPath(that.options.urls.edit_plugin), that.options.plugin_name, []);
        });

        // adds edit tooltip
        this.ui.container
            .off(Plugin.pointerOverAndOut + ' ' + Plugin.touchStart)
            .on(Plugin.pointerOverAndOut + ' ' + Plugin.touchStart, function(e) {
                if (e.type !== 'touchstart') {
                    e.stopPropagation();
                }
                var name = that.options.plugin_name;
                var id = that.options.plugin_id;

                CMS.API.Tooltip.displayToggle(e.type === 'pointerover' || e.type === 'touchstart', e, name, id);
            });
    },

    /**
     * Checks if paste is allowed into current plugin/placeholder based
     * on restrictions we have. Also determines which tooltip to show.
     *
     * WARNING: this relies on clipboard plugins always being instantiated
     * first, so they have data('cms') by the time this method is called.
     *
     * @method _checkIfPasteAllowed
     * @private
     * @returns {Boolean}
     */
    _checkIfPasteAllowed: function _checkIfPasteAllowed() {
        var pasteButton = this.ui.dropdown.find('[data-rel=paste]');
        var pasteItem = pasteButton.parent();

        if (!clipboardDraggable.length) {
            pasteItem.addClass('cms-submenu-item-disabled');
            pasteItem.find('a').attr('tabindex', '-1').attr('aria-disabled', 'true');
            pasteItem.find('.cms-submenu-item-paste-tooltip-empty').css('display', 'block');
            return false;
        }

        if (this.ui.draggable && this.ui.draggable.hasClass('cms-draggable-disabled')) {
            pasteItem.addClass('cms-submenu-item-disabled');
            pasteItem.find('a').attr('tabindex', '-1').attr('aria-disabled', 'true');
            pasteItem.find('.cms-submenu-item-paste-tooltip-disabled').css('display', 'block');
            return false;
        }

        var bounds = this.options.plugin_restriction;

        if (clipboardDraggable.data('cms')) {
            var clipboardPluginData = clipboardDraggable.data('cms');
            var type = clipboardPluginData.plugin_type;
            var parent_bounds = $.grep(clipboardPluginData.plugin_parent_restriction, function(restriction) {
                // special case when PlaceholderPlugin has a parent restriction named "0"
                return restriction !== '0';
            });
            var currentPluginType = this.options.plugin_type;

            if (
                (bounds.length && $.inArray(type, bounds) === -1) ||
                (parent_bounds.length && $.inArray(currentPluginType, parent_bounds) === -1)
            ) {
                pasteItem.addClass('cms-submenu-item-disabled');
                pasteItem.find('a').attr('tabindex', '-1').attr('aria-disabled', 'true');
                pasteItem.find('.cms-submenu-item-paste-tooltip-restricted').css('display', 'block');
                return false;
            }
        } else {
            return false;
        }

        pasteItem.find('a').removeAttr('tabindex').removeAttr('aria-disabled');
        pasteItem.removeClass('cms-submenu-item-disabled');

        return true;
    },

    /**
     * Calls api to create a plugin and then proceeds to edit it.
     *
     * @method addPlugin
     * @param {String} type type of the plugin, e.g "Bootstrap3ColumnCMSPlugin"
     * @param {String} name name of the plugin, e.g. "Column"
     * @param {String} parent id of a parent plugin
     */
    addPlugin: function(type, name, parent) {
        var params = {
            placeholder_id: this.options.placeholder_id,
            plugin_type: type,
            cms_path: path,
            plugin_language: CMS.config.request.language
        };

        if (parent) {
            params.plugin_parent = parent;
        }
        var url = this.options.urls.add_plugin + '?' + $.param(params);
        var modal = new Modal({
            onClose: this.options.onClose || false,
            redirectOnClose: this.options.redirectOnClose || false
        });

        modal.open({
            url: url,
            title: name
        });

        this.modal = modal;

        Helpers.removeEventListener('modal-closed.add-plugin');
        Helpers.addEventListener('modal-closed.add-plugin', (e, { instance }) => {
            if (instance !== modal) {
                return;
            }
            Plugin._removeAddPluginPlaceholder();
        });
    },

    /**
     * Opens the modal for editing a plugin.
     *
     * @method editPlugin
     * @param {String} url editing url
     * @param {String} name Name of the plugin, e.g. "Column"
     * @param {Object[]} breadcrumb array of objects representing a breadcrumb,
     *     each item is `{ title: 'string': url: 'string' }`
     */
    editPlugin: function(url, name, breadcrumb) {
        // trigger modal window
        var modal = new Modal({
            onClose: this.options.onClose || false,
            redirectOnClose: this.options.redirectOnClose || false
        });

        this.modal = modal;

        Helpers.removeEventListener('modal-closed.edit-plugin modal-loaded.edit-plugin');
        Helpers.addEventListener('modal-closed.edit-plugin modal-loaded.edit-plugin', (e, { instance }) => {
            if (instance === modal) {
                // cannot be cached
                Plugin._removeAddPluginPlaceholder();
            }
        });
        modal.open({
            url: url,
            title: name,
            breadcrumbs: breadcrumb,
            width: 850
        });
    },

    /**
     * Used for copying _and_ pasting a plugin. If either of params
     * is present method assumes that it's "paste" and will make a call
     * to api to insert current plugin to specified `options.target_plugin_id`
     * or `options.target_placeholder_id`. Copying a plugin also first
     * clears the clipboard.
     *
     * @method copyPlugin
     * @param {Object} [opts=this.options]
     * @param {String} source_language
     * @returns {Boolean|void}
     */
    // eslint-disable-next-line complexity
    copyPlugin: function(opts, source_language) {
        // cancel request if already in progress
        if (CMS.API.locked) {
            return false;
        }
        CMS.API.locked = true;

        // set correct options (don't mutate them)
        var options = $.extend({}, opts || this.options);
        var sourceLanguage = source_language;
        let copyingFromLanguage = false;

        if (sourceLanguage) {
            copyingFromLanguage = true;
            options.target = options.placeholder_id;
            options.plugin_id = '';
            options.parent = '';
        } else {
            sourceLanguage = CMS.config.request.language;
        }

        var data = {
            source_placeholder_id: options.placeholder_id,
            source_plugin_id: options.plugin_id || '',
            source_language: sourceLanguage,
            target_plugin_id: options.parent || '',
            target_placeholder_id: options.target || CMS.config.clipboard.id,
            csrfmiddlewaretoken: CMS.config.csrf,
            target_language: CMS.config.request.language
        };
        var request = {
            type: 'POST',
            url: Helpers.updateUrlWithPath(options.urls.copy_plugin),
            data: data,
            success: function(response) {
                CMS.API.Messages.open({
                    message: CMS.config.lang.success
                });
                if (copyingFromLanguage) {
                    CMS.API.StructureBoard.invalidateState('PASTE', $.extend({}, data, response));
                } else {
                    CMS.API.StructureBoard.invalidateState('COPY', response);
                }
                CMS.API.locked = false;
                hideLoader();
            },
            error: function(jqXHR) {
                CMS.API.locked = false;
                var msg = CMS.config.lang.error;

                // trigger error
                CMS.API.Messages.open({
                    message: msg + jqXHR.responseText || jqXHR.status + ' ' + jqXHR.statusText,
                    error: true
                });
            }
        };

        $.ajax(request);
    },

    /**
     * Essentially clears clipboard and moves plugin to a clipboard
     * placholder through `movePlugin`.
     *
     * @method cutPlugin
     * @returns {Boolean|void}
     */
    cutPlugin: function() {
        // if cut is once triggered, prevent additional actions
        if (CMS.API.locked) {
            return false;
        }
        CMS.API.locked = true;

        var that = this;
        var data = {
            placeholder_id: CMS.config.clipboard.id,
            plugin_id: this.options.plugin_id,
            plugin_parent: '',
            plugin_order: [this.options.plugin_id],
            target_language: CMS.config.request.language,
            csrfmiddlewaretoken: CMS.config.csrf
        };

        // move plugin
        $.ajax({
            type: 'POST',
            url: Helpers.updateUrlWithPath(that.options.urls.move_plugin),
            data: data,
            success: function(response) {
                CMS.API.locked = false;
                CMS.API.Messages.open({
                    message: CMS.config.lang.success
                });
                CMS.API.StructureBoard.invalidateState('CUT', $.extend({}, data, response));
                hideLoader();
            },
            error: function(jqXHR) {
                CMS.API.locked = false;
                var msg = CMS.config.lang.error;

                // trigger error
                CMS.API.Messages.open({
                    message: msg + jqXHR.responseText || jqXHR.status + ' ' + jqXHR.statusText,
                    error: true
                });
                hideLoader();
            }
        });
    },

    /**
     * Method is called when you click on the paste button on the plugin.
     * Uses existing solution of `copyPlugin(options)`
     *
     * @method pastePlugin
     */
    pastePlugin: function() {
        var id = this._getId(clipboardDraggable);
        var eventData = {
            id: id
        };

        const clipboardDraggableClone = clipboardDraggable.clone(true, true);

        clipboardDraggableClone.appendTo(this.ui.draggables);
        if (this.options.plugin_id) {
            StructureBoard.actualizePluginCollapseStatus(this.options.plugin_id);
        }
        this.ui.draggables.trigger('cms-structure-update', [eventData]);
        clipboardDraggableClone.trigger('cms-paste-plugin-update', [eventData]);
    },

    /**
     * Moves plugin by querying the API and then updates some UI parts
     * to reflect that the page has changed.
     *
     * @method movePlugin
     * @param {Object} [opts=this.options]
     * @param {String} [opts.placeholder_id]
     * @param {String} [opts.plugin_id]
     * @param {String} [opts.plugin_parent]
     * @param {Boolean} [opts.move_a_copy]
     * @returns {Boolean|void}
     */
    movePlugin: function(opts) {
        // cancel request if already in progress
        if (CMS.API.locked) {
            return false;
        }
        CMS.API.locked = true;

        // set correct options
        var options = opts || this.options;

        var dragitem = $(`.cms-draggable-${options.plugin_id}:last`);

        // SAVING POSITION
        var placeholder_id = this._getId(dragitem.parents('.cms-draggables').last().prevAll('.cms-dragbar').first());

        var plugin_parent = this._getId(dragitem.parent().closest('.cms-draggable'));
        var plugin_order = this._getIds(dragitem.siblings('.cms-draggable').andSelf());

        if (options.move_a_copy) {
            plugin_order = plugin_order.map(function(pluginId) {
                var id = pluginId;

                // correct way would be to check if it's actually a
                // pasted plugin and only then replace the id with copy token
                // otherwise if we would copy from the same placeholder we would get
                // two copy tokens instead of original and a copy.
                // it's ok so far, as long as we copy only from clipboard
                if (id === options.plugin_id) {
                    id = '__COPY__';
                }
                return id;
            });
        }

        // cancel here if we have no placeholder id
        if (placeholder_id === false) {
            return false;
        }

        // gather the data for ajax request
        var data = {
            placeholder_id: placeholder_id,
            plugin_id: options.plugin_id,
            plugin_parent: plugin_parent || '',
            target_language: CMS.config.request.language,
            plugin_order: plugin_order,
            csrfmiddlewaretoken: CMS.config.csrf,
            move_a_copy: options.move_a_copy
        };

        showLoader();

        $.ajax({
            type: 'POST',
            url: Helpers.updateUrlWithPath(options.urls.move_plugin),
            data: data,
            success: function(response) {
                CMS.API.StructureBoard.invalidateState(
                    data.move_a_copy ? 'PASTE' : 'MOVE',
                    $.extend({}, data, response)
                );

                // enable actions again
                CMS.API.locked = false;
                hideLoader();
            },
            error: function(jqXHR) {
                CMS.API.locked = false;
                var msg = CMS.config.lang.error;

                // trigger error
                CMS.API.Messages.open({
                    message: msg + jqXHR.responseText || jqXHR.status + ' ' + jqXHR.statusText,
                    error: true
                });
                hideLoader();
            }
        });
    },

    /**
     * Changes the settings attributes on an initialised plugin.
     *
     * @method _setSettings
     * @param {Object} oldSettings current settings
     * @param {Object} newSettings new settings to be applied
     * @private
     */
    _setSettings: function _setSettings(oldSettings, newSettings) {
        var settings = $.extend(true, {}, oldSettings, newSettings);
        var plugin = $('.cms-plugin-' + settings.plugin_id);
        var draggable = $('.cms-draggable-' + settings.plugin_id);

        // set new setting on instance and plugin data
        this.options = settings;
        if (plugin.length) {
            var index = plugin.data('cms').findIndex(function(pluginData) {
                return pluginData.plugin_id === settings.plugin_id;
            });

            plugin.each(function() {
                $(this).data('cms')[index] = settings;
            });
        }
        if (draggable.length) {
            draggable.data('cms', settings);
        }
    },

    /**
     * Opens a modal to delete a plugin.
     *
     * @method deletePlugin
     * @param {String} url admin url for deleting a page
     * @param {String} name plugin name, e.g. "Column"
     * @param {Object[]} breadcrumb array of objects representing a breadcrumb,
     *     each item is `{ title: 'string': url: 'string' }`
     */
    deletePlugin: function(url, name, breadcrumb) {
        // trigger modal window
        var modal = new Modal({
            onClose: this.options.onClose || false,
            redirectOnClose: this.options.redirectOnClose || false
        });

        this.modal = modal;

        Helpers.removeEventListener('modal-loaded.delete-plugin');
        Helpers.addEventListener('modal-loaded.delete-plugin', (e, { instance }) => {
            if (instance === modal) {
                Plugin._removeAddPluginPlaceholder();
            }
        });
        modal.open({
            url: url,
            title: name,
            breadcrumbs: breadcrumb
        });
    },

    /**
     * Destroys the current plugin instance removing only the DOM listeners
     *
     * @method destroy
     * @param {Object}  options - destroy config options
     * @param {Boolean} options.mustCleanup - if true it will remove also the plugin UI components from the DOM
     * @returns {void}
     */
    destroy(options = {}) {
        const mustCleanup = options.mustCleanup || false;

        // close the plugin modal if it was open
        if (this.modal) {
            this.modal.close();
            // unsubscribe to all the modal events
            this.modal.off();
        }

        if (mustCleanup) {
            this.cleanup();
        }

        // remove event bound to global elements like document or window
        $document.off(`.${this.uid}`);
        $window.off(`.${this.uid}`);
    },

    /**
     * Remove the plugin specific ui elements from the DOM
     *
     * @method cleanup
     * @returns {void}
     */
    cleanup() {
        // remove all the plugin UI DOM elements
        // notice that $.remove will remove also all the ui specific events
        // previously attached to them
        Object.keys(this.ui).forEach(el => this.ui[el].remove());
    },

    /**
     * Called after plugin is added through ajax.
     *
     * @method editPluginPostAjax
     * @param {Object} toolbar CMS.API.Toolbar instance (not used)
     * @param {Object} response response from server
     */
    editPluginPostAjax: function(toolbar, response) {
        this.editPlugin(Helpers.updateUrlWithPath(response.url), this.options.plugin_name, response.breadcrumb);
    },

    /**
     * _setSettingsMenu sets up event handlers for settings menu.
     *
     * @method _setSettingsMenu
     * @private
     * @param {jQuery} nav
     */
    _setSettingsMenu: function _setSettingsMenu(nav) {
        var that = this;

        this.ui.dropdown = nav.siblings('.cms-submenu-dropdown-settings');
        var dropdown = this.ui.dropdown;

        nav
            .off(Plugin.pointerUp)
            .on(Plugin.pointerUp, function(e) {
                e.preventDefault();
                e.stopPropagation();
                var trigger = $(this);

                if (trigger.hasClass('cms-btn-active')) {
                    Plugin._hideSettingsMenu(trigger);
                } else {
                    Plugin._hideSettingsMenu();
                    that._showSettingsMenu(trigger);
                }
            })
            .off(Plugin.touchStart)
            .on(Plugin.touchStart, function(e) {
                // required on some touch devices so
                // ui touch punch is not triggering mousemove
                // which in turn results in pep triggering pointercancel
                e.stopPropagation();
            });

        dropdown
            .off(Plugin.mouseEvents)
            .on(Plugin.mouseEvents, function(e) {
                e.stopPropagation();
            })
            .off(Plugin.touchStart)
            .on(Plugin.touchStart, function(e) {
                // required for scrolling on mobile
                e.stopPropagation();
            });

        that._setupActions(nav);
        // prevent propagation
        nav
            .on([Plugin.pointerUp, Plugin.pointerDown, Plugin.click, Plugin.doubleClick].join(' '))
            .on([Plugin.pointerUp, Plugin.pointerDown, Plugin.click, Plugin.doubleClick].join(' '), function(e) {
                e.stopPropagation();
            });

        nav
            .siblings('.cms-quicksearch, .cms-submenu-dropdown-settings')
            .off([Plugin.pointerUp, Plugin.click, Plugin.doubleClick].join(' '))
            .on([Plugin.pointerUp, Plugin.click, Plugin.doubleClick].join(' '), function(e) {
                e.stopPropagation();
            });
    },

    /**
     * Simplistic implementation, only scrolls down, only works in structuremode
     * and highly depends on the styles of the structureboard to work correctly
     *
     * @method _scrollToElement
     * @private
     * @param {jQuery} el element to scroll to
     * @param {Object} [opts]
     * @param {Number} [opts.duration=200] time to scroll
     * @param {Number} [opts.offset=50] distance in px to the bottom of the screen
     */
    _scrollToElement: function _scrollToElement(el, opts) {
        var DEFAULT_DURATION = 200;
        var DEFAULT_OFFSET = 50;
        var duration = opts && opts.duration !== undefined ? opts.duration : DEFAULT_DURATION;
        var offset = opts && opts.offset !== undefined ? opts.offset : DEFAULT_OFFSET;
        var scrollable = el.offsetParent();
        var scrollHeight = $window.height();
        var scrollTop = scrollable.scrollTop();
        var elPosition = el.position().top;
        var elHeight = el.height();
        var isInViewport = elPosition + elHeight + offset <= scrollHeight;

        if (!isInViewport) {
            scrollable.animate(
                {
                    scrollTop: elPosition + offset + elHeight + scrollTop - scrollHeight
                },
                duration
            );
        }
    },

    /**
     * Opens a modal with traversable plugins list, adds a placeholder to where
     * the plugin will be added.
     *
     * @method _setAddPluginModal
     * @private
     * @param {jQuery} nav modal trigger element
     * @returns {Boolean|void}
     */
    _setAddPluginModal: function _setAddPluginModal(nav) {
        if (nav.hasClass('cms-btn-disabled')) {
            return false;
        }
        var that = this;
        var modal;
        var isTouching;
        var plugins;

        var initModal = once(function initModal() {
            var placeholder = $(
                '<div class="cms-add-plugin-placeholder">' + CMS.config.lang.addPluginPlaceholder + '</div>'
            );
            var dragItem = nav.closest('.cms-dragitem');
            var isPlaceholder = !dragItem.length;
            var childrenList;

            modal = new Modal({
                minWidth: 400,
                minHeight: 400
            });

            if (isPlaceholder) {
                childrenList = nav.closest('.cms-dragarea').find('> .cms-draggables');
            } else {
                childrenList = nav.closest('.cms-draggable').find('> .cms-draggables');
            }

            Helpers.addEventListener('modal-loaded', (e, { instance }) => {
                if (instance !== modal) {
                    return;
                }

                that._setupKeyboardTraversing();
                if (childrenList.hasClass('cms-hidden') && !isPlaceholder) {
                    that._toggleCollapsable(dragItem);
                }
                Plugin._removeAddPluginPlaceholder();
                placeholder.appendTo(childrenList);
                that._scrollToElement(placeholder);
            });

            Helpers.addEventListener('modal-closed', (e, { instance }) => {
                if (instance !== modal) {
                    return;
                }
                Plugin._removeAddPluginPlaceholder();
            });

            Helpers.addEventListener('modal-shown', (e, { instance }) => {
                if (modal !== instance) {
                    return;
                }
                var dropdown = $('.cms-modal-markup .cms-plugin-picker');

                if (!isTouching) {
                    // only focus the field if using mouse
                    // otherwise keyboard pops up
                    dropdown.find('input').trigger('focus');
                }
                isTouching = false;
            });

            plugins = nav.siblings('.cms-plugin-picker');

            that._setupQuickSearch(plugins);
        });

        nav
            .on(Plugin.touchStart, function(e) {
                isTouching = true;
                // required on some touch devices so
                // ui touch punch is not triggering mousemove
                // which in turn results in pep triggering pointercancel
                e.stopPropagation();
            })
            .on(Plugin.pointerUp, function(e) {
                e.preventDefault();
                e.stopPropagation();

                Plugin._hideSettingsMenu();

                initModal();

                // since we don't know exact plugin parent (because dragndrop)
                // we need to know the parent id by the time we open "add plugin" dialog
                var pluginsCopy = that._updateWithMostUsedPlugins(
                    plugins
                        .clone(true, true)
                        .data('parentId', that._getId(nav.closest('.cms-draggable')))
                        .append(that._getPossibleChildClasses())
                );

                modal.open({
                    title: that.options.addPluginHelpTitle,
                    html: pluginsCopy,
                    width: 530,
                    height: 400
                });
            });

        // prevent propagation
        nav.on([Plugin.pointerUp, Plugin.pointerDown, Plugin.click, Plugin.doubleClick].join(' '), function(e) {
            e.stopPropagation();
        });

        nav
            .siblings('.cms-quicksearch, .cms-submenu-dropdown')
            .on([Plugin.pointerUp, Plugin.click, Plugin.doubleClick].join(' '), function(e) {
                e.stopPropagation();
            });
    },

    _updateWithMostUsedPlugins: function _updateWithMostUsedPlugins(plugins) {
        const items = plugins.find('.cms-submenu-item');
        // eslint-disable-next-line no-unused-vars
        const mostUsedPlugins = toPairs(pluginUsageMap).sort(([x, a], [y, b]) => a - b).reverse();
        const MAX_MOST_USED_PLUGINS = 5;
        let count = 0;

        if (items.filter(':not(.cms-submenu-item-title)').length <= MAX_MOST_USED_PLUGINS) {
            return plugins;
        }

        let ref = plugins.find('.cms-quicksearch');

        mostUsedPlugins.forEach(([name]) => {
            if (count === MAX_MOST_USED_PLUGINS) {
                return;
            }
            const item = items.find(`[href=${name}]`);

            if (item.length) {
                const clone = item.closest('.cms-submenu-item').clone(true, true);

                ref.after(clone);
                ref = clone;
                count += 1;
            }
        });

        if (count) {
            plugins.find('.cms-quicksearch').after(
                $(`<div class="cms-submenu-item cms-submenu-item-title" data-cms-most-used>
                    <span>${CMS.config.lang.mostUsed}</span>
                </div>`)
            );
        }

        return plugins;
    },

    /**
     * Returns a specific plugin namespaced event postfixing the plugin uid to it
     * in order to properly manage it via jQuery $.on and $.off
     *
     * @method _getNamepacedEvent
     * @private
     * @param {String} base - plugin event type
     * @param {String} additionalNS - additional namespace (like '.traverse' for example)
     * @returns {String} a specific plugin event
     *
     * @example
     *
     * plugin._getNamepacedEvent(Plugin.click); // 'click.cms.plugin.42'
     * plugin._getNamepacedEvent(Plugin.keyDown, '.traverse'); // 'keydown.cms.plugin.traverse.42'
     */
    _getNamepacedEvent(base, additionalNS = '') {
        return `${base}${additionalNS ? '.'.concat(additionalNS) : ''}.${this.uid}`;
    },

    /**
     * Returns available plugin/placeholder child classes markup
     * for "Add plugin" modal
     *
     * @method _getPossibleChildClasses
     * @private
     * @returns {jQuery} "add plugin" menu
     */
    _getPossibleChildClasses: function _getPossibleChildClasses() {
        var that = this;
        var childRestrictions = this.options.plugin_restriction;
        // have to check the placeholder every time, since plugin could've been
        // moved as part of another plugin
        var placeholderId = that._getId(that.ui.submenu.closest('.cms-dragarea'));
        var resultElements = $($('#cms-plugin-child-classes-' + placeholderId).html());

        if (childRestrictions && childRestrictions.length) {
            resultElements = resultElements.filter(function() {
                var item = $(this);

                return (
                    item.hasClass('cms-submenu-item-title') ||
                    childRestrictions.indexOf(item.find('a').attr('href')) !== -1
                );
            });

            resultElements = resultElements.filter(function(index) {
                var item = $(this);

                return (
                    !item.hasClass('cms-submenu-item-title') ||
                    (item.hasClass('cms-submenu-item-title') &&
                        (!resultElements.eq(index + 1).hasClass('cms-submenu-item-title') &&
                            resultElements.eq(index + 1).length))
                );
            });
        }

        resultElements.find('a').on(Plugin.click, e => this._delegate(e));

        return resultElements;
    },

    /**
     * Sets up event handlers for quicksearching in the plugin picker.
     *
     * @method _setupQuickSearch
     * @private
     * @param {jQuery} plugins plugins picker element
     */
    _setupQuickSearch: function _setupQuickSearch(plugins) {
        var that = this;
        var FILTER_DEBOUNCE_TIMER = 100;
        var FILTER_PICK_DEBOUNCE_TIMER = 110;

        var handler = debounce(function() {
            var input = $(this);
            // have to always find the pluginsPicker in the handler
            // because of how we move things into/out of the modal
            var pluginsPicker = input.closest('.cms-plugin-picker');

            that._filterPluginsList(pluginsPicker, input);
        }, FILTER_DEBOUNCE_TIMER);

        plugins.find('> .cms-quicksearch').find('input').on(Plugin.keyUp, handler).on(
            Plugin.keyUp,
            debounce(function(e) {
                var input;
                var pluginsPicker;

                if (e.keyCode === KEYS.ENTER) {
                    input = $(this);
                    pluginsPicker = input.closest('.cms-plugin-picker');
                    pluginsPicker
                        .find('.cms-submenu-item')
                        .not('.cms-submenu-item-title')
                        .filter(':visible')
                        .first()
                        .find('> a')
                        .focus()
                        .trigger('click');
                }
            }, FILTER_PICK_DEBOUNCE_TIMER)
        );
    },

    /**
     * Sets up click handlers for various plugin/placeholder items.
     * Items can be anywhere in the plugin dragitem, not only in dropdown.
     *
     * @method _setupActions
     * @private
     * @param {jQuery} nav dropdown trigger with the items
     */
    _setupActions: function _setupActions(nav) {
        var items = '.cms-submenu-edit, .cms-submenu-item a';
        var parent = nav.parent();

        parent.find('.cms-submenu-edit').off(Plugin.touchStart).on(Plugin.touchStart, function(e) {
            // required on some touch devices so
            // ui touch punch is not triggering mousemove
            // which in turn results in pep triggering pointercancel
            e.stopPropagation();
        });
        parent.find(items).off(Plugin.click).on(Plugin.click, nav, e => this._delegate(e));
    },

    /**
     * Handler for the "action" items
     *
     * @method _delegate
     * @param {$.Event} e event
     * @private
     */
    // eslint-disable-next-line complexity
    _delegate: function _delegate(e) {
        e.preventDefault();
        e.stopPropagation();

        var nav;
        var that = this;

        if (e.data && e.data.nav) {
            nav = e.data.nav;
        }

        // show loader and make sure scroll doesn't jump
        showLoader();

        var items = '.cms-submenu-edit, .cms-submenu-item a';
        var el = $(e.target).closest(items);

        Plugin._hideSettingsMenu(nav);

        // set switch for subnav entries
        switch (el.attr('data-rel')) {
            // eslint-disable-next-line no-case-declarations
            case 'add':
                const pluginType = el.attr('href').replace('#', '');

                Plugin._updateUsageCount(pluginType);
                that.addPlugin(pluginType, el.text(), el.closest('.cms-plugin-picker').data('parentId'));
                break;
            case 'ajax_add':
                CMS.API.Toolbar.openAjax({
                    url: el.attr('href'),
                    post: JSON.stringify(el.data('post')),
                    text: el.data('text'),
                    callback: $.proxy(that.editPluginPostAjax, that),
                    onSuccess: el.data('on-success')
                });
                break;
            case 'edit':
                that.editPlugin(
                    Helpers.updateUrlWithPath(that.options.urls.edit_plugin),
                    that.options.plugin_name,
                    that._getPluginBreadcrumbs()
                );
                break;
            case 'copy-lang':
                that.copyPlugin(that.options, el.attr('data-language'));
                break;
            case 'copy':
                if (el.parent().hasClass('cms-submenu-item-disabled')) {
                    hideLoader();
                } else {
                    that.copyPlugin();
                }
                break;
            case 'cut':
                that.cutPlugin();
                break;
            case 'paste':
                hideLoader();
                if (!el.parent().hasClass('cms-submenu-item-disabled')) {
                    that.pastePlugin();
                }
                break;
            case 'delete':
                that.deletePlugin(
                    Helpers.updateUrlWithPath(that.options.urls.delete_plugin),
                    that.options.plugin_name,
                    that._getPluginBreadcrumbs()
                );
                break;
            case 'highlight':
                hideLoader();
                // eslint-disable-next-line no-magic-numbers
                window.location.hash = `cms-plugin-${this.options.plugin_id}`;
                Plugin._highlightPluginContent(this.options.plugin_id, { seeThrough: true });
                e.stopImmediatePropagation();
                break;
            default:
                hideLoader();
                CMS.API.Toolbar._delegate(el);
        }
    },

    /**
     * Sets up keyboard traversing of plugin picker.
     *
     * @method _setupKeyboardTraversing
     * @private
     */
    _setupKeyboardTraversing: function _setupKeyboardTraversing() {
        var dropdown = $('.cms-modal-markup .cms-plugin-picker');
        const keyDownTraverseEvent = this._getNamepacedEvent(Plugin.keyDown, 'traverse');

        if (!dropdown.length) {
            return;
        }
        // add key events
        $document.off(keyDownTraverseEvent);
        // istanbul ignore next: not really possible to reproduce focus state in unit tests
        $document.on(keyDownTraverseEvent, function(e) {
            var anchors = dropdown.find('.cms-submenu-item:visible a');
            var index = anchors.index(anchors.filter(':focus'));

            // bind arrow down and tab keys
            if (e.keyCode === KEYS.DOWN || (e.keyCode === KEYS.TAB && !e.shiftKey)) {
                e.preventDefault();
                if (index >= 0 && index < anchors.length - 1) {
                    anchors.eq(index + 1).focus();
                } else {
                    anchors.eq(0).focus();
                }
            }

            // bind arrow up and shift+tab keys
            if (e.keyCode === KEYS.UP || (e.keyCode === KEYS.TAB && e.shiftKey)) {
                e.preventDefault();
                if (anchors.is(':focus')) {
                    anchors.eq(index - 1).focus();
                } else {
                    anchors.eq(anchors.length).focus();
                }
            }
        });
    },

    /**
     * Opens the settings menu for a plugin.
     *
     * @method _showSettingsMenu
     * @private
     * @param {jQuery} nav trigger element
     */
    _showSettingsMenu: function(nav) {
        this._checkIfPasteAllowed();

        var dropdown = this.ui.dropdown;
        var parents = nav.parentsUntil('.cms-dragarea').last();
        var MIN_SCREEN_MARGIN = 10;

        nav.addClass('cms-btn-active');
        parents.addClass('cms-z-index-9999');

        // set visible states
        dropdown.show();

        // calculate dropdown positioning
        if (
            $window.height() + $window.scrollTop() - nav.offset().top - dropdown.height() <= MIN_SCREEN_MARGIN &&
            nav.offset().top - dropdown.height() >= 0
        ) {
            dropdown.removeClass('cms-submenu-dropdown-top').addClass('cms-submenu-dropdown-bottom');
        } else {
            dropdown.removeClass('cms-submenu-dropdown-bottom').addClass('cms-submenu-dropdown-top');
        }
    },

    /**
     * Filters given plugins list by a query.
     *
     * @method _filterPluginsList
     * @private
     * @param {jQuery} list plugins picker element
     * @param {jQuery} input input, which value to filter plugins with
     * @returns {Boolean|void}
     */
    _filterPluginsList: function _filterPluginsList(list, input) {
        var items = list.find('.cms-submenu-item');
        var titles = list.find('.cms-submenu-item-title');
        var query = input.val();

        // cancel if query is zero
        if (query === '') {
            items.add(titles).show();
            return false;
        }

        var mostRecentItems = list.find('.cms-submenu-item[data-cms-most-used]');

        mostRecentItems = mostRecentItems.add(mostRecentItems.nextUntil('.cms-submenu-item-title'));

        var itemsToFilter = items.toArray().map(function(el) {
            var element = $(el);

            return {
                value: element.text(),
                element: element
            };
        });

        var filteredItems = fuzzyFilter(itemsToFilter, query, { key: 'value' });

        items.hide();
        filteredItems.forEach(function(item) {
            item.element.show();
        });

        // check if a title is matching
        titles.filter(':visible').each(function(index, item) {
            titles.hide();
            $(item).nextUntil('.cms-submenu-item-title').show();
        });

        // always display title of a category
        items.filter(':visible').each(function(index, titleItem) {
            var item = $(titleItem);

            if (item.prev().hasClass('cms-submenu-item-title')) {
                item.prev().show();
            } else {
                item.prevUntil('.cms-submenu-item-title').last().prev().show();
            }
        });

        mostRecentItems.hide();
    },

    /**
     * Toggles collapsable item.
     *
     * @method _toggleCollapsable
     * @private
     * @param {jQuery} el element to toggle
     * @returns {Boolean|void}
     */
    _toggleCollapsable: function toggleCollapsable(el) {
        var that = this;
        var id = that._getId(el.parent());
        var draggable = el.closest('.cms-draggable');
        var items;

        var settings = CMS.settings;

        settings.states = settings.states || [];

        if (!draggable || !draggable.length) {
            return;
        }

        // collapsable function and save states
        if (el.hasClass('cms-dragitem-expanded')) {
            settings.states.splice($.inArray(id, settings.states), 1);
            el
                .removeClass('cms-dragitem-expanded')
                .parent()
                .find('> .cms-collapsable-container')
                .addClass('cms-hidden');

            if ($document.data('expandmode')) {
                items = draggable.find('.cms-draggable').find('.cms-dragitem-collapsable');
                if (!items.length) {
                    return false;
                }
                items.each(function() {
                    var item = $(this);

                    if (item.hasClass('cms-dragitem-expanded')) {
                        that._toggleCollapsable(item);
                    }
                });
            }
        } else {
            settings.states.push(id);
            el
                .addClass('cms-dragitem-expanded')
                .parent()
                .find('> .cms-collapsable-container')
                .removeClass('cms-hidden');

            if ($document.data('expandmode')) {
                items = draggable.find('.cms-draggable').find('.cms-dragitem-collapsable');
                if (!items.length) {
                    return false;
                }
                items.each(function() {
                    var item = $(this);

                    if (!item.hasClass('cms-dragitem-expanded')) {
                        that._toggleCollapsable(item);
                    }
                });
            }
        }

        this._updatePlaceholderCollapseState();

        // make sure structurboard gets updated after expanding
        $document.trigger('resize.sideframe');

        // save settings
        Helpers.setSettings(settings);
    },

    _updatePlaceholderCollapseState() {
        if (this.options.type !== 'plugin' || !this.options.placeholder_id) {
            return;
        }

        const pluginsOfCurrentPlaceholder = CMS._plugins
            .filter(([, o]) => o.placeholder_id === this.options.placeholder_id && o.type === 'plugin')
            .map(([, o]) => o.plugin_id);

        const openedPlugins = CMS.settings.states;
        const closedPlugins = difference(pluginsOfCurrentPlaceholder, openedPlugins);
        const areAllRemainingPluginsLeafs = every(closedPlugins, id => {
            return !find(
                CMS._plugins,
                ([, o]) => o.placeholder_id === this.options.placeholder_id && o.plugin_parent === id
            );
        });
        const el = $(`.cms-dragarea-${this.options.placeholder_id} .cms-dragbar-title`);
        var settings = CMS.settings;

        if (areAllRemainingPluginsLeafs) {
            // meaning that all plugins in current placeholder are expanded
            el.addClass('cms-dragbar-title-expanded');

            settings.dragbars = settings.dragbars || [];
            settings.dragbars.push(this.options.placeholder_id);
        } else {
            el.removeClass('cms-dragbar-title-expanded');

            settings.dragbars = settings.dragbars || [];
            settings.dragbars.splice($.inArray(this.options.placeholder_id, settings.states), 1);
        }
    },

    /**
     * Sets up collabspable event handlers.
     *
     * @method _collapsables
     * @private
     * @returns {Boolean|void}
     */
    _collapsables: function() {
        // one time setup
        var that = this;

        this.ui.draggable = $('.cms-draggable-' + this.options.plugin_id);
        // cancel here if its not a draggable
        if (!this.ui.draggable.length) {
            return false;
        }

        var dragitem = this.ui.draggable.find('> .cms-dragitem');

        // check which button should be shown for collapsemenu
        var els = this.ui.draggable.find('.cms-dragitem-collapsable');
        var open = els.filter('.cms-dragitem-expanded');

        if (els.length === open.length && els.length + open.length !== 0) {
            this.ui.draggable.find('.cms-dragbar-title').addClass('cms-dragbar-title-expanded');
        }

        // attach events to draggable
        // debounce here required because on some devices click is not triggered,
        // so we consolidate latest click and touch event to run the collapse only once
        dragitem.find('> .cms-dragitem-text').on(
            Plugin.touchEnd + ' ' + Plugin.click,
            debounce(function() {
                if (!dragitem.hasClass('cms-dragitem-collapsable')) {
                    return;
                }
                that._toggleCollapsable(dragitem);
            }, 0)
        );
    },

    /**
     * Expands all the collapsables in the given placeholder.
     *
     * @method _expandAll
     * @private
     * @param {jQuery} el trigger element that is a child of a placeholder
     * @returns {Boolean|void}
     */
    _expandAll: function(el) {
        var that = this;
        var items = el.closest('.cms-dragarea').find('.cms-dragitem-collapsable');

        // cancel if there are no items
        if (!items.length) {
            return false;
        }
        items.each(function() {
            var item = $(this);

            if (!item.hasClass('cms-dragitem-expanded')) {
                that._toggleCollapsable(item);
            }
        });

        el.addClass('cms-dragbar-title-expanded');

        var settings = CMS.settings;

        settings.dragbars = settings.dragbars || [];
        settings.dragbars.push(this.options.placeholder_id);
        Helpers.setSettings(settings);
    },

    /**
     * Collapses all the collapsables in the given placeholder.
     *
     * @method _collapseAll
     * @private
     * @param {jQuery} el trigger element that is a child of a placeholder
     */
    _collapseAll: function(el) {
        var that = this;
        var items = el.closest('.cms-dragarea').find('.cms-dragitem-collapsable');

        items.each(function() {
            var item = $(this);

            if (item.hasClass('cms-dragitem-expanded')) {
                that._toggleCollapsable(item);
            }
        });

        el.removeClass('cms-dragbar-title-expanded');

        var settings = CMS.settings;

        settings.dragbars = settings.dragbars || [];
        settings.dragbars.splice($.inArray(this.options.placeholder_id, settings.states), 1);
        Helpers.setSettings(settings);
    },

    /**
     * Gets the id of the element, uses CMS.StructureBoard instance.
     *
     * @method _getId
     * @private
     * @param {jQuery} el element to get id from
     * @returns {String}
     */
    _getId: function(el) {
        return CMS.API.StructureBoard.getId(el);
    },

    /**
     * Gets the ids of the list of elements, uses CMS.StructureBoard instance.
     *
     * @method _getIds
     * @private
     * @param {jQuery} els elements to get id from
     * @returns {String[]}
     */
    _getIds: function(els) {
        return CMS.API.StructureBoard.getIds(els);
    },

    /**
     * Traverses the registry to find plugin parents
     *
     * @method _getPluginBreadcrumbs
     * @returns {Object[]} array of breadcrumbs in `{ url, title }` format
     * @private
     */
    _getPluginBreadcrumbs: function _getPluginBreadcrumbs() {
        var breadcrumbs = [];

        breadcrumbs.unshift({
            title: this.options.plugin_name,
            url: this.options.urls.edit_plugin
        });

        var findParentPlugin = function(id) {
            return $.grep(CMS._plugins || [], function(pluginOptions) {
                return pluginOptions[0] === 'cms-plugin-' + id;
            })[0];
        };

        var id = this.options.plugin_parent;
        var data;

        while (id && id !== 'None') {
            data = findParentPlugin(id);

            if (!data) {
                break;
            }

            breadcrumbs.unshift({
                title: data[1].plugin_name,
                url: data[1].urls.edit_plugin
            });
            id = data[1].plugin_parent;
        }

        return breadcrumbs;
    }
});

Plugin.click = 'click.cms.plugin';
Plugin.pointerUp = 'pointerup.cms.plugin';
Plugin.pointerDown = 'pointerdown.cms.plugin';
Plugin.pointerOverAndOut = 'pointerover.cms.plugin pointerout.cms.plugin';
Plugin.doubleClick = 'dblclick.cms.plugin';
Plugin.keyUp = 'keyup.cms.plugin';
Plugin.keyDown = 'keydown.cms.plugin';
Plugin.mouseEvents = 'mousedown.cms.plugin mousemove.cms.plugin mouseup.cms.plugin';
Plugin.touchStart = 'touchstart.cms.plugin';
Plugin.touchEnd = 'touchend.cms.plugin';

/**
 * Updates plugin data in CMS._plugins / CMS._instances or creates new
 * plugin instances if they didn't exist
 *
 * @method _updateRegistry
 * @private
 * @static
 * @param {Object[]} plugins plugins data
 */
Plugin._updateRegistry = function _updateRegistry(plugins) {
    plugins.forEach(pluginData => {
        const pluginContainer = `cms-plugin-${pluginData.plugin_id}`;
        const pluginIndex = findIndex(CMS._plugins, ([pluginStr]) => pluginStr === pluginContainer);

        if (pluginIndex === -1) {
            CMS._plugins.push([pluginContainer, pluginData]);
            CMS._instances.push(new Plugin(pluginContainer, pluginData));
        } else {
            Plugin.aliasPluginDuplicatesMap[pluginData.plugin_id] = false;
            CMS._plugins[pluginIndex] = [pluginContainer, pluginData];
            CMS._instances[pluginIndex] = new Plugin(pluginContainer, pluginData);
        }
    });
};

/**
 * Hides the opened settings menu. By default looks for any open ones.
 *
 * @method _hideSettingsMenu
 * @static
 * @private
 * @param {jQuery} [navEl] element representing the subnav trigger
 */
Plugin._hideSettingsMenu = function(navEl) {
    var nav = navEl || $('.cms-submenu-btn.cms-btn-active');

    if (!nav.length) {
        return;
    }
    nav.removeClass('cms-btn-active');

    // set correct active state
    nav.closest('.cms-draggable').data('active', false);
    $('.cms-z-index-9999').removeClass('cms-z-index-9999');

    nav.siblings('.cms-submenu-dropdown').hide();
    nav.siblings('.cms-quicksearch').hide();
    // reset search
    nav.siblings('.cms-quicksearch').find('input').val('').trigger(Plugin.keyUp).blur();

    // reset relativity
    $('.cms-dragbar').css('position', '');
};

/**
 * Initialises handlers that affect all plugins and don't make sense
 * in context of each own plugin instance, e.g. listening for a click on a document
 * to hide plugin settings menu should only be applied once, and not every time
 * CMS.Plugin is instantiated.
 *
 * @method _initializeGlobalHandlers
 * @static
 * @private
 */
Plugin._initializeGlobalHandlers = function _initializeGlobalHandlers() {
    var timer;
    var clickCounter = 0;

    Plugin._updateClipboard();

    // Structureboard initialized too late
    setTimeout(function() {
        var pluginData = {};
        var html = '';

        if (clipboardDraggable.length) {
            pluginData = find(
                CMS._plugins,
                ([desc]) => desc === `cms-plugin-${CMS.API.StructureBoard.getId(clipboardDraggable)}`
            )[1];
            html = clipboardDraggable.parent().html();
        }
        if (CMS.API && CMS.API.Clipboard) {
            CMS.API.Clipboard.populate(html, pluginData);
        }
    }, 0);

    $document
        .off(Plugin.pointerUp)
        .off(Plugin.keyDown)
        .off(Plugin.keyUp)
        .off(Plugin.click, '.cms-plugin a, a:has(.cms-plugin), a.cms-plugin')
        .on(Plugin.pointerUp, function() {
            // call it as a static method, because otherwise we trigger it the
            // amount of times CMS.Plugin is instantiated,
            // which does not make much sense.
            Plugin._hideSettingsMenu();
        })
        .on(Plugin.keyDown, function(e) {
            if (e.keyCode === KEYS.SHIFT) {
                $document.data('expandmode', true);
                try {
                    $('.cms-plugin:hover').last().trigger('mouseenter');
                    $('.cms-dragitem:hover').last().trigger('mouseenter');
                } catch (err) {}
            }
        })
        .on(Plugin.keyUp, function(e) {
            if (e.keyCode === KEYS.SHIFT) {
                $document.data('expandmode', false);
                try {
                    $(':hover').trigger('mouseleave');
                } catch (err) {}
            }
        })
        .on(Plugin.click, '.cms-plugin a, a:has(.cms-plugin), a.cms-plugin', function(e) {
            var DOUBLECLICK_DELAY = 300;

            // prevents single click from messing up the edit call
            // don't go to the link if there is custom js attached to it
            // or if it's clicked along with shift, ctrl, cmd
            if (e.shiftKey || e.ctrlKey || e.metaKey || e.isDefaultPrevented()) {
                return;
            }
            e.preventDefault();
            if (++clickCounter === 1) {
                timer = setTimeout(function() {
                    var anchor = $(e.target).closest('a');

                    clickCounter = 0;
                    window.open(anchor.attr('href'), anchor.attr('target') || '_self');
                }, DOUBLECLICK_DELAY);
            } else {
                clearTimeout(timer);
                clickCounter = 0;
            }
        });

    // have to delegate here because there might be plugins that
    // have their content replaced by something dynamic. in case that tool
    // copies the classes - double click to edit would still work
    // also - do not try to highlight render_model_blocks, only actual plugins
    $document.on(Plugin.click, '.cms-plugin:not([class*=cms-render-model])', Plugin._clickToHighlightHandler);
    $document.on(`${Plugin.pointerOverAndOut} ${Plugin.touchStart}`, '.cms-plugin', function(e) {
        // required for both, click and touch
        // otherwise propagation won't work to the nested plugin

        e.stopPropagation();
        const pluginContainer = $(e.target).closest('.cms-plugin');
        const allOptions = pluginContainer.data('cms');

        if (!allOptions || !allOptions.length) {
            return;
        }

        const options = allOptions[0];

        if (e.type === 'touchstart') {
            CMS.API.Tooltip._forceTouchOnce();
        }
        var name = options.plugin_name;
        var id = options.plugin_id;
        var type = options.type;

        if (type === 'generic') {
            return;
        }
        var placeholderId = CMS.API.StructureBoard.getId($(`.cms-draggable-${id}`).closest('.cms-dragarea'));
        var placeholder = $('.cms-placeholder-' + placeholderId);

        if (placeholder.length && placeholder.data('cms')) {
            name = placeholder.data('cms').name + ': ' + name;
        }

        CMS.API.Tooltip.displayToggle(e.type === 'pointerover' || e.type === 'touchstart', e, name, id);
    });

    $document.on(Plugin.click, '.cms-dragarea-static .cms-dragbar', e => {
        const placeholder = $(e.target).closest('.cms-dragarea');

        if (placeholder.hasClass('cms-dragarea-static-expanded') && e.isDefaultPrevented()) {
            return;
        }

        placeholder.toggleClass('cms-dragarea-static-expanded');
    });

    $window.on('blur.cms', () => {
        $document.data('expandmode', false);
    });
};

/**
 * @method _isContainingMultiplePlugins
 * @param {jQuery} node to check
 * @static
 * @private
 * @returns {Boolean}
 */
Plugin._isContainingMultiplePlugins = function _isContainingMultiplePlugins(node) {
    var currentData = node.data('cms');

    // istanbul ignore if
    if (!currentData) {
        throw new Error('Provided node is not a cms plugin.');
    }

    var pluginIds = currentData.map(function(pluginData) {
        return pluginData.plugin_id;
    });

    if (pluginIds.length > 1) {
        // another plugin already lives on the same node
        // this only works because the plugins are rendered from
        // the bottom to the top (leaf to root)
        // meaning the deepest plugin is always first
        return true;
    }

    return false;
};

/**
 * Shows and immediately fades out a success notification (when
 * plugin was successfully moved.
 *
 * @method _highlightPluginStructure
 * @private
 * @static
 * @param {jQuery} el draggable element
 */
// eslint-disable-next-line no-magic-numbers
Plugin._highlightPluginStructure = function _highlightPluginStructure(
    el,
    // eslint-disable-next-line no-magic-numbers
    { successTimeout = 200, delay = 1500, seeThrough = false }
) {
    const tpl = $(`
        <div class="cms-dragitem-success ${seeThrough ? 'cms-plugin-overlay-see-through' : ''}">
        </div>
    `);

    el.addClass('cms-draggable-success').append(tpl);
    // start animation
    if (successTimeout) {
        setTimeout(() => {
            tpl.fadeOut(successTimeout, function() {
                $(this).remove();
                el.removeClass('cms-draggable-success');
            });
        }, delay);
    }
    // make sure structurboard gets updated after success
    $(Helpers._getWindow()).trigger('resize.sideframe');
};

/**
 * Highlights plugin in content mode
 *
 * @method _highlightPluginContent
 * @private
 * @static
 * @param {String|Number} pluginId
 */
Plugin._highlightPluginContent = function _highlightPluginContent(
    pluginId,
    // eslint-disable-next-line no-magic-numbers
    { successTimeout = 200, seeThrough = false, delay = 1500, prominent = false } = {}
) {
    var coordinates = {};
    var positions = [];
    var OVERLAY_POSITION_TO_WINDOW_HEIGHT_RATIO = 0.2;

    $('.cms-plugin-' + pluginId).each(function() {
        var el = $(this);
        var offset = el.offset();
        var ml = parseInt(el.css('margin-left'), 10);
        var mr = parseInt(el.css('margin-right'), 10);
        var mt = parseInt(el.css('margin-top'), 10);
        var mb = parseInt(el.css('margin-bottom'), 10);
        var width = el.outerWidth();
        var height = el.outerHeight();

        if (width === 0 && height === 0) {
            return;
        }

        if (isNaN(ml)) {
            ml = 0;
        }
        if (isNaN(mr)) {
            mr = 0;
        }
        if (isNaN(mt)) {
            mt = 0;
        }
        if (isNaN(mb)) {
            mb = 0;
        }

        positions.push({
            x1: offset.left - ml,
            x2: offset.left + width + mr,
            y1: offset.top - mt,
            y2: offset.top + height + mb
        });
    });

    if (positions.length === 0) {
        return;
    }

    // turns out that offset calculation will be off by toolbar height if
    // position is set to "relative" on html element.
    var html = $('html');
    var htmlMargin = html.css('position') === 'relative' ? parseInt($('html').css('margin-top'), 10) : 0;

    coordinates.left = Math.min(...positions.map(pos => pos.x1));
    coordinates.top = Math.min(...positions.map(pos => pos.y1)) - htmlMargin;
    coordinates.width = Math.max(...positions.map(pos => pos.x2)) - coordinates.left;
    coordinates.height = Math.max(...positions.map(pos => pos.y2)) - coordinates.top - htmlMargin;

    $window.scrollTop(coordinates.top - $window.height() * OVERLAY_POSITION_TO_WINDOW_HEIGHT_RATIO);

    $(
        `
        <div class="
            cms-plugin-overlay
            cms-dragitem-success
            cms-plugin-overlay-${pluginId}
            ${seeThrough ? 'cms-plugin-overlay-see-through' : ''}
            ${prominent ? 'cms-plugin-overlay-prominent' : ''}
        "
            data-success-timeout="${successTimeout}"
        >
        </div>
    `
    )
        .css(coordinates)
        .css({
            zIndex: 9999
        })
        .appendTo($('body'));

    if (successTimeout) {
        setTimeout(() => {
            $(`.cms-plugin-overlay-${pluginId}`).fadeOut(successTimeout, function() {
                $(this).remove();
            });
        }, delay);
    }
};

Plugin._clickToHighlightHandler = function _clickToHighlightHandler(e) {
    if (CMS.settings.mode !== 'structure') {
        return;
    }
    e.preventDefault();
    e.stopPropagation();
    // FIXME refactor into an object
    CMS.API.StructureBoard._showAndHighlightPlugin(200, true); // eslint-disable-line no-magic-numbers
};

Plugin._removeHighlightPluginContent = function(pluginId) {
    $(`.cms-plugin-overlay-${pluginId}[data-success-timeout=0]`).remove();
};

Plugin.aliasPluginDuplicatesMap = {};
Plugin.staticPlaceholderDuplicatesMap = {};

// istanbul ignore next
Plugin._initializeTree = function _initializeTree() {
    CMS._plugins = uniqWith(CMS._plugins, ([x], [y]) => x === y);
    CMS._instances = CMS._plugins.map(function(args) {
        return new CMS.Plugin(args[0], args[1]);
    });

    // return the cms plugin instances just created
    return CMS._instances;
};

Plugin._updateClipboard = function _updateClipboard() {
    clipboardDraggable = $('.cms-draggable-from-clipboard:first');
};

Plugin._updateUsageCount = function _updateUsageCount(pluginType) {
    var currentValue = pluginUsageMap[pluginType] || 0;

    pluginUsageMap[pluginType] = currentValue + 1;

    if (Helpers._isStorageSupported) {
        localStorage.setItem('cms-plugin-usage', JSON.stringify(pluginUsageMap));
    }
};

Plugin._removeAddPluginPlaceholder = function removeAddPluginPlaceholder() {
    // this can't be cached since they are created and destroyed all over the place
    $('.cms-add-plugin-placeholder').remove();
};

Plugin._refreshPlugins = function refreshPlugins() {
    Plugin.aliasPluginDuplicatesMap = {};
    Plugin.staticPlaceholderDuplicatesMap = {};
    CMS._plugins = uniqWith(CMS._plugins, isEqual);

    CMS._instances.forEach(instance => {
        if (instance.options.type === 'placeholder') {
            instance._setupUI(`cms-placeholder-${instance.options.placeholder_id}`);
            instance._ensureData();
            instance.ui.container.data('cms', instance.options);
            instance._setPlaceholder();
        }
    });

    CMS._instances.forEach(instance => {
        if (instance.options.type === 'plugin') {
            instance._setupUI(`cms-plugin-${instance.options.plugin_id}`);
            instance._ensureData();
            instance.ui.container.data('cms').push(instance.options);
            instance._setPluginContentEvents();
        }
    });

    CMS._plugins.forEach(([type, opts]) => {
        if (opts.type !== 'placeholder' && opts.type !== 'plugin') {
            const instance = find(
                CMS._instances,
                i => i.options.type === opts.type && Number(i.options.plugin_id) === Number(opts.plugin_id)
            );

            if (instance) {
                // update
                instance._setupUI(type);
                instance._ensureData();
                instance.ui.container.data('cms').push(instance.options);
                instance._setGeneric();
            } else {
                // create
                CMS._instances.push(new Plugin(type, opts));
            }
        }
    });
};

// shorthand for jQuery(document).ready();
$(Plugin._initializeGlobalHandlers);

export default Plugin;
