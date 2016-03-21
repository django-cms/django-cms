'use strict';

// #############################################################################
// Handles JavaScript page errors

module.exports = {
    bind: function () {
        casper.on('page.error', function (msg) {
            casper.echo('Error on page: ' + JSON.stringify(msg), 'ERROR');
        });
    }
};
