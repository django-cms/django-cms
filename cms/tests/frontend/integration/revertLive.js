'use strict';

// #############################################################################
// Change Settings behaviour

var casperjs = require('casper');
var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
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
                    id_body: 'Revert to Live'
                }
            })
        )
        .run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.removePage()).then(cms.logout()).run(done);
});

casper.test.begin('Revert History', function(test) {
    casper
        .start(globals.editUrl)
        // publishes page
        .waitForSelector('.cms-btn-publish-active', function() {
            this.click('.cms-btn-publish-active');
        })
        .waitForResource(/publish/)
        .waitWhileVisible('.cms-toolbar-expanded')
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertExist('.cms-btn-switch-edit', 'published page');
            // clicks on edit mode
            this.click('.cms-btn-switch-edit');
        })
        // Adds a second plugin
        .then(
            cms.addPlugin({
                type: 'TextPlugin',
                content: {
                    id_body: 'Second TextPlugin'
                }
            })
        )
        // counts that there are two plugins in the placeholder
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertElementCount(
                '.cms-dragarea:nth-child(1) > .cms-draggables > .cms-draggable',
                2,
                'second plugins gets added and shown'
            );
        })
        // click on history
        .waitForSelector('.cms-toolbar-expanded', function() {
            this.click('.cms-toolbar-item-navigation > li:nth-child(3) > a');
        })
        // clicks on 'revert to live'
        .wait(10, function() {
            test.assertExist('.cms-toolbar-revert', 'Revert to live is enabled');
            this.click('.cms-toolbar-revert a');
        })
        // checks if there's only one element again
        .waitForResource(/revert/)
        .waitWhileVisible('.cms-toolbar-expanded')
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertElementCount(
                '.cms-dragarea:nth-child(1) > .cms-draggables > .cms-draggable',
                1,
                'Reverted to live'
            );
        })
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertExist('.cms-btn-switch-save', 'view published exists');
            // clicks on edit mode
            this.click('.cms-btn-switch-save');
        })
        .waitForUrl(/edit_off/)
        .wait(100)
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertExist('.cms-btn-switch-edit', 'Not in Edit mode');
        })
        .run(function() {
            test.done();
        });
});
