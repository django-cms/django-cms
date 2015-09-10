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
         * open a url within the sideframe
         *
         * @class Sideframe
         * @namespace CMS
         * @requires CMS.API.Helpers
         */
        CMS.Sideframe = new CMS.Class({

            implement: [CMS.API.Helpers],

            options: {
                onClose: false,
                sideframeDuration: 300,
                sideframeWidth: 0.8, // matches 80% of window width
                urls: {
                    css_sideframe: 'cms/css/cms.toolbar.sideframe.css'
                }
            },

            initialize: function initialize(options) {
                this.options = $.extend(true, {}, this.options, options);
                this.config = CMS.config;
                this.settings = CMS.settings;

                // elements
                this._setupUI();

                // states and event
                this.click = 'click.cms.sideframe';
                this.pointerDown = 'pointerdown.cms.sideframe contextmenu.cms.sideframe';
                this.pointerUp = 'pointerup.cms.sideframe pointercancel.cms.sideframe';
                this.pointerMove = 'pointermove.cms.sideframe';
                this.enforceReload = false;

                // if the modal is initialized the first time, set the events
                if (!this.ui.sideframe.data('ready')) {
                    this._events();
                }

                // set a state to determine if we need to reinitialize this._events();
                this.ui.sideframe.data('ready', true);
            },

            /**
             * stores all jQuery referemces within this.ui
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
             * Handles all internal events such as closing and resizing
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
            },

            /**
             * opens a given url within a sideframe
             *
             * @method open
             * @param url {String} URL string
             * @param animate {Number} Animation speed in ms
             */
            open: function open(url, animate) {
                // prepare iframe
                var that = this;
                var language = 'language=' + CMS.config.request.language;
                var page_id = 'page_id=' + CMS.config.request.page_id;
                var holder = this.ui.frame;
                var initialized = false;

                function insertHolder(iframe) {
                    // show iframe after animation
                    that.ui.frame.addClass('cms-loader');
                    holder.html(iframe);
                }

                // show dimmer even before iframe is loaded
                this.ui.dimmer.show();

                // push required params if defined
                // only apply params on tree view
                if (url.indexOf(CMS.config.request.tree) >= 0) {
                    var params = [];
                    if (CMS.config.request.language) {
                        params.push(language);
                    }
                    if (CMS.config.request.page_id) {
                        params.push(page_id);
                    }
                    url = this._url(url, params);
                }

                var iframe = $('<iframe src="' + url + '" class="" frameborder="0" />');
                iframe.hide();

                var width = this.settings.sideframe.position || (window.innerWidth * this.options.sideframeWidth);

                // attach load event to iframe
                iframe.on('load', function () {
                    var contents = iframe.contents();

                    // after iframe is loaded append css
                    contents.find('head').append(
                        $('<link rel="stylesheet" type="text/css" href="' +
                            that.config.urls.static +
                            that.options.urls.css_sideframe + '" />')
                    );
                    // remove loader
                    that.ui.frame.removeClass('cms-loader');
                    // than show
                    iframe.show();

                    // add debug infos
                    if (that.config.debug) {
                        iframe.contents().find('body').addClass('cms-debug');
                    }

                    // save url in settings
                    that.settings.sideframe.url = iframe.get(0).contentWindow.location.href;
                    that.settings = that.setSettings(that.settings);

                    // bind extra events
                    contents.find('body').on(that.click, function () {
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

                // cancel animation if sideframe is already shown
                if (this.ui.sideframe.is(':visible')) {
                    // sideframe is already open
                    insertHolder(iframe);
                    // reanimate the frame
                    if (this.ui.sideframe.outerWidth() < width) {
                        // The user has performed an action that requires the
                        // sideframe to be shown, this intent outweighs any
                        // previous intent to minimize the frame.
                        this.settings.sideframe.hidden = false;
                        this._show(width, animate);
                    }
                } else {
                    // load iframe after frame animation is done
                    setTimeout(function () {
                        insertHolder(iframe);
                    }, this.options.sideframeDuration);
                    // display the frame
                    this._show(width, animate);
                }
            },

            /**
             * helper function for open, handles internals
             *
             * @method _show
             * @module open
             * @private
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
                        this.ui.sideframe.animate({
                            width: $(window).width() - 30,
                            overflow: 'visible'
                        }, 0);
                    }
                }

                // lock toolbar, set timeout to make sure CMS.API is ready
                setTimeout(function () {
                    CMS.API.Toolbar._lock(true);
                    CMS.API.Toolbar._showToolbar(true);
                }, 100);
            },

            /**
             * closes the current instance
             *
             * @method close
             */
            close: function close() {
                this._hide(true);

                // hide dimmer immediately
                this.ui.dimmer.hide();

                // remove url in settings
                this.settings.sideframe = {
                    url: null,
                    hidden: false,
                    width: this.options.sideframeWidth
                };

                // update settings
                this.settings = this.setSettings(this.settings);

                // handle refresh option
                this.reloadBrowser(this.options.onClose, false, true);
            },

            /**
             * helper function for close, handles internals
             *
             * @method _show
             * @module open
             * @private
             */
            _hide: function _hide(close) {
                var duration = this.options.sideframeDuration;
                // remove the iframe
                if (close && this.ui.sideframe.width() <= 0) {
                    duration = 0;
                }
                if (close) {
                    this.ui.sideframe.find('iframe').remove();
                }
                this.ui.sideframe.animate({ width: 0 }, duration, function () {
                    if (close) {
                        $(this).hide();
                    }
                });
                this.ui.frame.removeClass('cms-loader');

                // lock toolbar, set timeout to make sure CMS.API is ready
                setTimeout(function () {
                    CMS.API.Toolbar._lock(false);
                }, 100);
            },

            /**
             * initiates the start resize event from _events
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

                    // trigger the resize event
                    $(window).trigger('resize.sideframe');

                    // save position
                    clearTimeout(timer);
                    timer = setTimeout(function () {
                        that.settings = that.setSettings(that.settings);
                    }, 500);
                });
            },

            /**
             * initiates the stop resize event from _startResize
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
                this.ui.window.trigger('resize.sideframe');
            },

            // FIXME: this should be replaced with a utility method
            _url: function _url(url, params) {
                var arr = [];
                var keys = [];
                var values = [];
                var tmp = '';
                var urlArray = [];
                var urlParams = [];
                var origin = url;

                // return url if there is no param
                if (!(url.split('?').length <= 1 || window.JSON === undefined)) {
                    // setup local vars
                    urlArray = url.split('?');
                    urlParams = urlArray[1].split('&');
                    origin = urlArray[0];
                }

                // loop through the available params
                $.each(urlParams, function (index, param) {
                    arr.push({
                        param: param.split('=')[0],
                        value: param.split('=')[1]
                    });
                });
                // loop through the new params
                $.each(params, function (index, param) {
                    arr.push({
                        param: param.split('=')[0],
                        value: param.split('=')[1]
                    });
                });

                // merge manually because jquery...
                $.each(arr, function (index, item) {
                    var i = $.inArray(item.param, keys);

                    if (i === -1) {
                        keys.push(item.param);
                        values.push(item.value);
                    } else {
                        values[i] = item.value;
                    }
                });

                // merge new url
                $.each(keys, function (index, key) {
                    tmp += '&' + key + '=' + values[index];
                });
                tmp = tmp.replace('&', '?');
                url = origin + tmp;

                return url;
            }

        });

    });
})(CMS.$);
