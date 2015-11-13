/*
 * Copyright https://github.com/divio/django-cms
 */

// #############################################################################
// NAMESPACES
/**
 * @module CMS
 */
var CMS = window.CMS || {};

// #############################################################################
// Toolbar
(function ($) {
    'use strict';

    // shorthand for jQuery(document).ready();
    $(function () {
        /**
         * The toolbar is the generic element which holds various components
         * together and provides several commonly used API methods such as
         * show/hide, message display or loader indication.
         *
         * @class Toolbar
         * @namespace CMS
         * @uses CMS.API.Helpers
         */
        CMS.Toolbar = new CMS.Class({

            implement: [CMS.API.Helpers],

            options: {
                preventSwitch: false,
                preventSwitchMessage: 'Switching is disabled.',
                toolbarDuration: 200
            },

            initialize: function initialize(options) {
                this.options = $.extend(true, {}, this.options, options);

                // elements
                this._setupUI();

                /**
                 * @property {CMS.Navigation} navigation
                 */
                this.navigation = new CMS.Navigation();

                // states
                this.click = 'click.cms.toolbar';
                this.touchStart = 'touchstart.cms.toolbar';
                this.pointerUp = 'pointerup.cms.toolbar';
                this.pointerOverOut = 'pointerover.cms.toolbar pointerout.csm.toolbar';
                this.pointerLeave = 'pointerleave.csm.toolbar';
                this.mouseEnter = 'mouseenter.cms.toolbar';
                this.mouseLeave = 'mouseleave.cms.toolbar';
                this.resize = 'resize.cms.toolbar';
                this.key = 'keydown.cms.toolbar keyup.cms.toolbar';

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
                }, 200);

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
                    switcher: container.find('.cms-toolbar-item-switch'),
                    messages: container.find('.cms-messages'),
                    screenBlock: container.find('.cms-screenblock'),
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

                // attach event to the trigger handler
                this.ui.toolbarTrigger.on(this.pointerUp, function (e) {
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

                    // remove events from first level
                    navigation.find('a').on(that.click + ', ' + that.key, function (e) {
                        var el = $(this);
                        // we need to restore the default behaviour once a user
                        // presses ctrl/cmd and clicks on the entry. In this
                        // case a new tab should open. First we determine if
                        // ctrl/cmd is pressed:
                        if (
                            e.keyCode === CMS.KEYS.CMD_LEFT ||
                            e.keyCode === CMS.KEYS.CMD_RIGHT ||
                            e.keyCode === CMS.KEYS.CMD_FIREFOX ||
                            e.keyCode === CMS.KEYS.SHIFT ||
                            e.keyCode === CMS.KEYS.CTRL
                        ) {
                            cmdPressed = true;
                        }
                        if (e.type === 'keyup') {
                            cmdPressed = false;
                        }

                        if (el.attr('href') !== '' &&
                            el.attr('href') !== '#' &&
                            !el.parent().hasClass(disabled)) {

                            if (cmdPressed) {
                                // control the behaviour when ctrl/cmd is pressed
                                window.open(el.attr('href'), '_blank');
                            } else {
                                // otherwise delegate as usual
                                that._delegate($(this));
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

                        if (el.parent().hasClass(root) && el.hasClass(hover) || el.hasClass(disabled)) {
                            return false;
                        } else {
                            el.addClass(hover);
                        }

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
                        that.ui.window.on('resize', CMS.API.Helpers.throttle(reset, 1000));
                        // update states
                        open = true;
                    });

                    // attach hover
                    lists.on(that.pointerOverOut, 'li', function () {
                        var el = $(this);
                        var parent = el.closest('.cms-toolbar-item-navigation-children')
                            .add(el.parents('.cms-toolbar-item-navigation-children'));
                        var hasChildren = el.hasClass(children) || parent.length;

                        // do not attach hover effect if disabled
                        // cancel event if element has already hover class
                        if (el.hasClass(disabled)) {
                            return false;
                        }
                        if (el.hasClass(hover)) {
                            return true;
                        }

                        // reset
                        lists.find('li').removeClass(hover);

                        // add hover effect
                        el.addClass(hover);

                        // handle children elements
                        if (hasChildren) {
                            el.find('> ul').show();
                            // add parent class
                            parent.addClass(hover);
                        } else {
                            lists.find('ul ul').hide();
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

                    // removes classes and events
                    function reset() {
                        open = false;
                        cmdPressed = false;
                        lists.removeClass(hover);
                        lists.find('ul ul').hide();
                        navigation.find('> li').off(that.mouseEnter);
                        that.ui.document.off(that.click);
                        that.ui.toolbar.off(that.click, reset);
                        that.ui.structureBoard.off(that.click);
                    }
                });

                // attach event to the switcher elements
                this.ui.switcher.each(function () {
                    $(this).on(that.click, function (e) {
                        e.preventDefault();
                        that._setSwitcher($(e.currentTarget));
                    });
                });

                // attach event for first page publish
                this.ui.buttons.each(function () {
                    var btn = $(this);

                    // in case the button has a data-rel attribute
                    if (btn.find('a').attr('data-rel')) {
                        btn.on(that.click, function (e) {
                            e.preventDefault();
                            that._delegate($(this).find('a'));
                        });
                    } else {
                        btn.find('a').on(that.click, function (e) {
                            e.stopPropagation();
                        });
                    }

                    // in case of the publish button
                    btn.find('.cms-publish-page').on(that.click, function (e) {
                        if (!CMS.API.Helpers.secureConfirm(CMS.config.lang.publish)) {
                            e.preventDefault();
                        }
                    });

                    btn.find('.cms-btn-publish').on(that.click, function (e) {
                        e.preventDefault();
                        // send post request to prevent xss attacks
                        $.ajax({
                            'type': 'post',
                            'url': $(this).prop('href'),
                            'data': {
                                'csrfmiddlewaretoken': CMS.config.csrf
                            },
                            'success': function () {
                                var url = CMS.API.Helpers.makeURL(
                                    window.location.href.split('?')[0],
                                    [CMS.settings.edit_off + '=true']
                                );
                                CMS.API.Helpers.reloadBrowser(url);
                            },
                            'error': function (request) {
                                throw new Error(request);
                            }
                        });
                    });
                });
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
                    setInterval(function () {
                        CMS.$('.cms-toolbar-item-switch').toggleClass('cms-toolbar-item-switch-highlight');
                    }, CMS.API.Messages.messageDelay);
                }

                // open sideframe if it was previously opened
                if (CMS.settings.sideframe.url) {
                    var sideframe = new CMS.Sideframe();
                    sideframe.open({
                        url: CMS.settings.sideframe.url,
                        animate: false
                    });
                }

                // if there is a screenblock, do some resize magic
                if (this.ui.screenBlock.length) {
                    this._screenBlock();
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
                var speed = opts && opts.duration !== undefined ? opts.duration : this.options.toolbarDuration;
                var debugHeight = $('.cms-debug-bar').height() || 0;
                var toolbarHeight = $('.cms-toolbar').height() + 10;

                this.ui.toolbar.css({
                    'transition': 'margin-top ' + speed + 'ms',
                    'margin-top': 0
                });
                this.ui.toolbarTrigger.addClass('cms-toolbar-trigger-expanded');
                // animate html
                this.ui.body.addClass('cms-toolbar-expanded');
                this.ui.body.animate({ 'margin-top': toolbarHeight - 10 + debugHeight }, speed, 'linear');
                // set messages top to toolbar height
                this.ui.messages.css('top', toolbarHeight - 10);
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
             */
            _hide: function _hide() {
                var speed = this.options.toolbarDuration;
                var toolbarHeight = $('.cms-toolbar').height() + 10;

                this.ui.toolbar.css('transition', 'margin-top ' + speed + 'ms');
                // cancel if sideframe is active
                if (this.lockToolbar) {
                    return false;
                }

                this.ui.toolbarTrigger.removeClass('cms-toolbar-trigger-expanded');
                this.ui.toolbar.css('margin-top', -toolbarHeight);
                // animate html
                this.ui.body.removeClass('cms-toolbar-expanded');
                this.ui.body.animate({ 'margin-top': (CMS.config.debug) ? 5 : 0 }, speed);
                // set messages top to 0
                this.ui.messages.css('top', 0);
            },

            /**
             * Makes a request to the given url, runs optional callbacks.
             *
             * @method openAjax
             * @param {Object} opts
             * @param {String} opts.url url where the ajax points to
             * @param {Object} [opts.post] post data to be passed
             * @param {String} [opts.text] message to be displayed
             * @param {Function} [opts.callback] custom callback instead of reload
             * @param {String} [opts.onSuccess] reload and display custom message
             * @return {Boolean|jQuery.Deferred} either false or a promise
             */
            openAjax: function (opts) {
                var that = this;
                // url, post, text, callback, onSuccess
                var url = opts.url;
                var post = opts.post || '{}';
                var text = opts.text || '';
                var callback = opts.callback;
                var onSuccess = opts.onSuccess;
                var question = (text) ? CMS.API.Helpers.secureConfirm(text) : true;

                // cancel if question has been denied
                if (!question) {
                    return false;
                }

                // set loader
                this.showLoader();

                return $.ajax({
                    type: 'POST',
                    url: url,
                    data: (post) ? JSON.parse(post) : {}
                }).done(function (response) {
                    CMS.API.locked = false;

                    if (callback) {
                        callback(that, response);
                        that.hideLoader();
                    } else if (onSuccess) {
                        CMS.API.Helpers.reloadBrowser(onSuccess, false, true);
                    } else {
                        // reload
                        CMS.API.Helpers.reloadBrowser(false, false, true);
                    }
                }).fail(function (jqXHR) {
                    CMS.API.locked = false;

                    CMS.API.Messages.open({
                        message: jqXHR.response + ' | ' + jqXHR.status + ' ' + jqXHR.statusText,
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
             */
            _delegate: function _delegate(el) {
                // save local vars
                var target = el.data('rel');
                if (el.hasClass('cms-btn-disabled')) {
                    return false;
                }

                switch (target) {
                    case 'modal':
                        var modal = new CMS.Modal({
                            onClose: el.data('on-close')
                        });
                        modal.open({
                            url: el.attr('href'),
                            title: el.data('name')
                        });
                        break;
                    case 'message':
                        CMS.API.Messages.open({
                            message: el.data('text')
                        });
                        break;
                    case 'sideframe':
                        var sideframe = new CMS.Sideframe({
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
                        window.location.href = el.attr('href');
                }
            },

            /**
             * Sets the functionality for the switcher button.
             *
             * @method _setSwitcher
             * @param {jQuery} el button element
             * @private
             * @deprecated
             */
            _setSwitcher: function _setSwitcher(el) {
                // save local vars
                var active = el.hasClass('cms-toolbar-item-switch-active');
                var anchor = el.find('a');
                var knob = el.find('.cms-toolbar-item-switch-knob');
                var duration = 300;

                // prevent if switchopstion is passed
                if (this.options.preventSwitch) {
                    CMS.API.Messages.open({
                        message: this.options.preventSwitchMessage,
                        dir: 'right'
                    });
                    return false;
                }

                // determin what to trigger
                if (active) {
                    knob.animate({
                        'right': anchor.outerWidth(true) - (knob.outerWidth(true) + 2)
                    }, duration);
                    // move anchor behind the knob
                    anchor.css('z-index', 1).animate({
                        'padding-top': 6,
                        'padding-right': 14,
                        'padding-bottom': 4,
                        'padding-left': 28
                    }, duration);
                } else {
                    knob.animate({
                        'left': anchor.outerWidth(true) - (knob.outerWidth(true) + 2)
                    }, duration);
                    // move anchor behind the knob
                    anchor.css('z-index', 1).animate({
                        'padding-top': 6,
                        'padding-right': 28,
                        'padding-bottom': 4,
                        'padding-left': 14
                    }, duration);
                }

                // reload
                setTimeout(function () {
                    window.location.href = anchor.attr('href');
                }, duration);
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
                var that = this;
                var timeout = 1000;
                var timer = function () {};

                // bind message event
                var debug = this.ui.container.find('.cms-debug-bar');
                debug.on(this.mouseEnter + ' ' + this.mouseLeave, function (e) {
                    clearTimeout(timer);

                    if (e.type === that.mouseEnter) {
                        timer = setTimeout(function () {
                            CMS.API.Messages.open({
                                message: CMS.config.lang.debug
                            });
                        }, timeout);
                    }
                });
            },

            /**
             * This shows a dark screen with a note "This page is a redirect"
             * on a page where the settings have been modified to redirect to
             * another page.
             *
             * @method _screenBlock
             * @private
             */
            _screenBlock: function _screenBlock() {
                var that = this;
                var interval = 20;
                var blocker = this.ui.screenBlock;
                var sideframe = $('.cms-sideframe');

                // automatically resize screenblock window according to given attributes
                $(window).on(this.resize, function () {
                    blocker.css({
                        'width': $(this).width() - sideframe.width(),
                        'height': $(window).height()
                    });
                }).trigger('resize');

                // set update interval
                setInterval(function () {
                    $(window).trigger(that.resize);
                }, interval);
            }

        });
    });
})(CMS.$);
