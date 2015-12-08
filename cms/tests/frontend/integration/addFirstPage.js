'use strict';

// #############################################################################
// Create the first page

var globals = require('./settings/globals');
var messages = require('./settings/messages').page;

casper.test.begin('Add First Page', function (test) {
    casper
        .run(function () {
            test.done();
        });
});
