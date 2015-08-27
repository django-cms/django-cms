//##################################################################################################################
// #PLUGINS#
/* global CMS */

(function ($) {
    'use strict';

    // TODO move out to separate module CMS-276
    var KEYS = {
        SHIFT: 16
    };
    // CMS.$ will be passed for $
    $(document).ready(function () {
        $(document).on('keydown', function (e) {
            if (e.keyCode === KEYS.SHIFT) {
                $(this).data('expandmode', true);
            }
        }).on('keyup', function (e) {
            if (e.keyCode === KEYS.SHIFT) {
                $(this).data('expandmode', false);
            }
        });

        /*!
         * Plugins
         * for created plugins or generics (static content)
         */
        CMS.Plugin = new CMS.Class({

            implement: [CMS.API.Helpers],

            options: {
                'type': '', // bar, plugin or generic
                'placeholder_id': null,
                'plugin_type': '',
                'plugin_id': null,
                'plugin_language': '',
                'plugin_parent': null,
                'plugin_order': null,
                'plugin_breadcrumb': [],
                'plugin_restriction': [],
                'urls': {
                    'add_plugin': '',
                    'edit_plugin': '',
                    'move_plugin': '',
                    'copy_plugin': '',
                    'delete_plugin': ''
                }
            },

            initialize: function (container, options) {
                this.container = $('.' + container);
                this.options = $.extend(true, {}, this.options, options);

                // elements
                this.body = $(document);

                // states
                this.csrf = CMS.config.csrf;
                this.timer = function () {};
                this.timeout = 250;
                this.focused = false;
                this.click = 'pointerup.cms';

                // bind data element to the container
                this.container.data('settings', this.options);

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

            // initial methods
            _setPlaceholder: function () {
                var that = this;
                var title = '.cms-dragbar-title';
                var expanded = 'cms-dragbar-title-expanded';
                var dragbar = $('.cms-dragbar-' + this.options.placeholder_id);

                // register the subnav on the placeholder
                this._setSubnav(dragbar.find('.cms-submenu'));

                var settings = CMS.settings;
                settings.dragbars = settings.dragbars || [];

                // enable expanding/collapsing globally within the placeholder
                dragbar.find(title).bind(this.click, function () {
                    ($(this).hasClass(expanded)) ? that._collapseAll($(this)) : that._expandAll($(this));
                });

                if ($.inArray(this.options.placeholder_id, settings.dragbars) !== -1) {
                    dragbar.find(title).addClass(expanded);
                }
            },

            _setPlugin: function () {
                var that = this;

                // adds double click to edit
                this.container.bind('dblclick', function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    that.editPlugin(
                        that.options.urls.edit_plugin,
                        that.options.plugin_name,
                        that.options.plugin_breadcrumb
                    );
                });

                // adds edit tooltip
                this.container.bind('pointerover.cms pointerout.cms', function (e) {
                    e.stopPropagation();
                    var name = that.options.plugin_name;
                    var id = that.options.plugin_id;
                    (e.type === 'pointerover') ? that.showTooltip(name, id) : that.hideTooltip();
                });

                // adds listener for all plugin updates
                this.container.bind('cms.plugins.update', function (e) {
                    e.stopPropagation();
                    that.movePlugin();
                });
                // adds listener for copy/paste updates
                this.container.bind('cms.plugin.update', function (e) {
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
                var draggable = $('.cms-draggable-' + this.options.plugin_id);
                var dragitem = draggable.find('> .cms-dragitem');

                // attach event to the plugin menu
                this._setSubnav(draggable.find('> .cms-dragitem .cms-submenu'));

                // adds double click to edit
                dragitem.bind('dblclick', function (e) {
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
                this.container.bind('dblclick', function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    that.editPlugin(that.options.urls.edit_plugin, that.options.plugin_name, []);
                });

                // adds edit tooltip
                this.container.bind('pointerover.cms pointerout.cms', function (e) {
                    e.stopPropagation();
                    var name = that.options.plugin_name;
                    var id = that.options.plugin_id;
                    (e.type === 'pointerover') ? that.showTooltip(name, id) : that.hideTooltip();
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
                    'placeholder_id': this.options.placeholder_id,
                    'plugin_type': type,
                    'plugin_parent': parent || '',
                    'plugin_language': this.options.plugin_language,
                    'csrfmiddlewaretoken': this.csrf
                };

                $.ajax({
                    'type': 'POST',
                    'url': this.options.urls.add_plugin,
                    'data': data,
                    'success': function (data) {
                        CMS.API.locked = false;
                        that.newPlugin = data;
                        that.editPlugin(data.url, name, data.breadcrumb);
                    },
                    'error': function (jqXHR) {
                        CMS.API.locked = false;
                        var msg = CMS.config.lang.error;
                        // trigger error
                        that._showError(msg + jqXHR.responseText || jqXHR.status + ' ' + jqXHR.statusText);
                    }
                });
            },

            editPlugin: function (url, name, breadcrumb) {
                // trigger modal window
                var modal = new CMS.Modal({
                    'newPlugin': this.newPlugin || false,
                    'onClose': this.options.onClose || false,
                    'redirectOnClose': this.options.redirectOnClose || false
                });
                modal.open(url, name, breadcrumb);
            },

            copyPlugin: function (options, source_language) {
                // cancel request if already in progress
                if (CMS.API.locked) {
                    return false;
                }
                CMS.API.locked = true;

                var that = this;
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
                    'source_placeholder_id': options.placeholder_id,
                    'source_plugin_id': options.plugin_id || '',
                    'source_language': source_language,
                    'target_plugin_id': options.parent || '',
                    'target_placeholder_id': options.target || CMS.config.clipboard.id,
                    'target_language': options.page_language || source_language,
                    'csrfmiddlewaretoken': this.csrf
                };
                var request = {
                    'type': 'POST',
                    'url': options.urls.copy_plugin,
                    'data': data,
                    'success': function () {
                        CMS.API.Toolbar.openMessage(CMS.config.lang.success);
                        // reload
                        CMS.API.Helpers.reloadBrowser();
                    },
                    'error': function (jqXHR) {
                        CMS.API.locked = false;
                        var msg = CMS.config.lang.error;
                        // trigger error
                        that._showError(msg + jqXHR.responseText || jqXHR.status + ' ' + jqXHR.statusText);
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
                    'placeholder_id': CMS.config.clipboard.id,
                    'plugin_id': this.options.plugin_id,
                    'plugin_parent': '',
                    'plugin_language': this.options.page_language,
                    'plugin_order': [this.options.plugin_id],
                    'csrfmiddlewaretoken': this.csrf
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
                        'type': 'POST',
                        'url': that.options.urls.move_plugin,
                        'data': data,
                        'success': function () {
                            CMS.API.Toolbar.openMessage(CMS.config.lang.success);
                            // if response is reload
                            CMS.API.Helpers.reloadBrowser();
                        },
                        'error': function (jqXHR) {
                            CMS.API.locked = false;
                            var msg = CMS.config.lang.error;
                            // trigger error
                            that._showError(msg + jqXHR.responseText || jqXHR.status + ' ' + jqXHR.statusText);
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
                        that._showError(msg + jqXHR.responseText || jqXHR.status + ' ' + jqXHR.statusText);
                    }
                });

                // show publish button
                $('.cms-btn-publish')
                    .addClass('cms-btn-publish-active')
                    .removeClass('cms-btn-disabled')
                    .parent().show();

                // enable revert to live
                $('.cms-toolbar-revert').removeClass('cms-toolbar-item-navigation-disabled');
            },

            deletePlugin: function (url, name, breadcrumb) {
                // trigger modal window
                var modal = new CMS.Modal({
                    'newPlugin': this.newPlugin || false,
                    'onClose': this.options.onClose || false,
                    'redirectOnClose': this.options.redirectOnClose || false
                });
                modal.open(url, name, breadcrumb);
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

            _setSubnav: function (nav) {
                var that = this;

                nav.bind('click', function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    var trigger = $(this);
                    trigger.hasClass('cms-btn-active') ?
                        that._hideSubnav(trigger) : that._showSubnav(trigger);
                });

                nav.siblings('.cms-submenu-dropdown').on('mousedown mousemove mouseup', function (e) {
                    e.stopPropagation();
                }).on('touchstart', function (e) {
                    // required for scrolling on mobile
                    e.stopPropagation();
                });

                nav.siblings('.cms-submenu-dropdown').find('a').bind('click.cms', function (e) {
                    e.preventDefault();
                    e.stopPropagation();

                    // show loader and make sure scroll doesn't jump
                    CMS.API.Toolbar._loader(true);

                    var el = $(this);
                    that._hideSubnav(nav);

                    // set switch for subnav entries
                    switch (el.attr('data-rel')) {
                        case 'add':
                            that.addPlugin(
                                el.attr('href').replace('#', ''),
                                el.text(),
                                that._getId(el.closest('.cms-draggable'))
                            );
                            break;
                        case 'ajax_add':
                            CMS.API.Toolbar.openAjax(
                                el.attr('href'),
                                JSON.stringify(el.data('post')),
                                el.data('text'),
                                that.editPluginPostAjax(that),
                                el.data('on-success')
                            );
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
                            CMS.API.Toolbar._loader(false);
                            CMS.API.Toolbar._delegate(el);
                    }
                });

                nav.siblings('.cms-submenu-quicksearch')
                    .find('input').on('keyup keydown focus pointerup', function (e) {
                    if (e.type === 'focus') {
                        that.focused = true;
                    }
                    if (e.type === 'keyup') {
                        clearTimeout(that.timer);
                        // keybound is not required
                        that.timer = setTimeout(function () {
                            that._searchSubnav(nav, $(e.currentTarget).val());
                        }, 100);
                    }
                });

                // set data attributes for original top positioning
                nav.siblings('.cms-submenu-dropdown').each(function () {
                    $(this).data('top', $(this).css('top'));
                });

                // prevent propagnation
                nav.on(this.click + ' dblclick', function (e) {
                    e.stopPropagation();
                });
                nav.siblings('.cms-submenu-quicksearch, .cms-submenu-dropdown').on(this.click, function (e) {
                    e.stopPropagation();
                });

                $(document).add('.cms-submenu').not(nav).on(this.click, function () {
                    that._hideSubnav(nav);
                });
            },

            _showSubnav: function (nav) {
                var that = this;
                var dropdown = nav.siblings('.cms-submenu-dropdown');
                var offset = parseInt(dropdown.data('top'));
                nav.addClass('cms-btn-active');

                // reset z indexes
                var reset = $('.cms-submenu').parentsUntil('.cms-dragarea');
                var scrollHint = dropdown.find('.cms-submenu-scroll-hint');

                reset.css('z-index', 0);

                var parents = nav.parentsUntil('.cms-dragarea');
                parents.css('z-index', 999);

                // show subnav
                nav.siblings('.cms-submenu-quicksearch').show().find('input');

                // set visible states
                nav.siblings('.cms-submenu-dropdown').show().on('scroll', function () {
                    scrollHint.fadeOut(100);
                    $(this).off('scroll');
                });

                // show scrollHint for FF on OSX
                if (dropdown[0].scrollHeight > dropdown.height()) {
                    scrollHint.show();
                }

                // add key events
                $(document).unbind('keydown.cms');
                $(document).bind('keydown.cms', function (e) {
                    var anchors = nav.siblings('.cms-submenu-dropdown').find('.cms-submenu-item:visible a');
                    var index = anchors.index(anchors.filter(':focus'));

                    // bind arrow down and tab keys
                    if (e.keyCode === 40 || e.keyCode === 9) {
                        that.traverse = true;
                        e.preventDefault();
                        if (index >= 0 && index < anchors.length - 1) {
                            anchors.eq(index + 1).focus();
                        } else {
                            anchors.eq(0).focus();
                        }
                    }

                    // bind arrow up and shift+tab keys
                    if (e.keyCode === 38 || (e.keyCode === 9 && e.shiftKey)) {
                        e.preventDefault();
                        if (anchors.is(':focus')) {
                            anchors.eq(index - 1).focus();
                        } else {
                            anchors.eq(anchors.length).focus();
                        }
                    }

                    // hide subnav when hitting enter or escape
                    if (e.keyCode === 13 || e.keyCode === 27) {
                        that.traverse = false;
                        nav.siblings('.cms-submenu-quicksearch').find('input').blur();
                        that._hideSubnav(nav);
                    }
                });

                // calculate subnav bounds
                if ($(window).height() + $(window).scrollTop() - nav.offset().top - dropdown.height() <= 10 &&
                    nav.offset().top - dropdown.height() >= 0) {
                    dropdown.css('top', 'auto');
                    dropdown.css('bottom', offset);
                    // if parent is within a plugin, add additional offset
                    if (dropdown.closest('.cms-draggable').length) {
                        dropdown.css('bottom', offset - 1);
                    }
                } else {
                    dropdown.css('top', offset);
                    dropdown.css('bottom', 'auto');
                }
            },

            _hideSubnav: function (nav) {
                nav.removeClass('cms-btn-active');

                // set correct active state
                nav.closest('.cms-draggable').data('active', false);

                nav.siblings('.cms-submenu-dropdown').hide();
                nav.siblings('.cms-submenu-quicksearch').hide();
                // reset search
                nav.siblings('.cms-submenu-quicksearch').find('input').val('').blur();

                // reset relativity
                $('.cms-dragbar').css('position', '');
            },

            _searchSubnav: function (nav, value) {
                var items = nav.siblings('.cms-submenu-dropdown').find('.cms-submenu-item');
                var titles = nav.siblings('.cms-submenu-dropdown').find('.cms-submenu-item-title');

                // cancel if value is zero
                if (value === '') {
                    items.add(titles).show();
                    return false;
                }

                // loop through items and figure out if we need to hide items
                items.find('a, span').each(function (index, item) {
                    item = $(item);
                    var text = item.text().toLowerCase();
                    var search = value.toLowerCase();

                    (text.indexOf(search) >= 0) ? item.parent().show() : item.parent().hide();
                });

                // check if a title is matching
                titles.filter(':visible').each(function (index, item) {
                    titles.hide();
                    $(item).nextUntil('.cms-submenu-item-title').show();
                });

                // always display title of a category
                items.filter(':visible').each(function (index, item) {
                    if ($(item).prev().hasClass('cms-submenu-item-title')) {
                        $(item).prev().show();
                    } else {
                        $(item).prevUntil('.cms-submenu-item-title').last().prev().show();
                    }
                });

                // if there is no element visible, show only first categoriy
                nav.siblings('.cms-submenu-dropdown').show();
                if (items.add(titles).filter(':visible').length <= 0) {
                    nav.siblings('.cms-submenu-dropdown').hide();
                }

                // hide scrollHint
                nav.siblings('.cms-submenu-dropdown').find('.cms-submenu-scroll-hint').hide();
            },

            _collapsables: function () {
                // one time setup
                var that = this;
                var settings = CMS.settings;
                var draggable = $('.cms-draggable-' + this.options.plugin_id);

                // check which button should be shown for collapsemenu
                this.container.each(function (index, item) {
                    var els = $(item).find('.cms-dragitem-collapsable');
                    var open = els.filter('.cms-dragitem-expanded');
                    if (els.length === open.length && (els.length + open.length !== 0)) {
                        $(item).find('.cms-dragbar-title').addClass('cms-dragbar-title-expanded');
                    }
                });
                // cancel here if its not a draggable
                if (!draggable.length) {
                    return false;
                }

                // attach events to draggable
                draggable.find('> .cms-dragitem-collapsable').bind(this.click, function () {
                    var el = $(this);
                    var id = that._getId($(this).parent());
                    var items;

                    var settings = CMS.settings;
                    settings.states = settings.states || [];

                    // collapsable function and save states
                    if (el.hasClass('cms-dragitem-expanded')) {
                        settings.states.splice($.inArray(id, settings.states), 1);
                        el.removeClass('cms-dragitem-expanded').parent().find('> .cms-draggables').hide();
                        if ($(document).data('expandmode')) {
                            items = draggable.find('.cms-draggable').find('.cms-dragitem-collapsable');
                            if (!items.length) {
                                return false;
                            }
                            items.each(function () {
                                if ($(this).hasClass('cms-dragitem-expanded')) {
                                    $(this).trigger(that.click);
                                }
                            });
                        }

                    } else {
                        settings.states.push(id);
                        el.addClass('cms-dragitem-expanded').parent().find('> .cms-draggables').show();
                        if ($(document).data('expandmode')) {
                            items = draggable.find('.cms-draggable').find('.cms-dragitem-collapsable');
                            if (!items.length) {
                                return false;
                            }
                            items.each(function () {
                                if (!$(this).hasClass('cms-dragitem-expanded')) {
                                    $(this).trigger(that.click);
                                }
                            });
                        }
                    }

                    // make sure structurboard gets updated after expanding
                    $(window).trigger('resize.sideframe');

                    // save settings
                    CMS.API.Toolbar.setSettings(settings);
                });
                // adds double click event
                draggable.bind('dblclick', function (e) {
                    e.stopPropagation();
                    $('.cms-plugin-' + that._getId($(this))).trigger('dblclick');
                });

                // only needs to be excecuted once
                if (CMS.Toolbar.ready) {
                    return false;
                }

                // removing dublicate entries
                var sortedArr = settings.states.sort();
                var filteredArray = [];
                for (var i = 0; i < sortedArr.length; i++) {
                    if (sortedArr[i] !== sortedArr[i + 1]) {
                        filteredArray.push(sortedArr[i]);
                    }
                }
                settings.states = filteredArray;

                // loop through the items
                $.each(CMS.settings.states, function (index, id) {
                    var el = $('.cms-draggable-' + id);
                    // only add this class to elements which have a draggable area
                    if (el.find('.cms-draggables').length) {
                        el.find('> .cms-draggables').show();
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
                    if (!$(this).hasClass('cms-dragitem-expanded')) {
                        $(this).trigger(that.click);
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
                    if ($(this).hasClass('cms-dragitem-expanded')) {
                        $(this).trigger(that.click);
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

            _showError: function (msg) {
                return CMS.API.Toolbar.showError(msg, true);
            },

            _showSuccess: function (el) {
                var tpl = $('<div class="cms-dragitem-success"></div>');
                el.append(tpl);
                // start animation
                tpl.fadeOut(function () {
                    $(this).remove();
                });
                // make sure structurboard gets updated after success
                $(window).trigger('resize.sideframe');
            }

        });

    });
})(CMS.$);
