'use strict';

// #############################################################################
// User login via the CMS toolbar

var globals = require('./settings/globals');
var messages = require('./settings/messages').login.toolbar;

casper.test.begin('User Login (via Toolbar)', function (test) {
    casper
        .run(function () {
            test.done();
        });
});
