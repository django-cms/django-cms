'use strict';

// #############################################################################
// Change Settings behaviour

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var casperjs = require('casper');
var xPath = casperjs.selectXPath;
var cms = helpers(casperjs);

casper.test.setUp(function(done) {
    casper
        .start()
        .then(cms.login())
        .then(cms.addPage({ title: 'home' }))
        .then(
            cms.addPlugin({
                type: 'TextPlugin',
                content: {
                    id_body: 'Dummy to create history'
                }
            })
        )
        .then(
            cms.addPlugin({
                type: 'TextPlugin',
                content: {
                    id_body: 'Test-text'
                }
            })
        )
        .run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.removePage()).then(cms.logout()).run(done);
});

casper.test.begin('History', function(test) {
    casper
        .start(globals.editUrl)
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertElementCount(
                '.cms-dragarea:nth-child(1) > .cms-draggables > .cms-draggable',
                2,
                'Both plugins are in first placeholder'
            );

            // click on History
            this.click(
                // mouse clicks on the History link
                xPath('//a[.//span[text()[contains(.,"History")]]]')
            );
        })
        // click on Undo
        .wait(10, function() {
            this.click(
                // mouse clicks on the Undo link
                xPath('//a[.//span[text()[contains(.,"Undo")]]]')
            );
        })
        .waitForResource(/undo/)
        .wait(1500)
        .waitForSelector('.cms-toolbar-expanded', function() {
            // Counts plugins in the first placeholder if there's only one
            test.assertElementCount(
                '.cms-dragarea:nth-child(1) > .cms-draggables > .cms-draggable',
                1,
                'Second plugin is removed'
            );

            // click on History
            this.click(
                // mouse clicks on the History link
                xPath('//a[.//span[text()[contains(.,"History")]]]')
            );
        })
        // click on Redo
        .wait(10, function() {
            this.click(
                // mouse clicks on the Redo link
                xPath('//a[.//span[text()[contains(.,"Redo")]]]')
            );
        })
        // Clicking again on redo after resource have been loaded
        .waitForResource(/redo/)
        .wait(1000)
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertElementCount(
                '.cms-dragarea:nth-child(1) > .cms-draggables > .cms-draggable',
                2,
                'Both Plugin are back'
            );
            this.click('.cms-toolbar-item-navigation > li:nth-child(3) > a');
        })
        // Clicks on View history
        .wait(10, function() {
            this.click(
                // mouse clicks on the redo link
                xPath('//a[.//span[text()[contains(.,"View history...")]]]')
            );
        })
        .wait(1000)
        // Wait for modal
        .withFrame(0, function() {
            casper
                .waitForSelector('#change-history', function() {
                    test.assertExists('#change-history', 'The page creation wizard form is available');
                    // clicks on the second row of the history table (which had one plugin)
                    this.click('tr:nth-child(2) th a ');
                })
                // waits that the form gets loaded
                .waitForSelector('#page_form', function() {
                    test.assertExists('#page_form', 'Page Form loaded');
                });
        })
        // clicks on the save button
        .then(function() {
            this.click('.cms-modal-item-buttons .cms-btn-action');
        })
        // counts again that there is only one plugin
        .waitForResource(/cms\/page\/\d+\/history/)
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertElementCount(
                '.cms-dragarea:nth-child(1) > .cms-draggables > .cms-draggable',
                1,
                'History reverted'
            );
        })
        .run(function() {
            test.done();
        });
});
