/*
 * Copyright https://github.com/divio/django-cms
 */

import $ from 'jquery';
import keyboard from './keyboard';
import Plugin from './cms.plugins';
import Clipboard from './cms.clipboard';
import URI from 'urijs';
import DiffDOM from 'diff-dom';
import { find, once, remove, uniqWith, compact, isEqual } from 'lodash';

import './jquery.ui.custom';
import './jquery.ui.touchpunch';
import './jquery.ui.nestedsortable';

import preloadImagesFromMarkup from './preload-images';

const Helpers = require('./cms.base').default.API.Helpers;
var KEYS = require('./cms.base').default.KEYS;

let dd;
const DOMParser = window.DOMParser; // needed only for testing

var placeholders;

const triggerWindowResize = () => {
    try {
        var evt = document.createEvent('UIEvents');

        evt.initUIEvent('resize', true, false, window, 0);
        window.dispatchEvent(evt);
    } catch (e) {}
};


/**
 * Handles drag & drop, mode switching and collapsables.
 *
 * @class StructureBoard
 * @namespace CMS
 */
class StructureBoard {
    constructor() {
        // elements
        this._setupUI();

        // states
        this.click = 'click.cms';
        this.pointerUp = 'pointerup.cms';
        this.state = false;
        this.dragging = false;

        dd = new DiffDOM();

        // setup initial stuff
        const setup = this._setup();

        // istanbul ignore if
        if (typeof setup === 'undefined' && CMS.config.mode === 'draft') {
            this._preloadOppositeMode();
        }
        this._setupModeSwitcher();
        StructureBoard.actualizeEmptyPlaceholders();
    }

    /**
     * Stores all jQuery references within `this.ui`.
     *
     * @method _setupUI
     * @private
     */
    _setupUI() {
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
    }

    /**
     * Initial setup (and early bail if specific
     * elements do not exist).
     *
     * @method _setup
     * @private
     * @returns {Boolean|void}
     */
    _setup() {
        var that = this;

        // cancel if there is no structure / content switcher
        if (!this.ui.toolbarModeSwitcher.length) {
            return false;
        }

        // setup toolbar mode
        if (CMS.config.settings.mode === 'structure') {
            that.show(true);
            that._loadedStructure = true;
            StructureBoard._initializeDragItemsStates();
        } else {
            // triggering hide here to switch proper classnames on switcher
            that.hide(true);
            that._loadedContent = true;
        }

        // check if modes should be visible
        if (this.ui.dragareas.length || this.ui.placeholders.length) { // eslint-disable-line
            this.ui.toolbarModeSwitcher.show();
        }

        // add drag & drop functionality
        StructureBoard.actualizeEmptyPlaceholders();
        // istanbul ignore next
        $('.cms-draggable').one('pointerover.cms.drag', once(() => {
            $('.cms-draggable').off('pointerover.cms.drag');
            this._drag();
        }));
    }

    _preloadOppositeMode() {
        const WAIT_BEFORE_PRELOADING = 2000;

        $(Helpers._getWindow()).one('load', () => {
            setTimeout(() => {
                if (this._loadedStructure) {
                    this._requestMode('content');
                } else {
                    this._requestMode('structure');
                }
            }, WAIT_BEFORE_PRELOADING);
        });
    }

    /**
     * Sets up events handlers for switching
     * structureboard modes.
     *
     * @method _setupModeSwitcher
     * @private
     */
    _setupModeSwitcher() {
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
        if (that.ui.toolbarModeSwitcher.length && that.ui.toolbarModeSwitcher.is(':visible')) {
            keyboard.setContext('cms');
            keyboard.bind('space', function (e) {
                e.preventDefault();
                that._toggleStructureBoard();
            });
            keyboard.bind('shift+space', function (e) {
                e.preventDefault();
                that._toggleStructureBoard({ useHoveredPlugin: true });
            });
        }
    }

    /**
     * @method _toggleStructureBoard
     * @private
     * @param {Object} [opts] options
     * @param {Boolean} [opts.useHoveredPlugin] should the plugin be taken into account
     */
    _toggleStructureBoard(opts) {
        var that = this;
        var options = opts ? opts : {};

        if (options.useHoveredPlugin) {
            if (CMS.settings.mode === 'structure') {
                that._hideAndHighlightPlugin();
            } else {
                that._showAndHighlightPlugin();
            }
        } else {
            // eslint-disable-next-line no-lonely-if
            if (CMS.settings.mode === 'structure') {
                that.hide();
            } else /* istanbul ignore else */ if (CMS.settings.mode === 'edit') {
                that.show();
            }
        }
    }

