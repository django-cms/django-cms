'use strict';

// #############################################################################
// Change Settings behaviour

var globals = require('./settings/globals');
var casperjs = require('casper');
var cms = require('./helpers/cms')(casperjs);

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        .then(cms.addPage({ title: 'spaceSwitch' }))
        .then(cms.addPlugin({
            type: 'TextPlugin',
            content: {
                id_body: 'sample text'
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

casper.test.begin('Switch mode with space', function (test) {
    casper
        .start(globals.editUrl)
        // publishes page
        .waitForSelector('.cms-btn-publish-active', function () {
            this.click('.cms-btn-publish-active');
        })
        .waitForResource(/publish/)
        .waitWhileVisible('.cms-toolbar-expanded')
        .waitForSelector('.cms-toolbar-expanded', function () {
            test.assertExist('.cms-btn-switch-edit', 'published page');
            // clicks on edit mode
            this.click('.cms-btn-switch-edit');
        })
        // counts the element in structure mode
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            test.assertElementCount(
                '.cms-dragarea:nth-child(1) > .cms-draggables > .cms-draggable',
                1,
                'plugin is created'
            );
        })
        .then(function () {
            // triggers space
            this.sendKeys('html', casper.page.event.key.Space);
            // checks the name of the page which gets shown only on content mode
            test.assertEquals(this.fetchText('.nav li a'),
            'spaceSwitch', 'switch via space worked');
        })
        .then(function () {
            // triggers space again
            this.sendKeys('html', casper.page.event.key.Space);
        })
            // counts the placeholder
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            test.assertElementCount(
                '.cms-dragarea:nth-child(1) > .cms-draggables > .cms-draggable',
                1,
                'switched back to structure'
            );
        })
        .run(function () {
            test.done();
        });
});
