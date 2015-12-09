'use strict';

// #############################################################################
// Handles 404 and 500 pages

module.exports = {
    bind: function () {
        casper.on('http.status.404', function (resource) {
            casper.echo('404 page found: ' + resource.url, 'ERROR');
        });

        casper.on('http.status.500', function (resource) {
            casper.echo('500 page found: ' + resource.url, 'ERROR');
        });
    }
};