    /**
     * Shows structureboard, scrolls into view and highlights hovered plugin.
     * Uses CMS.API.Tooltip because it already handles multiple plugins living on
     * the same DOM node.
     *
     * @method _showAndHighlightPlugin
     * @private
     * @returns {Promise}
     */
    _showAndHighlightPlugin() {
        // cancel show if live modus is active
        if (CMS.config.mode === 'live') {
            return Promise.reject(false);
        }

        if (!CMS.API.Tooltip) {
            return Promise.reject(false);
        }

        var tooltip = CMS.API.Tooltip.domElem;
        var HIGHLIGHT_TIMEOUT = 10;
        var DRAGGABLE_HEIGHT = 50; // it's not precisely 50, but it fits

        if (!tooltip.is(':visible')) {
            return Promise.reject(false);
        }

        var pluginId = tooltip.data('plugin_id');

        return this.show().then(function () {
            var draggable = $('.cms-draggable-' + pluginId);

            // expand necessary parents
            $(document).data('expandmode', false);
            draggable.parents('.cms-draggable').find(
                '> .cms-dragitem-collapsable:not(".cms-dragitem-expanded") > .cms-dragitem-text').trigger('click');

            setTimeout(function () {
                var offsetParent = draggable.offsetParent();
                var position = draggable.position().top + offsetParent.scrollTop();

                draggable.offsetParent().scrollTop(position - window.innerHeight / 2 + DRAGGABLE_HEIGHT);

                Plugin._highlightPluginStructure(draggable.find('.cms-dragitem:first'));
            }, HIGHLIGHT_TIMEOUT);
        });
    }

    /**
     * Hides structureboard, scrolls into view, expands tree, highlights hovered plugin.
     *
     * @method _hideAndHighlightPlugin
     * @private
     * @returns {Promise}
     */
    _hideAndHighlightPlugin() {
        // cancel show if live modus is active
        if (CMS.config.mode === 'live') {
            return Promise.reject(false);
        }

        var dragitem = [];
        var HIGHLIGHT_TIMEOUT = 10;

        try {
            dragitem = $('.cms-dragitem:hover');
        } catch (e) {
            // weird bug in jQuery where `:hover` is seen as invalid pseudo, dance around it
            /* istanbul ignore next */
            $('.cms-dragitem').each(function () {
                var el = $(this);

                if (el.is(':hover')) {
                    dragitem = el;
                }
            });
        }

        if (!dragitem.length || dragitem.closest('.cms-clipboard-containers').length) {
            return Promise.reject(false);
        }

        var draggable = dragitem.closest('.cms-draggable');
        var pluginId = this.getId(draggable);

        return this.hide().then(function () {
            setTimeout(function () {
                Plugin._highlightPluginContent(pluginId);
            }, HIGHLIGHT_TIMEOUT);
        });
    }

    /**
     * Shows the structureboard. (Structure mode)
     *
     * @method show
     * @public
     * @param {Boolean} init true if this is first initialization
     * @returns {Boolean|void}
     */
    show(init) {
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
            this._saveStateInURL();
        }


        // ensure all elements are visible
        this.ui.dragareas.show();

