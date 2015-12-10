'use strict';

// #############################################################################
// CasperJS options

module.exports = {
    init: function () {
        this.viewportSize();
        this.timeout();
    },

    viewportSize: function (width, height) {
        var viewportWidth = width || 1280;
        var viewportHeight = height || 1024;

        casper.echo('Current viewport size is ' + viewportWidth + 'x' + viewportHeight + '.', 'INFO');

        casper.options.viewportSize = {
            width: viewportWidth,
            height: viewportHeight
        };
    },

    timeout: function (timeout) {
        casper.options.pageSettings.resourceTimeout = timeout || 10000;
    }
};
