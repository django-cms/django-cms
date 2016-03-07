/*!
 * CMS.API.Helpers
 * Multiple helpers used accross all CMS features
 */

//##############################################################################
// COMPATIBILITY

// ensuring django namespace is set correctly
window.django = window.django || undefined;

// ensuring jQuery namespace is set correctly
window.jQuery = (window.django && window.django.jQuery) ? window.django.jQuery : window.jQuery || undefined;

// ensuring Class namespace is set correctly
window.Class = window.Class || undefined;

// ensuring CMS namespace is set correctly
/**
 * @module CMS
 */
var CMS = {
    $: (typeof window.jQuery === 'function') ? window.jQuery : undefined,
    Class: (typeof window.Class === 'function') ? window.Class : undefined,
    /**
     * @module CMS
     * @submodule CMS.API
     */
    API: {},
    /**
     * Provides key codes for common keys.
     *
     * @module CMS
     * @submodule CMS.KEYS
     * @example
     *     if (e.keyCode === CMS.KEYS.ENTER) { ... };
     */
    KEYS: {
        SHIFT: 16,
        TAB: 9,
        UP: 38,
        DOWN: 40,
        ENTER: 13,
        SPACE: 32,
        ESC: 27,
        CMD_LEFT: 91,
        CMD_RIGHT: 93,
        CMD_FIREFOX: 224,
        CTRL: 17
    },
    /**
     * Provides breakpoints for certain device widths
     *
     * @module CMS
     * @submodule CMS.BREAKPOINTS
     * @example
     *     if (window.width >= CMS.BREAKPOINTS.mobile) { ... };
     */
    BREAKPOINTS: {
        mobile: 420
    }
};

