'use strict';
// #############################################################################
// Admin panel opened in sideframe

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers();

casper.test.setUp(function(done) {
    casper.start().then(cms.login()).run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.logout()).run(done);
});

casper.test.begin('Sideframe', function(test) {
    casper
        .start(globals.baseUrl)
        // close default wizard modal
        .waitUntilVisible('.cms-modal', function() {
            this.click('.cms-modal .cms-modal-close');
        })
        .waitWhileVisible('.cms-modal', function() {
            // open "Example.com" menu
            this.click('.cms-toolbar-item-navigation li:first-child a');
        })
        // open "Administration"
        .waitForSelector('.cms-toolbar-item-navigation-hover', function() {
            this.click('.cms-toolbar-item-navigation-hover a[href$="/admin/"]');
        })
        // wait until sideframe is open
        .waitUntilVisible('.cms-sideframe-frame', function() {
            test.assertVisible('.cms-sideframe-frame', 'The sideframe has been opened');
        })
        // wait until animation finishes
        .wait(300, function() {
            test.assertEvalEquals(
                function() {
                    return CMS.$('.cms-sideframe').width();
                },
                1280 * 0.95,
                'Sideframe opens with default width'
            );
        })
        // changes viewport to mobile
        .then(function() {
            this.viewport(767, 1024);
        })
        // checks current mobile width to be equal with sideframe width
        .wait(300, function() {
            test.assertEvalEquals(
                function() {
                    return CMS.$('.cms-sideframe').width();
                },
                767,
                'Sideframe is fullwidth with on mobile'
            );
        })
        // changes back to default width
        .then(function() {
            this.viewport(1280, 1024);
        })
        .then(function() {
            this.reload();
        })
        // wait until sideframe is fully visible after reload
        .waitUntilVisible('.cms-sideframe')
        .wait(300)
        .then(function() {
            test.assertVisible('.cms-sideframe', 'Sideframe is open after reload');
        })
        .then(function() {
            this.click('.cms-sideframe .cms-icon-close');
        })
        .thenOpen(globals.baseUrl)
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertNotVisible('.cms-sideframe-frame', 'The sideframe has been closed');
        })
        .viewport(1280, 1024)
        .run(function() {
            test.done();
        });
});
