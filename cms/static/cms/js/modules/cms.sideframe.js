//##################################################################################################################
// #SIDEFRAME#
/* global CMS */

(function ($) {
    'use strict';
    // CMS.$ will be passed for $
    $(document).ready(function () {
        /*!
         * Sideframe
         * Controls a cms specific sideframe
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

            initialize: function (options) {
                this.options = $.extend(true, {}, this.options, options);
                this.config = CMS.config;
                this.settings = CMS.settings;

                // elements
                this.sideframe = $('.cms-sideframe');
                this.dimmer = this.sideframe.find('.cms-sideframe-dimmer');

                // states
                this.click = 'click.cms';
                this.enforceReload = false;

                // if the modal is initialized the first time, set the events
                if (!this.sideframe.data('ready')) {
                    this._events();
                }

                // ready sideframe
                this.sideframe.data('ready', true);
            },

            // initial methods
            _events: function () {
                var that = this;

                // attach close event
                this.sideframe.find('.cms-sideframe-close').bind(this.click, function () {
                    that.close(true);
                });

                this.sideframe.find('.cms-sideframe-resize').bind('pointerdown.cms.sideframe', function (e) {
                    e.preventDefault();
                    that._startResize();
                });

                // stopper events
                // FIXME should not be here forever, only when needed
                $('html').bind('pointerup.cms.sideframe', function () {
                    that._stopResize();
                });
            },

            // public methods
            open: function (url, animate) {
                // prepare iframe
                var that = this;
                var language = 'language=' + CMS.config.request.language;
                var page_id = 'page_id=' + CMS.config.request.page_id;
                var holder = this.sideframe.find('.cms-sideframe-frame');
                var initialized = false;

                function insertHolder(iframe) {
                    // show iframe after animation
                    that.sideframe.find('.cms-sideframe-frame').addClass('cms-loader');
                    holder.html(iframe);
                }

                // show dimmer even before iframe is loaded
                this.dimmer.show();

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
                iframe.bind('load', function () {
                    var contents = iframe.contents();

                    // after iframe is loaded append css
                    contents.find('head').append(
                        $('<link rel="stylesheet" type="text/css" href="' +
                            that.config.urls.static +
                            that.options.urls.css_sideframe + '" />')
                    );
                    // remove loader
                    that.sideframe.find('.cms-sideframe-frame').removeClass('cms-loader');
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
                    contents.find('body').bind(that.click, function () {
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
                if (this.sideframe.is(':visible')) {
                    // sideframe is already open
                    insertHolder(iframe);
                    // reanimate the frame
                    if (this.sideframe.outerWidth() < width) {
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

            close: function () {
                this._hide(true);

                // hide dimmer immediately
                this.dimmer.hide();

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

            // private methods
            _show: function (width, animate) {
                this.sideframe.show();

                // check if sideframe should be hidden
                if (this.settings.sideframe.hidden) {
                    this._hide();
                }

                // otherwise do normal behaviour
                if (animate) {
                    this.sideframe.animate({
                        width: width,
                        overflow: 'visible'
                    }, this.options.sideframeDuration);
                } else {
                    this.sideframe.css('width', width);
                    // reset width if larger than available space
                    if (width >= $(window).width()) {
                        this.sideframe.animate({
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

            _hide: function (close) {
                var duration = this.options.sideframeDuration;
                // remove the iframe
                if (close && this.sideframe.width() <= 0) {
                    duration = 0;
                }
                if (close) {
                    this.sideframe.find('iframe').remove();
                }
                this.sideframe.animate({ width: 0 }, duration, function () {
                    if (close) {
                        $(this).hide();
                    }
                });
                this.sideframe.find('.cms-sideframe-frame').removeClass('cms-loader');

                // lock toolbar, set timeout to make sure CMS.API is ready
                setTimeout(function () {
                    CMS.API.Toolbar._lock(false);
                }, 100);
            },

            _startResize: function () {
                var that = this;
                var outerOffset = 30;
                var timer = function () {};
                // this prevents the iframe from being focusable
                this.sideframe.find('.cms-sideframe-shim').css('z-index', 20);

                $('html').attr('data-touch-action', 'none').bind('pointermove.cms.sideframe', function (e) {
                    if (e.originalEvent.clientX <= 320) {
                        e.originalEvent.clientX = 320;
                    }
                    if (e.originalEvent.clientX >= $(window).width() - outerOffset) {
                        e.originalEvent.clientX = $(window).width() - outerOffset;
                    }

                    that.sideframe.css('width', e.originalEvent.clientX);

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

            _stopResize: function () {
                this.sideframe.find('.cms-sideframe-shim').css('z-index', 1);
                $(window).trigger('resize.sideframe');

                $('html').removeAttr('data-touch-action').unbind('pointermove.cms.sideframe');
            },

            _url: function (url, params) {
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
