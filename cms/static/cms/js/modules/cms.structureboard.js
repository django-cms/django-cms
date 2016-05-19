/**
 * @module CMS
 */
/* istanbul ignore next */
var CMS = window.CMS || {};

(function ($) {
    'use strict';

    var placeholders;

    /**
     * TODO make these static methods on CMS.StructureBoard
     * @function actualizeEmptyPlaceholders
     * @private
     */
    function actualizeEmptyPlaceholders() {
        placeholders.each(function () {
            var placeholder = $(this);
            var copyAll = placeholder.find('.cms-dragbar .cms-submenu-item:has(a[data-rel="copy"]):first');

            if (placeholder
                .find('> .cms-draggables')
                .children('.cms-draggable:not(.cms-draggable-is-dragging)').length) {
                placeholder.removeClass('cms-dragarea-empty');
                copyAll.removeClass('cms-submenu-item-disabled');
            } else {
                placeholder.addClass('cms-dragarea-empty');
                copyAll.addClass('cms-submenu-item-disabled');

            }
        });
    }

    /**
     * @function actualizePluginsCollapsibleStatus
     * @private
     * @param {jQuery} els lists of plugins (.cms-draggables)
     */
    function actualizePluginsCollapsibleStatus(els) {
        els.each(function () {
            var childList = $(this);
            var pluginDragItem = childList.closest('.cms-draggable').find('> .cms-dragitem');

            if (childList.children().length) {
                pluginDragItem.addClass('cms-dragitem-collapsable cms-dragitem-expanded');
            } else {
                pluginDragItem.removeClass('cms-dragitem-collapsable');
            }
        });
    }

    /**
     * Handles drag & drop, mode switching and collapsables.
     *
     * @class StructureBoard
     * @namespace CMS
     * @uses CMS.API.Helpers
     */
    CMS.StructureBoard = new CMS.Class({

        implement: [CMS.API.Helpers],

        initialize: function () {
            // elements
            this._setupUI();

            // states
            this.click = 'click.cms';
            this.pointerUp = 'pointerup.cms';
            this.state = false;
            this.dragging = false;

            // setup initial stuff
            this._setup();

            this._setupModeSwitcher();
            actualizeEmptyPlaceholders();
        },

        /**
         * Stores all jQuery references within `this.ui`.
         *
         * @method _setupUI
         * @private
         */
        _setupUI: function setupUI() {
            var container = $('.cms-structure');
            var toolbar = $('.cms-toolbar');

            this.ui = {
                container: container,
                content: $('.cms-structure-content'),
                doc: $(document),
                window: $(window),
                html: $('html'),
                toolbar: toolbar,
                sortables: $('.cms-draggables'), // global scope to include clipboard
                plugins: $('.cms-plugin'),
                render_model: $('.cms-render-model'),
                placeholders: $('.cms-placeholder'),
                dragitems: $('.cms-draggable'),
                dragareas: $('.cms-dragarea'),
                toolbarModeSwitcher: toolbar.find('.cms-toolbar-item-cms-mode-switcher'),
                toolbarModeLinks: toolbar.find('.cms-toolbar-item-cms-mode-switcher a'),
                toolbarTrigger: $('.cms-toolbar-trigger')
            };
        },

        /**
         * Initial setup (and early bail if specific
         * elements do not exist).
         *
         * @method _setup
         * @private
         * @returns {Boolean|void}
         */
        _setup: function () {
            var that = this;

            // cancel if there are no dragareas
            if (!this.ui.dragareas.length) {
                return false;
            }

            // cancel if there is no structure / content switcher
            if (!this.ui.toolbarModeSwitcher.length) {
                return false;
            }

            // setup toolbar mode
            if (CMS.settings.mode === 'structure') {
                that.show(true);
            } else {
                // triggering hide here to switch proper classnames on switcher
                that.hide(true);
            }

            // check if modes should be visible
            if (this.ui.placeholders.length) {
                this.ui.toolbarModeSwitcher.show();
            }

            // add drag & drop functionality
            this._drag();
        },

        /**
         * Sets up events handlers for switching
         * structureboard modes.
         *
         * @method _setupModeSwitcher
         * @private
         */
        _setupModeSwitcher: function () {
            var that = this;
            var modes = that.ui.toolbarModeLinks;

            // show edit mode
            modes.eq(1).on(that.click + ' ' + that.pointerUp, function (e) {
                e.preventDefault();
                // cancel if already active
                if (CMS.settings.mode === 'edit') {
                    return false;
                }
                // otherwise hide
                that.hide();
            });
            // show structure mode
            modes.eq(0).on(that.click + ' ' + that.pointerUp, function (e) {
                e.preventDefault();
                // cancel if already active
                if (CMS.settings.mode === 'structure') {
                    return false;
                }
                // otherwise show
                that.show();
            });

            // keyboard handling
            // only if there is a structure / content switcher
            if (that.ui.toolbarModeSwitcher.length) {
                that.ui.doc.on('keydown.cms.structureboard.switcher', function (e) {
                    // check if we have an important focus
                    var haveFocusedField = document.activeElement !== document.body;

                    if (e.keyCode === CMS.KEYS.SPACE && !haveFocusedField) {
                        e.preventDefault();
                        if (CMS.settings.mode === 'structure') {
                            that.hide();
                        } else /* istanbul ignore else */ if (CMS.settings.mode === 'edit') {
                            that.show();
                        }
                    }
                });
            }
        },

        /**
         * Shows the structureboard. (Structure mode)
         *
         * @method show
         * @public
         * @param {Boolean} init true if this is first initialization
         * @returns {Boolean|void}
         */
        show: function (init) {
            // cancel show if live modus is active
            if (CMS.config.mode === 'live') {
                return false;
            }

            // in order to get consistent positioning
            // of the toolbar we have to know if the page
            // had the scrollbar nad if it had - we adjust
            // the toolbar positioning
            var width = this.ui.toolbar.width();
            var scrollBarWidth = this.ui.window[0].innerWidth - width;

            if (scrollBarWidth) {
                this.ui.toolbar.css('right', scrollBarWidth);
                this.ui.toolbarTrigger.css('right', scrollBarWidth);
            }

            // set active item
            var modes = this.ui.toolbarModeLinks;

            modes.removeClass('cms-btn-active').eq(0).addClass('cms-btn-active');
            this.ui.html.removeClass('cms-structure-mode-content')
                .addClass('cms-structure-mode-structure');

            // apply new settings
            CMS.settings.mode = 'structure';
            if (!init) {
                CMS.settings = this.setSettings(CMS.settings);
            }

            // ensure all elements are visible
            this.ui.dragareas.show();

            // show canvas
            this._showBoard();
        },

        /**
         * Hides the structureboard. (Content mode)
         *
         * @method hide
         * @param {Boolean} init true if this is first initialization
         * @returns {Boolean|void}
         */
        hide: function (init) {
            // cancel show if live modus is active
            if (CMS.config.mode === 'live') {
                return false;
            }

            // reset toolbar positioning
            this.ui.toolbar.css('right', '');
            this.ui.toolbarTrigger.css('right', '');

            // set active item
            var modes = this.ui.toolbarModeLinks;

            modes.removeClass('cms-btn-active').eq(1).addClass('cms-btn-active');
            this.ui.html.removeClass('cms-structure-mode-structure')
                .addClass('cms-structure-mode-content');

            CMS.settings.mode = 'edit';
            if (!init) {
                CMS.settings = this.setSettings(CMS.settings);
            }

            // hide canvas
            this._hideBoard();
        },

        /**
         * Gets the id of the element.
         * TODO: relies on cms-{item}-{id} to always be second in a string of classes
         *
         * @method getId
         * @param {jQuery} el element to get id from
         * @returns {String}
         */
        getId: function (el) {
            // cancel if no element is defined
            if (el === undefined || el === null || el.length <= 0) {
                return false;
            }

            var id = null;
            var cls = el.attr('class').split(' ')[1];

            if (el.hasClass('cms-plugin')) {
                id = cls.replace('cms-plugin-', '');
            } else if (el.hasClass('cms-draggable')) {
                id = cls.replace('cms-draggable-', '');
            } else if (el.hasClass('cms-placeholder')) {
                id = cls.replace('cms-placeholder-', '');
            } else if (el.hasClass('cms-dragbar')) {
                id = cls.replace('cms-dragbar-', '');
            } else if (el.hasClass('cms-dragarea')) {
                id = cls.replace('cms-dragarea-', '');
            }

            return id;
        },

        /**
         * Gets the ids of the list of  elements.
         *
         * @method getIds
         * @param {jQuery} els elements to get id from
         * @returns {String[]}
         */
        getIds: function (els) {
            var that = this;
            var array = [];

            els.each(function () {
                array.push(that.getId($(this)));
            });
            return array;
        },

        /**
         * Actually shows the board canvas.
         *
         * @method _showBoard
         * @private
         */
        _showBoard: function () {
            // show container
            this.ui.container.show();
            this.ui.dragareas.css('opacity', 1);

            this.ui.plugins.not(this.ui.render_model).hide();
            this.ui.placeholders.show();

            // attach event
            var content = this.ui.content;
            var areas = content.find('.cms-dragarea');

            // lets reorder placeholders
            areas.each(function (index, item) {
                if ($(item).hasClass('cms-dragarea-static')) {
                    content.append(item);
                }
            });
            // now lets get the first instance and add some padding
            areas.filter('.cms-dragarea-static').eq(0).css('margin-top', '50px');
        },

        /**
         * Hides the board canvas.
         *
         * @method _hideBoard
         * @private
         */
        _hideBoard: function () {
            // hide elements
            this.ui.container.hide();
            this.ui.plugins.show();
            this.ui.placeholders.hide();

            // detach event
            this.ui.window.off('resize.sideframe');

            this.ui.window.trigger('structureboard_hidden.sideframe');

            // this is sometimes required for user-side scripts to
            // render dynamic elements on the page correctly.
            // e.g. you have a parallax script that calculates position
            // of elements based on document height. but if the page is
            // loaded with structureboard active - the document height
            // would be same as screen height, which is likely incorrect,
            // so triggering resize on window would force user scripts
            // to recalculate whatever is required there
            // istanbul ignore catch
            try {
                var evt = document.createEvent('UIEvents');

                evt.initUIEvent('resize', true, false, window, 0);
                window.dispatchEvent(evt);
            } catch (e) {}
        },

        /**
         * Sets up all the sortables.
         *
         * @method _drag
         * @private
         */
        _drag: function () {
            var that = this;
            var originalPluginContainer;

            this.ui.sortables.nestedSortable({
                items: '> .cms-draggable:not(.cms-draggable-disabled .cms-draggable)',
                placeholder: 'cms-droppable',
                connectWith: '.cms-draggables:not(.cms-hidden)',
                tolerance: 'intersect',
                toleranceElement: '> div',
                dropOnEmpty: true,
                // cloning huge structure is a performance loss compared to cloning just a dragitem
                helper: function createHelper(e, item) {
                    var clone = item.find('> .cms-dragitem').clone();

                    clone.wrap('<div class="' + item[0].className + '"></div>');
                    return clone.parent();
                },
                appendTo: '.cms-structure-content',
                // appendTo: '.cms',
                cursor: 'move',
                cursorAt: { left: -15, top: -15 },
                opacity: 1,
                zIndex: 9999999,
                delay: 100,
                tabSize: 15,
                // nestedSortable
                listType: 'div.cms-draggables',
                doNotClear: true,
                disableNestingClass: 'cms-draggable-disabled',
                errorClass: 'cms-draggable-disallowed',
                scrollSpeed: 15,
                // eslint-disable-next-line no-magic-numbers
                scrollSensitivity: that.ui.window.height() * 0.2,
                start: function (e, ui) {
                    that.ui.content.attr('data-touch-action', 'none');

                    originalPluginContainer = ui.item.closest('.cms-draggables');
                    that.dragging = true;
                    // show empty
                    actualizeEmptyPlaceholders();
                    // ensure all menus are closed
                    CMS.Plugin._hideSettingsMenu();
                    // keep in mind that caching cms-draggables query only works
                    // as long as we don't create them on the fly
                    that.ui.sortables.each(function () {
                        var element = $(this);

                        if (element.children().length === 0) {
                            element.removeClass('cms-hidden');
                        }
                    });

                    // fixes placeholder height
                    ui.item.addClass('cms-is-dragging');
                    ui.helper.addClass('cms-draggable-is-dragging');
                    if (ui.item.find('> .cms-draggables').children().length) {
                        ui.helper.addClass('cms-draggable-stack');
                    }

                    // attach escape event to cancel dragging
                    that.ui.doc.on('keyup.cms.interrupt', function (event, cancel) {
                        if (event.keyCode === CMS.KEYS.ESC && that.dragging || cancel) {
                            that.state = false;
                            $.ui.sortable.prototype._mouseStop();
                            that.ui.sortables.trigger('mouseup');
                        }
                    });
                },

                beforeStop: function (event, ui) {
                    that.dragging = false;
                    ui.item.removeClass('cms-is-dragging cms-draggable-stack');
                    that.ui.doc.off('keyup.cms.interrupt');
                    that.ui.content.attr('data-touch-action', 'pan-y');
                },

                update: function (event, ui) {
                    // cancel if isAllowed returns false
                    if (!that.state) {
                        return false;
                    }

                    var newPluginContainer = ui.item.closest('.cms-draggables');

                    if (originalPluginContainer.is(newPluginContainer)) {
                        // if we moved inside same container,
                        // but event is fired on a parent, discard update
                        if (!newPluginContainer.is(this)) {
                            return false;
                        }
                    } else {
                        actualizePluginsCollapsibleStatus(newPluginContainer.add(originalPluginContainer));
                    }

                    // we pass the id to the updater which checks within the backend the correct place
                    var id = that.getId(ui.item);
                    var plugin = $('.cms-plugin-' + id);

                    // check if we copy/paste a plugin or not
                    if (plugin.closest('.cms-clipboard').length) {
                        plugin.trigger('cms.plugin.update');
                    } else {
                        plugin.trigger('cms.plugins.update');
                    }

                    // reset placeholder without entries
                    that.ui.sortables.each(function () {
                        var element = $(this);

                        if (element.children().length === 0) {
                            element.addClass('cms-hidden');
                        }
                    });

                    actualizeEmptyPlaceholders();
                },
                // eslint-disable-next-line complexity
                isAllowed: function (placeholder, placeholderParent, originalItem) {
                    // cancel if action is executed
                    if (CMS.API.locked) {
                        return false;
                    }
                    // getting restriction array
                    var bounds = [];
                    var immediateParentType;

                    if (placeholder && placeholder.closest('.cms-clipboard-containers').length) {
                        return false;
                    }

                    // if parent has class disabled, dissalow drop
                    if (placeholder && placeholder.parent().hasClass('cms-draggable-disabled')) {
                        return false;
                    }

                    // save original state events
                    var original = $('.cms-plugin-' + that.getId(originalItem));

                    // cancel if item has no settings
                    if (original.length === 0 || !original.data('settings')) {
                        return false;
                    }
                    var parent_bounds = $.grep(original.data('settings').plugin_parent_restriction, function (r) {
                        // special case when PlaceholderPlugin has a parent restriction named "0"
                        return r !== '0';
                    });
                    var type = original.data('settings').plugin_type;
                    // prepare variables for bound
                    var holderId = that.getId(placeholder.closest('.cms-dragarea'));
                    var holder = $('.cms-placeholder-' + holderId);
                    var plugin;

                    if (placeholderParent && placeholderParent.length) {
                        // placeholderParent is always latest, it maybe that
                        // isAllowed is called _before_ placeholder is moved to a child plugin
                        plugin = $('.cms-plugin-' + that.getId(placeholderParent.closest('.cms-draggable')));
                    } else {
                        plugin = $('.cms-plugin-' + that.getId(placeholder.closest('.cms-draggable')));
                    }

                    // now set the correct bounds
                    if (holder.length) {
                        bounds = holder.data('settings').plugin_restriction;
                        immediateParentType = holder.data('settings').plugin_type;
                    }
                    if (plugin.length) {
                        bounds = plugin.data('settings').plugin_restriction;
                        immediateParentType = plugin.data('settings').plugin_type;
                    }

                    // if restrictions is still empty, proceed
                    that.state = !(bounds.length && $.inArray(type, bounds) === -1);

                    // check if we have a parent restriction
                    if (parent_bounds.length) {
                        that.state = $.inArray(immediateParentType, parent_bounds) !== -1;
                    }

                    return that.state;
                }
            }).on('cms.update', actualizeEmptyPlaceholders);
        }

    });

    /**
     * Similar to CMS.Plugin populates globally required
     * variables, that only need querying once, e.g. placeholders.
     *
     * @method _initializeGlobalHandlers
     * @static
     * @private
     */
    CMS.StructureBoard._initializeGlobalHandlers = function _initializeGlobalHandlers() {
        placeholders = $('.cms-dragarea:not(.cms-clipboard-containers)');
    };

    // shorthand for jQuery(document).ready();
    $(CMS.StructureBoard._initializeGlobalHandlers);

})(CMS.$);
