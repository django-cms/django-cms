'use strict';

// #############################################################################
// Change Settings behaviour

var globals = require('./settings/globals');
var casperjs = require('casper');
var cms = require('./helpers/cms')(casperjs);

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        .then(cms.addPage({ title: 'home' }))
        .then(cms.addPlugin({
            type: 'TextPlugin',
            content: {
                id_body: 'Revert to Live'
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

casper.test.begin('Revert History', function (test) {
    casper
        .start(globals.editUrl)
        // publishes page
        .waitForSelector('.cms-btn-publish-active', function () {
            this.click('.cms-btn-publish-active');
        })
        // clicks on edit mode
        .waitForResource(/publish/)
        .waitForSelector('.cms-toolbar-expanded', function () {
            test.assertExist('.cms-btn-switch-edit', 'published page');
            this.click('.cms-btn-switch-edit');
        })
        // Adds a second plugin
        .then(cms.addPlugin({
            type: 'TextPlugin',
            content: {
                id_body: 'Second TextPlugin'
            }
        }))
        // counds that there are two plugins in the placeholder
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            test.assertElementCount(
                '.cms-dragarea:nth-child(1) > .cms-draggables > .cms-draggable',
                2,
                'second plugins gets added and shown'
            );
        })
        // click on history
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            this.click('.cms-toolbar-item-navigation > li:nth-child(3) > a');
        })
        // clicks on 'revert to live'
        .waitUntilVisible('.cms-toolbar-item-navigation-hover', function () {
            test.assertExist('.cms-toolbar-revert', 'Revert to live is enabled');
            this.click('.cms-toolbar-revert a');
        })
        // checks if there's only one element again
        .waitForResource(/revert/)
        .waitWhileVisible('.cms-toolbar-expanded')
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            test.assertElementCount(
                '.cms-dragarea:nth-child(1) > .cms-draggables > .cms-draggable',
                1,
                'Reverted to live'
            );
        })
        .run(function () {
            test.done();
        });
});
