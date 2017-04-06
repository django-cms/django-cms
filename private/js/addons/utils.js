/*
 * Copyright (c) 2013, Divio AG
 * Licensed under BSD
 * http://github.com/divio/djangocms-boilerplate-webpack
 */

import $ from 'jquery';

/**
 * Localstorage shim from Modernizr
 *
 * @property {Boolean} isStorageSupported localstorage availability
 */
export const isStorageSupported = /*#__PURE__*/(function localStorageCheck () {
    var mod = 'modernizr';

    try {
        localStorage.setItem(mod, mod);
        localStorage.removeItem(mod);
        return true;
    } catch (e) {
        return false;
    }
})();

/**
 * Document setup for no javascript fallbacks and logging
 *
 * @method noscript
 * @private
 */
export function noscript () {
    // remove no-js class if javascript is activated
    $(document.body).removeClass('no-js');
}

/**
 * Simple redirection
 *
 * @method redirectTo
 * @param {String} url - URL string
 */
export function redirectTo (url) {
    window.location.href = url;
}

/**
 * Save information within local storage
 *
 * @method setStorage
 * @param {String} token - namespace
 * @param {String} value - storage value
 * @returns {Boolean|String} item value or negative result
 */
export function setStorage (token, value) {
    if (token && value && isStorageSupported) {
        localStorage.setItem(token, value);
        return value;
    }
    return false;
}

/**
 * Retrieve information from local storage
 *
 * @method getStorage
 * @param {String} token - namespace
 * @returns {Object|Boolean} localStorage item or negative result
 */
export function getStorage (token) {
    if (token && isStorageSupported) {
        return localStorage.getItem(token);
    }
    return false;
}
