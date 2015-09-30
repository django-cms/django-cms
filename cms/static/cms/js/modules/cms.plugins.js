//##################################################################################################################
// #PLUGINS#
/* global CMS */

(function ($) {
    'use strict';

    // CMS.$ will be passed for $
    $(function () {
        var doc = $(document);
        doc.on('pointerup.cms', function () {
            // call it as a static method, because otherwise we trigger it the amount of times
            // CMS.Plugin is instantiated, which does not make much sense
            CMS.Plugin._hideSettingsMenu();
        }).on('keydown.cms', function (e) {
            if (e.keyCode === CMS.KEYS.SHIFT) {
                doc.data('expandmode', true);
            }
        }).on('keyup.cms', function (e) {
            if (e.keyCode === CMS.KEYS.SHIFT) {
                doc.data('expandmode', false);
            }
        });

        /*!
         * Plugins
         * for created plugins or generics (static content)
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
                plugin_breadcrumb: [],
                plugin_restriction: [],
                urls: {
                    add_plugin: '',
                    edit_plugin: '',
                    move_plugin: '',
                    copy_plugin: '',
                    delete_plugin: ''
                }
            },

            initialize: function (container, options) {
                this.options = $.extend(true, {}, this.options, options);

                this._setupUI(container);

                // states
                this.csrf = CMS.config.csrf;
                this.click = 'pointerup.cms';

                // bind data element to the container
                this.ui.container.data('settings', this.options);

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

            _setupUI: function setupUI(container) {
                container = $('.' + container);
                this.ui = {
                    container: container,
                    publish: $('.cms-btn-publish'),
                    window: $(window),
                    revert: $('.cms-toolbar-revert'),
                    dragbar: null,
                    draggable: null,
                    submenu: null,
                    dropdown: null
                };
            },

            // initial methods
            _setPlaceholder: function () {
                var that = this;
                this.ui.dragbar = $('.cms-dragbar-' + this.options.placeholder_id);
                this.ui.submenu = this.ui.dragbar.find('.cms-submenu-settings');
                var title = this.ui.dragbar.find('.cms-dragbar-title');
                var togglerLinks = this.ui.dragbar.find('.cms-dragbar-toggler a');
                var expanded = 'cms-dragbar-title-expanded';

                // register the subnav on the placeholder
                this._setSettingsMenu(this.ui.submenu);
                this._setAddPluginModal(this.ui.dragbar.find('.cms-submenu-add'));

                CMS.settings.dragbars = CMS.settings.dragbars || []; // expanded dragbars array

                // enable expanding/collapsing globally within the placeholder
                togglerLinks.on('click', function (e) {
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
            },

            _setPlugin: function () {
                var that = this;

                // adds double click to edit
                this.ui.container.on('dblclick', function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    that.editPlugin(
                        that.options.urls.edit_plugin,
                        that.options.plugin_name,
                        that.options.plugin_breadcrumb
                    );
                });

                // adds edit tooltip
                this.ui.container.on('pointerover.cms pointerout.cms', function (e) {
                    e.stopPropagation();
                    var name = that.options.plugin_name;
                    var id = that.options.plugin_id;
                    (e.type === 'pointerover') ? that.showTooltip(e, name, id) : that.hideTooltip();
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

                    that.copyPlugin(data);
                });

                // variables for dragitems
                this.ui.draggable = $('.cms-draggable-' + this.options.plugin_id);
                this.ui.dragitem = this.ui.draggable.find('> .cms-dragitem');
                this.ui.submenu = this.ui.dragitem.find('.cms-submenu');

                // attach event to the plugin menu
                this._setSettingsMenu(this.ui.submenu);
                this._setAddPluginModal(this.ui.dragitem.find('.cms-submenu-add'));

                // adds double click to edit
                this.ui.dragitem.on('dblclick', function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    that.editPlugin(
                        that.options.urls.edit_plugin,
                        that.options.plugin_name,
                        that.options.plugin_breadcrumb
                    );
                });
            },

            _setGeneric: function () {
                var that = this;

                // adds double click to edit
                this.ui.container.on('dblclick', function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    that.editPlugin(that.options.urls.edit_plugin, that.options.plugin_name, []);
                });

                // adds edit tooltip
                this.ui.container.on('pointerover.cms pointerout.cms', function (e) {
                    e.stopPropagation();
                    var name = that.options.plugin_name;
                    var id = that.options.plugin_id;
                    if (e.type === 'pointerover') {
                        that.showTooltip(e, name, id);
                    } else {
                        that.hideTooltip();
                    }
                });
            },

            // public methods
            addPlugin: function (type, name, parent) {
                // cancel request if already in progress
                if (CMS.API.locked) {
                    return false;
                }
                CMS.API.locked = true;

                var that = this;
                var data = {
                    placeholder_id: this.options.placeholder_id,
                    plugin_type: type,
                    plugin_parent: parent || '',
                    plugin_language: this.options.plugin_language,
                    csrfmiddlewaretoken: this.csrf
                };

                $.ajax({
                    type: 'POST',
                    url: this.options.urls.add_plugin,
                    data: data,
                    success: function (data) {
                        CMS.API.locked = false;
                        that.newPlugin = data;
                        that.editPlugin(data.url, name, data.breadcrumb);
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
            },

            editPlugin: function (url, name, breadcrumb) {
                // trigger modal window
                var modal = new CMS.Modal({
                    newPlugin: this.newPlugin || false,
                    onClose: this.options.onClose || false,
                    redirectOnClose: this.options.redirectOnClose || false
                });
                if (!this.newPlugin) {
                    modal.on('cms.modal.loaded', function removePlaceholder() {
                        $('.cms-add-plugin-placeholder').remove();
                    });
                }
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

            copyPlugin: function (options, source_language) {
                // cancel request if already in progress
                if (CMS.API.locked) {
                    return false;
                }
                CMS.API.locked = true;

                var move = (options || source_language) ? true : false;

                // set correct options
                options = options || this.options;
                if (source_language) {
                    options.target = options.placeholder_id;
                    options.plugin_id = '';
                    options.parent = '';
                } else {
                    source_language = options.plugin_language;
                }

                var data = {
                    source_placeholder_id: options.placeholder_id,
                    source_plugin_id: options.plugin_id || '',
                    source_language: source_language,
                    target_plugin_id: options.parent || '',
                    target_placeholder_id: options.target || CMS.config.clipboard.id,
                    target_language: options.page_language || source_language,
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

            cutPlugin: function () {
                // if cut is once triggered, prevend additional actions
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
                            CMS.API.Messages.open(CMS.config.lang.success);
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

            movePlugin: function (options) {
                // cancel request if already in progress
                if (CMS.API.locked) {
                    return false;
                }
                CMS.API.locked = true;

                var that = this;
                // set correct options
                options = options || this.options;

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
                    csrfmiddlewaretoken: this.csrf
                };

                $.ajax({
                    type: 'POST',
                    url: options.urls.move_plugin,
                    data: data,
                    success: function (response) {
                        // if response is reload
                        if (response.reload) {
                            CMS.API.Helpers.reloadBrowser();
                        }

                        // enable actions again
                        CMS.API.locked = false;

                        // TODO: show only if (response.status)
                        that._showSuccess(dragitem);
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

                // show publish button
                this.ui.publish
                    .addClass('cms-btn-publish-active')
                    .removeClass('cms-btn-disabled')
                    .parent().show();
                this.ui.window.trigger('resize');

                // enable revert to live
                this.ui.revert.removeClass('cms-toolbar-item-navigation-disabled');
            },

            deletePlugin: function (url, name, breadcrumb) {
                // trigger modal window
                var modal = new CMS.Modal({
                    newPlugin: this.newPlugin || false,
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

            // private methods
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

            editPluginPostAjax: function (caller, toolbar, response) {
                if (typeof toolbar === 'undefined' || typeof response === 'undefined') {
                    return function (toolbar, response) {
                        var that = caller;
                        that.editPlugin(response.url, that.options.plugin_name, response.breadcrumb);
                    };
                }
                this.editPlugin(response.url, this.options.plugin_name, response.breadcrumb);
            },

            /**
             * _setSettingsMenu sets up event handlers for settings menu
             *
             * @param nav jQuery
             * @private
             */
            _setSettingsMenu: function _setSettingsMenu(nav) {
                var that = this;
                this.ui.dropdown = nav.siblings('.cms-submenu-dropdown-settings');
                var dropdown = this.ui.dropdown;

                nav.on(this.click, function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    var trigger = $(this);
                    if (trigger.hasClass('cms-btn-active')) {
                        CMS.Plugin._hideSettingsMenu(trigger);
                    } else {
                        CMS.Plugin._hideSettingsMenu();
                        that._showSettingsMenu(trigger);
                    }
                });

                dropdown.on('mousedown mousemove mouseup', function (e) {
                    e.stopPropagation();
                }).on('touchstart', function (e) {
                    // required for scrolling on mobile
                    e.stopPropagation();
                });

                that._setupActions(nav);
                // prevent propagnation
                nav.on(this.click + ' pointerup.cms pointerdown.cms click.cms dblclick.cms', function (e) {
                    e.stopPropagation();
                });

                nav.siblings('.cms-quicksearch, .cms-submenu-dropdown-settings')
                    .on(this.click + ' click.cms dblclick.cms', function (e) {
                    e.stopPropagation();
                });
            },

            /**
             * Simplistic implementation, only scrolls down, only works in structuremode
             * and highly depends on the styles of the structureboard to work correctly
             *
             * @method _scrollToElement
             * @private
             * @param el {jQuery} element to scroll to
             * @param [opts] {Object}
             * @param [opts.duration=200] {Number} time to scroll
             * @param [opts.offset=50] {Number} distance in px to the bottom of the screen
             */
            _scrollToElement: function _scrollToElement(el, opts) {
                var duration = opts && opts.duration !== undefined ? opts.duration : 200;
                var offset = opts && opts.offset !== undefined ? opts.offset : 50;
                var scrollable = el.offsetParent();
                var win = $(window);
                var scrollHeight = win.height();
                var scrollTop = scrollable.scrollTop();
                var elPosition = el.position().top;
                var elHeight = el.height();
                var isInViewport = (elPosition + elHeight + offset <= scrollHeight);

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
             * @private
             * @param nav {jQuery} modal trigger element
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
                var isPlaceholder = !Boolean(dragItem.length);
                var childrenList;
                if (isPlaceholder) {
                    childrenList = nav.closest('.cms-dragarea').find('> .cms-draggables');
                } else {
                    childrenList = nav.closest('.cms-draggable').find('> .cms-draggables');
                }

                modal.on('cms.modal.loaded', that._setupKeyboardTraversing);
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
                    dropdown.find('input').trigger('focus');
                });
                var plugins = nav.siblings('.cms-plugin-picker');

                that._setupQuickSearch(plugins);

                nav.on(this.click, function (e) {
                    e.preventDefault();
                    e.stopPropagation();

                    CMS.Plugin._hideSettingsMenu();

                    // since we don't know exact plugin parent (because dragndrop)
                    // we need to know the parent id by the time we open "add plugin" dialog
                    var pluginsCopy = plugins.clone(true, true).data(
                        'parentId', that._getId(nav.closest('.cms-draggable'))
                    );

                    modal.open({
                        title: that.ui.container.data('settings').addPluginHelpTitle,
                        html: pluginsCopy,
                        width: 530,
                        height: 400
                    });
                });

                // prevent propagnation
                nav.on(this.click + ' pointerup.cms pointerdown.cms click.cms dblclick.cms', function (e) {
                    e.stopPropagation();
                });

                nav.siblings('.cms-quicksearch, .cms-submenu-dropdown')
                    .on(this.click + ' click.cms dblclick.cms', function (e) {
                    e.stopPropagation();
                });
            },

            /**
             * Sets up event handlers for quicksearching in the plugin picker.
             *
             * @private
             * @param plugins jQuery plugins picker element
             */
            _setupQuickSearch: function _setupQuickSearch(plugins) {
                var that = this;
                var input = plugins.find('> .cms-quicksearch').find('input');

                var handler = CMS.API.Helpers.debounce(function () {
                    var input = $(this);
                    // have to always find the pluginsPicker in the handler
                    // because of how we move things into/out of the modal
                    var pluginsPicker = input.closest('.cms-plugin-picker');
                    that._filterPluginsList(pluginsPicker, input);
                }, 100);

                input.on('keyup.cms', handler).on('keyup.cms', CMS.API.Helpers.debounce(function (e) {
                    var input;
                    var pluginsPicker;
                    if (e.keyCode === CMS.KEYS.ENTER) {
                        input = $(this);
                        pluginsPicker = input.closest('.cms-plugin-picker');
                        pluginsPicker.find('.cms-submenu-item')
                            .not('.cms-submenu-item-title').filter(':visible').first().find('> a').focus()
                            .trigger('click');
                    }
                }, 110));
            },

            /**
             * Sets up click handlers for various plugin/placeholder items.
             * Items can be anywhere in the plugin dragitem, not only in dropdown.
             *
             * @private
             * @param nav jQuery dropdown trigger with the items
             */
            _setupActions: function _setupActions(nav) {
                var that = this;
                nav.parent().find('a').on('click.cms', function (e) {
                    e.preventDefault();
                    e.stopPropagation();

                    // show loader and make sure scroll doesn't jump
                    CMS.API.Toolbar.showLoader();

                    var el = $(this);
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
                                callback: that.editPluginPostAjax(that),
                                onSuccess: el.data('on-success')
                            });
                            break;
                        case 'edit':
                            that.editPlugin(
                                that.options.urls.edit_plugin,
                                that.options.plugin_name,
                                that.options.plugin_breadcrumb
                            );
                            break;
                        case 'copy-lang':
                            that.copyPlugin(this.options, el.attr('data-language'));
                            break;
                        case 'copy':
                            that.copyPlugin();
                            break;
                        case 'cut':
                            that.cutPlugin();
                            break;
                        case 'delete':
                            that.deletePlugin(
                                that.options.urls.delete_plugin,
                                that.options.plugin_name,
                                that.options.plugin_breadcrumb
                            );
                            break;
                        default:
                            CMS.API.Toolbar.hideLoader();
                            CMS.API.Toolbar._delegate(el);
                    }
                });

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
                doc.off('keydown.cms.traverse');
                doc.on('keydown.cms.traverse', function (e) {
                    var anchors = dropdown.find('.cms-submenu-item:visible a');
                    var index = anchors.index(anchors.filter(':focus'));

                    // bind arrow down and tab keys
                    if (e.keyCode === CMS.KEYS.DOWN || e.keyCode === CMS.KEYS.TAB) {
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
             * @private
             * @param nav {jQuery} trigger element
             */
            _showSettingsMenu: function (nav) {
                var dropdown = this.ui.dropdown;
                var parents = nav.parentsUntil('.cms-dragarea').last();

                nav.addClass('cms-btn-active');
                parents.addClass('cms-z-index-9999');

                // set visible states
                dropdown.show();

                // calculate dropdown positioning
                if (this.ui.window.height() + this.ui.window.scrollTop() -
                    nav.offset().top - dropdown.height() <= 10 && nav.offset().top - dropdown.height() >= 0) {
                    dropdown.removeClass('cms-submenu-dropdown-top').addClass('cms-submenu-dropdown-bottom');
                } else {
                    dropdown.removeClass('cms-submenu-dropdown-bottom').addClass('cms-submenu-dropdown-top');
                }
            },

            /**
             * Filters given plugins list by a query.
             *
             * @private
             * @param list {jQuery} plugins picker element
             * @param input {jQuery} input, which value to filter plugins with
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
                items.find('a, span').each(function (index, item) {
                    item = $(item);
                    var text = item.text().toLowerCase();
                    var search = query.toLowerCase();

                    (text.indexOf(search) >= 0) ? item.parent().show() : item.parent().hide();
                });

                // check if a title is matching
                titles.filter(':visible').each(function (index, item) {
                    titles.hide();
                    $(item).nextUntil('.cms-submenu-item-title').show();
                });

                // always display title of a category
                items.filter(':visible').each(function (index, item) {
                    item = $(item);
                    if (item.prev().hasClass('cms-submenu-item-title')) {
                        item.prev().show();
                    } else {
                        item.prevUntil('.cms-submenu-item-title').last().prev().show();
                    }
                });

                // if there is no element visible, show only first categoriy
                list.siblings('.cms-submenu-dropdown-children').show();
                if (items.add(titles).filter(':visible').length <= 0) {
                    list.siblings('.cms-submenu-dropdown-children').hide();
                }
            },

            /**
             * Toggles collapsable item
             *
             * @method toggleCollapsable
             * @param el jQuery element to toggle
             * @private
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
                    el.removeClass('cms-dragitem-expanded').parent().find('> .cms-draggables').addClass('cms-hidden');
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
                    el.addClass('cms-dragitem-expanded').parent().find('> .cms-draggables').removeClass('cms-hidden');
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
                dragitem.find('> .cms-dragitem-text').on('click.cms.plugin', function () {
                    if (!dragitem.hasClass('cms-dragitem-collapsable')) {
                        return;
                    }
                    that._toggleCollapsable(dragitem);
                });

                // adds double click event
                this.ui.draggable.on('dblclick', function (e) {
                    e.stopPropagation();
                    $('.cms-plugin-' + that._getId($(this))).trigger('dblclick');
                });

                // only needs to be excecuted once
                if (CMS.Toolbar.ready) {
                    return false;
                }

                // removing duplicate entries
                var sortedArr = CMS.settings.states.sort();
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
                        el.find('> .cms-draggables').removeClass('cms-hidden');
                        el.find('> .cms-dragitem').addClass('cms-dragitem-expanded');
                    }
                });

                // set global setup
                CMS.Toolbar.ready = true;
            },

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

            _getId: function (el) {
                return CMS.API.StructureBoard.getId(el);
            },

            _getIds: function (els) {
                return CMS.API.StructureBoard.getIds(els);
            },

            _showSuccess: function (el) {
                var tpl = $('<div class="cms-dragitem-success"></div>');
                el.addClass('cms-draggable-success').append(tpl);
                // start animation
                tpl.fadeOut(1000, function () {
                    $(this).remove();
                    el.removeClass('cms-draggable-success');
                });
                // make sure structurboard gets updated after success
                this.ui.window.trigger('resize.sideframe');
            }
        });

        /**
         * Hides the opened settings menu. By default looks for any open ones.
         *
         * @static
         * @private
         * @param [nav] jQuery element representing the subnav trigger
         */
        CMS.Plugin._hideSettingsMenu = function (nav) {
            nav = nav || $('.cms-submenu-btn.cms-btn-active');
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
                .trigger('keyup.cms').blur();

            // reset relativity
            $('.cms-dragbar').css('position', '');
        };
    });

})(CMS.$);
