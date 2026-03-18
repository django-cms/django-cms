/*
 * Copyright https://github.com/divio/django-cms
 */

/* eslint-env es6 */
/* jshint esversion: 6 */
/* global CMS */

import $ from 'jquery';
import keyboard from './keyboard';
import Plugin from './cms.plugins';
import { getPlaceholderIds } from './cms.toolbar';
import Clipboard from './cms.clipboard';
import { DiffDOM, nodeToObj } from 'diff-dom';
import PreventParentScroll from 'prevent-parent-scroll';
import { find, findIndex, once, remove, compact, isEqual, zip, every } from 'lodash';
import ls from 'local-storage';

import './jquery.ui.custom';
import './jquery.ui.touchpunch';
import './jquery.ui.nestedsortable';

import measureScrollbar from './scrollbar';
import preloadImagesFromMarkup from './preload-images';

import { Helpers, KEYS } from './cms.base';
import { showLoader, hideLoader } from './loader';

const DOMParser = window.DOMParser; // needed only for testing
const storageKey = 'cms-structure';

let dd;
let placeholders;
let originalPluginContainer;

const triggerWindowResize = () => {
    'use strict';
    try {
        const evt = document.createEvent('UIEvents');

        evt.initUIEvent('resize', true, false, window, 0);
        window.dispatchEvent(evt);
    } catch (e) {}
};

