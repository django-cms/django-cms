/*
 * Copyright https://github.com/divio/django-cms
 */

import $ from 'jquery';
import Class from 'classjs';
import Navigation from './cms.navigation';
import Sideframe from './cms.sideframe';
import Modal from './cms.modal';
import Plugin from './cms.plugins';
import { filter, throttle, uniq } from 'lodash';
import { showLoader, hideLoader } from './loader';
import { Helpers, KEYS } from './cms.base';

var SECOND = 1000;
var TOOLBAR_OFFSCREEN_OFFSET = 10; // required to hide box-shadow

export const getPlaceholderIds = pluginRegistry =>
    uniq(filter(pluginRegistry, ([, opts]) => opts.type === 'placeholder').map(([, opts]) => opts.placeholder_id));

/**
 * @function hideDropdownIfRequired
 * @private
 * @param {jQuery} publishBtn
 */
function hideDropdownIfRequired(publishBtn) {
    var dropdown = publishBtn.closest('.cms-dropdown');

    if (dropdown.length && dropdown.find('li[data-cms-hidden]').length === dropdown.find('li').length) {
        dropdown.hide().attr('data-cms-hidden', 'true');
    }
}

/**
 * The toolbar is the generic element which holds various components
 * together and provides several commonly used API methods such as
 * show/hide, message display or loader indication.
 *
 * @class Toolbar
 * @namespace CMS
 * @uses CMS.API.Helpers
 */
