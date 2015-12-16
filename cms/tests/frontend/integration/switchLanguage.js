'use strict';

// #############################################################################
// Switch language via the admin panel

var globals = require('./settings/globals');
var messages = require('./settings/messages').page.switchLanguage;
var randomString = require('./helpers/randomString').randomString;

// random text string for filtering and content purposes
var randomText = randomString(10);

casper.test.begin('Switch language', function (test) {
    casper
        .start(globals.editUrl)
        // click on language bar
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            this.click('.cms-toolbar-item-navigation > li:nth-child(4) > a');
        })
        // select german language
        .waitUntilVisible('.cms-toolbar-item-navigation > li:nth-child(4) > ul', function () {
            this.click('.cms-toolbar-item-navigation-hover a[href="/de/"]');
        })
        // no page should be here (warning message instead)
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            test.assertSelectorHasText('.cms-screenblock-inner h1', 'This page has no preview', messages.noContentPreview);
            this.click('.cms-toolbar-item-navigation > li:nth-child(4) > a');
        })
        // add german translation
        .waitUntilVisible('.cms-toolbar-item-navigation > li:nth-child(4) > ul', function () {
            this.click('.cms-toolbar-item-navigation-hover a[href*="?language=de"]');
        })
        // open Change pane modal
        .waitUntilVisible('.cms-modal-open', function () {
            this.page.switchToChildFrame(0);
            this.fill('#page_form', {
                'title': randomText,
                'slug': randomText
            });
            this.page.switchToParentFrame();
            this.click('.cms-modal-open .cms-modal-item-buttons .cms-btn-action')
        })
        // check if german version appears
        .waitWhileVisible('.cms-modal-open', function () {
            test.assertSelectorHasText('ul.nav > .child > a[href="/de/"]', randomText, messages.newContentAvailable);
        })
        // click on language bar
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            this.click('.cms-toolbar-item-navigation > li:nth-child(4) > a');
        })
        // delete german translation
        .waitUntilVisible('.cms-toolbar-item-navigation > li:nth-child(4) > ul', function () {
            this.click('.cms-toolbar-item-navigation-hover a[href*="delete-translation/?language=de"]');
        })
        // submit translation deletion
        .waitUntilVisible('.cms-modal-open', function () {
            this.click('.cms-modal-open .cms-modal-item-buttons .cms-btn.deletelink')
        })
        // make sure translation has been deleted
        .waitWhileVisible('.cms-modal-open', function () {
            test.assertSelectorHasText('.cms-screenblock-inner h1', 'This page has no preview', messages.noContentPreview);
        })
        .run(function () {
            test.done();
        });
});
