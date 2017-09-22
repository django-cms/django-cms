'use strict';

// #############################################################################
// Switch language via the admin panel

var casperjs = require('casper');
var helpers = require('djangocms-casper-helpers');
var randomString = helpers.randomString;
var globals = helpers.settings;
var cms = helpers(casperjs);
var xPath = casperjs.selectXPath;

// random text string for filtering and content purposes
var randomText = randomString({ length: 50, withWhitespaces: false });
// No Preview Template text
var noPreviewText = 'This page has no preview';

casper.test.setUp(function(done) {
    casper.start().then(cms.login()).then(cms.addPage({ title: 'First page' })).run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.removePage()).then(cms.logout()).run(done);
});

casper.test.begin('Switch language', function(test) {
    casper
        .start(globals.editUrl)
        // click on language bar
        .waitForSelector('.cms-toolbar-expanded', function() {
            this.click(xPath(cms.createToolbarItemXPath('Language')));
        })
        // select german language
        .waitUntilVisible('.cms-toolbar-item-navigation-hover ul', function() {
            this.click('.cms-toolbar-item-navigation-hover a[href="/de/"]');
        })
        // no page should be here (warning message instead)
        .wait(300)
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertSelectorHasText('.cms-screenblock-inner h1', noPreviewText, "This page isn't available");
            this.click(xPath(cms.createToolbarItemXPath('Language')));
        })
        // add german translation
        .waitUntilVisible('.cms-toolbar-item-navigation-hover ul', function() {
            this.click('.cms-toolbar-item-navigation-hover a[href*="?language=de"]');
        })
        // open Change pane modal and fill with data
        .waitUntilVisible('.cms-modal-open')
        .withFrame(0, function() {
            this.fill('#page_form', {
                title: randomText,
                slug: randomText
            });
        })
        // submit Change pane modal
        .then(function() {
            this.click('.cms-modal-open .cms-modal-item-buttons .cms-btn-action');
        })
        // check if german version appears
        .waitWhileVisible('.cms-modal-open', function() {
            test.assertSelectorHasText('ul.nav > .child > a[href="/de/"]', randomText, 'New translation page appears');
        })
        // click on language bar
        .waitForSelector('.cms-toolbar-expanded', function() {
            this.click(xPath(cms.createToolbarItemXPath('Language')));
        })
        // delete german translation
        .waitUntilVisible('.cms-toolbar-item-navigation-hover ul', function() {
            this.click('.cms-toolbar-item-navigation-hover a[href*="delete-translation/?language=de"]');
        })
        // submit translation deletion
        .waitUntilVisible('.cms-modal-open', function() {
            this.click('.cms-modal-open .cms-modal-item-buttons .cms-btn.deletelink');
        })
        // make sure translation has been deleted
        .waitWhileVisible('.cms-modal-open', function() {
            test.assertSelectorHasText('.cms-screenblock-inner h1', noPreviewText, "This page isn't available");
        })
        .run(function() {
            test.done();
        });
});