        return this._loadStructure()
            .then(this._showBoard.bind(this));
    }

    _loadStructure() {
        var that = this;

        // case when structure mode is already loaded
        if (CMS.config.settings.mode === 'structure' || this._loadedStructure) {
            return Promise.resolve();
        }

        CMS.API.Toolbar.showLoader();
        return that._requestMode('structure').done(function (contentMarkup) {
            that._requeststructure = null;
            CMS.API.Toolbar.hideLoader();
            var bodyRegex = /<body[\S\s]*?>([\S\s]*)<\/body>/gi;
            var body = $(bodyRegex.exec(contentMarkup)[1]);

            var structure = body.find('.cms-structure-content');
            var toolbar = body.find('.cms-toolbar');
            var scripts = body.filter(function () {
                var elem = $(this);

                return elem.is('[type="text/cms-template"]'); // cms scripts
            });

            CMS.API.Toolbar._refreshMarkup(toolbar);

            $('body').append(scripts);
            $('.cms-structure-content').html(structure.html());

            triggerWindowResize();

            StructureBoard._initializeGlobalHandlers();
            StructureBoard.actualizeEmptyPlaceholders();

            // FIXME we don't handle the case when there are more plugins in structure
            // than in content, which is quite tricky

            CMS._instances.forEach(function (instance) {
                if (instance.options.type === 'placeholder') {
                    instance._setPlaceholder();
                }
            });
            CMS._instances.forEach(function (instance) {
                if (instance.options.type === 'plugin') {
                    instance._setPluginStructureEvents();
                    instance._collapsables();
                }
            });

            that.ui.sortables = $('.cms-draggables');
            that._drag();
            StructureBoard._initializeDragItemsStates();

            // TODO handle the case when there is a mismatch in number of plugins/placeholders
            // TODO might be edge cases when page doesn't exist anymore (moved/removed)
            that._loadedStructure = true;
        }).fail(/* istanbul ignore next */ function () {
            window.location.href = new URI(window.location.href).addSearch(CMS.settings.structure).toString();
        });
    }

    _requestMode(mode) {
        var url = new URI(window.location.href);

        if (mode === 'structure') {
            url.addSearch(CMS.settings.structure);
        } else {
            url.addSearch(CMS.settings.edit || 'edit').removeSearch(CMS.settings.structure);
        }

        if (!this[`_request${mode}`]) {
            this[`_request${mode}`] = $.ajax({
                url: url.toString(),
                method: 'GET'
            }).then((markup) => {
                preloadImagesFromMarkup(markup);

                return markup;
            });
        }

        return this[`_request${mode}`];
    }

    _loadContent() {
        var that = this;

        // case when content mode is already loaded
        if (CMS.config.settings.mode === 'edit' || this._loadedContent) {
            return Promise.resolve();
        }

        CMS.API.Toolbar.showLoader();
        return that._requestMode('content').done(function (contentMarkup) {
            that._requestcontent = null;
            CMS.API.Toolbar.hideLoader();
            var htmlRegex = /<html([\S\s]*?)>[\S\s]*<\/html>/gi;
            var bodyRegex = /<body([\S\s]*?)>([\S\s]*)<\/body>/gi;
            var headRegex = /<head[\S\s]*?>([\S\s]*)<\/head>/gi;
            var matches = bodyRegex.exec(contentMarkup);
            var bodyAttrs = matches[1];
            var body = $(matches[2]);
            var head = $(headRegex.exec(contentMarkup)[1]);
            var htmlAttrs = htmlRegex.exec(contentMarkup)[1];
            var bodyAttributes = $('<div ' + bodyAttrs + '></div>')[0].attributes;
            var htmlAttributes = $('<div ' + htmlAttrs + '></div>')[0].attributes;
            var newToolbar = body.find('.cms-toolbar');
            var toolbar = $('.cms').add('[data-cms]').detach();
            var title = head.filter('title');
            var bodyElement = $('body');

            // istanbul ignore else
            if (title) {
                document.title = title.text();
            }

            body = body.filter(function () {
                var elem = $(this);

                return !elem.is('.cms#cms-top') && // toolbar
                    !elem.is('[data-cms]:not([data-cms-generic])'); // cms scripts
            });
            body.find('[data-cms]:not([data-cms-generic])').remove(); // cms scripts

            [].slice.call(bodyAttributes).forEach(function (attr) {
                bodyElement.attr(attr.name, attr.value);
            });

            [].slice.call(htmlAttributes).forEach(function (attr) {
                $('html').attr(attr.name, attr.value);
            });

            bodyElement.append(body);
            $('head').append(head);
            bodyElement.prepend(toolbar);

            CMS.API.Toolbar._refreshMarkup(newToolbar);
            $(window).trigger('resize');

            // TODO find better way to reset
            Plugin.aliasPluginDuplicatesMap = {};
            Plugin.staticPlaceholderDuplicatesMap = {};
            CMS._plugins = uniqWith(CMS._plugins, isEqual);

            CMS._instances.forEach(function (instance, index) {
                if (instance.options.type === 'placeholder') {
                    instance._setupUI(CMS._plugins[index][0]);
                    instance._ensureData();
                    instance.ui.container.data('cms', instance.options);
                }
            });
            CMS._instances.forEach(function (instance, index) {
                if (instance.options.type === 'plugin') {
                    instance._setupUI(CMS._plugins[index][0]);
                    instance._ensureData();
                    instance.ui.container.data('cms').push(instance.options);
                    instance._setPluginContentEvents();
                }
            });

            CMS._plugins.forEach(([type, opts]) => {
                if (opts.type !== 'placeholder' && opts.type !== 'plugin') {
                    const instance = find(
                        CMS._instances,
                        (i) => i.options.type === opts.type && Number(i.options.plugin_id) === Number(opts.plugin_id)
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

            const scripts = $('script');

            // handle the page scripts that execute on DOM ready manually
            // since DOM was ready a while ago
            // istanbul ignore next
            scripts.on('load', function () {
                window.dispatchEvent(new Event('load'));
                window.dispatchEvent(new Event('DOMContentLoaded'));
            });

            const unhandledPlugins = bodyElement.find('template.cms-plugin');

            // istanbul ignore if
            if (unhandledPlugins.length) {
                CMS.API.Messages.open({
                    message: 'The page was changed in the meantime, reloading...'
                });
                Helpers.reloadBrowser();
            }

            that._loadedContent = true;
        }).fail(/* istanbul ignore next */ function () {
            window.location.href = new URI(window.location.href).removeSearch(CMS.settings.structure).toString();
        });
    }

    _saveStateInURL() {
        var url = new URI(window.location.href);

        url[CMS.settings.mode === 'structure' ? 'addSearch' : 'removeSearch'](CMS.settings.structure);

        history.replaceState({}, '', url.toString());
    }

    /**
     * Hides the structureboard. (Content mode)
     *
     * @method hide
     * @param {Boolean} init true if this is first initialization
     * @returns {Boolean|void}
     */
    hide(init) {
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
            this._saveStateInURL();
        }

        // hide canvas
        return this._loadContent().then(this._hideBoard.bind(this));
    }

    /**
     * Gets the id of the element.
     * relies on cms-{item}-{id} to always be second in a string of classes (!)
     *
     * @method getId
     * @param {jQuery} el element to get id from
     * @returns {String}
     */
    getId(el) {
        // cancel if no element is defined
        if (el === undefined || el === null || el.length <= 0) {
            return false;
        }

        var id = null;
        var cls = el.attr('class').split(' ')[1];

        if (el.hasClass('cms-plugin')) {
            id = cls.replace('cms-plugin-', '').trim();
        } else if (el.hasClass('cms-draggable')) {
            id = cls.replace('cms-draggable-', '').trim();
        } else if (el.hasClass('cms-placeholder')) {
            id = cls.replace('cms-placeholder-', '').trim();
        } else if (el.hasClass('cms-dragbar')) {
            id = cls.replace('cms-dragbar-', '').trim();
        } else if (el.hasClass('cms-dragarea')) {
            id = cls.replace('cms-dragarea-', '').trim();
        }

        return id;
    }

    /**
     * Gets the ids of the list of  elements.
     *
     * @method getIds
     * @param {jQuery} els elements to get id from
     * @returns {String[]}
     */
    getIds(els) {
        var that = this;
        var array = [];

        els.each(function () {
            array.push(that.getId($(this)));
        });
        return array;
    }

    /**
     * Actually shows the board canvas.
     *
     * @method _showBoard
     * @private
     */
    _showBoard() {
        // show container
        this.ui.container.show();
        this.ui.dragareas.css('opacity', 1);

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
    }

    /**
     * Hides the board canvas.
     *
     * @method _hideBoard
     * @private
     */
    _hideBoard() {
        // hide elements
        this.ui.container.hide();

        // this is sometimes required for user-side scripts to
        // render dynamic elements on the page correctly.
        // e.g. you have a parallax script that calculates position
        // of elements based on document height. but if the page is
        // loaded with structureboard active - the document height
        // would be same as screen height, which is likely incorrect,
        // so triggering resize on window would force user scripts
        // to recalculate whatever is required there
        // istanbul ignore catch
        triggerWindowResize();
    }

    /**
     * Sets up all the sortables.
     *
     * @method _drag
     * @private
     */
    _drag() {
        var that = this;
        var originalPluginContainer;

        try {
            this.ui.sortables.nestedSortable('destroy');
        } catch (e) {

        }
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
                StructureBoard.actualizeEmptyPlaceholders();
                // ensure all menus are closed
                Plugin._hideSettingsMenu();
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
                    if (event.keyCode === KEYS.ESC && that.dragging || cancel) {
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
                    StructureBoard.actualizePluginsCollapsibleStatus(newPluginContainer.add(originalPluginContainer));
                }

                // we pass the id to the updater which checks within the backend the correct place
                var id = that.getId(ui.item);
                var plugin = $(`.cms-draggable-${id}`);
                var eventData = {
                    id: id
                };
                var previousParentPlugin = originalPluginContainer.closest('.cms-draggable');

                if (previousParentPlugin.length) {
                    var previousParentPluginId = that.getId(previousParentPlugin);

                    eventData.previousParentPluginId = previousParentPluginId;
                }

                // check if we copy/paste a plugin or not
                if (originalPluginContainer.hasClass('cms-clipboard-containers')) {
                    originalPluginContainer.html(plugin.eq(0).clone(true, true));
                    plugin.trigger('cms-paste-plugin-update', [eventData]);
                } else {
                    plugin.trigger('cms-plugins-update', [eventData]);
                }

                // reset placeholder without entries
                that.ui.sortables.each(function () {
                    var element = $(this);

                    if (element.children().length === 0) {
                        element.addClass('cms-hidden');
                    }
                });

                StructureBoard.actualizeEmptyPlaceholders();
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

                var originalItemId = that.getId(originalItem);
                // save original state events
                var original = $('.cms-draggable-' + originalItemId);

                // cancel if item has no settings
                if (original.length === 0 || !original.data('cms')) {
                    return false;
                }
                var originalItemData = original.data('cms');
                var parent_bounds = $.grep(originalItemData.plugin_parent_restriction, function (r) {
                    // special case when PlaceholderPlugin has a parent restriction named "0"
                    return r !== '0';
                });
                var type = originalItemData.plugin_type;
                // prepare variables for bound
                var holderId = that.getId(placeholder.closest('.cms-dragarea'));
                var holder = $('.cms-placeholder-' + holderId);
                var plugin;

                if (placeholderParent && placeholderParent.length) {
                    // placeholderParent is always latest, it maybe that
                    // isAllowed is called _before_ placeholder is moved to a child plugin
                    plugin = $('.cms-draggable-' + that.getId(placeholderParent.closest('.cms-draggable')));
                } else {
                    plugin = $('.cms-draggable-' + that.getId(placeholder.closest('.cms-draggable')));
                }

                // now set the correct bounds
                // istanbul ignore else
                if (holder.length) {
                    bounds = holder.data('cms').plugin_restriction;
                    immediateParentType = holder.data('cms').plugin_type;
                }
                if (plugin.length) {
                    bounds = plugin.data('cms').plugin_restriction;
                    immediateParentType = plugin.data('cms').plugin_type;
                }

                // if restrictions is still empty, proceed
                that.state = !(bounds.length && $.inArray(type, bounds) === -1);

                // check if we have a parent restriction
                if (parent_bounds.length) {
                    that.state = $.inArray(immediateParentType, parent_bounds) !== -1;
                }

                return that.state;
            }
        }).on('cms-structure-update', StructureBoard.actualizeEmptyPlaceholders);
    }

    // TODO deal with already loaded states as well
    //
    //
    // Currently is only called when something changed on the page, but shouldn't make that assumption
    // eslint-disable-next-line complexity
    invalidateState(action, data) {
        // eslint-disable-next-line default-case
        switch (action) {
            case 'COPY': {
                this.handleCopyPlugin(data);
                break;
            }

            case 'ADD': {
                this.handleAddPlugin(data);
                break;
            }

            case 'EDIT': {
                this.handleEditPlugin(data);
                break;
            }

            case 'DELETE': {
                this.handleDeletePlugin(data);
                break;
            }

            case 'CLEAR_PLACEHOLDER': {
                this.handleClearPlaceholder(data);
                break;
            }

            case 'PASTE':
            case 'MOVE': {
                this.handleMovePlugin(data);
                break;
            }

            case 'CUT': {
                this.handleCutPlugin(data);
                break;
            }
        }

        if (!action) {
            CMS.API.Helpers.reloadBrowser();
            return;
        }

        // refresh content mode if needed
        // refresh toolbar
        var currentMode = CMS.settings.mode;


        this._loadToolbar()
            .done((newToolbar) => {
                CMS.API.Toolbar._refreshMarkup($(newToolbar).find('.cms-toolbar'));
            })
            .fail(() => Helpers.reloadBrowser());

        if (currentMode === 'structure') {
            this._requestcontent = null;

            // TODO update it in two secs (maybe debounce);

            if (this._loadedContent) {
                this._requestMode('content')
                    .done(this.refreshContent.bind(this))
                    .fail(() => Helpers.reloadBrowser());
            }
            return;
        }

        // invalidate the content mode
        this._requestcontent = null;
        this._requestMode('content')
            .done(this.refreshContent.bind(this))
            .fail(() => Helpers.reloadBrowser());

        return;
    }

    _loadToolbar() {
        return $.ajax({
            url: Helpers.updateUrlWithPath(
                `${CMS.config.request.toolbar}` +
                `?obj_id=${CMS.config.request.pk}&` +
                `obj_type=${encodeURIComponent(CMS.config.request.model)}`
            )
        });
    }

    handleMovePlugin(data) {
        if (data.plugin_parent) {
            $(`.cms-draggable-${data.plugin_parent}`).replaceWith(data.html);
        } else {
            // the one in the clipboard is first, so we need to take the second one,
            // that is already visually moved into correct place
            const draggable = $(`.cms-draggable-${data.plugin_id}:last`);

            if (draggable.length) {
                draggable.replaceWith(data.html);
            } else if (data.target_placeholder_id) {
                // copy from language
                $(`.cms-dragarea-${data.target_placeholder_id} > .cms-draggables`).append(data.html);
            }
        }

        StructureBoard.actualizeEmptyPlaceholders();
        Plugin._updateRegistry(data.plugins);
        data.plugins.forEach((pluginData) => {
            StructureBoard.actualizePluginCollapseStatus(pluginData.plugin_id);
        });

        // FIXME When moving - update this from CMS.states instead
        // When pasting - keep this
        const topLevel = $(`.cms-draggable-${data.plugins[0].plugin_id} > .cms-dragitem`);

        // istanbul ignore else
        if (!topLevel.hasClass('cms-dragitem-expanded')) {
            topLevel.find('> .cms-dragitem-text').trigger('click');
        }

        this.ui.sortables = $('.cms-draggables');
        this._drag();
    }

    handleCopyPlugin(data) {
        if (CMS.API.Clipboard._isClipboardModalOpen()) {
            CMS.API.Clipboard.modal.close();
        }

        $('.cms-clipboard-containers').html(data.html);
        const cloneClipboard = $('.cms-clipboard').clone();

        $('.cms-clipboard').replaceWith(cloneClipboard);

        const pluginData = [`cms-plugin-${data.plugins[0].plugin_id}`, data.plugins[0]];

        Plugin.aliasPluginDuplicatesMap[pluginData[1].plugin_id] = false;
        CMS._plugins.push(pluginData);
        CMS._instances.push(new Plugin(pluginData[0], pluginData[1]));

        CMS.API.Clipboard = new Clipboard();

        Plugin._updateClipboard();

        let html = '';

        const clipboardDraggable = $('.cms-clipboard .cms-draggable:first');

        html = clipboardDraggable.parent().html();

        CMS.API.Clipboard.populate(html, pluginData[1]);
        CMS.API.Clipboard._enableTriggers();

        this.ui.sortables = $('.cms-draggables');
        this._drag();
    }

    handleCutPlugin(data) {
        this.handleDeletePlugin(data);
        this.handleCopyPlugin(data);
    }

    _extractMessages(doc) {
        let messageList = doc.find('.messagelist');
        let messages = messageList.find('li');

        if (!messageList.length || !messages.length) {
            messageList = doc.find('[data-cms-messages-container]');
            messages = messageList.find('[data-cms-message]');
        }

        if (messages.length) {
            messageList.remove();

            return compact(messages.toArray().map((el) => {
                const msgEl = $(el);
                const message = $(el).text().trim();

                if (message) {
                    return {
                        message,
                        error: msgEl.data('cms-message-tags') === 'error' ||
                            msgEl.hasClass('error')
                    };
                }
            }));
        }

        return [];
    }

    refreshContent(contentMarkup) {
        this._requestcontent = null;
        var fixedContentMarkup = contentMarkup; // .replace(/<noscript[\s\S]*?<\/noscript>/, '');
        var newDoc = new DOMParser().parseFromString(fixedContentMarkup, 'text/html');

        const structureScrollTop = $('.cms-structure-content').scrollTop();

        // check generics!
        var toolbar = $('#cms-top, [data-cms]').detach();
        var newToolbar = $(newDoc).find('.cms-toolbar').clone();

        $(newDoc).find('#cms-top, [data-cms]').remove();

        const messages = this._extractMessages($(newDoc));

        if (messages.length) {
            setTimeout(() => messages.forEach((message) => {
                CMS.API.Messages.open(message);
            }));
        }

        // TODO handle the case when there is a plugin count mismatch but not generics mismatch
        var diff = dd.diff(document.body, newDoc.body);
        var headDiff = dd.diff(document.head, newDoc.head);

        dd.apply(document.body, diff);
        dd.apply(document.head, headDiff);
        toolbar.prependTo(document.body);
        CMS.API.Toolbar._refreshMarkup(newToolbar);

        $('.cms-structure-content').scrollTop(structureScrollTop);

        // TODO find better way to reset
        Plugin.aliasPluginDuplicatesMap = {};
        Plugin.staticPlaceholderDuplicatesMap = {};
        CMS._instances.forEach(function (instance) {
            if (instance.options.type === 'placeholder') {
                instance._setupUI(`cms-placeholder-${instance.options.placeholder_id}`);
                instance._ensureData();
                instance.ui.container.data('cms', instance.options);
                instance._setPlaceholder();
            }
        });
        CMS._instances.forEach(function (instance) {
            if (instance.options.type === 'plugin') {
                instance._setupUI(`cms-plugin-${instance.options.plugin_id}`);
                instance._ensureData();
                instance.ui.container.data('cms').push(instance.options);
                instance._setPluginContentEvents();
                // TODO generics
            }
        });

        window.dispatchEvent(new Event('load'));
        window.dispatchEvent(new Event('DOMContentLoaded'));

        // TODO handle the case when there is a mismatch in number of plugins/placeholders
        // TODO might be edge cases when page doesn't exist anymore (moved/removed)
        this._loadedContent = true;
    }

    handleAddPlugin(data) {
        if (data.plugin_parent) {
            $(`.cms-draggable-${data.plugin_parent}`).replaceWith(data.structure.html);
        } else {
            // the one in the clipboard is first
            $(`.cms-dragarea-${data.placeholder_id} > .cms-draggables`).append(data.structure.html);
        }

        StructureBoard.actualizeEmptyPlaceholders();
        Plugin._updateRegistry(data.structure.plugins);
        data.structure.plugins.forEach((pluginData) => {
            StructureBoard.actualizePluginCollapseStatus(pluginData.plugin_id);
        });

        this.ui.sortables = $('.cms-draggables');
        this._drag();
    }

    handleEditPlugin(data) {
        if (data.plugin_parent) {
            $(`.cms-draggable-${data.plugin_parent}`).replaceWith(data.structure.html);
        } else {
            $(`.cms-draggable-${data.plugin_id}`).replaceWith(data.structure.html);
        }

        Plugin._updateRegistry(data.structure.plugins);

        data.structure.plugins.forEach((pluginData) => {
            StructureBoard.actualizePluginCollapseStatus(pluginData.plugin_id);
        });

        this.ui.sortables = $('.cms-draggables');
        this._drag();
    }

    handleDeletePlugin(data) {
        var deletedPluginIds = [data.plugin_id];
        var draggable = $('.cms-draggable-' + data.plugin_id);
        var children = draggable.find('.cms-draggable');
        let parent = draggable.parent().closest('.cms-draggable');

        if (!parent.length) {
            parent = draggable.closest('.cms-dragarea');
        }

        if (children.length) {
            deletedPluginIds = deletedPluginIds.concat(this.getIds(children));
        }

        draggable.remove();

        StructureBoard.actualizePluginsCollapsibleStatus(parent.find('> .cms-draggables'));
        StructureBoard.actualizeEmptyPlaceholders();
        deletedPluginIds.forEach(function (pluginId) {
            remove(CMS._plugins, (settings) => settings[0] === `cms-plugin-${pluginId}`);
            remove(CMS._instances, (instance) =>
                instance.options.plugin_id && Number(instance.options.plugin_id) === Number(pluginId));
        });
    }

    handleClearPlaceholder(data) {
        var deletedIds = CMS._instances.filter((instance) => {
            if (instance.options.plugin_id &&
                Number(instance.options.placeholder_id) === Number(data.placeholder_id)) {
                return true;
            }
        }).map((instance) => instance.options.plugin_id);

        deletedIds.forEach((id) => {
            remove(CMS._plugins, (settings) => settings[0] === `cms-plugin-${id}`);
            remove(CMS._instances, (instance) =>
                instance.options.plugin_id && Number(instance.options.plugin_id) === Number(id));

            $(`.cms-draggable-${id}`).remove();
        });

        StructureBoard.actualizeEmptyPlaceholders();
    }

    // this method currently isn't used, but in order to
    // fix some of the edge cases we might have to use it again
    // istanbul ignore next
    _getPluginIdsFromMarkup(markup) {
        const element = $(markup);
        const pluginId = this.getId(element);
        const pluginChildren = element.find('.cms-draggable');
        let pluginIds = [pluginId];

        if (pluginChildren.length) {
            pluginIds = pluginIds
                .concat(pluginChildren.toArray().map((el) => this.getId($(el)).trim()));
        }

        return pluginIds;
    }

    /*
      // usage:
      const pluginIdsToInit = this._getPluginIdsFromMarkup(newPluginStructure);

      ... find the ones that aren't initialized

      const pluginDataToInit = this._getPluginDataFromText(
      $(new DOMParser().parseFromString(response, 'text/html').documentElement)
         .find('script[data-cms]')
         .filter((i, el) => $(el).text().match(new RegExp(`cms-plugin-${data.plugin_id}`)))
         .text(),
          pluginIdsToAdd
      );
    */
    // istanbul ignore next
    _getPluginDataFromText(text, pluginIds) {
        return compact(pluginIds.map((pluginId) => {
            // oh boy there should be an easier way
            const regex = new RegExp(`CMS._plugins.push\\((\\["cms\-plugin\-${pluginId}",[\\s\\S]*?\\])\\);`, 'g');
            const matches = regex.exec(text);
            let settings;

            if (matches) {
                try {
                    settings = JSON.parse(matches[1]);
                } catch (e) {
                    // don't really see those happening
                    settings = false;
                }
            } else {
                settings = false;
            }

            return settings;
        }));
    }

    /**
     * Similar to CMS.Plugin populates globally required
     * variables, that only need querying once, e.g. placeholders.
     *
     * @method _initializeGlobalHandlers
     * @static
     * @private
     */
    static _initializeGlobalHandlers() {
        placeholders = $('.cms-dragarea:not(.cms-clipboard-containers)');
    }

    /**
     * @function actualizeEmptyPlaceholders
     * @private
     */
    static actualizeEmptyPlaceholders() {
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
     * actualizePluginCollapseStatus
     *
     * @public
     * @param {String} pluginId open the plugin if it should be open
     */
    static actualizePluginCollapseStatus(pluginId) {
        const el = $(`.cms-draggable-${pluginId}`);
        const open = find(
            CMS.settings.states,
            (openPluginId) => Number(openPluginId) === Number(pluginId)
        );

        // only add this class to elements which have a draggable area
        // istanbul ignore else
        if (open && el.find('> .cms-draggables').length) {
            el.find('> .cms-collapsable-container').removeClass('cms-hidden');
            el.find('> .cms-dragitem').addClass('cms-dragitem-expanded');
        }
    }

    /**
     * @function actualizePluginsCollapsibleStatus
     * @private
     * @param {jQuery} els lists of plugins (.cms-draggables)
     */
    static actualizePluginsCollapsibleStatus(els) {
        els.each(function () {
            var childList = $(this);
            var pluginDragItem = childList.closest('.cms-draggable').find('> .cms-dragitem');

            if (childList.children().length) {
                pluginDragItem.addClass('cms-dragitem-collapsable');
                if (childList.children().is(':visible')) {
                    pluginDragItem.addClass('cms-dragitem-expanded');
                }
            } else {
                pluginDragItem.removeClass('cms-dragitem-collapsable');
            }
        });
    }
}

/**
 * Initializes the collapsed/expanded states of dragitems in structureboard.
 *
 * @method _initializeDragItemsStates
 * @static
 * @private
 */
// istanbul ignore next
StructureBoard._initializeDragItemsStates = once(function _initializeDragItemsStates() {
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
$(StructureBoard._initializeGlobalHandlers);

export default StructureBoard;
