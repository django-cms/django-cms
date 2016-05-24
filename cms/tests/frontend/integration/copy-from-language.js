'use strict';

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings.configure({
    editOn: 'test-edit'
});
var casperjs = require('casper');
var cms = helpers(casperjs, globals);

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        .then(cms.addPlugin({
            type: 'TextPlugin',
            content: {
                id_body: 'Test text'
            }
        }))
        .run(done);
});

casper.test.tearDown(function (done) {
    casper.start()
        .then(cms.removePage())
        .then(cms.logout())
        .run(done);
});

casper.test.begin('Plugins can be copied from same page in a different language', function (test) {
    var pageId;

    casper.start()
        .thenOpen(globals.adminPagesUrl)
        .waitForSelector('.cms-pagetree')
        .then(cms.waitUntilAllAjaxCallsFinish())
        .wait(1000, function () {
            pageId = cms.getPageId('First page');
        })
        .then(function () {
            this.click('.js-cms-tree-advanced-settings[href*="' + pageId + '"]');
        })
        .waitUntilVisible('#page_form', function () {
            this.click('#itbutton');
        })
        .waitForSelector('#itbutton.selected', function () {
            this.sendKeys('#id_title', 'Prima pagina');
            this.click('input[name="_save"]');
        })
        .waitUntilVisible('.success')
        .then(cms.publishPage({ page: 'First page', language: 'en' }))
        .then(cms.publishPage({ page: 'First page', language: 'it' }))
        .then(function () {
            this.open(globals.baseUrl.replace('en', 'it') + '?test-edit');
        })
        .waitForSelector('.cms-toolbar-expanded', function () {
            test.assertElementCount('.cms-plugin', 0, 'No plugins on italian page');
        })
        .then(cms.switchTo('structure'))
        .waitUntilVisible('.cms-structure', function () {
            this.click('.cms-structure .cms-submenu-settings');
        })
        .waitUntilVisible('.cms-submenu-dropdown', function () {
            this.click('.cms-submenu-dropdown [data-rel="copy-lang"]');
        })
        .waitForResource(/copy-plugins/)
        .waitForUrl(/\//)
        .waitForSelector('.cms-toolbar-expanded', function () {
            test.assertElementCount('.cms-plugin', 1, 'Plugin was copied from english page');
            test.assertSelectorHasText('.cms-plugin', 'Test text', 'Plugin was copied from english page');
        })
        .run(function () {
            test.done();
        });
});
