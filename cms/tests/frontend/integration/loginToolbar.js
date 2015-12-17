'use strict';

// #############################################################################
// User login via the CMS toolbar

var globals = require('./settings/globals');
var messages = require('./settings/messages').login.toolbar;

casper.test.begin('User Login (via Toolbar)', function (test) {
    casper
        .start(globals.editUrl)
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            test.assertExists('.cms-toolbar .cms-form-login', messages.toolbarAvailable);

            this.fill('.cms-form-login', globals.credentials, true);
        })
        .waitForSelector('.cms-ready', function () {
            test.assertExists('.cms-toolbar-item-navigation', messages.loginOk);
        })
        .run(function () {
            test.done();
        });
});
