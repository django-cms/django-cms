'use strict';

/**
 * Generates random strings
 * @param {Object} [options] options
 * @param {Number} [options.length=6] length of the string to produce
 * @param {Boolean} [options.onlyDigits=false] make helper return string containing numbers only
 * @param {Boolean} [options.withWhitespaces=false] make helper return string containing numbers only
 * @returns {String} randomString
 */
module.exports.randomString = function (options) {
    // defaults
    var opts = options || {};
    var stringLength = opts.length || 6;
    var onlyDigits = opts.onlyDigits || false;
    var withWhitespaces = opts.withWhitespaces || false;

    var randomString = '';
    var possibleCharacters = '0123456789';

    if (stringLength <= 0) {
        return '';
    }
    if (!onlyDigits) {
        possibleCharacters += 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
    }
    if (withWhitespaces) {
        possibleCharacters += ' ';
    }
    for (var i = 0; i < stringLength; i++) {
        randomString += possibleCharacters.charAt(Math.floor(Math.random() * possibleCharacters.length));
    }

    return randomString;
};
