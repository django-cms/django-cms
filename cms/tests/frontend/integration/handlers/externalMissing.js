'use strict';

// #############################################################################
// Handles external resources load failures

module.exports = {
    bind: function () {
        casper.on('resource.error', function (resource) {
            casper.echo('Resource failed to load', 'ERROR');
            casper.echo(JSON.stringify(resource, null, 4));
        });
    }
};
