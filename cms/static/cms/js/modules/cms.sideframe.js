/*
 * Copyright https://github.com/divio/django-cms
 */

// #############################################################################
// NAMESPACES
/**
 * @module CMS
 */
/* istanbul ignore next */
var CMS = window.CMS || {};

// #############################################################################
// SIDEFRAME
(function ($) {
    'use strict';

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
            sideframeDuration: 300
        },

        initialize: function initialize(options) {
            this.options = $.extend(true, {}, this.options, options);

            // elements
            this._setupUI();

            // states and events
            this.click = 'click.cms.sideframe';
            this.pointerDown = 'pointerdown.cms.sideframe contextmenu.cms.sideframe';
            this.pointerUp = 'pointerup.cms.sideframe pointercancel.cms.sideframe';
            this.pointerMove = 'pointermove.cms.sideframe';
            this.enforceReload = false;
            this.settingsRefreshTimer = 600;
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
                frame: sideframe.find('.cms-sideframe-frame'),
                shim: sideframe.find('.cms-sideframe-shim'),
                historyBack: sideframe.find('.cms-sideframe-history .cms-icon-arrow-back'),
                historyForward: sideframe.find('.cms-sideframe-history .cms-icon-arrow-forward')
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

            // we need to set the history state on event creation
            // to ensure we start with clean states in new instances
            this.history = {
                back: [],
                forward: []
            };

            this.ui.close.off(this.click).on(this.click, function () {
                that.close();
            });

            // close sideframe when clicking on the dimmer
            this.ui.dimmer.off(this.click).on(this.click, function () {
                that.close();
            });

            // attach events to the back button
            this.ui.historyBack.off(this.click).on(this.click, function () {
                if (that.ui.historyBack.hasClass('cms-icon-disabled')) {
                    return false;
                }
                that._goToHistory('back');
            });

            // attach events to the forward button
            this.ui.historyForward.off(this.click).on(this.click, function () {
                if (that.ui.historyForward.hasClass('cms-icon-disabled')) {
                    return false;
                }
                that._goToHistory('forward');
            });
        },

        /**
         * Opens a given url within a sideframe.
         *
         * @method open
         * @chainable
         * @param {Object} opts
         * @param {String} opts.url url to render iframe
         * @param {Boolean} [opts.animate] should sideframe be animated
         * @returns {Class} this
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

            // We have to rebind events every time we open a sideframe
            // because the event handlers contain references to the instance
            // and since we reuse the same markup we need to update
            // that instance reference every time.
            this._events();

            // show dimmer even before iframe is loaded
            this.ui.dimmer.show();
            this.ui.frame.addClass('cms-loader');

            // istanbul ignore else: always show loader
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

            // The user has performed an action that requires the
            // sideframe to be shown, this intent outweighs any
            // previous intent to minimize the frame.
            CMS.settings.sideframe.hidden = false;

            // show iframe
            this._show(animate);

            return this;
        },

        /**
         * Handles content replacement mechanisms.
         *
         * @method _content
         * @private
         * @param {String} url valid uri to pass on the iframe
         */
        _content: function _content(url) {
            var that = this;
            var iframe = $('<iframe src="' + url + '" class="" frameborder="0" />');
            var holder = this.ui.frame;
            var contents;
            var body;
            var iOS = (/iPhone|iPod|iPad/).test(navigator.userAgent);

            // istanbul ignore next
            /**
             * On iOS iframes do not respect the size set in css or attributes, and
             * is always matching the content. However, if you first load the page
             * with one amount of content (small) and then from there you'd go to a page
             * with lots of content (long, scroll requred) it won't be scrollable, because
             * iframe would retain the size of previous page. When this happens we
             * need to rerender the iframe (that's why we are animating the width here, so far
             * that was the only reliable way). But after that if you try to scroll the iframe
             * which height was just adjusted it will hide completely from the screen
             * (this is an iOS glitch, the content would still be there and in fact it would
             * be usable, but just not visible). To get rid of that we bring up the shim element
             * up and down again and this fixes the glitch. (same shim we use for resizing the sideframe)
             *
             * It is not recommended to expose it and use it on other devices rather than iOS ones.
             *
             * @function forceRerenderOnIOS
             * @private
             */
            function forceRerenderOnIOS() {
                var w = that.ui.sideframe.width();

                that.ui.sideframe.animate({ width: w + 1 }, 0);
                setTimeout(function () {
                    that.ui.sideframe.animate({ width: w }, 0);
                    // eslint-disable-next-line no-magic-numbers
                    that.ui.shim.css('z-index', 20);
                    setTimeout(function () {
                        that.ui.shim.css('z-index', 1);
                    }, 0);
                }, 0);
            }

            // attach load event to iframe
            iframe.hide().on('load', function () {
                // check if iframe can be accessed
                try {
                    iframe.contents();
                } catch (error) {
                    CMS.API.Messages.open({
                        message: '<strong>' + error + '</strong>',
                        error: true
                    });
                    that.close();
                    return;
                }

                contents = iframe.contents();
                body = contents.find('body');

                // inject css class
                body.addClass('cms-admin cms-admin-sideframe');

                // remove loader
                that.ui.frame.removeClass('cms-loader');
                // than show
                iframe.show();

                // istanbul ignore if: force style recalculation on iOS
                if (iOS) {
                    forceRerenderOnIOS();
                }

                // add debug infos
                if (CMS.config.debug) {
                    body.addClass('cms-debug');
                }

                // save url in settings
                CMS.settings.sideframe.url = iframe[0].contentWindow.location.href;
                CMS.settings = that.setSettings(CMS.settings);

                // This essentially hides the toolbar dropdown when
                // click happens inside of a sideframe iframe
                body.on(that.click, function () {
                    $(document).trigger(that.click);
                });

                // attach close event
                body.on('keydown.cms', function (e) {
                    if (e.keyCode === CMS.KEYS.ESC) {
                        that.close();
                    }
                });

                // adding django hacks
                contents.find('.viewsitelink').attr('target', '_top');

                // update history
                that._addToHistory(this.contentWindow.location.href);
            });

            // clear the frame (removes all the handlers)
            holder.empty();
            // inject iframe
            holder.html(iframe);
        },

        /**
         * Animation helper for opening the sideframe.
         *
         * @method _show
         * @private
         * @param {Number} [animate] Animation duration
         */
        _show: function _show(animate) {
            var that = this;
            var width = '95%';

            this.ui.sideframe.show();

            // otherwise do normal behaviour
            if (animate) {
                this.ui.sideframe.animate({
                    width: width,
                    overflow: 'visible'
                }, this.options.sideframeDuration);
            } else {
                this.ui.sideframe.css('width', width);
            }

            // istanbul ignore else: always trigger API handlers
            if (CMS.API && CMS.API.Toolbar) {
                // FIXME: initialization needs to be done after our libs are loaded
                CMS.API.Toolbar.open();
                CMS.API.Toolbar.hideLoader();
                CMS.API.Toolbar._lock(true);
            }

            // add esc close event
            this.ui.body.off('keydown.cms.close').on('keydown.cms.close', function (e) {
                if (e.keyCode === CMS.KEYS.ESC) {
                    that.options.onClose = null;
                    that.close();
                }
            });

            // disable scrolling for touch
            this.ui.body.addClass('cms-prevent-scrolling');
            this.preventTouchScrolling($(document), 'sideframe');
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
            CMS.settings.sideframe = {
                url: null,
                hidden: false
            };
            CMS.settings = this.setSettings(CMS.settings);

            // check for reloading
            this.reloadBrowser(this.options.onClose, false, true);

            // trigger hide animation
            this._hide({
                duration: this.options.sideframeDuration / 2
            });
        },

        /**
         * Animation helper for closing the iframe.
         *
         * @method _hide
         * @private
         * @param {Object} [opts]
         * @param {Number} [opts.duration=this.options.sideframeDuration] animation duration
         */
        _hide: function _hide(opts) {
            var duration = this.options.sideframeDuration;

            if (opts && typeof opts.duration === 'number') {
                duration = opts.duration;
            }

            this.ui.sideframe.animate({ width: 0 }, duration, function () {
                $(this).hide();
            });
            this.ui.frame.removeClass('cms-loader');

            // istanbul ignore else
            if (CMS.API && CMS.API.Toolbar) {
                CMS.API.Toolbar._lock(false);
            }

            this.ui.body.off('keydown.cms.close');

            // enable scrolling again
            this.ui.body.removeClass('cms-prevent-scrolling');
            this.allowTouchScrolling($(document), 'sideframe');
        },

        /**
         * Retrieves the history states from `this.history`.
         *
         * @method _goToHistory
         * @private
         * @param {String} type can be either `back` or `forward`
         */
        _goToHistory: function _goToHistory(type) {
            var iframe = this.ui.frame.find('iframe');
            var tmp;

            if (type === 'back') {
                // remove latest entry (which is the current site)
                this.history.forward.push(this.history.back.pop());
                iframe.attr('src', this.history.back[this.history.back.length - 1]);
            }

            if (type === 'forward') {
                tmp = this.history.forward.pop();
                this.history.back.push(tmp);
                iframe.attr('src', tmp);
            }

            this._updateHistoryButtons();
        },

        /**
         * Stores the history states in `this.history`.
         *
         * @method _addToHistory
         * @private
         * @param {String} url url to be stored in `this.history.back`
         */
        _addToHistory: function _addToHistory(url) {
            // we need to update history first
            this.history.back.push(url);

            // and then set local variables
            var length = this.history.back.length;

            // check for duplicates
            if (this.history.back[length - 1] === this.history.back[length - 2]) {
                this.history.back.pop();
            }

            this._updateHistoryButtons();
        },

        /**
         * Sets the correct states for the history UI elements.
         *
         * @method _updateHistoryButtons
         * @private
         */
        _updateHistoryButtons: function _updateHistoryButtons() {
            if (this.history.back.length > 1) {
                this.ui.historyBack.removeClass('cms-icon-disabled');
            } else {
                this.ui.historyBack.addClass('cms-icon-disabled');
            }

            if (this.history.forward.length >= 1) {
                this.ui.historyForward.removeClass('cms-icon-disabled');
            } else {
                this.ui.historyForward.addClass('cms-icon-disabled');
            }
        }
    });
})(CMS.$);
