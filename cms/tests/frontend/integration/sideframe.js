'use strict';

// #############################################################################
// Admin panel opened in sideframe

var globals = require('./settings/globals');
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
            test.assertVisible('.cms-sideframe-frame', 'The sideframe has been opened');

            this.click('.cms-sideframe .cms-icon-close');
        })
        .waitForSelector('.cms-ready', function () {
            test.assertVisible('.cms-sideframe-frame', 'The sideframe remains open on page reload');
        })
        .thenOpen(globals.baseUrl)
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            test.assertNotVisible('.cms-sideframe-frame', 'The sideframe has been closed');
        })
        .run(function () {
            test.done();
        });
});
