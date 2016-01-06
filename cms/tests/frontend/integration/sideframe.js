'use strict';

// #############################################################################
// Admin panel opened in sideframe

var globals = require('./settings/globals');
var messages = require('./settings/messages').sideframe;
var cms = require('./helpers/cms')();

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        .run(done);
});

casper.test.tearDown(function (done) {
    casper.start()
        .then(cms.logout())
        .run(done);
});

casper.test.begin('Sideframe', function (test) {
    casper
        .start(globals.baseUrl)
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            this.click('.cms-toolbar-item-navigation li:first-child a');
        })
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click('.cms-toolbar-item-navigation-hover a[href$="/admin/"]');
        })
        .waitUntilVisible('.cms-sideframe-frame', function () {
            test.assertVisible('.cms-sideframe-frame', messages.sideframeOpened);

            this.click('.cms-sideframe .cms-icon-close');
        })
        .waitForSelector('.cms-ready', function () {
            test.assertVisible('.cms-sideframe-frame', messages.sideframeRemainsOpen);
        })
        .thenOpen(globals.baseUrl)
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            test.assertNotVisible('.cms-sideframe-frame', messages.sideframeClosed);
        })
        .run(function () {
            test.done();
        });
});
