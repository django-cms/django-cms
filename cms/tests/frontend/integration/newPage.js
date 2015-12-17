'use strict';

// #############################################################################
// Users managed via the admin panel

var globals = require('./settings/globals');
var messages = require('./settings/messages').users;

casper.test.begin('New Page Creation', function (test) {
    casper
        .start(globals.editUrl)
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            this.click('.cms-toolbar-item-navigation > li:nth-child(2) > a');
        })
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click('.cms-toolbar-item-navigation-hover li:first-child a');
        })
        .then(function () {
            this.click('.cms-toolbar-item-navigation-hover .cms-toolbar-item-navigation-hover li:first-child a');
        })
        .waitUntilVisible('.cms-modal', function () {
            test.assertVisible('.cms-modal', 'modal visible');

            this.click('.cms-modal .cms-btn-action');

        })
        .withFrame(0, function () {
            casper
                .waitForSelector('#page_form', function () {
                    test.assertExists('.errornote', 'failed to submit empty');
                });
        })
        .run(function () {
            test.done();
        });
});
