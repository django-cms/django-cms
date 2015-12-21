'use strict';

/**
 * Generates random strings
 * @param {Number} [opts.length=6] - length of the string to produce
 * @param {Boolean} [opts.onlyDigits=false] - make helper return string containing numbers only
 * @param {Boolean} [opts.withWhitespaces=false] - make helper return string containing numbers only
 *
 * @returns {String} randomString
 */
module.exports.randomString = function (options) {
    // defaults
    options = options || {};
    var stringLength = options.length || 6;
    var onlyDigits = options.onlyDigits || false;
    var withWhitespaces = options.withWhitespaces || false;

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
