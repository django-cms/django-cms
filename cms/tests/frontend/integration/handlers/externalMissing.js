'use strict';

// #############################################################################
// Handles external resources load failures

module.exports = {
    bind: function () {
        casper.on('resource.error', function (resource) {
            casper.echo('Resource failed to load: ' + resource.url, 'ERROR');
        });
    }
};
