/**
 * CMS.API.Helpers
 * Multiple helpers used across all CMS features
 */
import $ from 'jquery';
import URL from 'urijs';
import { once, debounce, throttle } from 'lodash';
import { showLoader, hideLoader } from './loader';

var _CMS = {
    API: {}
};

/**
 * @function _ns
 * @private
 * @param {String} events space separated event names to be namespaces
 * @returns {String} string containing space separated namespaced event names
 */
var _ns = function nameSpaceEvent(events) {
    return events
        .split(/\s+/g)
        .map(function(eventName) {
            return 'cms-' + eventName;
        })
        .join(' ');
};

// Handy shortcut to cache the window and the document objects
// in a jquery wrapper
export const $window = $(window);
export const $document = $(document);

/**
 * Creates always an unique identifier if called
 * @returns {Number} incremental numbers starting from 0
 */
export const uid = (function() {
    let i = 0;

    return () => ++i;
})();

/**
 * Checks if the current version of the CMS matches provided one
 *
 * @param {Object} settings
 * @param {String} settings.version CMS version
 * @returns {Boolean}
 */
export const currentVersionMatches = ({ version }) => {
    return version === __CMS_VERSION__;
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
export const Helpers = {
    /**
     * See {@link reloadBrowser}
     *
     * @property {Boolean} isRloading
     * @private
     */
    _isReloading: false,

    // aliasing the $window and the $document objects
    $window,
    $document,

    uid,

    once,
    debounce,
    throttle,

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
     * @returns {Boolean|void}
     */
    // eslint-disable-next-line max-params
    reloadBrowser: function(url, timeout, ajax, data) {
        var that = this;
        // is there a parent window?
        var win = this._getWindow();
        var parent = win.parent ? win.parent : win;

        that._isReloading = true;

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
                success: function(response) {
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
                    }
                }
            });

            // cancel further operations
            return false;
        }

        // add timeout if provided
        parent.setTimeout(function() {
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
     * Overridable callback that is being called in close_frame.html when plugin is saved
     *
     * @function onPluginSave
     * @public
     */
    onPluginSave: function() {
        var data = this.dataBridge;
        var editedPlugin =
            data &&
            data.plugin_id &&
            window.CMS._instances.some(function(plugin) {
                return Number(plugin.options.plugin_id) === Number(data.plugin_id) && plugin.options.type === 'plugin';
            });
        var addedPlugin = !editedPlugin && data && data.plugin_id;

        if (editedPlugin || addedPlugin) {
            CMS.API.StructureBoard.invalidateState(addedPlugin ? 'ADD' : 'EDIT', data);
            return;
        }

        // istanbul ignore else
        if (!this._isReloading) {
            this.reloadBrowser(null, 300); // eslint-disable-line
        }
    },

    /**
     * Assigns an event handler to forms located in the toolbar
     * to prevent multiple submissions.
     *
     * @method preventSubmit
     */
    preventSubmit: function() {
        var forms = $('.cms-toolbar').find('form');
        var SUBMITTED_OPACITY = 0.5;

        forms.submit(function() {
            // show loader
            showLoader();
            // we cannot use disabled as the name action will be ignored
            $('input[type="submit"]')
                .on('click', function(e) {
                    e.preventDefault();
                })
                .css('opacity', SUBMITTED_OPACITY);
        });
    },

    /**
     * Sets csrf token header on ajax requests.
     *
     * @method csrf
     * @param {String} csrf_token
     */
    csrf: function(csrf_token) {
        $.ajaxSetup({
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrf_token);
            }
        });
    },

    /**
     * Sends or retrieves a JSON from localStorage
     * or the session (through synchronous ajax request)
     * if localStorage is not available. Does not merge with
     * previous setSettings calls.
     *
     * @method setSettings
     * @param {Object} newSettings
     * @returns {Object}
     */
    setSettings: function(newSettings) {
        // merge settings
        var settings = JSON.stringify($.extend({}, window.CMS.config.settings, newSettings));

        // use local storage or session
        if (this._isStorageSupported) {
            // save within local storage
            localStorage.setItem('cms_cookie', settings);
        } else {
            // save within session
            CMS.API.locked = true;
            showLoader();

            $.ajax({
                async: false,
                type: 'POST',
                url: window.CMS.config.urls.settings,
                data: {
                    csrfmiddlewaretoken: window.CMS.config.csrf,
                    settings: settings
                },
                success: function(data) {
                    CMS.API.locked = false;
                    // determine if logged in or not
                    settings = data ? JSON.parse(data) : window.CMS.config.settings;
                    hideLoader();
                },
                error: function(jqXHR) {
                    CMS.API.Messages.open({
                        message: jqXHR.responseText + ' | ' + jqXHR.status + ' ' + jqXHR.statusText,
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
     * Gets user settings (from localStorage or the session)
     * in the same way as setSettings sets them.
     *
     * @method getSettings
     * @returns {Object}
     */
    getSettings: function() {
        var settings;


        // use local storage or session
        if (this._isStorageSupported) {
            // get from local storage
            settings = JSON.parse(localStorage.getItem('cms_cookie') || 'null');
        } else {
            showLoader();
            CMS.API.locked = true;
            // get from session
            $.ajax({
                async: false,
                type: 'GET',
                url: window.CMS.config.urls.settings,
                success: function(data) {
                    CMS.API.locked = false;
                    // determine if logged in or not
                    settings = data ? JSON.parse(data) : window.CMS.config.settings;
                    hideLoader();
                },
                error: function(jqXHR) {
                    CMS.API.Messages.open({
                        message: jqXHR.responseText + ' | ' + jqXHR.status + ' ' + jqXHR.statusText,
                        error: true
                    });
                }
            });
        }

        // edit_off is a random flag that should be available on the page, but sometimes can
        // be not set when settings are carried over from pagetree
        if (
            (!settings || !currentVersionMatches(settings))
        ) {
            settings = this.setSettings(window.CMS.config.settings);
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
     * @param {Array[]} [params] array of [`param`, `value`] arrays to update the url
     * @returns {String}
     */
    makeURL: function makeURL(url, params = []) {
        let newUrl = new URL(URL.decode(url.replace(/&amp;/g, '&')));

        params.forEach(pair => {
            const [key, value] = pair;

            newUrl.removeSearch(key);
            newUrl.addSearch(key, value);
        });

        return newUrl
            .toString()
            .split('#')
            .map((part, i) => {
                return i === 0 ? part.replace(/&/g, '&amp;') : part;
            })
            .join('#');
    },

    /**
     * Browsers allow to "Prevent this page form creating additional
     * dialogs." checkbox which prevents further input from confirm messages.
     * This method falls back to "true" once the user chooses this option.
     *
     * @method secureConfirm
     * @param {String} message to be displayed
     * @returns {Boolean}
     */
    secureConfirm: function secureConfirm(message) {
        var start = Number(new Date());
        var result = confirm(message); // eslint-disable-line
        var end = Number(new Date());
        var MINIMUM_DELAY = 10;

        return end < start + MINIMUM_DELAY || result === true;
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
            // istanbul ignore next
            return false;
        }
    })(),

    /**
     * Adds an event listener to the "CMS".
     *
     * @method addEventListener
     * @param {String} eventName string containing space separated event names
     * @param {Function} fn callback to run when the event happens
     * @returns {jQuery}
     */
    addEventListener: function addEventListener(eventName, fn) {
        return CMS._eventRoot && CMS._eventRoot.on(_ns(eventName), fn);
    },

    /**
     * Removes the event listener from the "CMS". If a callback is provided - removes only that callback.
     *
     * @method removeEventListener
     * @param {String} eventName string containing space separated event names
     * @param {Function} [fn] specific callback to be removed
     * @returns {jQuery}
     */
    removeEventListener: function removeEventListener(eventName, fn) {
        return CMS._eventRoot && CMS._eventRoot.off(_ns(eventName), fn);
    },

    /**
     * Dispatches an event
     * @method dispatchEvent
     * @param {String} eventName event name
     * @param {Object} payload whatever payload required for the consumer
     * @returns {$.Event} event that was just triggered
     */
    dispatchEvent: function dispatchEvent(eventName, payload) {
        var event = new $.Event(_ns(eventName));

        CMS._eventRoot.trigger(event, [payload]);
        return event;
    },

    /**
     * Prevents scrolling with touch in an element.
     *
     * @method preventTouchScrolling
     * @param {jQuery} element element where we are preventing the scroll
     * @param {String} namespace so we don't mix events from two different places on the same element
     */
    preventTouchScrolling: function preventTouchScrolling(element, namespace) {
        element.on('touchmove.cms.preventscroll.' + namespace, function(e) {
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
    },

    /**
     * Returns window object.
     *
     * @method _getWindow
     * @private
     * @returns {Window}
     */
    _getWindow: function() {
        return window;
    },

    /**
     * We need to update the url with cms_path param for undo/redo
     *
     * @function updateUrlWithPath
     * @private
     * @param {String} url url
     * @returns {String} modified url
     */
    updateUrlWithPath: function(url) {
        var win = this._getWindow();
        var path = win.location.pathname + win.location.search;

        return this.makeURL(url, [['cms_path', path]]);
    }
};

/**
 * Provides key codes for common keys.
 *
 * @module CMS
 * @submodule CMS.KEYS
 * @example
 *     if (e.keyCode === CMS.KEYS.ENTER) { ... };
 */
export const KEYS = {
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
};

// shorthand for jQuery(document).ready();
$(function() {
    CMS._eventRoot = $('#cms-top');
    // autoinits
    Helpers.preventSubmit();
});

export default _CMS;
