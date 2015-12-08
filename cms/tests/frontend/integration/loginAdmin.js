'use strict';

// #############################################################################
// User login via the admin panel

var globals = require('./settings/globals');
var messages = require('./settings/messages').login;

casper.test.begin('User Login (via Admin)', function (test) {
    casper
        .run(function () {
            test.done();
        });
});
