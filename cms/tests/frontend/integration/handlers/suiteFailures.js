'use strict';

// #############################################################################
// Handles test suite errors (assert and waitFor)

module.exports = {
    bind: function () {
        casper.on('step.error', function (error) {
            casper.die('assert failed: ' +  error.result.standard);
        });

        casper.on('waitFor.timeout', function (timeout, error) {
            casper.die('waitFor failed, couldn\'t find ' + error.selector + ' within ' + timeout + 'ms');
        });
    }
};
