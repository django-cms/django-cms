'use strict';

// #############################################################################
// User logout

var globals = require('./settings/globals');
var messages = require('./settings/messages').logout;

casper.test.begin('User Logout', function (test) {
    casper
        .run(function () {
            test.done();
        });
});
