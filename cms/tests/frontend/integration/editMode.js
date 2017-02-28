'use strict';

// #############################################################################
// Users managed via the admin panel

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var content = globals.content.page;
var cms = helpers();

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        .then(cms.addPage({ title: content.title }))
        .run(done);
});

casper.test.tearDown(function (done) {
    casper.start()
        .then(cms.removePage())
        .then(cms.logout())
        .run(done);
});

casper.test.begin('Opening Page in Edit Mode', function (test) {
    casper
        // opening the page in edit off mode
        .start(globals.editOffUrl)
        .waitForSelector('.cms-toolbar-expanded', function () {
            test.assertExists('.cms-btn-switch-edit', 'The page is on edit off mode');
            this.click('.cms-btn-switch-edit');
        })
        // checking the mode after clicking on toolbar "Edit" button
        .waitForSelector('.cms-toolbar-expanded', function () {
            test.assertExists('.cms-toolbar-item-switch-save-edit',
                'The page is in edit mode after clicking on edit button');
        })
        // going back to edit off mode and opening the "Page" menu item
        .thenOpen(globals.editOffUrl)
        .waitForSelector('.cms-toolbar-expanded', function () {
            test.assertExists('.cms-btn-switch-edit', 'The page is on edit off mode');
            this.click('.cms-toolbar-item-navigation > li:nth-child(2) > a');
        })
        // opening "Edit this Page" menu item
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click('.cms-toolbar-item-navigation-hover a[href$="?edit"]');
        })
        // checking the mode after clicking on "Page -> Edit this Page"
        .waitForSelector('.cms-toolbar-expanded', function () {
            test.assertExists('.cms-toolbar-item-switch-save-edit',
                'The page is in edit mode after clicking Page -> Edit this Page');
        })
        .run(function () {
            test.done();
        });
});
