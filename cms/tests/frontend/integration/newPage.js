'use strict';

// #############################################################################
// Users managed via the admin panel

var globals = require('./settings/globals');
var messages = require('./settings/messages').page.creation.toolbar;
var randomString = require('./helpers/randomString').randomString;
var cms = require('./helpers/cms')();

var newPageTitle = randomString({ length: 50, withWhitespaces: false });

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login)
        .then(cms.addPage({ title: 'First page' }))
        .run(done);
});

casper.test.tearDown(function (done) {
    casper.start()
        .then(cms.removePage({ title: newPageTitle }))
        .then(cms.removePage({ title: 'First page' })) // removing both pages
        .then(cms.logout)
        .run(done);
});

casper.test.begin('New Page Creation', function (test) {
    casper
        .start(globals.editUrl)
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            this.click('.cms-toolbar-item-navigation > li:nth-child(2) > a');
        })
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click('.cms-toolbar-item-navigation-hover li:first-child a');
        })
        .then(function () {
            this.click('.cms-toolbar-item-navigation-hover .cms-toolbar-item-navigation-hover li:first-child a');
        })
        .waitUntilVisible('.cms-modal', function () {
            test.assertVisible('.cms-modal', messages.modalOpened);

            this.click('.cms-modal .cms-btn-action');
        })
        .withFrame(0, function () {
            casper
                .waitForSelector('#page_form', function () {
                    test.assertExists('.errornote', messages.addFail);

                    this.fill('#page_form', {
                        'title': newPageTitle,
                        'slug': newPageTitle
                    }, true);
                });
        })
        .waitForSelector('.cms-ready', function () {
            test.assertTitleMatch(new RegExp(newPageTitle), messages.addOk);
        })
        .run(function () {
            test.done();
        });
});