//##############################################################################
// CMS.API
(function ($) {
    'use strict';
    // shorthand for jQuery(document).ready();
    $(function () {
        var root = $('#cms-top');
        /**
         * @function _ns
         * @private
         * @param {String} events space separated event names to be namespaces
         * @return {String} string containing space separated namespaced event names
         */
        var _ns = function nameSpaceEvent(events) {
            return events.split(/\s+/g).map(function (className) {
                return 'cms-' + className;
            }).join(' ');
        };

        /**
         * Provides various helpers that are mixed in all CMS classes.
         *
         * @class Helpers
         * @static
         * @module CMS
         * @submodule CMS.API
         * @namespace CMS.API
         */
        CMS.API.Helpers = {

            /**
             * Redirects to a specific url or reloads browser.
             *
             * @method reloadBrowser
             * @param {String} url where to redirect. if equal to `REFRESH_PAGE` will reload page instead
             * @param {Number} timeout=0 timeout in ms
             * @param {Boolean} ajax if set to true first initiates **synchronous**
             *     ajax request to figure out if the browser should reload current page,
             *     move to another one, or do nothing.
             * @param {Object} [data] optional data to be passed instead of one provided by request config
             * @param {String} [data.model=CMS.config.request.model]
             * @param {String|Number} [data.pk=CMS.config.request.pk]
             */
            reloadBrowser: function (url, timeout, ajax, data) {
                var that = this;
                // is there a parent window?
                var parent = (window.parent) ? window.parent : window;

                // if there is an ajax reload, prioritize
                if (ajax) {
                    parent.CMS.API.locked = true;
                    // check if the url has changed, if true redirect to the new path
                    // this requires an ajax request
                    $.ajax({
                        async: false,
                        type: 'GET',
                        url: parent.CMS.config.request.url,
                        data: data || {
                            model: parent.CMS.config.request.model,
                            pk: parent.CMS.config.request.pk
                        },
                        success: function (response) {
                            parent.CMS.API.locked = false;

                            if (response === '' && !url) {
                                // cancel if response is empty
                                return false;
                            } else if (parent.location.pathname !== response && response !== '') {
                                // api call to the backend to check if the current path is still the same
                                that.reloadBrowser(response);
                            } else if (url === 'REFRESH_PAGE') {
                                // if on_close provides REFRESH_PAGE, only do a reload
                                that.reloadBrowser();
                            } else if (url) {
                                // on_close can also provide a url, reload to the new destination
                                that.reloadBrowser(url);
                            } else {
                                that.reloadBrowser();
                            }
                        }
                    });

                    // cancel further operations
                    return false;
                }

                // add timeout if provided
                parent.setTimeout(function () {
                    if (url && url !== parent.location.href) {
                        // location.reload() takes precedence over this, so we
                        // don't want to reload the page if we need a redirect
                        parent.location.href = url;
                    } else {
                        // ensure page is always reloaded #3413
                        parent.location.reload();
                    }
                }, timeout || 0);
            },

            /**
             * Assigns an event handler to forms located in the toolbar
             * to prevent multiple submissions.
             *
             * @method preventSubmit
             */
            preventSubmit: function () {
                var forms = $('.cms-toolbar').find('form');
                forms.submit(function () {
                    // show loader
                    CMS.API.Toolbar.showLoader();
                    // we cannot use disabled as the name action will be ignored
                    $('input[type="submit"]').on('click', function (e) {
                        e.preventDefault();
                    }).css('opacity', 0.5);
                });
            },

            /**
             * Sets csrf token header on ajax requests.
             *
             * @method csrf
             * @param {String} csrf_token
             */
            csrf: function (csrf_token) {
                $.ajaxSetup({
                    beforeSend: function (xhr) {
                        xhr.setRequestHeader('X-CSRFToken', csrf_token);
                    }
                });
            },

            /**
             * Sends or retrieves a JSON from localStorage
             * or the session (through synchronous ajax request)
             * if localStorage is not available.
             *
             * @method setSettings
             * @param settings
             */
            setSettings: function (settings) {
                // merge settings
                settings = JSON.stringify($.extend({}, CMS.config.settings, settings));
                // set loader
                if (CMS.API.Toolbar) {
                    CMS.API.Toolbar.showLoader();
                }

                // use local storage or session
                if (this._isStorageSupported) {
                    // save within local storage
                    localStorage.setItem('cms_cookie', settings);
                    if (CMS.API.Toolbar) {
                        CMS.API.Toolbar.hideLoader();
                    }
                } else {
                    // save within session
                    CMS.API.locked = true;

                    $.ajax({
                        async: false,
                        type: 'POST',
                        url: CMS.config.urls.settings,
                        data: {
                            csrfmiddlewaretoken: CMS.config.csrf,
                            settings: settings
                        },
                        success: function (data) {
                            CMS.API.locked = false;
                            // determine if logged in or not
                            settings = (data) ? JSON.parse(data) : CMS.config.settings;
                            if (CMS.API.Toolbar) {
                                CMS.API.Toolbar.hideLoader();
                            }
                        },
                        error: function (jqXHR) {
                            CMS.API.Messages.open({
                                message: jqXHR.response + ' | ' + jqXHR.status + ' ' + jqXHR.statusText,
                                error: true
                            });
                        }
                    });
                }

                // save settings
                CMS.settings = typeof settings === 'object' ? settings : JSON.parse(settings);

                // ensure new settings are returned
                return CMS.settings;
            },

            /**
             * Gets user settings (from JSON or the session)
             * in the same way as setSettings sets them.
             *
             * @method getSettings
             */
            getSettings: function () {
                var settings;
                // set loader
                if (CMS.API.Toolbar) {
                    CMS.API.Toolbar.showLoader();
                }

                // use local storage or session
                if (this._isStorageSupported) {
                    // get from local storage
                    settings = JSON.parse(localStorage.getItem('cms_cookie'));
                    if (CMS.API.Toolbar) {
                        CMS.API.Toolbar.hideLoader();
                    }
                } else {
                    CMS.API.locked = true;
                    // get from session
                    $.ajax({
                        async: false,
                        type: 'GET',
                        url: CMS.config.urls.settings,
                        success: function (data) {
                            CMS.API.locked = false;
                            // determine if logged in or not
                            settings = (data) ? JSON.parse(data) : CMS.config.settings;
                            if (CMS.API.Toolbar) {
                                CMS.API.Toolbar.hideLoader();
                            }
                        },
                        error: function (jqXHR) {
                            CMS.API.Messages.open({
                                message: jqXHR.response + ' | ' + jqXHR.status + ' ' + jqXHR.statusText,
                                error: true
                            });
                        }
                    });
                }

                if (!settings) {
                    settings = this.setSettings(CMS.config.settings);
                }

                // save settings
                CMS.settings = settings;

                // ensure new settings are returned
                return CMS.settings;
            },

            /**
             * Modifies the url with new params and sanitises
             * the ampersand within the url for #3404.
             *
             * @method makeURL
             * @param {String} url original url
             * @param {String[]} [params] array of `param=value` strings to update the url
             */
            makeURL: function makeURL(url, params) {
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
                if (params && params.length) {
                    $.each(params, function (index, param) {
                        arr.push({
                            param: param.split('=')[0],
                            value: param.split('=')[1]
                        });
                    });
                }

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
                url = url.replace('&', '&amp;');

                return url;
            },

            /**
             * Creates a debounced function that delays invoking `func`
             * until after `wait` milliseconds have elapsed since
             * the last time the debounced function was invoked.
             * Optionally can be invoked first time immediately.
             *
             * @method debounce
             * @param {Function} func function to debounce
             * @param {Number} wait time in ms to wait
             * @param {Object} [opts]
             * @param {Boolean} [opts.immediate] trigger func immediately?
             * @return {Function}
             */
            debounce: function debounce(func, wait, opts) {
                var timeout;
                return function () {
                    var context = this, args = arguments;
                    var later = function () {
                        timeout = null;
                        if (!opts || !opts.immediate) {
                            func.apply(context, args);
                        }
                    };
                    var callNow = opts && opts.immediate && !timeout;
                    clearTimeout(timeout);
                    timeout = setTimeout(later, wait);
                    if (callNow) {
                        func.apply(context, args);
                    }
                };
            },

            /**
             * Returns a function that when invoked, will only be triggered
             * at most once during a given window of time. Normally, the
             * throttled function will run as much as it can, without ever
             * going more than once per `wait` duration, but if you’d like to
             * disable the execution on the leading edge, pass `{leading: false}`.
             * To disable execution on the trailing edge, ditto.
             *
             * @method throttle
             * @param {Function} func function to throttle
             * @param {Number} wait time window
             * @param {Object} [opts]
             * @param {Boolean} [opts.leading=true] execute on the leading edge
             * @param {Boolean} [opts.trailing=true] execute on the trailing edge
             * @return {Function}
             */
            throttle: function throttle(func, wait, opts) {
                var context, args, result;
                var timeout = null;
                var previous = 0;
                if (!opts) {
                    opts = {};
                }
                var later = function () {
                    previous = opts.leading === false ? 0 : $.now();
                    timeout = null;
                    result = func.apply(context, args);
                    if (!timeout) {
                        context = args = null;
                    }
                };
                return function () {
                    var now = $.now();
                    if (!previous && opts.leading === false) {
                        previous = now;
                    }
                    var remaining = wait - (now - previous);
                    context = this;
                    args = arguments;
                    if (remaining <= 0 || remaining > wait) {
                        if (timeout) {
                            clearTimeout(timeout);
                            timeout = null;
                        }
                        previous = now;
                        result = func.apply(context, args);
                        if (!timeout) {
                            context = args = null;
                        }
                    } else if (!timeout && opts.trailing !== false) {
                        timeout = setTimeout(later, remaining);
                    }
                    return result;
                };
            },

            /**
             * Browsers allow to "Prevent this page form creating additional
             * dialogs." checkbox which prevents further input from confirm messages.
             * This method falls back to "true" once the user chooses this option.
             *
             * @method secureConfirm
             * @param {String} message to be displayed
             * @return {Boolean}
             */
            secureConfirm: function secureConfirm(message) {
                var start = Number(new Date());
                var result = confirm(message);
                var end = Number(new Date());

                return (end < (start + 10) || result === true);
            },

            /**
             * Is localStorage truly supported?
             * Check is taken from modernizr.
             *
             * @property _isStorageSupported
             * @private
             * @type {Boolean}
             */
            _isStorageSupported: (function localStorageCheck() {
                var mod = 'modernizr';
                try {
                    localStorage.setItem(mod, mod);
                    localStorage.removeItem(mod);
                    return true;
                } catch (e) {
                    return false;
                }
            }()),

            /**
             * Adds an event listener to the "CMS".
             *
             * @method addEventListener
             * @param {String} eventName string containing space separated event names
             * @param {Function} fn callback to run when the event happens
             */
            addEventListener: function addEventListener(eventName, fn) {
                return root.on(_ns(eventName), fn);
            },

            /**
             * Removes the event listener from the "CMS". If a callback is provided - removes only that callback.
             *
             * @method addEventListener
             * @param {String} eventName string containing space separated event names
             * @param {Function} [fn] specific callback to be removed
             */
            removeEventListener: function removeEventListener(eventName, fn) {
                return root.off(_ns(eventName), fn);
            },

            /**
             * Dispatches an event
             * @method dispatchEvent
             * @param {String} eventName  string containing space separated event names
             * @param {Object} payload whatever payload required for the consumer
             */
            dispatchEvent: function dispatchEvent(eventName, payload) {
                return root.trigger(_ns(eventName), [payload]);
            },

            /**
             * Returns a function that wraps the passed function so the wrapped function
             * is executed only once, no matter how many times the wrapper function is executed.
             *
             * @method once
             * @param {Function} fn function to be executed only once
             * @return {Function}
             */
            once: function once(fn) {
                var result;
                var didRunOnce = false;

                return function () {
                    if (didRunOnce) {
                        fn = undefined;
                    } else {
                        didRunOnce = true;
                        result = fn.apply(this, arguments);
                    }
                    return result;
                };
            },

            /**
             * Prevents scrolling with touch in an element.
             *
             * @method preventTouchScrolling
             * @param {jQuery} element element where we are preventing the scroll
             * @param {String} namespace so we don't mix events from two different places on the same element
             */
            preventTouchScrolling: function preventTouchScrolling(element, namespace) {
                element.on('touchmove.cms.preventscroll.' + namespace, function (e) {
                    e.preventDefault();
                });
            },

            /**
             * Allows scrolling with touch in an element.
             *
             * @method allowTouchScrolling
             * @param {jQuery} element element where we are allowing the scroll again
             * @param {String} namespace so we don't accidentally remove events from a different handler
             */
            allowTouchScrolling: function allowTouchScrolling(element, namespace) {
                element.off('touchmove.cms.preventscroll.' + namespace);
            }
        };

        // autoinits
        CMS.API.Helpers.preventSubmit();

    });
})(CMS.$);
