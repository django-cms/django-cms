//##################################################################################################################
// #STRUCTUREBOARD#
/* global CMS */

(function ($) {
    'use strict';

    // TODO move out to separate module CMS-276
    var KEYS = {
        SPACE: 32,
        SHIFT: 16,
        ESC: 27
    };

    // CMS.$ will be passed for $
    $(function () {
        var emptyDropZones = $('.cms-dragbar-empty-wrapper');
        function actualizeEmptyPlaceholders() {
            emptyDropZones.each(function () {
                var wrapper = $(this);
                if (wrapper.next().children().not('.cms-is-dragging').length) {
                    wrapper.hide();
                } else {
                    wrapper.show();
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
                this.timer = function () {};
                this.interval = function () {};
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
                    dropareas: $('.cms-droppable'),
                    dimmer: container.find('.cms-structure-dimmer'),
                    clipboard: $('.cms-clipboard'),
                    toolbarModeSwitcher: toolbar.find('.cms-toolbar-item-cms-mode-switcher'),
                    toolbarModeLinks: toolbar.find('.cms-toolbar-item-cms-mode-switcher a')
                };
            },

            // initial methods
            _setup: function () {
                // cancel if there are no dragareas
                if (!this.ui.dragareas.length) {
                    return false;
                }

                // cancel if there is no structure / content switcher
                if (!this.ui.toolbarModeSwitcher.length) {
                    return false;
                }

                // setup toolbar mode
                if (this.settings.mode === 'structure') {
                    this.show(true);
                }

                // check if modes should be visible
                if (this.ui.placeholders.length) {
                    this.ui.toolbarModeSwitcher.show();
                }

                // add drag & drop functionality
                this._drag();
            },

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
                        if (e.keyCode === KEYS.SPACE && !haveFocusedField) {
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

                // show clipboard
                this.ui.clipboard.css('opacity', 1).fadeIn(this.options.speed);

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
                this.ui.dimmer.fadeIn(100);
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
                this.ui.dimmer.hide();

                // detach event
                this.ui.window.off('resize.sideframe');

                // clear interval
                clearInterval(this.interval);

                this.ui.window.trigger('structureboard_hidden.sideframe');
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
                var dropped = false;
                var droparea = null;
                var dropzone = null;
                var timer = function () {};

                this.ui.sortables.nestedSortable({
                    items: '.cms-draggable',
                    handle: '.cms-dragitem',
                    placeholder: 'cms-droppable',
                    connectWith: this.ui.sortables,
                    tolerance: 'pointer',
                    toleranceElement: '> div',
                    dropOnEmpty: true,
                    helper: 'clone',
                    appendTo: '.cms-structure-content',
                    cursor: 'move',
                    opacity: 0.4,
                    zIndex: 9999999,
                    delay: 100,
                    refreshPositions: true,
                    // nestedSortable
                    listType: 'div.cms-draggables',
                    doNotClear: true,
                    disableNestingClass: 'cms-draggable-disabled',
                    errorClass: 'cms-draggable-disallowed',
                    //'hoveringClass': 'cms-draggable-hover',
                    // methods
                    over: function () {
                        actualizeEmptyPlaceholders();
                    },
                    start: function (e, ui) {
                        that.dragging = true;
                        // show empty
                        actualizeEmptyPlaceholders();
                        // ensure all menus are closed
                        // FIXME find a better way to expose submenus so we can properly call
                        // _hideSubnav
                        $('.cms-submenu').removeClass('cms-btn-active');
                        $('.cms-submenu-quicksearch, .cms-submenu-dropdown').hide();
                        // remove classes from empty dropzones
                        $('.cms-dragbar-empty').removeClass('cms-draggable-disallowed');
                        // keep in mind that caching cms-draggables query only works
                        // as long as we don't create them on the fly
                        that.ui.sortables.each(function () {
                            if ($(this).children().length === 0) {
                                $(this).show();
                            }
                        });
                        // fixes placeholder height
                        ui.item.addClass('cms-is-dragging');
                        ui.placeholder.css('height', ui.helper.css('height'));
                        // add overflow hidden to body
                        that.ui.content.css({
                            'overflow-x': 'hidden'
                        });
                    },

                    stop: function (event, ui) {
                        // TODO prevent everything if nothing really changed
                        that.dragging = false;
                        // hide empty
                        ui.item.removeClass('cms-is-dragging');

                        // cancel if isAllowed returns false
                        if (!that.state) {
                            return false;
                        }

                        // handle dropped event
                        if (dropped) {
                            droparea.prepend(ui.item);
                            dropped = false;
                        }

                        // we pass the id to the updater which checks within the backend the correct place
                        //var id = ui.item.attr('class').replace('cms-draggable cms-draggable-', '');
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
                            if ($(this).children().length === 0) {
                                $(this).hide();
                            }
                        });

                        // add overflow hidden to body
                        that.ui.content.css({
                            'overflow': ''
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
                        var plugin = $('.cms-plugin-' + that.getId(placeholder.closest('.cms-draggable')));

                        // now set the correct bounds
                        if (holder.length) {
                            bounds = holder.data('settings').plugin_restriction;
                        }
                        if (plugin.length) {
                            bounds = plugin.data('settings').plugin_restriction;
                        }
                        if (dropzone) {
                            bounds = dropzone.data('settings').plugin_restriction;
                        }

                        // if parent has class disabled, dissalow drop
                        if (placeholder.parent().hasClass('cms-draggable-disabled')) {
                            return false;
                        }

                        // if restrictions is still empty, proceed
                        that.state = (bounds.length <= 0 || $.inArray(type, bounds) !== -1) ? true : false;

                        return that.state;
                    }
                });

                // attach escape event to cancel dragging
                this.ui.doc.on('keyup.cms', function (e, cancel) {
                    if (e.keyCode === KEYS.ESC || cancel) {
                        that.state = false;
                        that.ui.sortables.sortable('cancel');
                    }
                });

                // define droppable helpers
                this.ui.dropareas.droppable({
                    greedy: true,
                    accept: '.cms-draggable',
                    tolerance: 'pointer',
                    activeClass: 'cms-draggable-allowed',
                    hoverClass: 'cms-draggable-hover-allowed',
                    over: function (event) {
                        dropzone = $('.cms-placeholder-' + that.getId($(event.target).parent().prev()));
                        timer = setInterval(function () {
                            // reset other empty placeholders
                            $('.cms-dragbar-empty').removeClass('cms-draggable-disallowed');
                            if (that.state) {
                                $(event.target).removeClass('cms-draggable-disallowed');
                            } else {
                                $(event.target).addClass('cms-draggable-disallowed');
                            }
                        }, 10);
                    },
                    out: function (event) {
                        dropzone = null;
                        $(event.target).removeClass('cms-draggable-disallowed');
                        clearInterval(timer);
                    },
                    drop: function (event) {
                        dropped = true;
                        droparea = $(event.target).parent().nextAll('.cms-draggables').first();
                        clearInterval(timer);
                    }
                });
            }

        });
    });
})(CMS.$);
