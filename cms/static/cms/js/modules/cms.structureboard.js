//##################################################################################################################
// #STRUCTUREBOARD#
/* global CMS */

(function ($) {
    'use strict';

    // CMS.$ will be passed for $
    $(function () {
        var placeholders = $('.cms-dragarea:not(.cms-clipboard-containers)');
        function actualizeEmptyPlaceholders() {
            placeholders.each(function () {
                var placeholder = $(this);
                if (placeholder
                    .find('> .cms-draggables')
                    .children('.cms-draggable:not(.cms-draggable-is-dragging)').length) {
                    placeholder.removeClass('cms-dragarea-empty');
                } else {
                    placeholder.addClass('cms-dragarea-empty');
                }
            });
        }

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

        /*!
         * StructureBoard
         * handles drag & drop, mode switching and
         */
        CMS.StructureBoard = new CMS.Class({

            implement: [CMS.API.Helpers],

            options: {
                speed: 300
            },

            initialize: function (options) {
                this.options = $.extend(true, {}, this.options, options);
                this.config = CMS.config;
                this.settings = CMS.settings;

                // elements
                this._setupUI();

                // states
                this.click = 'click.cms';
                this.state = false;
                this.dragging = false;

                // setup initial stuff
                this._setup();

                // setup events
                this._events();
                actualizeEmptyPlaceholders();
            },

            _setupUI: function setupUI() {
                var container = $('.cms-structure');
                var toolbar = $('#cms-toolbar');
                this.ui = {
                    container: container,
                    content: $('.cms-structure-content'),
                    doc: $(document),
                    window: $(window),
                    toolbar: toolbar,
                    sortables: $('.cms-draggables'), // global scope to include clipboard
                    plugins: $('.cms-plugin'),
                    render_model: $('.cms-render-model'),
                    placeholders: $('.cms-placeholder'),
                    dragitems: $('.cms-draggable'),
                    dragareas: $('.cms-dragarea'),
                    clipboard: $('.cms-clipboard'),
                    toolbarModeSwitcher: toolbar.find('.cms-toolbar-item-cms-mode-switcher'),
                    toolbarModeLinks: toolbar.find('.cms-toolbar-item-cms-mode-switcher a')
                };
            },

            // initial methods
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
                // FIXME this setTimeout is needed because
                // plugins are initialized after all the scripts are processed
                // which should be fixed btw. _resizeBoard wants plugins to be initialized,
                // otherwise throws errors
                setTimeout(function () {
                    if (that.settings.mode === 'structure') {
                        that.show(true);
                    } else {
                        // triggering hide here to switch proper classnames on switcher
                        that.hide(true);
                    }
                }, 0);

                // check if modes should be visible
                if (this.ui.placeholders.length) {
                    this.ui.toolbarModeSwitcher.show();
                }

                // add drag & drop functionality
                this._drag();
            },

            /**
             * Uses history API to replace the url with new one
             * If history api is not available it's a noop. There's no sanity checks,
             * so use wisely.
             *
             * @method _setURL
             * @param opts {Object}
             * @param [opts.structure] {Boolean} go into structure mode
             * @param [opts.edit] {Boolean} go into edit (content) mode
             */
            _setURL: (window.history && 'pushState' in window.history) ? function _setURL(opts) {
                var addParams = [];
                var removeParams = [];
                var modeToUrl = {
                    structure: CMS.settings.structureURL,
                    edit: CMS.settings.editURL
                };

                $.each(opts, function (key, value) {
                    if (value) {
                        addParams.push(modeToUrl[key] + '=1');
                    } else {
                        removeParams.push(modeToUrl[key]);
                    }
                });
                var newUrl = this.makeURL(window.location.href, addParams, removeParams);
                history.replaceState({}, document.title, newUrl.replace('&amp;', '&'));
            } : $.noop,

            _events: function () {
                var that = this;
                var modes = that.ui.toolbarModeLinks;

                // show edit mode
                modes.eq(1).on(that.click, function (e) {
                    e.preventDefault();
                    // cancel if already active
                    if (that.settings.mode === 'edit') {
                        return false;
                    }
                    // otherwise hide
                    that.hide();
                });
                // show structure mode
                modes.eq(0).on(that.click, function (e) {
                    e.preventDefault();
                    // cancel if already active
                    if (that.settings.mode === 'structure') {
                        return false;
                    }
                    // otherwise show
                    that.show();
                });

                // keyboard handling
                // only if there is a structure / content switcher
                if (that.ui.toolbarModeSwitcher.length) {
                    that.ui.doc.on('keydown', function (e) {
                        // check if we have an important focus
                        var haveFocusedField = document.activeElement !== document.body;
                        if (e.keyCode === CMS.KEYS.SPACE && !haveFocusedField) {
                            e.preventDefault();
                            if (that.settings.mode === 'structure') {
                                that.hide();
                            } else if (that.settings.mode === 'edit') {
                                that.show();
                            }
                        }
                    });
                }
            },

            // public methods
            show: function (init) {
                // cancel show if live modus is active
                if (CMS.config.mode === 'live') {
                    return false;
                }

                // set active item
                var modes = this.ui.toolbarModeLinks;
                modes.removeClass('cms-btn-active').eq(0).addClass('cms-btn-active');
                this._setURL({ edit: false, structure: true });

                // show clipboard
                this.ui.clipboard.fadeIn(this.options.speed);

                // apply new settings
                this.settings.mode = 'structure';
                if (!init) {
                    this.settings = this.setSettings(this.settings);
                }

                // ensure all elements are visible
                this.ui.dragareas.show();

                // show canvas
                this._showBoard();
            },

            hide: function (init) {
                // cancel show if live modus is active
                if (CMS.config.mode === 'live') {
                    return false;
                }

                // set active item
                var modes = this.ui.toolbarModeLinks;
                modes.removeClass('cms-btn-active').eq(1).addClass('cms-btn-active');
                this._setURL({ edit: true, structure: false });

                // hide clipboard if in edit mode
                this.ui.container.find('.cms-clipboard').hide();

                // hide clipboard
                this.ui.clipboard.hide();

                this.settings.mode = 'edit';
                if (!init) {
                    this.settings = this.setSettings(this.settings);
                }

                // hide canvas
                this._hideBoard();
            },

            /**
             * gets the id of the element
             *
             * @param el jQuery element to get id from
             * @return String
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

            getIds: function (els) {
                var that = this;
                var array = [];
                els.each(function () {
                    array.push(that.getId($(this)));
                });
                return array;
            },

            // private methods
            _showBoard: function () {
                var that = this;

                // show container
                this.ui.container.show();
                this.ui.dragareas.css('opacity', 1);

                this.ui.plugins.not(this.ui.render_model).hide();
                this.ui.placeholders.show();

                // attach event
                if (CMS.config.simpleStructureBoard) {
                    var content = this.ui.content;
                    var areas = content.find('.cms-dragarea');
                    // set correct css attributes for the new mode
                    content.addClass('cms-structure-content-simple');
                    areas.addClass('cms-dragarea-simple');
                    // lets reorder placeholders
                    areas.each(function (index, item) {
                        if ($(item).hasClass('cms-dragarea-static')) {
                            content.append(item);
                        }
                    });
                    // now lets get the first instance and add some padding
                    areas.filter('.cms-dragarea-static').eq(0).css('margin-top', '50px');
                } else {
                    this.ui.container.addClass('cms-structure-dynamic');
                    this.ui.window.on('resize.sideframe', function () {
                        that._resizeBoard();
                    }).trigger('resize.sideframe');
                }
            },

            _hideBoard: function () {
                // hide elements
                this.ui.container.hide();
                this.ui.plugins.show();
                this.ui.placeholders.hide();

                // detach event
                this.ui.window.off('resize.sideframe');

                this.ui.window.trigger('structureboard_hidden.sideframe');
                if (!CMS.config.simpleStructureBoard) {
                    this.ui.container.height(this.ui.doc.outerHeight());
                }
            },

            /*
             * @deprecated as of CMS 3.2
             */
            _resizeBoard: function () {
                // calculate placeholder position
                var id = null;
                var area = null;
                var min = null;
                var areaParentOffset = null;
                var that = this;

                // have to delay since height changes when toggling modes
                setTimeout(function () {
                    that.ui.container.height(that.ui.doc.outerHeight());
                }, 0);

                // start calculating
                this.ui.placeholders.each(function (index, item) {
                    item = $(item);
                    id = item.data('settings').placeholder_id;
                    area = $('.cms-dragarea-' + id);
                    // to calculate the correct offset, we need to set the
                    // placeholders correct heights and than set the according position
                    item.height(area.outerHeight(true));
                    // set min width
                    min = (item.width()) ? 0 : 150;
                    // as area is "css positioned" and jquery offset function is relative to the
                    // document (not the first relative/absolute parent) we need to substract
                    // first relative/absolute parent offset.
                    areaParentOffset = $(area).offsetParent().offset();
                    area.css({
                        top: item.offset().top - areaParentOffset.top - 5,
                        left: item.offset().left - areaParentOffset.left - min,
                        width: item.width() + min
                    });
                });
            },

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
                    // appendTo: '#cms-toolbar',
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
                    start: function (e, ui) {
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
                        that.ui.doc.on('keyup.cms.interrupt', function (e, cancel) {
                            if (e.keyCode === CMS.KEYS.ESC && that.dragging || cancel) {
                                that.state = false;
                                that.ui.sortables.sortable('cancel');
                            }
                        });
                    },

                    beforeStop: function (event, ui) {
                        that.dragging = false;
                        ui.item.removeClass('cms-is-dragging cms-draggable-stack');
                        that.ui.doc.off('keyup.cms.interrupt');
                    },

                    update: function (event, ui) {
                        // cancel if isAllowed returns false
                        if (!that.state) {
                            return false;
                        }

                        var newPluginContainer = ui.item.closest('.cms-draggables');
                        if (!originalPluginContainer.is(newPluginContainer)) {
                            actualizePluginsCollapsibleStatus(newPluginContainer.add(originalPluginContainer));
                        } else {
                            // if we moved inside same container,
                            // but event is fired on a parent, discard update
                            if (!newPluginContainer.is(this)) {
                                return false;
                            }
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
                    isAllowed: function (placeholder, placeholderParent, originalItem) {
                        // cancel if action is excecuted
                        if (CMS.API.locked) {
                            return false;
                        }
                        // getting restriction array
                        var bounds = [];
                        // save original state events
                        var original = $('.cms-plugin-' + that.getId(originalItem));
                        // cancel if item has no settings
                        if (original.length === 0 || original.data('settings') === null) {
                            return false;
                        }
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
                        }
                        if (plugin.length) {
                            bounds = plugin.data('settings').plugin_restriction;
                        }

                        // if parent has class disabled, dissalow drop
                        if (placeholder.parent().hasClass('cms-draggable-disabled')) {
                            return false;
                        }

                        // if restrictions is still empty, proceed
                        that.state = (!bounds.length || $.inArray(type, bounds) !== -1) ? true : false;

                        return that.state;
                    }
                });
            }

        });
    });
})(CMS.$);
