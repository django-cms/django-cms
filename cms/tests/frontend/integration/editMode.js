'use strict';

// #############################################################################
// Users managed via the admin panel

var globals = require('./settings/globals');
var messages = require('./settings/messages').page.editMode;
var content = require('./settings/globals').content.page;

var cms = require('./helpers/cms')();

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
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            test.assertExists('.cms-btn-switch-edit', messages.editOff);
            this.click('.cms-btn-switch-edit');
        })
        // checking the mode after clicking on toolbar "Edit" button
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            test.assertExists('.cms-toolbar-item-switch-save-edit', messages.editOnByEditButton);
        })
        // going back to edit off mode and opening the "Page" menu item
        .thenOpen(globals.editOffUrl)
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            test.assertExists('.cms-btn-switch-edit', messages.editOff);
            this.click('.cms-toolbar-item-navigation > li:nth-child(2) > a');
        })
        // opening "Edit this Page" menu item
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click('.cms-toolbar-item-navigation-hover a[href$="?edit"]');
        })
        // checking the mode after clicking on "Page -> Edit this Page"
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            test.assertExists('.cms-toolbar-item-switch-save-edit', messages.editOnByNav);
        })
        .run(function () {
            test.done();
        });
});
