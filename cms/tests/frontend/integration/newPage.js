'use strict';

// #############################################################################
// Users managed via the admin panel

var globals = require('./settings/globals');
var messages = require('./settings/messages').users;

casper.test.begin('New Page Creation', function (test) {
    casper
        .run(function () {
            test.done();
        });
});
