'use strict';

// #############################################################################
// Handles test suite errors (assert and waitFor)

module.exports = {
    bind: function () {
        casper.on('step.error', function (error) {
            casper.die('assert failed: ' + error.message);
        });

        casper.on('waitFor.timeout', function (timeout, error) {
            if (error.selector) {
                casper.die('waitFor failed, couldn\'t find ' + error.selector + ' within ' + timeout + 'ms');
            } else if (error.visible) {
                casper.die('waitFor failed, couldn\'t find ' + error.visible + ' within ' + timeout + 'ms');
            } else {
                casper.die('waitFor failed with error', JSON.stringify(error, null, 4));
            }
        });
    }
};
