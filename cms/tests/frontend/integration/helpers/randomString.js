'use strict';

module.exports.randomString = function (length, onlyDigits) {
    var stringLength = length || 6;
    var randomString = '';
    var possibleCharacters = '0123456789';
    if (stringLength <= 0) {
        return '';
    }

    if (!onlyDigits) {
        possibleCharacters += 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
    }

    for (var i = 0; i < stringLength; i++) {
        randomString += possibleCharacters.charAt(Math.floor(Math.random() * possibleCharacters.length));
    }
    return randomString;
}