const arrayEquals = (a1, a2) => every(zip(a1, a2), ([a, b]) => a === b);

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
        this.click = 'click.cms.structure';
        this.keyUpAndDown = 'keyup.cms.structure keydown.cms.structure';
        this.pointerUp = 'pointerup.cms';
        this.state = false;
        this.dragging = false;
        this.latestAction = [];
        this.scriptReferenceCount = 0;
        ls.remove(storageKey);

        dd = new DiffDOM();

        // setup initial stuff
        const setup = this._setup();

        // istanbul ignore if
        if (typeof setup === 'undefined' && CMS.config.mode === 'draft') {
            this._preloadOppositeMode();
        }
        this._setupModeSwitcher();
        this._events();
        StructureBoard.actualizePlaceholders();

        setTimeout(() => this.highlightPluginFromUrl(), 0);
        this._listenToExternalUpdates();
    }

    /**
     * Stores all jQuery references within `this.ui`.
     *
     * @method _setupUI
     * @private
     */
    _setupUI() {
        const container = $('.cms-structure');
        const toolbar = $('.cms-toolbar');

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
            toolbarModeLinks: toolbar.find('.cms-toolbar-item-cms-mode-switcher a')
        };

        this._preventScroll = new PreventParentScroll(this.ui.content[0]);
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
        const that = this;

        // cancel if there is no structure / content switcher
        if (!this.ui.toolbarModeSwitcher.length) {
            return false;
        }

        // setup toolbar mode
        if (CMS.config.settings.mode === 'structure') {
            that.show({ init: true });
            that._loadedStructure = true;
            StructureBoard._initializeDragItemsStates();
        } else {
            // triggering hide here to switch proper classnames on switcher
            that.hide();
            that._loadedContent = true;
        }

        if (CMS.config.settings.legacy_mode) {
            that._loadedStructure = true;
            that._loadedContent = true;
        }

        // check if modes should be visible
        if (this.ui.dragareas.not('.cms-clipboard .cms-dragarea').length || this.ui.placeholders.length) {
            // eslint-disable-line
            this.ui.toolbarModeSwitcher.find('.cms-btn').removeClass('cms-btn-disabled');
        }

        // add drag & drop functionality
        // istanbul ignore next
        $('.cms-draggable:not(.cms-drag-disabled)').one(
            'pointerover.cms.drag',
            once(() => {
                $('.cms-draggable').off('pointerover.cms.drag');
                this._drag();
            })
        );
    }

    _preloadOppositeMode() {
        if (CMS.config.settings.legacy_mode) {
            return;
        }
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

    _events() {
        this.ui.window.on('resize.cms.structureboard', () => {
            if (!this._loadedContent || CMS.config.mode !== 'draft') {
                return;
            }
            const width = this.ui.window[0].innerWidth;
            const BREAKPOINT = 1024;

            if (width > BREAKPOINT && !this.condensed) {
                this._makeCondensed();
            }

            if (width <= BREAKPOINT && this.condensed) {
                this._makeFullWidth();
            }
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
        const modes = this.ui.toolbarModeLinks;
        let cmdPressed;

        $(Helpers._getWindow())
            .on(this.keyUpAndDown, e => {
                if (
                    e.keyCode === KEYS.CMD_LEFT ||
                    e.keyCode === KEYS.CMD_RIGHT ||
                    e.keyCode === KEYS.CMD_FIREFOX ||
                    e.keyCode === KEYS.SHIFT ||
                    e.keyCode === KEYS.CTRL
                ) {
                    cmdPressed = true;
                }
                if (e.type === 'keyup') {
                    cmdPressed = false;
                }
            })
            .on('blur', () => {
                cmdPressed = false;
            });

        // show edit mode
        modes.on(this.click, e => {
            e.preventDefault();
            e.stopImmediatePropagation();

            if (modes.hasClass('cms-btn-disabled')) {
                return;
            }

            if (cmdPressed && e.type === 'click') {
                // control the behaviour when ctrl/cmd is pressed
                Helpers._getWindow().open(modes.attr('href'), '_blank');
                return;
            }

            if (CMS.settings.mode === 'edit') {
                this.show();
            } else {
                this.hide();
            }
        });

        // keyboard handling
        // only if there is a structure / content switcher
        if (
            this.ui.toolbarModeSwitcher.length &&
            !this.ui.toolbarModeSwitcher.find('.cms-btn').is('.cms-btn-disabled')
        ) {
            keyboard.setContext('cms');
            keyboard.bind('space', e => {
                e.preventDefault();
                this._toggleStructureBoard();
            });
            keyboard.bind('shift+space', e => {
                e.preventDefault();
                this._toggleStructureBoard({ useHoveredPlugin: true });
            });
        }
    }

    /**
     * @method _toggleStructureBoard
     * @private
     * @param {Object} [options] options
     * @param {Boolean} [options.useHoveredPlugin] should the plugin be taken into account
     */
    _toggleStructureBoard(options = {}) {
        const that = this;

        if (options.useHoveredPlugin && CMS.settings.mode !== 'structure') {
            that._showAndHighlightPlugin(options.successTimeout).then($.noop, $.noop);
        } else if (!options.useHoveredPlugin) {
            // eslint-disable-next-line no-lonely-if
            if (CMS.settings.mode === 'structure') {
                that.hide();
            } else if (CMS.settings.mode === 'edit') {
                /* istanbul ignore else */ that.show();
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
    // eslint-disable-next-line no-magic-numbers
    _showAndHighlightPlugin(successTimeout = 200, seeThrough = false) {
        // cancel show if live modus is active
        if (CMS.config.mode === 'live') {
            return Promise.resolve(false);
        }

        if (!CMS.API.Tooltip) {
            return Promise.resolve(false);
        }

        const tooltip = CMS.API.Tooltip.domElem;
        const HIGHLIGHT_TIMEOUT = 10;
        const DRAGGABLE_HEIGHT = 50; // it's not precisely 50, but it fits

        if (!tooltip.is(':visible')) {
            return Promise.resolve(false);
        }

        const pluginId = tooltip.data('plugin_id');

        return this.show().then(function() {
            const draggable = $('.cms-draggable-' + pluginId);
            const doc = $(document);
            const currentExpandmode = doc.data('expandmode');

            // expand necessary parents
            doc.data('expandmode', false);
            draggable
                .parents('.cms-draggable')
                .find('> .cms-dragitem-collapsable:not(".cms-dragitem-expanded") > .cms-dragitem-text')
                .each((i, el) => $(el).triggerHandler(Plugin.click));

            setTimeout(() => doc.data('expandmode', currentExpandmode));
            setTimeout(function() {
                const offsetParent = draggable.offsetParent();
                const position = draggable.position().top + offsetParent.scrollTop();

                draggable.offsetParent().scrollTop(position - window.innerHeight / 2 + DRAGGABLE_HEIGHT);

                Plugin._highlightPluginStructure(draggable.find('.cms-dragitem:first'), { successTimeout, seeThrough });
            }, HIGHLIGHT_TIMEOUT);
        });
    }

    /**
     * Shows the structureboard. (Structure mode)
     *
     * @method show
     * @public
     * @param {Boolean} init true if this is first initialization
     * @returns {Promise}
     */
    show({ init = false } = {}) {
        // cancel show if live modus is active
        if (CMS.config.mode === 'live') {
            return Promise.resolve(false);
        }

        // in order to get consistent positioning
        // of the toolbar we have to know if the page
        // had the scrollbar and if it had - we adjust
        // the toolbar positioning
        if (init) {
            const width = this.ui.toolbar.width();
            let scrollBarWidth = this.ui.window[0].innerWidth - width;

            if (!scrollBarWidth && init) {
                scrollBarWidth = measureScrollbar();
            }

            if (scrollBarWidth) {
                this.ui.toolbar.css('right', scrollBarWidth);
            }
        }
        // apply new settings
        CMS.settings.mode = 'structure';
        Helpers.setSettings(CMS.settings);

        return this._loadStructure().then(this._showBoard.bind(this, init));
    }

    _loadStructure() {
        // case when structure mode is already loaded
        if (CMS.config.settings.mode === 'structure' || this._loadedStructure) {
            return Promise.resolve();
        }

        showLoader();
        return this
            ._requestMode('structure')
            .done(contentMarkup => {
                this._requeststructure = null;
                hideLoader();

                CMS.settings.states = Helpers.getSettings().states;

                const bodyRegex = /<body[\S\s]*?>([\S\s]*)<\/body>/gi;
                const body = document.createElement('div');  // Switch to plain JS due to problem with $(body)

                body.innerHTML = bodyRegex.exec(contentMarkup)[1];

                const structure = $(body.querySelector('.cms-structure-content'));
                const toolbar = $(body.querySelector('.cms-toolbar'));
                const scripts = $(body.querySelectorAll('[type="text/cms-template"]')); // cms scripts
                const pluginIds = this.getIds($(body.querySelectorAll('.cms-draggable')));
                const pluginData = StructureBoard._getPluginDataFromMarkup(
                    body,
                    pluginIds
                );

                Plugin._updateRegistry(pluginData);

                CMS.API.Toolbar._refreshMarkup(toolbar);

                $('body').append(scripts);
                $('.cms-structure-content').html(structure.html());
                triggerWindowResize();

                StructureBoard._initializeGlobalHandlers();
                StructureBoard.actualizePlaceholders();
                CMS._instances.forEach(instance => {
                    if (instance.options.type === 'placeholder') {
                        instance._setPlaceholder();
                    }
                });
                CMS._instances.forEach(instance => {
                    if (instance.options.type === 'plugin') {
                        instance._setPluginStructureEvents();
                        instance._collapsables();
                    }
                });

                this.ui.sortables = $('.cms-draggables');
                this._drag();
                StructureBoard._initializeDragItemsStates();

                this._loadedStructure = true;
            })
            .fail(function() {
                window.location.href = CMS.config.settings.structure;
            });
    }

    _requestMode(mode) {
        let url;

        if (mode === 'structure') {
            url = CMS.config.settings.structure;
        } else {
            url = CMS.config.settings.edit;
        }

        if (!this[`_request${mode}`]) {
            this[`_request${mode}`] = $.ajax({
                url: url.toString(),
                method: 'GET'
            }).then(markup => {
                preloadImagesFromMarkup(markup);

                return markup;
            });
        }

        return this[`_request${mode}`];
    }

    _loadContent() {
        const that = this;

        // case when content mode is already loaded
        if (CMS.config.settings.mode === 'edit' || this._loadedContent) {
            return Promise.resolve();
        }

        showLoader();
        return that
            ._requestMode('content')
            .done(function(contentMarkup) {
                that._requestcontent = null;
                hideLoader();
                const htmlRegex = /<html([\S\s]*?)>[\S\s]*<\/html>/gi;
                const bodyRegex = /<body([\S\s]*?)>([\S\s]*)<\/body>/gi;
                const headRegex = /<head[\S\s]*?>([\S\s]*)<\/head>/gi;
                const matches = bodyRegex.exec(contentMarkup);
                // we don't handle cases where body or html doesn't exist, cause it's highly unlikely
                // and will result in way more troubles for cms than this
                const bodyAttrs = matches[1];
                let body = $(matches[2]);
                const head = $(headRegex.exec(contentMarkup)[1]);
                const htmlAttrs = htmlRegex.exec(contentMarkup)[1];
                const bodyAttributes = $('<div ' + bodyAttrs + '></div>')[0].attributes;
                const htmlAttributes = $('<div ' + htmlAttrs + '></div>')[0].attributes;
                const newToolbar = body.find('.cms-toolbar');
                const toolbar = $('.cms').add('[data-cms]').detach();
                const title = head.filter('title');
                const bodyElement = $('body');

                // istanbul ignore else
                if (title) {
                    document.title = title.text();
                }

                body = body.filter(function() {
                    const elem = $(this);

                    return (
                        !elem.is('.cms#cms-top') && !elem.is('[data-cms]:not([data-cms-generic])') // toolbar
                    ); // cms scripts
                });
                body.find('[data-cms]:not([data-cms-generic])').remove();  // cms scripts

                [].slice.call(bodyAttributes).forEach(function(attr) {
                    bodyElement.attr(attr.name, attr.value);
                });

                [].slice.call(htmlAttributes).forEach(function(attr) {
                    $('html').attr(attr.name, attr.value);
                });

                bodyElement.append(body);
                $('head').append(head);
                bodyElement.prepend(toolbar);

                CMS.API.Toolbar._refreshMarkup(newToolbar);
                $(window).trigger('resize');

                Plugin._refreshPlugins();

                const scripts = $('script');

                // istanbul ignore next
                scripts.on('load', function() {
                    window.document.dispatchEvent(new Event('DOMContentLoaded'));
                    window.dispatchEvent(new Event('load'));
                });

                const unhandledPlugins = bodyElement.find('template.cms-plugin');

                if (unhandledPlugins.length) {
                    CMS.API.Messages.open({
                        message: CMS.config.lang.unhandledPageChange
                    });
                    Helpers.reloadBrowser('REFRESH_PAGE');
                }

                that._loadedContent = true;
            })
            .fail(function() {
                window.location.href = CMS.config.settings.edit;
            });
    }

    /**
     * Hides the structureboard. (Content mode)
     *
     * @method hide
     * @returns {Boolean|void}
     */
    hide() {
        // cancel show if live modus is active
        if (CMS.config.mode === 'live') {
            return false;
        }

        // reset toolbar positioning
        this.ui.toolbar.css('right', '');
        $('html').removeClass('cms-overflow');

        // set active item
        const modes = this.ui.toolbarModeLinks;

        modes.removeClass('cms-btn-active').eq(1).addClass('cms-btn-active');
        this.ui.html.removeClass('cms-structure-mode-structure').addClass('cms-structure-mode-content');

        CMS.settings.mode = 'edit';

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

        let id = null;
        const cls = el.attr('class').split(' ')[1];

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
        const that = this;
        const array = [];

        els.each(function() {
            array.push(that.getId($(this)));
        });
        return array;
    }

    /**
     * Actually shows the board canvas.
     *
     * @method _showBoard
     * @param {Boolean} init init
     * @private
     */
    _showBoard(init) {
        // set active item
        const modes = this.ui.toolbarModeLinks;

        modes.removeClass('cms-btn-active').eq(0).addClass('cms-btn-active');
        this.ui.html.removeClass('cms-structure-mode-content').addClass('cms-structure-mode-structure');

        this.ui.container.show();
        hideLoader();

        if (!init) {
            this._makeCondensed();
        }

        if (init && !this._loadedContent) {
            this._makeFullWidth();
        }

        this._preventScroll.start();
        this.ui.window.trigger('resize');
    }

    _makeCondensed() {
        this.condensed = true;
        this.ui.container.addClass('cms-structure-condensed');

        if (CMS.settings.mode === 'structure') {
            history.replaceState({}, '', CMS.config.settings.edit);
        }

        const width = this.ui.toolbar.width();
        let scrollBarWidth = this.ui.window[0].innerWidth - width;

        if (!scrollBarWidth) {
            scrollBarWidth = measureScrollbar();
        }

        this.ui.html.removeClass('cms-overflow');

        if (scrollBarWidth) {
            // this.ui.toolbar.css('right', scrollBarWidth);
            this.ui.container.css('right', -scrollBarWidth);
        }
    }

    _makeFullWidth() {
        this.condensed = false;
        this.ui.container.removeClass('cms-structure-condensed');

        if (CMS.settings.mode === 'structure') {
            history.replaceState({}, '', CMS.config.settings.structure);
            $('html.cms-structure-mode-structure').addClass('cms-overflow');
        }

        this.ui.container.css('right', 0);
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
        this._preventScroll.stop();

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
     * @param {jQuery} [elem=this.ui.sortables] which element to initialize
     * @private
     */
    _drag(elem = this.ui.sortables) {
        const that = this;

        elem
            .nestedSortable({
                items: '> .cms-draggable:not(.cms-drag-disabled):not(.cms-draggable-disabled .cms-draggable)',
                placeholder: 'cms-droppable',
                connectWith: '.cms-draggables:not(.cms-hidden)',
                tolerance: 'intersect',
                toleranceElement: '> div',
                dropOnEmpty: true,
                // cloning huge structure is a performance loss compared to cloning just a dragitem
                helper: function createHelper(e, item) {
                    const clone = item.find('> .cms-dragitem').clone();

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
                start: function(e, ui) {
                    that.ui.content.attr('data-touch-action', 'none');

                    originalPluginContainer = ui.item.closest('.cms-draggables');

                    that.dragging = true;
                    // show empty
                    StructureBoard.actualizePlaceholders();
                    // ensure all menus are closed
                    Plugin._hideSettingsMenu();
                    // keep in mind that caching cms-draggables query only works
                    // as long as we don't create them on the fly
                    that.ui.sortables.each(function() {
                        const element = $(this);

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
                    that.ui.doc.on('keyup.cms.interrupt', function(event, cancel) {
                        if ((event.keyCode === KEYS.ESC && that.dragging) || cancel) {
                            that.state = false;
                            $.ui.sortable.prototype._mouseStop();
                            that.ui.sortables.trigger('mouseup');
                        }
                    });
                },

                beforeStop: function(event, ui) {
                    that.dragging = false;
                    ui.item.removeClass('cms-is-dragging cms-draggable-stack');
                    that.ui.doc.off('keyup.cms.interrupt');
                    that.ui.content.attr('data-touch-action', 'pan-y');
                },

                update: function(event, ui) {
                    // cancel if isAllowed returns false
                    if (!that.state) {
                        return false;
                    }

                    const newPluginContainer = ui.item.closest('.cms-draggables');

                    if (originalPluginContainer.is(newPluginContainer)) {
                        // if we moved inside same container,
                        // but event is fired on a parent, discard update
                        if (!newPluginContainer.is(this)) {
                            return false;
                        }
                    } else {
                        StructureBoard.actualizePluginsCollapsibleStatus(
                            newPluginContainer.add(originalPluginContainer)
                        );
                    }

                    // we pass the id to the updater which checks within the backend the correct place
                    const id = that.getId(ui.item);
                    const plugin = $(`.cms-draggable-${id}`);
                    const eventData = {
                        id: id
                    };
                    const previousParentPlugin = originalPluginContainer.closest('.cms-draggable');

                    if (previousParentPlugin.length) {
                        eventData.previousParentPluginId = that.getId(previousParentPlugin);
                    }

                    // check if we copy/paste a plugin or not
                    if (originalPluginContainer.hasClass('cms-clipboard-containers')) {
                        originalPluginContainer.html(plugin.eq(0).clone(true, true));
                        Plugin._updateClipboard();
                        plugin.trigger('cms-paste-plugin-update', [eventData]);
                    } else {
                        plugin.trigger('cms-plugins-update', [eventData]);
                    }

                    // reset placeholder without entries
                    that.ui.sortables.each(function() {
                        const element = $(this);

                        if (element.children().length === 0) {
                            element.addClass('cms-hidden');
                        }
                    });

                    StructureBoard.actualizePlaceholders();
                },
                // eslint-disable-next-line complexity
                isAllowed: function(placeholder, placeholderParent, originalItem) {
                    // cancel if action is executed
                    if (CMS.API.locked) {
                        return false;
                    }
                    // getting restriction array
                    let bounds = [];
                    let immediateParentType;

                    if (placeholder && placeholder.closest('.cms-clipboard-containers').length) {
                        return false;
                    }

                    // if parent has class disabled, dissalow drop
                    if (placeholder && placeholder.parent().hasClass('cms-drag-disabled')) {
                        return false;
                    }

                    // if parent has class disabled, dissalow drop
                    if (placeholder && placeholder.parent().hasClass('cms-draggable-disabled')) {
                        return false;
                    }

                    const originalItemId = that.getId(originalItem);
                    // save original state events
                    const original = $('.cms-draggable-' + originalItemId);

                    // cancel if item has no settings
                    if (original.length === 0 || !original.data('cms')) {
                        return false;
                    }
                    const originalItemData = original.data('cms');
                    const parent_bounds = $.grep(originalItemData.plugin_parent_restriction, function(r) {
                        // special case when PlaceholderPlugin has a parent restriction named "0"
                        return r !== '0';
                    });
                    const type = originalItemData.plugin_type;
                    // prepare variables for bound
                    const holderId = that.getId(placeholder.closest('.cms-dragarea'));
                    const holder = $('.cms-placeholder-' + holderId);
                    let plugin;

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
            })
            .on('cms-structure-update', StructureBoard.actualizePlaceholders);
    }

    _dragRefresh() {
        this.ui.sortables.each((i, el) => {
            const element = $(el);

            if (element.data('mjsNestedSortable')) {
                return;
            }

            this._drag(element);
        });
    }

    /**
     * @method invalidateState
     * @param {String} action - action to handle
     * @param {Object} data - data required to handle the object
     * @param {Object} opts
     * @param {Boolean} [opts.propagate=true] - should we propagate the change to other tabs or not
     */
    // eslint-disable-next-line complexity
    invalidateState(action, data, { propagate = true } = {}) {
        // eslint-disable-next-line default-case

        // By default, any edit action will result in changed content and therefore a need for an update
        let updateNeeded = true;

        switch (action) {
            case 'COPY': {
                this.handleCopyPlugin(data);
                updateNeeded = false;  // Copying, however, only changes the clipboard - no update needed
                break;
            }

             // For other actions, only refresh, if the new state cannot be determined from the data bridge
            case 'ADD': {
                updateNeeded = this.handleAddPlugin(data);
                break;
            }

            case 'EDIT': {
                updateNeeded = this.handleEditPlugin(data);
                break;
            }

            case 'DELETE': {
                updateNeeded = this.handleDeletePlugin(data);
                break;
            }

            case 'CLEAR_PLACEHOLDER': {
                updateNeeded = this.handleClearPlaceholder(data);
                break;
            }

            case 'PASTE':
            case 'MOVE': {
                updateNeeded = this.handleMovePlugin(data);
                break;
            }

            case 'CUT': {
                updateNeeded = this.handleCutPlugin(data);
                break;
            }

            case undefined:
            case false:
            case '': {
                CMS.API.Helpers.reloadBrowser();
                return;
            }

            default:
                break;
        }
        Plugin._recalculatePluginPositions(action, data);

        if (propagate) {
            this._propagateInvalidatedState(action, data);
        }

        // refresh content mode if needed
        // refresh toolbar
        const currentMode = CMS.settings.mode;

        if (currentMode === 'structure') {
            this._requestcontent = null;

            if (this._loadedContent && updateNeeded) {
                this.updateContent();
                return;  // Toolbar loaded
            }
        } else if (updateNeeded === true) {
            this._requestcontent = null;
            this.updateContent();
            return;  // Toolbar loaded

        }
        this._loadToolbar()
            .done(newToolbar => {
                CMS.API.Toolbar._refreshMarkup($(newToolbar).find('.cms-toolbar'));
            })
            .fail(() => Helpers.reloadBrowser());
    }

    _propagateInvalidatedState(action, data) {
        this.latestAction = [action, data];

        ls.set(storageKey, JSON.stringify([action, data, window.location.pathname]));
    }

    _listenToExternalUpdates() {
        if (!Helpers._isStorageSupported) {
            return;
        }

        ls.on(storageKey, this._handleExternalUpdate.bind(this));
    }

    _handleExternalUpdate(value) {
        // means localstorage was cleared while this page was open
        if (!value) {
            return;
        }

        const [action, data, pathname] = JSON.parse(value);

        if (pathname !== window.location.pathname) {
            return;
        }

        if (isEqual([action, data], this.latestAction)) {
            return;
        }

        this.invalidateState(action, data, { propagate: false });
    }

    updateContent() {
        const loader = $('<div class="cms-content-reloading"></div>');

        $('.cms-structure').before(loader);
        return this._requestMode('content')
            .done(markup => {
                // eslint-disable-next-line no-magic-numbers
                loader.fadeOut(100, () => loader.remove());
                this.refreshContent(markup);
            })
            .fail(() => loader.remove() && Helpers.reloadBrowser());
    }

    _updateSingleContent(content) {
        if (!content.pluginIds || content.pluginIds.length < 1 || content.html === undefined) {
            // No valid content data available – update needed.
            return true;
        }

        let nextEl = $(`:not(template).cms-plugin.cms-plugin-${content.pluginIds[0]}.cms-plugin-start`);

        if (nextEl.length < 1 || content.insert) {
            // Plugin not found, but placeholder is known – plugin was added.
            nextEl = this._findNextElement(content.position, content.placeholder_id, content.pluginIds);
        }

        if (nextEl.length === 0) {
            // Placeholder not found – update needed.
            return true;
        }

        nextEl.before(content.html);

        // Remove previous plugin and related script elements.
        content.pluginIds.forEach(id => {
            $(`:not(template).cms-plugin.cms-plugin-${id}`).remove();
            $(`script[data-cms-plugin]#cms-plugin-${id}`).remove();
        });

        // Update Sekizai blocks.
        this._updateSekizai(content, 'css');
        this._updateSekizai(content, 'js');

        return false;
    }

    _updateContentFromDataBridge(data) {
        if (!data || !data.content || data.content.length === 0) {
            return true;
        }
        if (data.source_placeholder_id && !CMS._instances.some(
                instance => instance.options.type === 'plugin' &&
                instance.options.placeholder_id == data.source_placeholder_id  // eslint-disable-line eqeqeq
        )) {
            // If last plugin was moved from a placeholder, the placeholder needs to be updated
            return true;  // Update needed
        }

        for (const content of data.content) {
            if (this._updateSingleContent(content)) {
                return true; // Early exit if full content update is needed.
            }
        }
        this._contentChanged(data.messages);

        if (this.scriptReferenceCount === 0) {
            // No scripts need to be loaded - content update is already done
            StructureBoard._triggerRefreshEvents();
        }
        return false;
    }

    _findNextElement(position, placeholder_id, excludedPlugins) {
        let nextEl = $(`div.cms-placeholder.cms-placeholder-${placeholder_id}`);
        const nextPlugins = CMS._instances.filter(instance =>
            instance.options.type === 'plugin' &&
            instance.options.placeholder_id == placeholder_id &&  // eslint-disable-line eqeqeq
            instance.options.position >= position &&
            !excludedPlugins.includes(1 * instance.options.plugin_id));

        if (nextPlugins.length > 0) {
            // Plugins found with higher position, get the one with lowest position
            const nextPluginId = nextPlugins.reduce((acc, instance) => {
                return instance.options.position < acc.options.position ? instance : acc;
            }, nextPlugins[0]).options.plugin_id;

            nextEl = $(`.cms-plugin.cms-plugin-${nextPluginId}.cms-plugin-start`);
        }
        return nextEl;
    }

    _updateSekizai(data, block) {
        if ((data[block] || '').length === 0) {
            return;
        }

        // Find existing candiates, selector and cursor to write to
        let current;
        let selector;
        let location;

        if (block === 'css') {
            selector = 'link, style, meta';
            current = document.head.querySelectorAll(selector);
            location = document.head;
        } else if (block === 'js') {
            selector = 'script';
            current = document.body.querySelectorAll(selector);
            location = document.body;
        } else {
            return;
        }

        // Parse new block, by creating the diff
        // Cannot use innerHTML since this would prevent scripts to be executed.
        const newElements = document.createElement('div');
        const diff = dd.diff(newElements, `<div>${data[block]}</div>`);

        dd.apply(newElements, diff);

        // Collect deferred scripts to ensure firing
        this.scriptReferenceCount = 0;

        for (const element of newElements.querySelectorAll(selector)) {
            if (StructureBoard._elementPresent(current, element)) {
                element.remove();
            } else {
                if (element.hasAttribute('src')) {
                    this.scriptReferenceCount++;
                    element.onload = element.onerror = this._scriptLoaded.bind(this);
                }
                location.appendChild(element);
            }
        }
        return this.scriptReferenceCount > 0;
    }

    _loadToolbar() {
        const placeholderIds = getPlaceholderIds(CMS._plugins).map(id => `placeholders[]=${id}`).join('&');

        return $.ajax({
            url: Helpers.updateUrlWithPath(
                `${CMS.config.request.toolbar}?` +
                    placeholderIds +
                    '&' +
                    `obj_id=${CMS.config.request.pk}&` +
                    `obj_type=${encodeURIComponent(CMS.config.request.model)}` +
                    `&language=${encodeURIComponent(CMS.config.request.language)}`
            )
        });
    }

    // i think this should probably be a separate class at this point that handles all the reloading
    // stuff, it's a bit too much
    // eslint-disable-next-line complexity
    handleMovePlugin(data) {
        if (data.plugin_parent) {
            if (data.plugin_id) {
                const draggable = $(`.cms-draggable-${data.plugin_id}:last`);

                if (
                    !draggable.closest(`.cms-draggable-${data.plugin_parent}`).length &&
                    !draggable.is('.cms-draggable-from-clipboard')
                ) {
                    draggable.remove();
                }
            }

            // empty the children first because replaceWith takes too much time
            // when it's trying to remove all the data and event handlers from potentially big tree of plugins
            $(`.cms-draggable-${data.plugin_parent}`).html('').replaceWith(data.html);
        } else {
            // the one in the clipboard is first, so we need to take the second one,
            // that is already visually moved into correct place
            let draggable = $(`.cms-draggable-${data.plugin_id}:last`);

            // external update, have to move the draggable to correct place first
            if (!draggable.closest('.cms-draggables').parent().is(`.cms-dragarea-${data.placeholder_id}`)) {
                const pluginOrder = data.plugin_order;
                const index = findIndex(
                    pluginOrder,
                    pluginId => Number(pluginId) === Number(data.plugin_id) || pluginId === '__COPY__'
                );
                const placeholderDraggables = $(`.cms-dragarea-${data.placeholder_id} > .cms-draggables`);

                if (draggable.is('.cms-draggable-from-clipboard')) {
                    draggable = draggable.clone();
                }

                if (index === 0) {
                    placeholderDraggables.prepend(draggable);
                } else if (index !== -1) {
                    placeholderDraggables.find(`.cms-draggable-${pluginOrder[index - 1]}`).after(draggable);
                }
            }

            // if we _are_ in the correct placeholder we still need to check if the order is correct
            // since it could be an external update of a plugin moved in the same placeholder. also we are top-level
            if (draggable.closest('.cms-draggables').parent().is(`.cms-dragarea-${data.placeholder_id}`)) {
                const placeholderDraggables = $(`.cms-dragarea-${data.placeholder_id} > .cms-draggables`);
                const actualPluginOrder = this.getIds(
                    placeholderDraggables.find('> .cms-draggable')
                );

                if (!arrayEquals(actualPluginOrder, data.plugin_order)) {
                    // so the plugin order is not correct, means it's an external update and we need to move
                    const pluginOrder = data.plugin_order;
                    const index = findIndex(
                        pluginOrder,
                        pluginId => Number(pluginId) === Number(data.plugin_id)
                    );

                    if (index === 0) {
                        placeholderDraggables.prepend(draggable);
                    } else if (index !== -1) {
                        placeholderDraggables.find(`.cms-draggable-${pluginOrder[index - 1]}`).after(draggable);
                    }
                }
            }

            if (draggable.length) {
                // empty the children first because replaceWith takes too much time
                // when it's trying to remove all the data and event handlers from potentially big tree of plugins
                draggable.html('').replaceWith(data.html);
            } else if (data.target_placeholder_id) {
                // copy from language
                $(`.cms-dragarea-${data.target_placeholder_id} > .cms-draggables`).append(data.html);
            }
        }

        StructureBoard.actualizePlaceholders();
        Plugin._updateRegistry(data.plugins);
        data.plugins.forEach(pluginData => {
            StructureBoard.actualizePluginCollapseStatus(pluginData.plugin_id);
        });

        StructureBoard._initializeDragItemsStates();

        this.ui.sortables = $('.cms-draggables');
        this._dragRefresh();
        return this._updateContentFromDataBridge(data);
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

        const clipboardDraggable = $('.cms-clipboard .cms-draggable:first');
        const html = clipboardDraggable.parent().html();

        CMS.API.Clipboard.populate(html, pluginData[1]);
        CMS.API.Clipboard._enableTriggers();

        this.ui.sortables = $('.cms-draggables');
        this._dragRefresh();
        return true;  // update needed
    }

    handleCutPlugin(data) {
        const updateNeededFromDelete = this.handleDeletePlugin(data);

        this.handleCopyPlugin(data);
        return updateNeededFromDelete;
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

            return compact(
                messages.toArray().map(el => {
                    const msgEl = $(el);
                    const message = $(el).text().trim();

                    if (message) {
                        return {
                            message,
                            error: msgEl.data('cms-message-tags') === 'error' || msgEl.hasClass('error')
                        };
                    }
                })
            );
        }

        return [];
    }

    refreshContent(contentMarkup) {
        this._requestcontent = null;
        if (!this._loadedStructure) {
            this._requeststructure = null;
        }
        const newDoc = new DOMParser().parseFromString(contentMarkup, 'text/html');

        const structureScrollTop = $('.cms-structure-content').scrollTop();

        const toolbar = $('#cms-top, [data-cms]').detach();
        const newToolbar = $(newDoc).find('.cms-toolbar').clone();

        $(newDoc).find('#cms-top, [data-cms]').remove();

        const messages = this._extractMessages($(newDoc));

        if (messages.length) {
            setTimeout(() =>
                messages.forEach(message => {
                    CMS.API.Messages.open(message);
                })
            );
        }
        const headDiff = dd.diff(document.head, nodeToObj(newDoc.head));

        this._replaceBodyWithHTML(newDoc.body);
        dd.apply(document.head, headDiff);

        toolbar.prependTo(document.body);
        CMS.API.Toolbar._refreshMarkup(newToolbar);

        $('.cms-structure-content').scrollTop(structureScrollTop);
        this._loadedContent = true;
        this._contentChanged();
    }

    _contentChanged(messages) {
        Plugin._refreshPlugins();
        if (messages) {
            CMS.API.Messages.close();
            if (messages.length) {
                CMS.API.Messages.open({
                    message: messages.map(message => `<p>${message.message}</p>`).join(''),
                    error: messages.some(message => message.level === 'error')
                });
            }
        }
    }

    handleAddPlugin(data) {
        if (data.plugin_parent) {
            $(`.cms-draggable-${data.plugin_parent}`).replaceWith(data.structure.html);
        } else {
            // the one in the clipboard is first
            $(`.cms-dragarea-${data.placeholder_id} > .cms-draggables`).append(data.structure.html);
        }

        StructureBoard.actualizePlaceholders();
        Plugin._updateRegistry(data.structure.plugins);
        data.structure.plugins.forEach(pluginData => {
            StructureBoard.actualizePluginCollapseStatus(pluginData.plugin_id);
        });

        this.ui.sortables = $('.cms-draggables');
        this._dragRefresh();
        return this._updateContentFromDataBridge(data.structure);
    }

    handleEditPlugin(data) {
        if (data.plugin_parent) {
            $(`.cms-draggable-${data.plugin_parent}`).replaceWith(data.structure.html);
        } else {
            $(`.cms-draggable-${data.plugin_id}`).replaceWith(data.structure.html);
        }

        Plugin._updateRegistry(data.structure.plugins);

        data.structure.plugins.forEach(pluginData => {
            StructureBoard.actualizePluginCollapseStatus(pluginData.plugin_id);
        });

        this.ui.sortables = $('.cms-draggables');
        this._dragRefresh();
        return this._updateContentFromDataBridge(data.structure);
    }

    handleDeletePlugin(data) {
        const { placeholder_id } = CMS._instances.find(
            // data.plugin_id might be string
            plugin => plugin && plugin.options.plugin_id == data.plugin_id  // eslint-disable-line eqeqeq
        ).options;
        const draggable = $('.cms-draggable-' + data.plugin_id);
        const children = draggable.find('.cms-draggable');
        let deletedPluginIds = [data.plugin_id];
        let parent = draggable.parent().closest('.cms-draggable');

        if (!parent.length) {
            parent = draggable.closest('.cms-dragarea');
        }

        if (children.length) {
            deletedPluginIds = deletedPluginIds.concat(this.getIds(children));
        }

        draggable.remove();

        StructureBoard.actualizePluginsCollapsibleStatus(parent.find('> .cms-draggables'));
        StructureBoard.actualizePlaceholders();
        const contentData = (data.structure || data);  // delete has content in data.structure, cut in data

        deletedPluginIds.forEach(function(pluginId) {
            if (!contentData.content) {
                $(`.cms-plugin.cms-plugin-${pluginId}`).remove();  // Remove from content
            }
            $(`script[data-cms-plugin]#cms-plugin-${pluginId}`).remove();  // Remove script elements
            remove(CMS._plugins, settings => settings[0] === `cms-plugin-${pluginId}`);
            remove(
                CMS._instances,
                instance => instance.options.plugin_id && Number(instance.options.plugin_id) === Number(pluginId)
            );
        });

        const lastPluginDeleted = CMS._instances.find(
            plugin => plugin.options.placeholder_id == placeholder_id  // eslint-disable-line eqeqeq
        ) === undefined;

        return lastPluginDeleted || contentData.content && this._updateContentFromDataBridge(contentData);
    }

    handleClearPlaceholder(data) {
        const deletedIds = CMS._instances
            .filter(instance => {
                if (
                    instance.options.plugin_id &&
                    Number(instance.options.placeholder_id) === Number(data.placeholder_id)
                ) {
                    return true;
                }
            })
            .map(instance => instance.options.plugin_id);

        deletedIds.forEach(id => {
            remove(CMS._plugins, settings => settings[0] === `cms-plugin-${id}`);
            remove(
                CMS._instances,
                instance => instance.options.plugin_id && Number(instance.options.plugin_id) === Number(id)
            );

            $(`.cms-draggable-${id}`).remove();
        });

        StructureBoard.actualizePlaceholders();
        return true;
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
     * Checks if placeholders are empty and enables/disables certain actions on them, hides or shows the
     * "empty placeholder" placeholder and adapts the location of "Plugin will be added here" placeholder
     *
     * @function actualizePlaceholders
     * @private
     */
    static actualizePlaceholders() {
        placeholders.each(function() {
            const placeholder = $(this);
            const copyAll = placeholder.find('.cms-dragbar .cms-submenu-item:has(a[data-rel="copy"]):first');

            if (
                placeholder.find('> .cms-draggables').children('.cms-draggable').not('.cms-draggable-is-dragging')
                    .length
            ) {
                placeholder.removeClass('cms-dragarea-empty');
                copyAll.removeClass('cms-submenu-item-disabled');
                copyAll.find('> a').removeAttr('aria-disabled');
            } else {
                placeholder.addClass('cms-dragarea-empty');
                copyAll.addClass('cms-submenu-item-disabled');
                copyAll.find('> a').attr('aria-disabled', 'true');
            }
        });

        const addPluginPlaceholder = $('.cms-dragarea .cms-add-plugin-placeholder');

        if (addPluginPlaceholder.length && !addPluginPlaceholder.is(':last')) {
            addPluginPlaceholder.appendTo(addPluginPlaceholder.parent());
        }
    }

    /**
     * actualizePluginCollapseStatus
     *
     * @public
     * @param {String} pluginId open the plugin if it should be open
     */
    static actualizePluginCollapseStatus(pluginId) {
        const el = $(`.cms-draggable-${pluginId}`);
        const open = find(CMS.settings.states, openPluginId => Number(openPluginId) === Number(pluginId));

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
        els.each(function() {
            const childList = $(this);
            const pluginDragItem = childList.closest('.cms-draggable').find('> .cms-dragitem');

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

    /**
     * Replaces the current document body with the provided HTML content.
     *
     * This method removes all existing script elements from the document body,
     * replaces the body content with the new HTML, and then re-inserts new script
     * elements to ensure they are executed.
     *
     * @param {HTMLElement} body - The new HTML content to replace the current body.
     *
     * @private
     */
    _replaceBodyWithHTML(body) {
        // Remove (i.e. detach) old scripts
        const oldScripts = document.body.querySelectorAll('script:not([type="application/json"])');

        oldScripts.forEach(script => script.remove());

        // Replace the body content
        document.body.innerHTML = body.innerHTML;

        // Process new scripts in a dedicated helper
        const newScripts = document.body.querySelectorAll('script:not([type="application/json"])');

        this._processNewScripts(newScripts, oldScripts);

        if (this.scriptReferenceCount === 0) {
            StructureBoard._triggerRefreshEvents();
        }
    }

    /**
     * Processes new script elements by comparing them with old script elements.
     * If a new script is not present in the old scripts, it rewrites the script to the DOM to force execution.
     *
     * @param {NodeList} newScripts - A list of new script elements to be processed.
     * @param {NodeList} oldScripts - A list of old script elements to compare against.
     * @private
     */
    _processNewScripts(newScripts, oldScripts) {
        newScripts.forEach(script => {
            if (!StructureBoard._elementPresent(oldScripts, script)) {
                // Rewrite script to DOM to force execution
                const newScript = document.createElement('script');

                // Copy attributes
                Array.from(script.attributes).forEach(attr => {
                    newScript.setAttribute(attr.name, attr.value);
                });
                if (script.src) {
                    // Needs to be loaded from a server
                    this.scriptReferenceCount++;
                    newScript.onload = newScript.onerror = this._scriptLoaded.bind(this);
                } else {
                    // Inline script
                    newScript.textContent = script.textContent;
                }
                script.parentNode.insertBefore(newScript, script.nextSibling);
                script.remove();
            }
        });
    }

    /**
     * Checks if a given element is present in the current set of elements.
     *
     * @param {NodeList} current - The current set of elements to check against.
     * @param {Element} element - The element to check for presence.
     * @returns {boolean} - Returns true if the element is present in the current set, otherwise false.
     * @private
     */
    static _elementPresent(current, element) {
        const markup = element.outerHTML;

        return [...current].some(el => el.outerHTML === markup);
    }

    /**
     * Handles the event when a script is loaded.
     * Decrements the script reference count and, if it reaches zero,
     * dispatches a 'load' event on the window and triggers a 'cms-content-refresh' event.
     *
     * @private
     */
    _scriptLoaded() {
        if (--this.scriptReferenceCount < 1) {
            StructureBoard._triggerRefreshEvents();
        }
    }

    /**
     * Triggers refresh events on the window and document.
     *
     * This method dispatches the 'DOMContentLoaded' event on the document,
     * the 'load' event on the window, and triggers the 'cms-content-refresh'
     * event using jQuery on the window. The events are dispatched asynchronously
     * to ensure that the current execution context is completed before the events
     * are triggered.
     *
     * @private
     * @static
     */
    static _triggerRefreshEvents() {
        setTimeout(() => {
            Helpers._getWindow().document.dispatchEvent(new Event('DOMContentLoaded'));
            Helpers._getWindow().dispatchEvent(new Event('load'));
            Helpers._getWindow().dispatchEvent(new Event('cms-content-refresh'));
        }, 0);
    }

    highlightPluginFromUrl() {
        const hash = window.location.hash;
        const regex = /cms-plugin-(\d+)/;

        if (!hash || !hash.match(regex)) {
            return;
        }

        const pluginId = regex.exec(hash)[1];

        if (this._loadedContent) {
            Plugin._highlightPluginContent(pluginId, {
                seeThrough: true,
                prominent: true,
                delay: 3000
            });
        }
    }

    /**
     * Get's plugins data from markup
     *
     * @method _getPluginDataFromMarkup
     * @private
     * @param {Node} body
     * @param {Array<Number | String>} pluginIds
     * @returns {Array<[String, Object]>}
     */
    static _getPluginDataFromMarkup(body, pluginIds) {
        return compact(
            pluginIds.map(pluginId => {
                const pluginData = body.querySelector(`#cms-plugin-${pluginId}`);
                let settings;

                if (pluginData) {
                    try {
                        settings = JSON.parse(pluginData.textContent);
                    } catch (e) {
                        settings = false;
                    }
                } else {
                    settings = false;
                }

                return settings;
            })
        );
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
StructureBoard._initializeDragItemsStates = function _initializeDragItemsStates() {
    // removing duplicate entries
    'use strict';

    const states = CMS.settings.states || [];
    const sortedArr = states.sort();
    const filteredArray = [];

    for (let i = 0; i < sortedArr.length; i++) {
        if (sortedArr[i] !== sortedArr[i + 1]) {
            filteredArray.push(sortedArr[i]);
        }
    }
    CMS.settings.states = filteredArray;

    // loop through the items
    $.each(CMS.settings.states, function(index, id) {
        const el = $('.cms-draggable-' + id);

        // only add this class to elements which have immediate children
        if (el.find('> .cms-collapsable-container > .cms-draggable').length) {
            el.find('> .cms-collapsable-container').removeClass('cms-hidden');
            el.find('> .cms-dragitem').addClass('cms-dragitem-expanded');
        }
    });
};

// shorthand for jQuery(document).ready();
$(StructureBoard._initializeGlobalHandlers);

export default StructureBoard;
