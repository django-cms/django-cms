'use strict';

// #############################################################################
// Init all settings on suite start

require('./../casperjs.conf').init();

// #############################################################################
// User login

var globals = require('/settings/globals.js');
var messages = require('/settings/messages.js').login;

casper.test.begin('User Login', function (test) {
    casper
        .start(globals.baseUrl, function () {
            test.assertTitle('home - example.com', messages.cmsAvailable);
            test.assertDoesntExist('.cms-toolbar', messages.toolbalMissing);
        })
        .thenOpen(globals.editUrl, function () {
            test.assertExists('.cms-toolbar', messages.toolbalAvailable);

            casper.fill('.cms-form-login', globals.credentials, true);
        })
        .waitForSelector('.cms-toolbar', function () {
            test.assertExists('.cms-toolbar-item-navigation', messages.loginOk);
        })
        .run(function () {
            test.done();
        });
});
