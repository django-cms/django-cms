'use strict';

// #############################################################################
// Handles external resources load failures

module.exports = {
    bind: function () {
        casper.on('resource.error', function(resource) {
            resource.url && warningMessage('Resource failed to load: ' + resource.url);
        });
    }
};
