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
                this.ui = {
                    container: container,
                    doc: $(document),
                    window: $(window),
                    toolbar: $('#cms-toolbar'),
                    sortables: $('.cms-draggables'), // global scope to include clipboard
                    plugins: $('.cms-plugin'),
                    render_model: $('.cms-render-model'),
                    placeholders: $('.cms-placeholder'),
                    dragitems: $('.cms-draggable'),
                    dragareas: $('.cms-dragarea'),
                    dropareas: $('.cms-droppable'),
                    dimmer: container.find('.cms-structure-dimmer'),
                    clipboard: $('.cms-clipboard')
                };
            },

            // initial methods
            _setup: function () {
                // cancel if there are no dragareas
                if (!this.ui.dragareas.length) {
                    return false;
                }

                // cancel if there is no structure / content switcher
                if (!this.ui.toolbar.find('.cms-toolbar-item-cms-mode-switcher').length) {
                    return false;
                }

                // setup toolbar mode
                if (this.settings.mode === 'structure') {
                    this.show(true);
                }

                // check if modes should be visible
                if (this.ui.placeholders.length) {
                    this.ui.toolbar.find('.cms-toolbar-item-cms-mode-switcher').show();
                }

                // add drag & drop functionality
                this._drag();
            },

            _events: function () {
                var that = this;
                var modes = this.ui.toolbar.find('.cms-toolbar-item-cms-mode-switcher a');

                // show edit mode
                modes.eq(1).on(this.click, function (e) {
                    e.preventDefault();
                    // cancel if already active
                    if (that.settings.mode === 'edit') {
                        return false;
                    }
                    // otherwise hide
                    that.hide();
                });
                // show structure mode
                modes.eq(0).on(this.click, function (e) {
                    e.preventDefault();
                    // cancel if already active
                    if (that.settings.mode === 'structure') {
                        return false;
                    }
                    // otherwise show
                    that.show();
                });

                // keyboard handling
                this.ui.doc.on('keydown', function (e) {
                    // check if we have an important focus
                    var fields = $('*:focus');
                    console.log(fields);
                    if (e.keyCode === KEYS.SPACE && that.settings.mode === 'structure' && !fields.length) {
                        // cancel if there is no structure / content switcher
                        if (!that.ui.toolbar.find('.cms-toolbar-item-cms-mode-switcher').length) {
                            return false;
                        }
                        e.preventDefault();
                        that.hide();
                    } else if (e.keyCode === KEYS.SPACE && that.settings.mode === 'edit' && !fields.length) {
                        // cancel if there is no structure / content switcher
                        if (!that.ui.toolbar.find('.cms-toolbar-item-cms-mode-switcher').length) {
                            return false;
                        }
                        e.preventDefault();
                        that.show();
                    } else if (e.keyCode === KEYS.SHIFT) {
                        $(this).data('expandmode', true);
                    }
                });

                this.ui.doc.on('keyup', function (e) {
                    if (e.keyCode === KEYS.SHIFT) {
                        $(this).data('expandmode', false);
                    }
                });

            },

            // public methods
            show: function (init) {
                // cancel show if live modus is active
                if (CMS.config.mode === 'live') {
                    return false;
                }

                // set active item
                var modes = this.ui.toolbar.find('.cms-toolbar-item-cms-mode-switcher a');
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
                var modes = this.ui.toolbar.find('.cms-toolbar-item-cms-mode-switcher a');
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

            setActive: function (id, state) {
                // resets
                this.ui.dragitems.removeClass('cms-draggable-selected');
                this.ui.plugins.removeClass('cms-plugin-active');

                // only reset if no id is provided
                if (id === false) {
                    return false;
                }

                // attach active class to current element
                var dragitem = $('.cms-draggable-' + id);
                var plugin = $('.cms-plugin-' + id);

                // if we switch from content to edit, show only a single plcaeholder
                if (state) {
                    // quick show
                    this._showBoard();

                    // show clipboard
                    this.ui.clipboard.show().css('opacity', 0.2);

                    // prevent default visibility
                    this.ui.dragareas.css('opacity', 0.2);

                    // show single placeholder
                    dragitem.closest('.cms-dragarea').show().css('opacity', 1);

                // otherwise hide and reset the board
                } else {
                    this.hide();
                }

                // collapse all previous elements
                var collapsed = dragitem.parentsUntil('.cms-dragarea').siblings().not('.cms-dragitem-expanded');
                collapsed.trigger(this.click);

                // set new classes
                dragitem.addClass('cms-draggable-selected');
                plugin.addClass('cms-plugin-active');
            },

            // private methods
            _showBoard: function () {
                var that = this;
                var timer = function () {};

                // show container
                this.ui.container.show();
                this.ui.dimmer.fadeIn(100);
                this.ui.dragareas.css('opacity', 1);

                // add dimmer close
                this.ui.dimmer.on('mousedown mouseup', function (e) {
                    // cancel on rightclick
                    if (e.which === 3 || e.button === 2) {
                        return false;
                    }
                    // proceed
                    clearTimeout(timer);
                    timer = setTimeout(function () {
                        that.hide();
                    }, 500);

                    if (e.type === 'mouseup') {
                        clearTimeout(timer);
                    }
                });

                this.ui.plugins.not(this.ui.render_model).hide();
                this.ui.placeholders.show();

                // attach event
                if (CMS.config.simpleStructureBoard) {
                    var content = $('.cms-structure-content');
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
                        $('.cms-draggables').each(function () {
                            if ($(this).children().length === 0) {
                                $(this).show();
                            }
                        });
                        // fixes placeholder height
                        ui.item.addClass('cms-is-dragging');
                        ui.placeholder.css('height', ui.helper.css('height'));
                        // add overflow hidden to body
                        $('.cms-structure-content').css({
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
                        $('.cms-draggables').each(function () {
                            if ($(this).children().length === 0) {
                                $(this).hide();
                            }
                        });

                        // add overflow hidden to body
                        $('.cms-structure-content').css({
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
