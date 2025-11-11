import keyboard from 'keyboardjs';

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
 * Check if the currently focused element is an input field
 * @returns {boolean}
 */
function isInputFocused() {
    const activeElement = document.activeElement;

    if (!activeElement) {
        return false;
    }

    const tagName = activeElement.tagName.toLowerCase();
    const isContentEditable = activeElement.contentEditable === 'true';

    return tagName === 'input' ||
           tagName === 'textarea' ||
           tagName === 'select' ||
           isContentEditable;
}

/**
 * Override keyboardjs methods to disallow running callbacks
 * if input is focused
 */
keyboard._applyBindings = override(keyboard._applyBindings, function(originalBind) {
    return function(event) {
        if (isInputFocused()) {
            return true;
        }

        originalBind.call(this, event);
    };
});

export default keyboard;
