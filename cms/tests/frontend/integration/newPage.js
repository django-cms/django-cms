'use strict';

// #############################################################################
// Users managed via the admin panel

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var randomString = helpers.randomString;
var cms = helpers();

var newPageTitle = randomString({ length: 50, withWhitespaces: false });

casper.test.setUp(function(done) {
    casper.start().then(cms.login()).then(cms.addPage({ title: 'First page' })).run(done);
});

casper.test.tearDown(function(done) {
    casper
        .start()
        .then(cms.removePage({ title: newPageTitle }))
        .then(cms.removePage({ title: 'First page' })) // removing both pages
        .then(cms.logout())
        .run(done);
});

casper.test.begin('New Page Creation', function(test) {
    casper
        .start(globals.editUrl)
        .waitForSelector('.cms-toolbar-expanded', function() {
            this.click('.cms-toolbar-item-navigation > li:nth-child(2) > a');
        })
        .waitForSelector('.cms-toolbar-item-navigation-hover', function() {
            this.click('.cms-toolbar-item-navigation-hover li:first-child a');
        })
        .then(function() {
            this.click('.cms-toolbar-item-navigation-hover .cms-toolbar-item-navigation-hover li:first-child a');
        })
        .waitUntilVisible('.cms-modal', function() {
            test.assertVisible('.cms-modal', 'The modal to add page is available');

            this.click('.cms-modal .cms-btn-action');
        })
        .withFrame(0, function() {
            casper.waitForSelector('#page_form', function() {
                test.assertExists('.errornote', 'Error message shows up if no data has been entered');

                this.fill(
                    '#page_form',
                    {
                        title: newPageTitle,
                        slug: newPageTitle
                    },
                    true
                );
            });
        })
        .waitForSelector('.cms-ready', function() {
            test.assertTitleMatch(new RegExp(newPageTitle), 'The new page has been created');
        })
        .run(function() {
            test.done();
        });
});
