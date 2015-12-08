'use strict';

// #############################################################################
// Init all settings on suite start

require('./../casperjs.conf').init();

// #############################################################################
// User login via the CMS toolbar

var globals = require('./settings/globals');
var messages = require('./settings/messages').login;

casper.test.begin('User Login (via Toolbar)', function (test) {
    casper
        .start(globals.baseUrl, function () {
            var titleRegExp = new RegExp(globals.websiteName, 'g');

            test.assertTitleMatch(titleRegExp, messages.cmsAvailable);
            test.assertDoesntExist('.cms-toolbar', messages.toolbarMissing);
        })
        .thenOpen(globals.editUrl, function () {
            test.assertExists('.cms-toolbar', messages.toolbarAvailable);

            casper.fill('.cms-form-login', globals.credentials, true);
        })
        .waitForSelector('.cms-toolbar', function () {
            test.assertExists('.cms-toolbar-item-navigation', messages.loginOk);
        })
        .run(function () {
            test.done();
        });
});
