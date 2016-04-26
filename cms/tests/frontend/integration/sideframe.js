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
        // close default wizard modal
        .waitUntilVisible('.cms-modal', function () {
            this.click('.cms-modal .cms-modal-close');
        })
        .waitWhileVisible('.cms-modal', function () {
            // open "Example.com" menu
            this.click('.cms-toolbar-item-navigation li:first-child a');
        })
        // open "Administration"
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click('.cms-toolbar-item-navigation-hover a[href$="/admin/"]');
        })
        // wait until sideframe is open
        .waitUntilVisible('.cms-sideframe-frame', function () {
            test.assertVisible('.cms-sideframe-frame', 'The sideframe has been opened');
        })
        // wait until animation finishes
        .wait(300, function () {
            test.assertEvalEquals(function () {
                return $('.cms-sideframe').width();
            }, 1280 * 0.8, 'Sideframe opens with default width');
        })
        .then(function () {
            this.mouse.down('.cms-sideframe-resize');
            this.mouse.move(400, 200);
        })
        .then(function () {
            this.mouse.up(400, 200);
            test.assertEvalEquals(function () {
                return $('.cms-sideframe').width();
            }, 400, 'Sideframe can be resized');
        })
        // have to wait after resize for the changes being saved (default is 600ms)
        .wait(700)
        .then(function () {
            this.reload();
        })
        // wait until sideframe is fully visible after reload
        .waitUntilVisible('.cms-sideframe')
        .wait(300)
        .then(function () {
            test.assertEvalEquals(function () {
                return $('.cms-sideframe').width();
            }, 400, 'Sideframe width is remembered after reload');
        })
        .then(function () {
            this.click('.cms-sideframe .cms-icon-close');
        })
        .thenOpen(globals.baseUrl)
        .waitForSelector('.cms-toolbar-expanded', function () {
            test.assertNotVisible('.cms-sideframe-frame', 'The sideframe has been closed');
        })
        .run(function () {
            test.done();
        });
});
