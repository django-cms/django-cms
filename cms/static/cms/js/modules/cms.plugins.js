/*
 * Copyright https://github.com/divio/django-cms
 */

// #############################################################################
// NAMESPACES
/**
 * @module CMS
 */
/* istanbul ignore next */
var CMS = window.CMS || {};

// #############################################################################
// Plugin
(function ($) {
    'use strict';

    var doc;
    var clipboard;
    var clipboardDraggable;
    var clipboardPlugin;

    /**
     * Class for handling Plugins / Placeholders or Generics.
     * Handles adding / moving / copying / pasting / menus etc
     * in structureboard.
     *
     * @class Plugin
     * @namespace CMS
     * @uses CMS.API.Helpers
     */
    CMS.Plugin = new CMS.Class({

        implement: [CMS.API.Helpers],

        options: {
            type: '', // bar, plugin or generic
            placeholder_id: null,
            plugin_type: '',
            plugin_id: null,
            plugin_language: '',
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

        initialize: function initialize(container, options) {
            this.options = $.extend(true, {}, this.options, options);

            this._setupUI(container);

            // states
            this.csrf = CMS.config.csrf;
            this.click = 'click.cms.plugin';
            this.pointerUp = 'pointerup.cms.plugin';
            this.pointerDown = 'pointerdown.cms.plugin';
            this.pointerOverAndOut = 'pointerover.cms.plugin pointerout.cms.plugin';
            this.doubleClick = 'dblclick.cms.plugin';
            this.keyUp = 'keyup.cms.plugin';
            this.keyDown = 'keydown.cms.plugin';
            this.mouseEvents = 'mousedown.cms.plugin mousemove.cms.plugin mouseup.cms.plugin';
            this.touchStart = 'touchstart.cms.plugin';
            this.touchEnd = 'touchend.cms.plugin';

            // bind data element to the container
            this.ui.container.data('settings', this.options);
            CMS.Plugin._initializeDragItemsStates();

            // determine type of plugin
            switch (this.options.type) {
                case 'placeholder': // handler for placeholder bars
                    this._setPlaceholder();
                    this._collapsables();
                    break;
                case 'plugin': // handler for all plugins
                    this._setPlugin();
                    this._collapsables();
                    break;
                default: // handler for static content
                    this._setGeneric();
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
            var wrapper = $('.' + container);

            this.ui = {
                container: wrapper,
                publish: $('.cms-btn-publish'),
                save: $('.cms-toolbar-item-switch-save-edit'),
                window: $(window),
                revert: $('.cms-toolbar-revert'),
                dragbar: null,
                draggable: null,
                draggables: null,
                submenu: null,
                dropdown: null
            };
        },

        /**
         * Sets up behaviours and ui for placeholder.
         *
         * @method _setPlaceholder
         * @private
         */
        _setPlaceholder: function () {
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
            togglerLinks.off(this.click).on(this.click, function (e) {
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
        _setPlugin: function () {
            var that = this;

            // adds double click to edit
            this.ui.container.add(this.ui.dragitem).on(this.doubleClick, function (e) {
                e.preventDefault();
                e.stopPropagation();

                that.editPlugin(
                    that.options.urls.edit_plugin,
                    that.options.plugin_name,
                    that._getPluginBreadcrumbs()
                );
            });

            // adds edit tooltip
            this.ui.container.on(this.pointerOverAndOut + ' ' + this.touchStart, function (e) {
                // required for both, click and touch
                // otherwise propagation won't work to the nested plugin
                e.stopPropagation();
                if (e.type === 'touchstart') {
                    CMS.API.Tooltip._forceTouchOnce();
                }
                var name = that.options.plugin_name;
                var id = that.options.plugin_id;

                var placeholderId = that._getId(that.ui.dragitem.closest('.cms-dragarea'));
                var placeholder = $('.cms-placeholder-' + placeholderId);

                if (placeholder.length && placeholder.data('settings')) {
                    name = placeholder.data('settings').name + ': ' + name;
                }

                CMS.API.Tooltip.displayToggle(e.type === 'pointerover' || e.type === 'touchstart', e, name, id);
            });

            // adds listener for all plugin updates
            this.ui.container.on('cms.plugins.update', function (e) {
                e.stopPropagation();
                that.movePlugin();
            });

            // adds listener for copy/paste updates
            this.ui.container.on('cms.plugin.update', function (e) {
                e.stopPropagation();

                var el = $(e.delegateTarget);
                var dragitem = $('.cms-draggable-' + el.data('settings').plugin_id);
                var placeholder_id = that._getId(
                    dragitem.parents('.cms-draggables').last().prevAll('.cms-dragbar').first()
                );

                // if placeholder_id is empty, cancel
                if (!placeholder_id) {
                    return false;
                }

                var data = el.data('settings');

                data.target = placeholder_id;
                data.parent = that._getId(dragitem.parent().closest('.cms-draggable'));
                data.move_a_copy = true;

                that.movePlugin(data);
            });

            // filling up ui object
            this.ui.draggable = $('.cms-draggable-' + this.options.plugin_id);
            this.ui.dragitem = this.ui.draggable.find('> .cms-dragitem');
            this.ui.draggables = this.ui.draggable.find('> .cms-draggables');
            this.ui.submenu = this.ui.dragitem.find('.cms-submenu');

            // attach event to the plugin menu
            this._setSettingsMenu(this.ui.submenu);

            // attach events for the "Add plugin" modal
            this._setAddPluginModal(this.ui.dragitem.find('.cms-submenu-add'));

            // clickability of "Paste" menu item
            this._checkIfPasteAllowed();
        },

        /**
         * Sets up behaviours and ui for generics.
         * Generics do not show up in structure board.
         *
         * @method _setGeneric
         * @private
         */
        _setGeneric: function () {
            var that = this;

            // adds double click to edit
            this.ui.container.on(this.doubleClick, function (e) {
                e.preventDefault();
                e.stopPropagation();
                that.editPlugin(that.options.urls.edit_plugin, that.options.plugin_name, []);
            });

            // adds edit tooltip
            this.ui.container.on(this.pointerOverAndOut + ' ' + this.touchStart, function (e) {
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
         * first, so they have data('settings') by the time this method is called.
         *
         * @method _checkIfPasteAllowed
         * @private
         * @returns {Boolean}
         */
        _checkIfPasteAllowed: function _checkIfPasteAllowed() {
            var pasteButton = this.ui.dropdown.find('[data-rel=paste]');
            var pasteItem = pasteButton.parent();

            if (!clipboardPlugin.length) {
                pasteItem.addClass('cms-submenu-item-disabled');
                pasteItem.find('.cms-submenu-item-paste-tooltip-empty').css('display', 'block');
                return false;
            }

            if (this.ui.draggable && this.ui.draggable.hasClass('cms-draggable-disabled')) {
                pasteItem.addClass('cms-submenu-item-disabled');
                pasteItem.find('.cms-submenu-item-paste-tooltip-disabled').css('display', 'block');
                return false;
            }

            var bounds = this.options.plugin_restriction;

            if (clipboardPlugin.data('settings')) {
                var type = clipboardPlugin.data('settings').plugin_type;
                var parent_bounds = $.grep(clipboardPlugin.data('settings').plugin_parent_restriction, function (r) {
                    // special case when PlaceholderPlugin has a parent restriction named "0"
                    return r !== '0';
                });
                var currentPluginType = this.options.plugin_type;

                if ((bounds.length && $.inArray(type, bounds) === -1) ||
                    (parent_bounds.length && $.inArray(currentPluginType, parent_bounds) === -1)) {
                    pasteItem.addClass('cms-submenu-item-disabled');
                    pasteItem.find('.cms-submenu-item-paste-tooltip-restricted').css('display', 'block');
                    return false;
                }
            } else {
                return false;
            }

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
        addPlugin: function (type, name, parent) {
            var params = {
                placeholder_id: this.options.placeholder_id,
                plugin_type: type,
                plugin_language: this.options.plugin_language
            };

            if (parent) {
                params.plugin_parent = parent;
            }
            var url = this.options.urls.add_plugin + '?' + $.param(params);
            var modal = new CMS.Modal({
                onClose: this.options.onClose || false,
                redirectOnClose: this.options.redirectOnClose || false
            });

            modal.open({
                url: url,
                title: name
            });
            modal.on('cms.modal.closed', function removePlaceholder() {
                $('.cms-add-plugin-placeholder').remove();
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
        editPlugin: function (url, name, breadcrumb) {
            // trigger modal window
            var modal = new CMS.Modal({
                onClose: this.options.onClose || false,
                redirectOnClose: this.options.redirectOnClose || false
            });

            modal.on('cms.modal.loaded', function removePlaceholder() {
                $('.cms-add-plugin-placeholder').remove();
            });
            modal.on('cms.modal.closed', function removePlaceholder() {
                $('.cms-add-plugin-placeholder').remove();
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
        copyPlugin: function (opts, source_language) {
            // cancel request if already in progress
            if (CMS.API.locked) {
                return false;
            }
            CMS.API.locked = true;

            var move = !!(opts || source_language);

            // set correct options
            var options = opts || this.options;
            var sourceLanguage = source_language;

            if (sourceLanguage) {
                options.target = options.placeholder_id;
                options.plugin_id = '';
                options.parent = '';
            } else {
                sourceLanguage = options.plugin_language;
            }

            var data = {
                source_placeholder_id: options.placeholder_id,
                source_plugin_id: options.plugin_id || '',
                source_language: sourceLanguage,
                target_plugin_id: options.parent || '',
                target_placeholder_id: options.target || CMS.config.clipboard.id,
                target_language: options.page_language || sourceLanguage,
                csrfmiddlewaretoken: this.csrf
            };
            var request = {
                type: 'POST',
                url: options.urls.copy_plugin,
                data: data,
                success: function () {
                    CMS.API.Messages.open({
                        message: CMS.config.lang.success
                    });
                    // reload
                    CMS.API.Helpers.reloadBrowser();
                },
                error: function (jqXHR) {
                    CMS.API.locked = false;
                    var msg = CMS.config.lang.error;

                    // trigger error
                    CMS.API.Messages.open({
                        message: msg + jqXHR.responseText || jqXHR.status + ' ' + jqXHR.statusText,
                        error: true
                    });
                }
            };

            if (move) {
                $.ajax(request);
            } else {
                // ensure clipboard is cleaned
                CMS.API.Clipboard.clear(function () {
                    $.ajax(request);
                });
            }
        },

        /**
         * Essentially clears clipboard and moves plugin to a clipboard
         * placholder through `movePlugin`.
         *
         * @method cutPlugin
         * @returns {Boolean|void}
         */
        cutPlugin: function () {
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
                plugin_language: this.options.page_language,
                plugin_order: [this.options.plugin_id],
                csrfmiddlewaretoken: this.csrf
            };

            // ensure clipboard is cleaned
            CMS.API.Clipboard.clear(function () {
                // cancel request if already in progress
                if (CMS.API.locked) {
                    return false;
                }
                CMS.API.locked = true;

                // move plugin
                $.ajax({
                    type: 'POST',
                    url: that.options.urls.move_plugin,
                    data: data,
                    success: function () {
                        CMS.API.Messages.open({
                            message: CMS.config.lang.success
                        });
                        // if response is reload
                        CMS.API.Helpers.reloadBrowser();
                    },
                    error: function (jqXHR) {
                        CMS.API.locked = false;
                        var msg = CMS.config.lang.error;

                        // trigger error
                        CMS.API.Messages.open({
                            message: msg + jqXHR.responseText || jqXHR.status + ' ' + jqXHR.statusText,
                            error: true
                        });
                    }
                });
            });
        },

        /**
         * Method is called when you click on the paste button on the plugin.
         * Uses existing solution of `copyPlugin(options)`
         *
         * @method pastePlugin
         */
        pastePlugin: function () {
            clipboardDraggable.appendTo(this.ui.draggables);
            this.ui.draggables.trigger('cms.update');
            clipboardPlugin.trigger('cms.plugin.update');
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
         * @param {String} [opts.plugin_language]
         * @param {Boolean} [opts.move_a_copy]
         * @returns {Boolean|void}
         */
        movePlugin: function (opts) {
            // cancel request if already in progress
            if (CMS.API.locked) {
                return false;
            }
            CMS.API.locked = true;

            var that = this;
            // set correct options
            var options = opts || this.options;

            var plugin = $('.cms-plugin-' + options.plugin_id);
            var dragitem = $('.cms-draggable-' + options.plugin_id);

            // SETTING POSITION
            this._setPosition(options.plugin_id, plugin, dragitem);

            // SAVING POSITION
            var placeholder_id = this._getId(
                dragitem.parents('.cms-draggables').last().prevAll('.cms-dragbar').first()
            );
            var plugin_parent = this._getId(dragitem.parent().closest('.cms-draggable'));
            var plugin_order = this._getIds(dragitem.siblings('.cms-draggable').andSelf());

            if (options.move_a_copy) {
                plugin_order = plugin_order.map(function (pluginId) {
                    var id = pluginId;

                    // TODO correct way would be to check if it's actually a
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
                // this is a hack: when moving to different languages use the global language
                plugin_language: options.page_language,
                plugin_order: plugin_order,
                csrfmiddlewaretoken: this.csrf,
                move_a_copy: options.move_a_copy
            };

            CMS.API.Toolbar.showLoader();

            $.ajax({
                type: 'POST',
                url: options.urls.move_plugin,
                data: data,
                success: function (response) {
                    // if response is reload
                    if (response.reload) {
                        CMS.API.Helpers.reloadBrowser();
                    }

                    // set new url settings when moving #4803
                    if (response.urls) {
                        that._setSettings(options, {
                            urls: response.urls
                        });
                    }

                    // enable actions again
                    CMS.API.locked = false;
                    CMS.API.Toolbar.hideLoader();

                    // TODO: show only if (response.status)
                    that._showSuccess(dragitem);
                    CMS.Plugin._updateRegistry({
                        pluginId: options.plugin_id,
                        update: {
                            plugin_parent: plugin_parent || '',
                            placeholder_id: placeholder_id
                        }
                    });
                    that._setSettings(that.options, {
                        plugin_parent: plugin_parent || '',
                        placeholder_id: placeholder_id
                    });
                },
                error: function (jqXHR) {
                    CMS.API.locked = false;
                    var msg = CMS.config.lang.error;

                    // trigger error
                    CMS.API.Messages.open({
                        message: msg + jqXHR.responseText || jqXHR.status + ' ' + jqXHR.statusText,
                        error: true
                    });
                    CMS.API.Toolbar.hideLoader();
                }
            });

            // show publish / save buttons
            this.ui.publish
                .addClass('cms-btn-publish-active')
                .removeClass('cms-btn-disabled')
                .parent().show();
            this.ui.window.trigger('resize');

            // enable revert to live
            this.ui.revert.removeClass('cms-toolbar-item-navigation-disabled');
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

            // set new setting on instance and plugin data
            this.options = settings;
            plugin.data('settings', settings);
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
        deletePlugin: function (url, name, breadcrumb) {
            // trigger modal window
            var modal = new CMS.Modal({
                onClose: this.options.onClose || false,
                redirectOnClose: this.options.redirectOnClose || false
            });

            modal.on('cms.modal.loaded', function removePlaceholder() {
                $('.cms-add-plugin-placeholder').remove();
            });
            modal.open({
                url: url,
                title: name,
                breadcrumbs: breadcrumb
            });
        },

        /**
         * Moves the plugin according to the place it should have in content mode.
         *
         * @method _setPosition
         * @private
         * @param {String} id
         * @param {jQuery} plugin the `.cms-plugin` element
         * @param {jQuery} dragitem the `.cms-draggable` of the plugin
         */
        _setPosition: function (id, plugin, dragitem) {
            // after we insert the plugin onto its new place, we need to figure out where to position it
            var prevItem = dragitem.prev('.cms-draggable');
            var nextItem = dragitem.next('.cms-draggable');
            var parent = dragitem.parent().closest('.cms-draggable');
            var child = $('.cms-plugin-' + this._getId(parent));
            var placeholder = dragitem.closest('.cms-dragarea');

            // determine if there are other plugins within the same level, this makes the move easier
            if (prevItem.length) {
                plugin.insertAfter($('.cms-plugin-' + this._getId(prevItem)));
            } else if (nextItem.length) {
                plugin.insertBefore($('.cms-plugin-' + this._getId(nextItem)));
            } else if (parent.length) {
                // if we can't find a plugin on the same level, we need to travel higher
                // for this we need to find the deepest child
                while (child.children().length) {
                    child = child.children();
                }
                child.append(plugin);
            } else if (placeholder.length) {
                // we also need to cover the case if we move the plugin to an empty placeholder
                plugin.insertAfter($('.cms-placeholder-' + this._getId(placeholder)));
            } else {
                // if we did not found a match, reload
                CMS.API.Helpers.reloadBrowser();
            }
        },

        /**
         * Called after plugin is added through ajax.
         *
         * @method editPluginPostAjax
         * @param {Object} toolbar CMS.API.Toolbar instance (not used)
         * @param {Object} response response from server
         */
        editPluginPostAjax: function (toolbar, response) {
            this.editPlugin(response.url, this.options.plugin_name, response.breadcrumb);
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

            nav.on(this.pointerUp, function (e) {
                e.preventDefault();
                e.stopPropagation();
                var trigger = $(this);

                if (trigger.hasClass('cms-btn-active')) {
                    CMS.Plugin._hideSettingsMenu(trigger);
                } else {
                    CMS.Plugin._hideSettingsMenu();
                    that._showSettingsMenu(trigger);
                }
            }).on(this.touchStart, function (e) {
                // required on some touch devices so
                // ui touch punch is not triggering mousemove
                // which in turn results in pep triggering pointercancel
                e.stopPropagation();
            });

            dropdown.on(this.mouseEvents, function (e) {
                e.stopPropagation();
            }).on(this.touchStart, function (e) {
                // required for scrolling on mobile
                e.stopPropagation();
            });

            that._setupActions(nav);
            // prevent propagation
            nav.on([this.pointerUp, this.pointerDown, this.click, this.doubleClick].join(' '), function (e) {
                e.stopPropagation();
            });

            nav.siblings('.cms-quicksearch, .cms-submenu-dropdown-settings')
                .on([this.pointerUp, this.click, this.doubleClick].join(' '), function (e) {
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
            var win = $(window);
            var scrollHeight = win.height();
            var scrollTop = scrollable.scrollTop();
            var elPosition = el.position().top;
            var elHeight = el.height();
            var isInViewport = elPosition + elHeight + offset <= scrollHeight;

            if (!isInViewport) {
                scrollable.animate({
                    scrollTop: elPosition + offset + elHeight + scrollTop - scrollHeight
                }, duration);
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
            var placeholder = $(
                '<div class="cms-add-plugin-placeholder">' +
                    CMS.config.lang.addPluginPlaceholder +
                '</div>'
            );
            var modal = new CMS.Modal({
                minWidth: 400,
                minHeight: 400
            });
            var dragItem = nav.closest('.cms-dragitem');
            var isPlaceholder = !dragItem.length;
            var childrenList;
            var isTouching;

            if (isPlaceholder) {
                childrenList = nav.closest('.cms-dragarea').find('> .cms-draggables');
            } else {
                childrenList = nav.closest('.cms-draggable').find('> .cms-draggables');
            }

            modal.on('cms.modal.loaded', $.proxy(that._setupKeyboardTraversing, that));
            modal.on('cms.modal.loaded', function addPlaceholder() {
                if (childrenList.hasClass('cms-hidden') && !isPlaceholder) {
                    that._toggleCollapsable(dragItem);
                }
                $('.cms-add-plugin-placeholder').remove();
                placeholder.appendTo(childrenList);
                that._scrollToElement(placeholder);
            });
            modal.on('cms.modal.closed', function removePlaceholder() {
                $('.cms-add-plugin-placeholder').remove();
            });
            modal.on('cms.modal.shown', function () {
                var dropdown = $('.cms-modal-markup .cms-plugin-picker');

                if (!isTouching) {
                    // only focus the field if using mouse
                    // otherwise keyboard pops up
                    dropdown.find('input').trigger('focus');
                }
                isTouching = false;
            });

            var plugins = nav.siblings('.cms-plugin-picker');

            that._setupQuickSearch(plugins);

            nav.on(this.touchStart, function (e) {
                isTouching = true;
                // required on some touch devices so
                // ui touch punch is not triggering mousemove
                // which in turn results in pep triggering pointercancel
                e.stopPropagation();
            }).on(this.pointerUp, function (e) {
                e.preventDefault();
                e.stopPropagation();

                CMS.Plugin._hideSettingsMenu();

                // since we don't know exact plugin parent (because dragndrop)
                // we need to know the parent id by the time we open "add plugin" dialog
                var pluginsCopy = plugins.clone(true, true).data(
                    'parentId', that._getId(nav.closest('.cms-draggable'))
                ).append(that._getPossibleChildClasses());

                modal.open({
                    title: that.options.addPluginHelpTitle,
                    html: pluginsCopy,
                    width: 530,
                    height: 400
                });
            });

            // prevent propagation
            nav.on([this.pointerUp, this.pointerDown, this.click, this.doubleClick].join(' '), function (e) {
                e.stopPropagation();
            });

            nav.siblings('.cms-quicksearch, .cms-submenu-dropdown')
                .on([this.pointerUp, this.click, this.doubleClick].join(' '), function (e) {
                    e.stopPropagation();
                });
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
                resultElements = resultElements.filter(function () {
                    var item = $(this);

                    return item.hasClass('cms-submenu-item-title') ||
                        childRestrictions.indexOf(item.find('a').attr('href')) !== -1;
                });

                resultElements = resultElements.filter(function (index) {
                    var item = $(this);

                    return !item.hasClass('cms-submenu-item-title') ||
                        item.hasClass('cms-submenu-item-title') && (
                            !resultElements.eq(index + 1).hasClass('cms-submenu-item-title') &&
                            resultElements.eq(index + 1).length
                        );
                });
            }

            resultElements.find('a').on(that.click, that._delegate.bind(that));

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

            var handler = CMS.API.Helpers.debounce(function () {
                var input = $(this);
                // have to always find the pluginsPicker in the handler
                // because of how we move things into/out of the modal
                var pluginsPicker = input.closest('.cms-plugin-picker');

                that._filterPluginsList(pluginsPicker, input);
            }, FILTER_DEBOUNCE_TIMER);

            plugins.find('> .cms-quicksearch').find('input')
                .on(this.keyUp, handler)
                .on(this.keyUp, CMS.API.Helpers.debounce(function (e) {
                    var input;
                    var pluginsPicker;

                    if (e.keyCode === CMS.KEYS.ENTER) {
                        input = $(this);
                        pluginsPicker = input.closest('.cms-plugin-picker');
                        pluginsPicker.find('.cms-submenu-item')
                            .not('.cms-submenu-item-title').filter(':visible').first().find('> a').focus()
                            .trigger('click');
                    }
                }, FILTER_PICK_DEBOUNCE_TIMER));
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

            nav.parent().find('.cms-submenu-edit').on(this.touchStart, function (e) {
                // required on some touch devices so
                // ui touch punch is not triggering mousemove
                // which in turn results in pep triggering pointercancel
                e.stopPropagation();
            });
            nav.parent().find(items).on(this.click, nav, this._delegate.bind(this));
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
            CMS.API.Toolbar.showLoader();

            var items = '.cms-submenu-edit, .cms-submenu-item a';
            var el = $(e.target).closest(items);

            CMS.Plugin._hideSettingsMenu(nav);

            // set switch for subnav entries
            switch (el.attr('data-rel')) {
                case 'add':
                    that.addPlugin(
                        el.attr('href').replace('#', ''),
                        el.text(),
                        el.closest('.cms-plugin-picker').data('parentId')
                    );
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
                        that.options.urls.edit_plugin,
                        that.options.plugin_name,
                        that._getPluginBreadcrumbs()
                    );
                    break;
                case 'copy-lang':
                    that.copyPlugin(that.options, el.attr('data-language'));
                    break;
                case 'copy':
                    if (el.parent().hasClass('cms-submenu-item-disabled')) {
                        CMS.API.Toolbar.hideLoader();
                    } else {
                        that.copyPlugin();
                    }
                    break;
                case 'cut':
                    that.cutPlugin();
                    break;
                case 'paste':
                    if (el.parent().hasClass('cms-submenu-item-disabled')) {
                        CMS.API.Toolbar.hideLoader();
                    } else {
                        that.pastePlugin();
                    }
                    break;
                case 'delete':
                    that.deletePlugin(
                        that.options.urls.delete_plugin,
                        that.options.plugin_name,
                        that._getPluginBreadcrumbs()
                    );
                    break;
                default:
                    CMS.API.Toolbar.hideLoader();
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

            if (!dropdown.length) {
                return;
            }
            // add key events
            doc.off(this.keyDown + '.traverse');
            // istanbul ignore next: not really possible to reproduce focus state in unit tests
            doc.on(this.keyDown + '.traverse', function (e) {
                var anchors = dropdown.find('.cms-submenu-item:visible a');
                var index = anchors.index(anchors.filter(':focus'));

                // bind arrow down and tab keys
                if (e.keyCode === CMS.KEYS.DOWN || (e.keyCode === CMS.KEYS.TAB && !e.shiftKey)) {
                    e.preventDefault();
                    if (index >= 0 && index < anchors.length - 1) {
                        anchors.eq(index + 1).focus();
                    } else {
                        anchors.eq(0).focus();
                    }
                }

                // bind arrow up and shift+tab keys
                if (e.keyCode === CMS.KEYS.UP || (e.keyCode === CMS.KEYS.TAB && e.shiftKey)) {
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
        _showSettingsMenu: function (nav) {
            var dropdown = this.ui.dropdown;
            var parents = nav.parentsUntil('.cms-dragarea').last();
            var MIN_SCREEN_MARGIN = 10;

            nav.addClass('cms-btn-active');
            parents.addClass('cms-z-index-9999');

            // set visible states
            dropdown.show();

            // calculate dropdown positioning
            if (this.ui.window.height() + this.ui.window.scrollTop() -
                nav.offset().top - dropdown.height() <= MIN_SCREEN_MARGIN &&
                nav.offset().top - dropdown.height() >= 0) {
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

            // loop through items and figure out if we need to hide items
            items.find('a, span').each(function (index, submenuItem) {
                var item = $(submenuItem);
                var text = item.text().toLowerCase();
                var search = query.toLowerCase();

                if (text.indexOf(search) >= 0) {
                    item.parent().show();
                } else {
                    item.parent().hide();
                }
            });

            // check if a title is matching
            titles.filter(':visible').each(function (index, item) {
                titles.hide();
                $(item).nextUntil('.cms-submenu-item-title').show();
            });

            // always display title of a category
            items.filter(':visible').each(function (index, titleItem) {
                var item = $(titleItem);

                if (item.prev().hasClass('cms-submenu-item-title')) {
                    item.prev().show();
                } else {
                    item.prevUntil('.cms-submenu-item-title').last().prev().show();
                }
            });
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
            var draggable = this.ui.draggable;
            var items;

            var settings = CMS.settings;

            settings.states = settings.states || [];

            // collapsable function and save states
            if (el.hasClass('cms-dragitem-expanded')) {
                settings.states.splice($.inArray(id, settings.states), 1);
                el.removeClass('cms-dragitem-expanded').parent()
                    .find('> .cms-collapsable-container').addClass('cms-hidden');

                if (doc.data('expandmode')) {
                    items = draggable.find('.cms-draggable').find('.cms-dragitem-collapsable');
                    if (!items.length) {
                        return false;
                    }
                    items.each(function () {
                        var item = $(this);

                        if (item.hasClass('cms-dragitem-expanded')) {
                            that._toggleCollapsable(item);
                        }
                    });
                }

            } else {
                settings.states.push(id);
                el.addClass('cms-dragitem-expanded').parent()
                    .find('> .cms-collapsable-container').removeClass('cms-hidden');

                if (doc.data('expandmode')) {
                    items = draggable.find('.cms-draggable').find('.cms-dragitem-collapsable');
                    if (!items.length) {
                        return false;
                    }
                    items.each(function () {
                        var item = $(this);

                        if (!item.hasClass('cms-dragitem-expanded')) {
                            that._toggleCollapsable(item);
                        }
                    });
                }
            }

            // make sure structurboard gets updated after expanding
            this.ui.window.trigger('resize.sideframe');

            // save settings
            CMS.API.Toolbar.setSettings(settings);
        },

        /**
         * Sets up collabspable event handlers.
         *
         * @method _collapsables
         * @private
         * @returns {Boolean|void}
         */
        _collapsables: function () {
            // one time setup
            var that = this;

            this.ui.draggable = $('.cms-draggable-' + this.options.plugin_id);
            var dragitem = this.ui.draggable.find('> .cms-dragitem');

            // check which button should be shown for collapsemenu
            this.ui.container.each(function (index, item) {
                var els = $(item).find('.cms-dragitem-collapsable');
                var open = els.filter('.cms-dragitem-expanded');

                if (els.length === open.length && (els.length + open.length !== 0)) {
                    $(item).find('.cms-dragbar-title').addClass('cms-dragbar-title-expanded');
                }
            });
            // cancel here if its not a draggable
            if (!this.ui.draggable.length) {
                return false;
            }

            // attach events to draggable
            // debounce here required because on some devices click is not triggered,
            // so we consolidate latest click and touch event to run the collapse only once
            dragitem.find('> .cms-dragitem-text').on(
                this.touchEnd + ' ' + this.click,
                CMS.API.Helpers.debounce(function () {
                    if (!dragitem.hasClass('cms-dragitem-collapsable')) {
                        return;
                    }
                    that._toggleCollapsable(dragitem);
                }, 0)
            );

            // adds double click event
            this.ui.draggable.on(this.doubleClick, function (e) {
                e.stopPropagation();
                $('.cms-plugin-' + that._getId($(this))).trigger('dblclick.cms');
            });
        },

        /**
         * Expands all the collapsables in the given placeholder.
         *
         * @method _expandAll
         * @private
         * @param {jQuery} el trigger element that is a child of a placeholder
         * @returns {Boolean|void}
         */
        _expandAll: function (el) {
            var that = this;
            var items = el.closest('.cms-dragarea').find('.cms-dragitem-collapsable');

            // cancel if there are no items
            if (!items.length) {
                return false;
            }
            items.each(function () {
                var item = $(this);

                if (!item.hasClass('cms-dragitem-expanded')) {
                    that._toggleCollapsable(item);
                }
            });

            el.addClass('cms-dragbar-title-expanded');

            var settings = CMS.settings;

            settings.dragbars = settings.dragbars || [];
            settings.dragbars.push(this.options.placeholder_id);
            CMS.API.Toolbar.setSettings(settings);
        },

        /**
         * Collapses all the collapsables in the given placeholder.
         *
         * @method _collapseAll
         * @private
         * @param {jQuery} el trigger element that is a child of a placeholder
         */
        _collapseAll: function (el) {
            var that = this;
            var items = el.closest('.cms-dragarea').find('.cms-dragitem-collapsable');

            items.each(function () {
                var item = $(this);

                if (item.hasClass('cms-dragitem-expanded')) {
                    that._toggleCollapsable(item);
                }
            });

            el.removeClass('cms-dragbar-title-expanded');

            var settings = CMS.settings;

            settings.dragbars = settings.dragbars || [];
            settings.dragbars.splice($.inArray(this.options.placeholder_id, settings.states), 1);
            CMS.API.Toolbar.setSettings(settings);
        },

        /**
         * Gets the id of the element, uses CMS.StructureBoard instance.
         *
         * @method _getId
         * @private
         * @param {jQuery} el element to get id from
         * @returns {String}
         */
        _getId: function (el) {
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
        _getIds: function (els) {
            return CMS.API.StructureBoard.getIds(els);
        },

        /**
         * Shows and immediately fades out a success notification (when
         * plugin was successfully moved.
         *
         * @method _showSuccess
         * @private
         * @param {jQuery} el draggable element
         */
        _showSuccess: function (el) {
            var tpl = $('<div class="cms-dragitem-success"></div>');
            var SUCCESS_TIMEOUT = 1000;

            el.addClass('cms-draggable-success').append(tpl);
            // start animation
            tpl.fadeOut(SUCCESS_TIMEOUT, function () {
                $(this).remove();
                el.removeClass('cms-draggable-success');
            });
            // make sure structurboard gets updated after success
            this.ui.window.trigger('resize.sideframe');
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

            var findParentPlugin = function (id) {
                return $.grep(CMS._plugins || [], function (pluginOptions) {
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


    /**
     * Updates plugin data in CMS._plugins.
     * Keep in mind that it doesn't update children plugins, and you
     * probably want that.
     *
     * @method _updateRegistry
     * @private
     * @static
     * @param {Object} opts options
     * @param {String|Number} opts.pluginId id
     * @param {Object} opts.update object with data to update
     */
    CMS.Plugin._updateRegistry = function _updateRegistry(opts) {
        var pluginEntryIndex = (CMS._plugins || []).findIndex(function (pluginOptions) {
            return pluginOptions[0] === 'cms-plugin-' + opts.pluginId;
        });

        if (pluginEntryIndex === -1) {
            return;
        }

        $.extend(true, CMS._plugins[pluginEntryIndex][1], opts.update);
    };

    /**
     * Hides the opened settings menu. By default looks for any open ones.
     *
     * @method _hideSettingsMenu
     * @static
     * @private
     * @param {jQuery} [navEl] element representing the subnav trigger
     */
    CMS.Plugin._hideSettingsMenu = function (navEl) {
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
        nav.siblings('.cms-quicksearch')
            .find('input')
            .val('')
            .trigger(this.keyUp).blur();

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
    CMS.Plugin._initializeGlobalHandlers = function _initializeGlobalHandlers() {
        var timer;
        var clickCounter = 0;

        doc = $(document);
        clipboard = $('.cms-clipboard');
        clipboardDraggable = clipboard.find('.cms-draggable:first');
        clipboardPlugin = clipboard.find('.cms-plugin:first');

        doc.on('pointerup.cms.plugin', function () {
            // call it as a static method, because otherwise we trigger it the
            // amount of times CMS.Plugin is instantiated,
            // which does not make much sense.
            CMS.Plugin._hideSettingsMenu();
        }).on('keydown.cms.plugin', function (e) {
            if (e.keyCode === CMS.KEYS.SHIFT) {
                doc.data('expandmode', true);
            }
        }).on('keyup.cms.plugin', function (e) {
            if (e.keyCode === CMS.KEYS.SHIFT) {
                doc.data('expandmode', false);
            }
        }).on('click.cms.plugin', '.cms-plugin a, a:has(.cms-plugin)', function (e) {
            var DOUBLECLICK_DELAY = 300;

            // prevents single click from messing up the edit call
            // don't go to the link if there is custom js attached to it
            // or if it's clicked along with shift, ctrl, cmd
            if (e.shiftKey || e.ctrlKey || e.metaKey || e.isDefaultPrevented()) {
                return;
            }
            e.preventDefault();
            if (++clickCounter === 1) {
                timer = setTimeout(function () {
                    var anchor = $(e.currentTarget);

                    clickCounter = 0;
                    // make sure that the target attribute is honoured on links
                    window.open(anchor.attr('href'), anchor.attr('target') || '_self');
                }, DOUBLECLICK_DELAY);
            } else {
                clearTimeout(timer);
                clickCounter = 0;
            }
        });
    };

    /**
     * Initializes the collapsed/expanded states of dragitems in structureboard.
     *
     * @method _initializeDragItemsStates
     * @static
     * @private
     */
    CMS.Plugin._initializeDragItemsStates = CMS.API.Helpers.once(function _initializeDragItemsStates() {
        // removing duplicate entries
        var states = CMS.settings.states || [];
        var sortedArr = states.sort();
        var filteredArray = [];

        for (var i = 0; i < sortedArr.length; i++) {
            if (sortedArr[i] !== sortedArr[i + 1]) {
                filteredArray.push(sortedArr[i]);
            }
        }
        CMS.settings.states = filteredArray;

        // loop through the items
        $.each(CMS.settings.states, function (index, id) {
            var el = $('.cms-draggable-' + id);

            // only add this class to elements which have a draggable area
            if (el.find('.cms-draggables').length) {
                el.find('> .cms-collapsable-container').removeClass('cms-hidden');
                el.find('> .cms-dragitem').addClass('cms-dragitem-expanded');
            }
        });
    });

    // shorthand for jQuery(document).ready();
    $(CMS.Plugin._initializeGlobalHandlers);

})(CMS.$);
