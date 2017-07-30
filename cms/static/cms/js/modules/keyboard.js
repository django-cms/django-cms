import keyboard from 'keyboardjs';
import $ from 'jquery';

/**
 * @function override
 * @private
 * @param {Function} originalFunction to override
 * @param {Function} functionBuilder function that accepts a function to wrap
 * @returns {Function}
 */
function override(originalFunction, functionBuilder) {
    var newFn = functionBuilder(originalFunction);

    newFn.prototype = originalFunction.prototype;
    return newFn;
}

/**
 * Override keyboardjs methods to disallow running callbacks
 * if input is focused
 */
keyboard._applyBindings = override(keyboard._applyBindings, function(originalBind) {
    return function(event) {
        if ($(':focus').is('input, textarea, select, [contenteditable]')) {
            return true;
        }

        originalBind.call(this, event);
    };
});

export default keyboard;
