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
// SIDEFRAME
(function ($) {
    'use strict';

    // shorthand for jQuery(document).ready();
    $(function () {
        /**
         * The sideframe is triggered via API calls from the backend either
         * through the toolbar navigation or from plugins. The APIs only allow to
         * open a url within the sideframe.
         *
         * @class Sideframe
         * @namespace CMS
         * @uses CMS.API.Helpers
         */
        CMS.Sideframe = new CMS.Class({

            implement: [CMS.API.Helpers],

            options: {
                onClose: false,
                sideframeDuration: 300,
                sideframeWidth: 0.8 // matches 80% of window width
            },

            initialize: function initialize(options) {
                this.options = $.extend(true, {}, this.options, options);
                this.config = CMS.config;
                this.settings = CMS.settings;

                // elements
                this._setupUI();

                // states and events
                this.click = 'click.cms.sideframe';
                this.pointerDown = 'pointerdown.cms.sideframe contextmenu.cms.sideframe';
                this.pointerUp = 'pointerup.cms.sideframe pointercancel.cms.sideframe';
                this.pointerMove = 'pointermove.cms.sideframe';
                this.enforceReload = false;
                this.settingsRefreshTimer = 600;

                // if the modal is initialized the first time, set the events
                if (!this.ui.sideframe.data('ready')) {
                    this._events();
                }

                // set a state to determine if we need to reinitialize this._events();
                this.ui.sideframe.data('ready', true);
            },

            /**
             * Stores all jQuery references within `this.ui`.
             *
             * @method _setupUI
             * @private
             */
            _setupUI: function _setupUI() {
                var sideframe = $('.cms-sideframe');
                this.ui = {
                    sideframe: sideframe,
                    body: $('html'),
                    window: $(window),
                    dimmer: sideframe.find('.cms-sideframe-dimmer'),
                    close: sideframe.find('.cms-sideframe-close'),
                    resize: sideframe.find('.cms-sideframe-resize'),
                    frame: sideframe.find('.cms-sideframe-frame'),
                    shim: sideframe.find('.cms-sideframe-shim')
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

                this.ui.close.on(this.click, function () {
                    that.close();
                });

                // the resize event attaches an off event to the body
                // which is handled within _startResize()
                this.ui.resize.on(this.pointerDown, function (e) {
                    e.preventDefault();
                    that._startResize();
                });

                // close sideframe when clicking on the dimmer
                this.ui.dimmer.on(this.click, function () {
                    that.close();
                });
            },

            /**
             * Opens a given url within a sideframe.
             *
             * @method open
             * @chainable
             * @param opts
             * @param opts.url {String} url to render iframe
             * @param [opts.animate] {Boolean} should modal be animated
             */
            open: function open(opts) {
                if (!(opts && opts.url)) {
                    throw new Error('The arguments passed to "open" were invalid.');
                }

                var url = opts.url;
                var animate = opts.animate;

                // setup internals
                var language = 'language=' + CMS.config.request.language;
                var page_id = 'page_id=' + CMS.config.request.page_id;
                var params = [];
                var width = this.settings.sideframe.position || (window.innerWidth * this.options.sideframeWidth);

                // show dimmer even before iframe is loaded
                this.ui.dimmer.show();
                this.ui.frame.addClass('cms-loader');

                // show loader
                if (CMS.API && CMS.API.Toolbar) {
                    CMS.API.Toolbar.showLoader();
                }

                // we need to modify the url appropriately to pass
                // language and page to the params
                if (url.indexOf(CMS.config.request.tree) >= 0) {
                    if (CMS.config.request.language) {
                        params.push(language);
                    }
                    if (CMS.config.request.page_id) {
                        params.push(page_id);
                    }
                }

                url = this.makeURL(url, params);

                // load the iframe
                this._content(url);

                // cancel animation if sideframe is already shown
                if (this.ui.sideframe.is(':visible') && this.ui.sideframe.outerWidth() < width) {
                    // The user has performed an action that requires the
                    // sideframe to be shown, this intent outweighs any
                    // previous intent to minimize the frame.
                    this.settings.sideframe.hidden = false;
                }

                // show iframe
                this._show(width, animate);

                return this;
            },

            /**
             * Handles content replacement mechanisms.
             *
             * @method _content
             * @private
             * @param url {String} valid uri to pass on the iframe
             */
            _content: function _content(url) {
                var that = this;
                var initialized = false;
                var iframe = $('<iframe src="' + url + '" class="" frameborder="0" />');
                var holder = this.ui.frame;
                var contents;
                var body;

                // attach load event to iframe
                iframe.hide().on('load', function () {
                    contents = iframe.contents();
                    body = contents.find('body');

                    // inject css class
                    body.addClass('cms-admin cms-admin-sideframe');

                    // remove loader
                    that.ui.frame.removeClass('cms-loader');
                    // than show
                    iframe.show();

                    // add debug infos
                    if (that.config.debug) {
                        iframe.contents().find('body').addClass('cms-debug');
                    }

                    // save url in settings
                    that.settings.sideframe.url = iframe.prop('src');
                    that.settings = that.setSettings(that.settings);

                    // bind extra events
                    body.on(that.click, function () {
                        $(document).trigger(that.click);
                    });

                    // attach reload event
                    if (initialized) {
                        that.reloadBrowser(false, false, true);
                    }
                    initialized = true;

                    // adding django hacks
                    contents.find('.viewsitelink').attr('target', '_top');
                });

                // inject iframe
                holder.html(iframe);
            },

            /**
             * Animation helper for opening the sideframe.
             *
             * @method _show
             * @private
             * @param width {Number} width that the iframes opens to
             * @param [animate] {Number} Animation duration
             */
            _show: function _show(width, animate) {
                this.ui.sideframe.show();

                // check if sideframe should be hidden
                if (this.settings.sideframe.hidden) {
                    this._hide();
                }

                // otherwise do normal behaviour
                if (animate) {
                    this.ui.sideframe.animate({
                        width: width,
                        overflow: 'visible'
                    }, this.options.sideframeDuration);
                } else {
                    this.ui.sideframe.css('width', width);
                    // reset width if larger than available space
                    if (width >= $(window).width()) {
                        this.ui.sideframe.css({
                            width: $(window).width() - 30,
                            overflow: 'visible'
                        });
                    }
                }

                // trigger API handlers
                if (CMS.API && CMS.API.Toolbar) {
                    // FIXME: initialization needs to be done after our libs are loaded
                    CMS.API.Toolbar.open();
                    CMS.API.Toolbar.hideLoader();
                    CMS.API.Toolbar._lock(true);
                }
            },

            /**
             * Closes the current instance.
             *
             * @method close
             */
            close: function close() {
                // hide dimmer immediately
                this.ui.dimmer.hide();

                // update settings
                this.settings.sideframe = {
                    url: null,
                    hidden: false,
                    width: this.options.sideframeWidth
                };
                this.settings = this.setSettings(this.settings);

                // check for reloading
                this.reloadBrowser(this.options.onClose, false, true);

                // trigger hide animation
                this._hide({ duration: 0 });
            },

            /**
             * Animation helper for closing the iframe.
             *
             * @method _hide
             * @private
             * @param opts
             * @param opts.duration {Number} animation duration
             */
            _hide: function _hide(opts) {
                var duration = this.options.sideframeDuration;
                if (opts && opts.duration) {
                    duration = opts.duration;
                }

                this.ui.sideframe.animate({ width: 0 }, duration, function () {
                    $(this).hide();
                });
                this.ui.frame.removeClass('cms-loader');

                if (CMS.API && CMS.API.Toolbar) {
                    CMS.API.Toolbar._lock(false);
                }
            },

            /**
             * Initiates the start resize event from `_events`.
             *
             * @method _startResize
             * @private
             */
            _startResize: function _startResize() {
                var that = this;
                var outerOffset = 30;
                var timer = function () {};

                // create event for stopping
                this.ui.body.on(this.pointerUp, function (e) {
                    e.preventDefault();
                    that._stopResize();
                });

                // this prevents the iframe from being focusable
                this.ui.shim.css('z-index', 20);

                this.ui.body.attr('data-touch-action', 'none').on(this.pointerMove, function (e) {
                    if (e.originalEvent.clientX <= 320) {
                        e.originalEvent.clientX = 320;
                    }
                    if (e.originalEvent.clientX >= $(window).width() - outerOffset) {
                        e.originalEvent.clientX = $(window).width() - outerOffset;
                    }

                    that.ui.sideframe.css('width', e.originalEvent.clientX);

                    // update settings
                    that.settings.sideframe.position = e.originalEvent.clientX;

                    // save position into our settings
                    clearTimeout(timer);
                    timer = setTimeout(function () {
                        that.settings = that.setSettings(that.settings);
                    }, that.settingsRefreshTimer);
                });
            },

            /**
             * Initiates the stop resize event from `_startResize`.
             *
             * @method _stopResize
             * @private
             */
            _stopResize: function _stopResize() {
                this.ui.shim.css('z-index', 1);
                this.ui.body
                    .off(this.pointerUp)
                    .off(this.pointerMove)
                    .removeAttr('data-touch-action');
            }
        });

    });
})(CMS.$);
