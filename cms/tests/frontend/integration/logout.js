'use strict';

// #############################################################################
// User logout

var globals = require('./settings/globals');
var messages = require('./settings/messages').logout;

casper.test.begin('User Logout', function (test) {
    casper
        /*
        TODO figure out why doesn't toolbar collapse
        .start(globals.editUrl, function () {
            casper.click('.cms-toolbar-item-navigation li:first-child a');
        })
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            casper.click('.cms-toolbar-item-navigation-hover ul li:last-child a');
        })
        .waitForSelector('body', function () {
            test.assertDoesntExist('.cms-toolbar', messages.logoutOk);
        })
        .thenOpen(globals.editUrl, function () {
            test.assertExists('.cms-toolbar', messages.toolbarOpened);
        })
        .thenOpen(globals.editOffUrl, function () {
            test.assertDoesntExist('.cms-toolbar', messages.toolbarClosed);
        })
        */
        .run(function () {
            test.done();
        });
});
