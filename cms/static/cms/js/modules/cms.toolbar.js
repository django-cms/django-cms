/*
 * Copyright https://github.com/divio/django-cms
 */

var $ = require('jquery');
var Class = require('classjs');
var Helpers = require('./cms.base').API.Helpers;
var KEYS = require('./cms.base').KEYS;
var Navigation = require('./cms.navigation');
var Sideframe = require('./cms.sideframe');
var Modal = require('./cms.modal');

var SECOND = 1000;
var TOOLBAR_OFFSCREEN_OFFSET = 10; // required to hide box-shadow
var DEBUG_BAR_HEIGHT = 5; // TODO has to be fixed

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
        this.pointerLeave = 'pointerleave.csm.toolbar';
        this.mouseEnter = 'mouseenter.cms.toolbar';
        this.mouseLeave = 'mouseleave.cms.toolbar';
        this.resize = 'resize.cms.toolbar';
        this.scroll = 'scroll.cms.toolbar';
        this.key = 'keydown.cms.toolbar keyup.cms.toolbar';

        // istanbul ignore next: function is always reassigned
        this.timer = function () {};
        this.lockToolbar = false;

        // setup initial stuff
        if (!this.ui.toolbar.data('ready')) {
            this._events();
        }

        // FIXME the general initialization is handled within the toolbar
        // rather than a separate cms.setup or similar. Yet other components
        // are loaded after the toolbar so it can create a clash where
        // CMS.API is not ready. This is a workaround until a proper fix
        // will be released in 3.x
        var that = this;

        setTimeout(function () {
            that._initialStates();
        }, 0);

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
            toolbarTrigger: container.find('.cms-toolbar-trigger'),
            navigations: container.find('.cms-toolbar-item-navigation'),
            buttons: container.find('.cms-toolbar-item-buttons'),
            messages: container.find('.cms-messages'),
            structureBoard: container.find('.cms-structure')
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

        // attach event to the trigger handler
        this.ui.toolbarTrigger.on(this.pointerUp + ' keyup.cms.toolbar', function (e) {
            if (e.type === 'keyup' && e.keyCode !== CMS.KEYS.ENTER) {
                return;
            }
            e.preventDefault();
            that.toggle();
            that.ui.document.trigger(that.click);
        }).on(this.click, function (e) {
            e.preventDefault();
        });

        // attach event to the navigation elements
        this.ui.navigations.each(function () {
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

            $(window).on('keyup.cms.toolbar', function (e) {
                if (e.keyCode === CMS.KEYS.ESC) {
                    reset();
                }
            });

            navigation.find('> li > a').add(
                that.ui.toolbar.find('.cms-toolbar-item:not(.cms-toolbar-item-navigation) > a')
            ).off('keyup.cms.toolbar.reset').on('keyup.cms.toolbar.reset', function (e) {
                if (e.keyCode === CMS.KEYS.TAB) {
                    reset();
                }
            });

            // remove events from first level
            navigation.find('a').on(that.click + ' ' + that.key, function (e) {
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

                if (el.attr('href') !== '' &&
                    el.attr('href') !== '#' &&
                    !el.parent().hasClass(disabled)) {

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

            }).on(that.touchStart, function () {
                isTouchingTopLevelMenu = true;
            });

            // handle click states
            lists.on(that.click, function (e) {
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

                if (isRootNode && el.hasClass(hover) || el.hasClass(disabled) && !isRootNode) {
                    return false;
                }

                el.addClass(hover);
                that._handleLongMenus();

                // activate hover selection
                if (!isTouchingTopLevelMenu) {
                    // we only set the handler for mouseover when not touching because
                    // the mouseover actually is triggered on touch devices :/
                    navigation.find('> li').on(that.mouseEnter, function () {
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
                that.ui.window.on(that.resize + '.menu.reset', Helpers.throttle(reset, SECOND));
                // update states
                open = true;
            });

            // attach hover
            lists.on(that.pointerOverOut + ' keyup.cms.toolbar', 'li', function (e) {
                // debugger
                var el = $(this);
                var parent = el.closest('.cms-toolbar-item-navigation-children')
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
                if (hasChildren && e.type !== 'keyup' ||
                    hasChildren && e.type === 'keyup' && e.keyCode === CMS.KEYS.ENTER) {
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
            }).on(that.click, function (e) {
                e.preventDefault();
                e.stopPropagation();
            });

            // fix leave event
            lists.on(that.pointerLeave, '> ul', function () {
                lists.find('li').removeClass(hover);
            });
        });

        // attach event for first page publish
        this.ui.buttons.each(function () {
            var btn = $(this);

            // in case the button has a data-rel attribute
            if (btn.find('a').attr('data-rel')) {
                btn.find('a').on(that.click, function (e) {
                    e.preventDefault();
                    that._delegate($(this));
                });
            } else {
                btn.find('a').on(that.click, function (e) {
                    e.stopPropagation();
                });
            }

            // in case of the publish button
            btn.find('.cms-publish-page').on(that.click, function (e) {
                if (!Helpers.secureConfirm(CMS.config.lang.publish)) {
                    e.preventDefault();
                }
            });

            btn.find('.cms-btn-publish').on(that.click, function (e) {
                e.preventDefault();
                that.showLoader();
                // send post request to prevent xss attacks
                $.ajax({
                    type: 'post',
                    url: $(this).prop('href'),
                    data: {
                        csrfmiddlewaretoken: CMS.config.csrf
                    },
                    success: function () {
                        var url = Helpers.makeURL(
                            Helpers._getWindow().location.href.split('?')[0],
                            [CMS.settings.edit_off + '=true']
                        );

                        Helpers.reloadBrowser(url);
                        that.hideLoader();
                    },
                    error: function (jqXHR) {
                        that.hideLoader();
                        CMS.API.Messages.open({
                            message: jqXHR.responseText + ' | ' + jqXHR.status + ' ' + jqXHR.statusText,
                            error: true
                        });
                    }
                });
            });

        });
        this.ui.window.on(
            [this.resize, this.scroll].join(' '),
            Helpers.throttle($.proxy(this._handleLongMenus, this), LONG_MENUS_THROTTLE)
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

        // setup toolbar visibility, we need to reverse the options to set the correct state
        if (CMS.settings.toolbar === 'expanded') {
            this.open({ duration: 0 });
        } else {
            this.close();
        }

        // hide publish button
        publishBtn.hide();

        if ($('.cms-btn-publish-active').length) {
            publishBtn.show();
            this.ui.window.trigger('resize');
        }

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

        // enforce open state if user is not logged in but requests the toolbar
        if (!CMS.config.auth || CMS.config.settings.version !== CMS.settings.version) {
            this.open({ duration: 0 });
            CMS.settings = this.setSettings(CMS.config.settings);
        }

        // should switcher indicate that there is an unpublished page?
        if (CMS.config.publisher) {
            CMS.API.Messages.open({
                message: CMS.config.publisher,
                dir: 'right'
            });
        }

        // open sideframe if it was previously opened
        if (CMS.settings.sideframe && CMS.settings.sideframe.url) {
            var sideframe = new Sideframe();

            sideframe.open({
                url: CMS.settings.sideframe.url,
                animate: false
            });
        }

        // add toolbar ready class to body and fire event
        this.ui.body.addClass('cms-ready');
        this.ui.document.trigger('cms-ready');
    },

    /**
     * Toggles the toolbar state: open > closes / closed > opens.
     *
     * @method toggle
     */
    toggle: function toggle() {
        // toggle bar
        if (CMS.settings.toolbar === 'collapsed') {
            this.open();
        } else {
            this.close();
        }
    },

    /**
     * Opens the toolbar (slide down).
     *
     * @method open
     * @param {Object} [opts]
     * @param {Number} [opts.duration] time in milliseconds for toolbar to animate
     */
    open: function open(opts) {
        this._show(opts);

        // set new settings
        CMS.settings.toolbar = 'expanded';
        CMS.settings = this.setSettings(CMS.settings);
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
        var debugHeight = $('.cms-debug-bar').height() || 0;
        var toolbarHeight = $('.cms-toolbar').height() + TOOLBAR_OFFSCREEN_OFFSET;

        this.ui.toolbar.css({
            'transition': 'margin-top ' + speed + 'ms',
            'margin-top': 0
        });
        this.ui.toolbarTrigger.addClass('cms-toolbar-trigger-expanded');
        this.ui.body.addClass('cms-toolbar-expanding');
        // animate html
        this.ui.body.animate({
            'margin-top': toolbarHeight - TOOLBAR_OFFSCREEN_OFFSET + debugHeight
        }, speed, 'linear', function () {
            that.ui.body.removeClass('cms-toolbar-expanding');
            that.ui.body.addClass('cms-toolbar-expanded');
        });
        // set messages top to toolbar height
        this.ui.messages.css('top', toolbarHeight - TOOLBAR_OFFSCREEN_OFFSET);
    },

    /**
     * Closes the toolbar (slide up).
     *
     * @method close
     */
    close: function close() {
        this._hide();

        // set new settings
        CMS.settings.toolbar = 'collapsed';
        CMS.settings = this.setSettings(CMS.settings);
    },

    /**
     * Animation helper for closing the toolbar.
     *
     * @method _hide
     * @private
     * @returns {Boolean|void}
     */
    _hide: function _hide() {
        var speed = this.options.toolbarDuration;
        var toolbarHeight = $('.cms-toolbar').height() + TOOLBAR_OFFSCREEN_OFFSET;
        var that = this;

        this.ui.toolbar.css('transition', 'margin-top ' + speed + 'ms');
        // cancel if sideframe is active
        if (this.lockToolbar) {
            return false;
        }

        this.ui.toolbar.css('margin-top', -toolbarHeight);
        this.ui.toolbarTrigger.removeClass('cms-toolbar-trigger-expanded');
        this.ui.body.addClass('cms-toolbar-collapsing');
        // animate html
        this.ui.body.animate({
            'margin-top': CMS.config.debug ? DEBUG_BAR_HEIGHT : 0
        }, speed, 'linear', function () {
            that.ui.body.removeClass('cms-toolbar-expanded cms-toolbar-collapsing');
        });
        // set messages top to 0
        this.ui.messages.css('top', 0);
    },

    /**
     * Makes a request to the given url, runs optional callbacks.
     *
     * @method openAjax
     * @param {Object} opts
     * @param {String} opts.url url where the ajax points to
     * @param {String} [opts.post] post data to be passed (must be stringified JSON)
     * @param {String} [opts.text] message to be displayed
     * @param {Function} [opts.callback] custom callback instead of reload
     * @param {String} [opts.onSuccess] reload and display custom message
     * @returns {Boolean|jQuery.Deferred} either false or a promise
     */
    openAjax: function (opts) {
        var that = this;
        // url, post, text, callback, onSuccess
        var url = opts.url;
        var post = opts.post || '{}';
        var text = opts.text || '';
        var callback = opts.callback;
        var onSuccess = opts.onSuccess;
        var question = text ? Helpers.secureConfirm(text) : true;

        // cancel if question has been denied
        if (!question) {
            return false;
        }

        // set loader
        this.showLoader();

        return $.ajax({
            type: 'POST',
            url: url,
            data: JSON.parse(post)
        }).done(function (response) {
            CMS.API.locked = false;

            if (callback) {
                callback(that, response);
                that.hideLoader();
            } else if (onSuccess) {
                Helpers.reloadBrowser(onSuccess, false, true);
            } else {
                // reload
                Helpers.reloadBrowser(false, false, true);
            }
        }).fail(function (jqXHR) {
            CMS.API.locked = false;

            CMS.API.Messages.open({
                message: jqXHR.responseText + ' | ' + jqXHR.status + ' ' + jqXHR.statusText,
                error: true
            });
        });
    },

    /**
     * Shows the loader spinner on the trigger knob for the toolbar.
     *
     * @method showLoader
     */
    showLoader: function showLoader() {
        this.ui.toolbarTrigger.addClass('cms-toolbar-loader');
    },

    /**
     * Hides the loader spinner on the trigger knob for the toolbar.
     *
     * @method hideLoader
     */
    hideLoader: function hideLoader() {
        this.ui.toolbarTrigger.removeClass('cms-toolbar-loader');
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
            case 'sideframe':
                var sideframe = new Sideframe({
                    onClose: el.data('on-close')
                });

                sideframe.open({
                    url: el.attr('href'),
                    animate: true
                });
                break;
            case 'ajax':
                this.openAjax({
                    url: el.attr('href'),
                    post: JSON.stringify(el.data('post')),
                    text: el.data('text'),
                    onSuccess: el.data('on-success')
                });
                break;
            default:
                Helpers._getWindow().location.href = el.attr('href');
        }
    },

    /**
     * Locks the toolbar so it cannot be closed.
     *
     * @method _lock
     * @param {Boolean} lock true if the toolbar should be locked
     * @private
     */
    _lock: function _lock(lock) {
        if (lock) {
            this.lockToolbar = true;
            // make button look disabled
            // eslint-disable-next-line
            this.ui.toolbarTrigger.css('opacity', 0.2);
        } else {
            this.lockToolbar = false;
            // make button look disabled
            this.ui.toolbarTrigger.css('opacity', 1);
        }
    },

    /**
     * Handles the debug bar when `DEBUG=true` on top of the toolbar.
     *
     * @method _debug
     * @private
     */
    _debug: function _debug() {
        var timeout = 1000;
        // istanbul ignore next: function always reassigned
        var timer = function () {};

        // bind message event
        var debug = this.ui.container.find('.cms-debug-bar');

        debug.on(this.mouseEnter + ' ' + this.mouseLeave, function (e) {
            clearTimeout(timer);

            if (e.type === 'mouseenter') {
                timer = setTimeout(function () {
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

        var positions = openMenus.toArray().map(function (item) {
            var el = $(item);

            return $.extend({}, el.position(), { height: el.height() });
        });
        var windowHeight = this.ui.window.height();

        this._position.top = this.ui.window.scrollTop();

        var shouldUnstickToolbar = positions.some(function (item) {
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
        this.ui.toolbar[0].style.setProperty(
            'top',
            (this._position.stickyTop + (CMS.config.debug ? DEBUG_BAR_HEIGHT : -DEBUG_BAR_HEIGHT)) + 'px',
            'important'
        );
        this._position.isSticky = false;
    }
});

module.exports = Toolbar;
