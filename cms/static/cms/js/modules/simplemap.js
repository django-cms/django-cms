require('../polyfills/array.prototype.findindex');

/**
 * Simplistic `Map` implementation, without
 * all the power features.
 *
 * @class SimpleMap
 * @private
 */
var SimpleMap = function () {
    this._keys = [];
    this._values = [];
};

SimpleMap.prototype.set = function set(key, value) {
    var index = this._keys.findIndex(function (item) {
        return item === key;
    });

    if (index > -1) {
        this._keys[index] = key;
        this._values[index] = value;
    } else {
        this._keys.push(key);
        this._values.push(value);
    }
};

SimpleMap.prototype.get = function get(key) {
    var index = this._keys.findIndex(function (item) {
        return item === key;
    });

    return index > -1 ? this._values[index] : /* istanbul ignore next */ undefined;
};

SimpleMap.prototype.has = function has(key) {
    var index = this._keys.findIndex(function (item) {
        return item === key;
    });

    return index > -1;
};

module.exports = SimpleMap;