var Toolbar = new Class({
    implement: [Helpers],

    options: {
        toolbarDuration: 200
    },

    initialize: function initialize(options) {
        this.options = $.extend(true, {}, this.options, options);

        // elements
        this._setupUI();

        /**
         * @property {CMS.Navigation} navigation
         */
        this.navigation = new Navigation();

        /**
         * @property {Object} _position
         * @property {Number} _position.top current position of the toolbar
         * @property {Number} _position.top position when toolbar became non-sticky
         * @property {Boolean} _position.isSticky is toolbar sticky?
         * @see _handleLongMenus
         * @private
         */
        this._position = {
            top: 0,
            stickyTop: 0,
            isSticky: true
        };

        // states
        this.click = 'click.cms.toolbar';
        this.touchStart = 'touchstart.cms.toolbar';
        this.pointerUp = 'pointerup.cms.toolbar';
        this.pointerOverOut = 'pointerover.cms.toolbar pointerout.cms.toolbar';
        this.pointerLeave = 'pointerleave.cms.toolbar';
        this.mouseEnter = 'mouseenter.cms.toolbar';
        this.mouseLeave = 'mouseleave.cms.toolbar';
        this.resize = 'resize.cms.toolbar';
        this.scroll = 'scroll.cms.toolbar';
        this.key = 'keydown.cms.toolbar keyup.cms.toolbar';

        // istanbul ignore next: function is always reassigned
        this.timer = function() {};
        this.lockToolbar = false;

        // setup initial stuff
        if (!this.ui.toolbar.data('ready')) {
            this._events();
        }

        this._initialStates();

        // set a state to determine if we need to reinitialize this._events();
        this.ui.toolbar.data('ready', true);
    },

    /**
     * Stores all jQuery references within `this.ui`.
     *
     * @method _setupUI
     * @private
     */
    _setupUI: function _setupUI() {
        var container = $('.cms');

        this.ui = {
            container: container,
            body: $('html'),
            document: $(document),
            window: $(window),
            toolbar: container.find('.cms-toolbar'),
            navigations: container.find('.cms-toolbar-item-navigation'),
            buttons: container.find('.cms-toolbar-item-buttons'),
            messages: container.find('.cms-messages'),
            structureBoard: container.find('.cms-structure'),
            toolbarSwitcher: $('.cms-toolbar-item-cms-mode-switcher'),
            revert: $('.cms-toolbar-revert')
        };
    },

    /**
     * Sets up all the event handlers, such as closing and resizing.
     *
     * @method _events
     * @private
     */
    _events: function _events() {
        var that = this;
        var LONG_MENUS_THROTTLE = 10;

        // attach event to the navigation elements
        this.ui.navigations.each(function() {
            var navigation = $(this);
            var lists = navigation.find('li');
            var root = 'cms-toolbar-item-navigation';
            var hover = 'cms-toolbar-item-navigation-hover';
            var disabled = 'cms-toolbar-item-navigation-disabled';
            var children = 'cms-toolbar-item-navigation-children';
            var isTouchingTopLevelMenu = false;
            var open = false;
            var cmdPressed = false;

            /**
             * Resets all the hover state classes and events
             * @function reset
             */
            function reset() {
                open = false;
                cmdPressed = false;
                lists.removeClass(hover);
                lists.find('ul ul').hide();
                navigation.find('> li').off(that.mouseEnter);
                that.ui.document.off(that.click);
                that.ui.toolbar.off(that.click, reset);
                that.ui.structureBoard.off(that.click);
                that.ui.window.off(that.resize + '.menu.reset');
                that._handleLongMenus();
            }

            that.ui.window.on('keyup.cms.toolbar', function(e) {
                if (e.keyCode === CMS.KEYS.ESC) {
                    reset();
                }
            });

            navigation
                .find('> li > a')
                .add(that.ui.toolbar.find('.cms-toolbar-item:not(.cms-toolbar-item-navigation) > a'))
                .off('keyup.cms.toolbar.reset')
                .on('keyup.cms.toolbar.reset', function(e) {
                    if (e.keyCode === CMS.KEYS.TAB) {
                        reset();
                    }
                });

            // remove events from first level
            navigation
                .find('a')
                .on(that.click + ' ' + that.key, function(e) {
                    var el = $(this);

                    // we need to restore the default behaviour once a user
                    // presses ctrl/cmd and clicks on the entry. In this
                    // case a new tab should open. First we determine if
                    // ctrl/cmd is pressed:
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

                    if (el.attr('href') !== '' && el.attr('href') !== '#' && !el.parent().hasClass(disabled)) {
                        if (cmdPressed && e.type === 'click') {
                            // control the behaviour when ctrl/cmd is pressed
                            Helpers._getWindow().open(el.attr('href'), '_blank');
                        } else if (e.type === 'click') {
                            // otherwise delegate as usual
                            that._delegate($(this));
                        } else {
                            // tabbing through
                            return;
                        }

                        reset();
                        return false;
                    }
                })
                .on(that.touchStart, function() {
                    isTouchingTopLevelMenu = true;
                });

            // handle click states
            lists.on(that.click, function(e) {
                e.preventDefault();
                e.stopPropagation();
                var el = $(this);

                // close navigation once it's pressed again
                if (el.parent().hasClass(root) && open) {
                    that.ui.body.trigger(that.click);
                    return false;
                }

                // close if el does not have children
                if (!el.hasClass(children)) {
                    reset();
                }

                var isRootNode = el.parent().hasClass(root);

                if ((isRootNode && el.hasClass(hover)) || (el.hasClass(disabled) && !isRootNode)) {
                    return false;
                }

                el.addClass(hover);
                that._handleLongMenus();

                // activate hover selection
                if (!isTouchingTopLevelMenu) {
                    // we only set the handler for mouseover when not touching because
                    // the mouseover actually is triggered on touch devices :/
                    navigation.find('> li').on(that.mouseEnter, function() {
                        // cancel if item is already active
                        if ($(this).hasClass(hover)) {
                            return false;
                        }
                        open = false;
                        $(this).trigger(that.click);
                    });
                }

                isTouchingTopLevelMenu = false;
                // create the document event
                that.ui.document.on(that.click, reset);
                that.ui.structureBoard.on(that.click, reset);
                that.ui.toolbar.on(that.click, reset);
                that.ui.window.on(that.resize + '.menu.reset', throttle(reset, SECOND));
                // update states
                open = true;
            });

            // attach hover
            lists
                .on(that.pointerOverOut + ' keyup.cms.toolbar', 'li', function(e) {
                    var el = $(this);
                    var parent = el
                        .closest('.cms-toolbar-item-navigation-children')
                        .add(el.parents('.cms-toolbar-item-navigation-children'));
                    var hasChildren = el.hasClass(children) || parent.length;

                    // do not attach hover effect if disabled
                    // cancel event if element has already hover class
                    if (el.hasClass(disabled)) {
                        e.stopPropagation();
                        return;
                    }
                    if (el.hasClass(hover) && e.type !== 'keyup') {
                        return true;
                    }

                    // reset
                    lists.find('li').removeClass(hover);

                    // add hover effect
                    el.addClass(hover);

                    // handle children elements
                    if (
                        (hasChildren && e.type !== 'keyup') ||
                        (hasChildren && e.type === 'keyup' && e.keyCode === CMS.KEYS.ENTER)
                    ) {
                        el.find('> ul').show();
                        // add parent class
                        parent.addClass(hover);
                        that._handleLongMenus();
                    } else if (e.type !== 'keyup') {
                        lists.find('ul ul').hide();
                        that._handleLongMenus();
                    }

                    // Remove stale submenus
                    el.siblings().find('> ul').hide();
                })
                .on(that.click, function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                });

            // fix leave event
            lists.on(that.pointerLeave, '> ul', function() {
                lists.find('li').removeClass(hover);
            });
        });

        // attach event for first page publish
        this.ui.buttons.each(function() {
            var btn = $(this);
            var links = btn.find('a');

            links.each(function(i, el) {
                var link = $(el);

                // in case the button has a data-rel attribute
                if (link.attr('data-rel') || link.hasClass('cms-form-post-method')) {
                    link.off(that.click).on(that.click, function(e) {
                        e.preventDefault();
                        that._delegate($(this));
                    });
                } else {
                    link.off(that.click).on(that.click, function(e) {
                        e.stopPropagation();
                    });
                }
            });
        });

        this.ui.window
            .off([this.resize, this.scroll].join(' '))
            .on(
                [this.resize, this.scroll].join(' '),
                throttle($.proxy(this._handleLongMenus, this), LONG_MENUS_THROTTLE)
            );
    },

    /**
     * We check for various states on load if elements in the toolbar
     * should appear or trigger other components. This precedes a timeout
     * which is not optimal and should be addressed separately.
     *
     * @method _initialStates
     * @private
     * @deprecated this method is deprecated now, it will be removed in > 3.2
     */
    // eslint-disable-next-line complexity
    _initialStates: function _initialStates() {
        var publishBtn = $('.cms-btn-publish').parent();

        this._show({ duration: 0 });

        // hide publish button
        publishBtn.hide().attr('data-cms-hidden', 'true');

        if ($('.cms-btn-publish-active').length) {
            publishBtn.show().removeAttr('data-cms-hidden');
            this.ui.window.trigger('resize');
        }

        hideDropdownIfRequired(publishBtn);

        // check if debug is true
        if (CMS.config.debug) {
            this._debug();
        }

        // check if there are messages and display them
        if (CMS.config.messages) {
            CMS.API.Messages.open({
                message: CMS.config.messages
            });
        }

        // check if there are error messages and display them
        if (CMS.config.error) {
            CMS.API.Messages.open({
                message: CMS.config.error,
                error: true
            });
        }

        // should switcher indicate that there is an unpublished page?
        if (CMS.config.publisher) {
            CMS.API.Messages.open({
                message: CMS.config.publisher,
                dir: 'right'
            });
        }

        // open sideframe if it was previously opened and it's enabled
        var sideFrameEnabled = typeof CMS.settings.sideframe_enabled === 'undefined' || CMS.settings.sideframe_enabled;

        if (CMS.settings.sideframe
            && CMS.settings.sideframe.url
            && CMS.config.auth
            && sideFrameEnabled
        ) {
            var sideframe = CMS.API.Sideframe || new Sideframe();

            sideframe.open({
                url: CMS.settings.sideframe.url,
                animate: false
            });
        }

        // set color scheme
        Helpers.setColorScheme (
            localStorage.getItem('theme') || CMS.config.color_scheme || 'auto'
        );

        // add toolbar ready class to body and fire event
        this.ui.body.addClass('cms-ready');
        this.ui.document.trigger('cms-ready');
    },

    /**
     * Animation helper for opening the toolbar.
     *
     * @method _show
     * @private
     * @param {Object} [opts]
     * @param {Number} [opts.duration] time in milliseconds for toolbar to animate
     */
    _show: function _show(opts) {
        var that = this;
        var speed = opts && opts.duration !== undefined ? opts.duration : this.options.toolbarDuration;
        var toolbarHeight = $('.cms-toolbar').height() + TOOLBAR_OFFSCREEN_OFFSET;

        this.ui.body.addClass('cms-toolbar-expanding');
        // animate html
        this.ui.body.animate(
            {
                'margin-top': toolbarHeight - TOOLBAR_OFFSCREEN_OFFSET
            },
            speed,
            'linear',
            function() {
                that.ui.body.removeClass('cms-toolbar-expanding');
                that.ui.body.addClass('cms-toolbar-expanded');
            }
        );
        // set messages top to toolbar height
        this.ui.messages.css('top', toolbarHeight - TOOLBAR_OFFSCREEN_OFFSET);
    },

    /**
     * Makes a request to the given url, runs optional callbacks.
     *
     * @method openAjax
     * @param {Object} opts
     * @param {String} opts.url url where the ajax points to
     * @param {String} [opts.post] post data to be passed (must be stringified JSON)
     * @param {String} [opts.method='POST'] ajax method
     * @param {String} [opts.text] message to be displayed
     * @param {Function} [opts.callback] custom callback instead of reload
     * @param {String} [opts.onSuccess] reload and display custom message
     * @returns {Boolean|jQuery.Deferred} either false or a promise
     */
    openAjax: function(opts) {
        var that = this;
        // url, post, text, callback, onSuccess
        var url = opts.url;
        var post = opts.post || '{}';
        var text = opts.text || '';
        var callback = opts.callback;
        var method = opts.method || 'POST';
        var onSuccess = opts.onSuccess;
        var question = text ? Helpers.secureConfirm(text) : true;

        // cancel if question has been denied
        if (!question) {
            return false;
        }

        showLoader();

        return $.ajax({
            type: method,
            url: url,
            data: JSON.parse(post)
        })
            .done(function(response) {
                CMS.API.locked = false;

                if (callback) {
                    callback(that, response);
                    hideLoader();
                } else if (onSuccess) {
                    if (onSuccess === 'FOLLOW_REDIRECT') {
                        Helpers.reloadBrowser(response.url);
                    } else {
                        Helpers.reloadBrowser(onSuccess);
                    }
                } else {
                    // reload
                    Helpers.reloadBrowser();
                }
            })
            .fail(function(jqXHR) {
                CMS.API.locked = false;

                CMS.API.Messages.open({
                    message: jqXHR.responseText + ' | ' + jqXHR.status + ' ' + jqXHR.statusText,
                    error: true
                });
            });
    },

    /**
     * Public api for `./loader.js`
     */
    showLoader: function () {
        showLoader();
    },

    hideLoader: function () {
        hideLoader();
    },

    /**
     * Delegates event from element to appropriate functionalities.
     *
     * @method _delegate
     * @param {jQuery} el trigger element
     * @private
     * @returns {Boolean|void}
     */
    _delegate: function _delegate(el) {
        // save local vars
        var target = el.data('rel');

        if (el.hasClass('cms-btn-disabled')) {
            return false;
        }

        switch (target) {
            case 'modal':
                Plugin._removeAddPluginPlaceholder();

                var modal = new Modal({
                    onClose: el.data('on-close')
                });

                modal.open({
                    url: Helpers.updateUrlWithPath(el.attr('href')),
                    title: el.data('name')
                });
                break;
            case 'message':
                CMS.API.Messages.open({
                    message: el.data('text')
                });
                break;
            case 'ajax':
                this.openAjax({
                    url: el.attr('href'),
                    post: JSON.stringify(el.data('post')),
                    method: el.data('method'),
                    text: el.data('text'),
                    onSuccess: el.data('on-success')
                });
                break;
            case 'color-toggle':
                Helpers.toggleColorScheme();
                break;
            case 'sideframe':
                // If the sideframe is enabled, show it
                if (typeof CMS.settings.sideframe_enabled === 'undefined' || CMS.settings.sideframe_enabled) {
                    this._openSideFrame(el);
                    break;
                }
                // Else fall through to default, the sideframe is disabled

            default:
                if (el.hasClass('cms-form-post-method')) {
                    this._sendPostRequest(el);
                } else {
                    Helpers._getWindow().location.href = el.attr('href');
                }
        }
    },

    _openSideFrame: function _openSideFrame(el) {
        var sideframe = CMS.API.Sideframe || new Sideframe({
            onClose: el.data('on-close')
        });

        sideframe.open({
            url: el.attr('href'),
            animate: true
        });
    },

    _sendPostRequest: function _sendPostRequest(el) {
        /* Allow post method to be used */
        var formToken = document.querySelector('form input[name="csrfmiddlewaretoken"]');
        var csrfToken = '<input type="hidden" name="csrfmiddlewaretoken" value="' +
            ((formToken ? formToken.value : formToken) || window.CMS.config.csrf) + '">';
        var fakeForm = $(
            '<form style="display: none" action="' + el.attr('href') + '" method="POST">' + csrfToken +
            '</form>'
        );

        fakeForm.appendTo(Helpers._getWindow().document.body).submit();
    },

    /**
     * Handles the debug bar when `DEBUG=true` on top of the toolbar.
     *
     * @method _debug
     * @private
     */
    _debug: function _debug() {
        if (!CMS.config.lang.debug) {
            return;
        }

        var timeout = 1000;
        // istanbul ignore next: function always reassigned
        var timer = function() {};

        // bind message event
        var debug = this.ui.container.find('.cms-debug-bar');

        debug.on(this.mouseEnter + ' ' + this.mouseLeave, function(e) {
            clearTimeout(timer);

            if (e.type === 'mouseenter') {
                timer = setTimeout(function() {
                    CMS.API.Messages.open({
                        message: CMS.config.lang.debug
                    });
                }, timeout);
            }
        });
    },

    /**
     * Handles the case when opened menu doesn't fit the screen.
     *
     * @method _handleLongMenus
     * @private
     */
    _handleLongMenus: function _handleLongMenus() {
        var openMenus = $('.cms-toolbar-item-navigation-hover > ul');

        if (!openMenus.length) {
            this._stickToolbar();
            return;
        }

        var positions = openMenus.toArray().map(function(item) {
            var el = $(item);

            return $.extend({}, el.position(), { height: el.height() });
        });
        var windowHeight = this.ui.window.height();

        this._position.top = this.ui.window.scrollTop();

        var shouldUnstickToolbar = positions.some(function(item) {
            return item.top + item.height > windowHeight;
        });

        if (shouldUnstickToolbar && this._position.top >= this._position.stickyTop) {
            if (this._position.isSticky) {
                this._unstickToolbar();
            }
        } else {
            this._stickToolbar();
        }
    },

    /**
     * Resets toolbar to the normal position.
     *
     * @method _stickToolbar
     * @private
     */
    _stickToolbar: function _stickToolbar() {
        this._position.stickyTop = 0;
        this._position.isSticky = true;
        this.ui.body.removeClass('cms-toolbar-non-sticky');
        this.ui.toolbar.css({
            top: 0
        });
    },

    /**
     * Positions toolbar absolutely so the long menus can be scrolled
     * (toolbar goes away from the screen if required)
     *
     * @method _unstickToolbar
     * @private
     */
    _unstickToolbar: function _unstickToolbar() {
        this._position.stickyTop = this._position.top;
        this.ui.body.addClass('cms-toolbar-non-sticky');
        // have to do the !important because of "debug" toolbar
        this.ui.toolbar[0].style.setProperty('top', this._position.stickyTop + 'px', 'important');
        this._position.isSticky = false;
    },

    /**
     * Show publish button and handle the case when it's in the dropdown.
     * Also enable revert to live
     *
     * @method onPublishAvailable
     * @public
     * @deprecated since 3.5 due to us reloading the toolbar instead
     */
    onPublishAvailable: function showPublishButton() {
        // show publish / save buttons
        // istanbul ignore next
        // eslint-disable-next-line no-console
        console.warn('This method is deprecated and will be removed in future versions');
    },

    _refreshMarkup: function(newToolbar) {
        const switcher = this.ui.toolbarSwitcher.detach();

        $(this.ui.toolbar).html(newToolbar.children());

        $('.cms-toolbar-item-cms-mode-switcher').replaceWith(switcher);

        this._setupUI();

        // have to clone the nav to eliminate double events
        // there must be a better way to do this
        var clone = this.ui.navigations.clone();

        this.ui.navigations.replaceWith(clone);
        this.ui.navigations = clone;

        this._events();
        this.navigation = new Navigation();
        this.navigation.ui.window.trigger('resize');

        CMS.API.Clipboard.ui.triggers = $('.cms-clipboard-trigger a');
        CMS.API.Clipboard.ui.triggerRemove = $('.cms-clipboard-empty a');
        CMS.API.Clipboard._toolbarEvents();
    }
});

export default Toolbar;
