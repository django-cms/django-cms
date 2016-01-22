'use strict';

// #############################################################################
// Page tree functionality

var globals = require('./settings/globals');
var casperjs = require('casper');
var cms = require('./helpers/cms')(casperjs);
var xPath = casperjs.selectXPath;

var closeWizard = function () {
    return function () {
        // close default wizard modal
        return this.waitUntilVisible('.cms-modal', function () {
            this.click('.cms-modal .cms-modal-close');
        })
        .waitWhileVisible('.cms-modal');
    };
};

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

casper.test.begin('Shows a message when there are no pages', function (test) {
    casper
        .start(globals.baseUrl)
        .then(closeWizard())
        .then(cms.openSideframe())
        .then(function () {
            test.assertVisible('.cms-sideframe-frame', 'The sideframe has been opened');
        })
        // switch to sideframe
        .withFrame(0, function () {
            casper.waitForSelector('#changelist-form', function () {
                test.assertSelectorHasText(
                    '#changelist-form',
                    'There is no page around yet.',
                    'Shows correct message if there are not pages yet'
                );
            });
        })
        .run(function () {
            test.done();
        });
});

casper.test.begin('Pages can be added through the page tree', function (test) {
    casper
        .start(globals.baseUrl)
        .then(closeWizard())
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function () {
            casper.waitForSelector('#changelist-form', function () {
                this.click('#changelist-form .addlink');
            })
            .waitForSelector('#page_form', function () {
                this.sendKeys('#id_title', 'Homepage');
                this.click('input[name="_save"]');
            })
            .waitUntilVisible('.success')
            .then(function () {
                var pageId = cms.getPageId('Homepage');
                test.assertExists(
                    xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]'),
                    'Page was successfully added'
                );
                test.assertExists(
                    '.cms-tree-item-lang a[href*="' + pageId + '"] span.published',
                    'Page is published by default'
                );
                // add nested page
                this.click('a[href*="/admin/cms/page/add/?target=' + pageId + '"]');
            })
            .waitForSelector('#page_form', function () {
                this.sendKeys('#id_title', 'Nested page');
                this.click('input[name="_save"]');
            })
            .waitUntilVisible('.success')
            .then(cms.expandPageTree())
            .then(function () {
                var pageId = cms.getPageId('Nested page');
                test.assertExists(
                    xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Nested page")]'),
                    'Nested page was successfully added'
                );
                test.assertExists(
                    xPath('//a[contains(text(), "Homepage")]' +
                          '/following-sibling::ul[contains(@class, "jstree-children")]' +
                          '[./li/a[contains(@class, "jstree-anchor")][contains(text(), "Nested page")]]'),
                    'Newly created page is indeed nested'
                );
                test.assertExists(
                    '.cms-tree-item-lang a[href*="' + pageId + '"] span.empty',
                    'Nested page is not published'
                );
            });
        })
        .then(cms.removePage({ title: 'Homepage' }))
        .run(function () {
            test.done();
        });
});
