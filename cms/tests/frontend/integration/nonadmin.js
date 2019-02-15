'use strict';

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var casperjs = require('casper');
var xPath = casperjs.selectXPath;
var cms = helpers(casperjs);

casper.test.setUp(function(done) {
    casper
        .start()
        .then(cms.login())
        .then(cms.addPage({ title: 'Home page' }))
        .then(
            cms.addPlugin({
                type: 'TextPlugin',
                content: {
                    id_body: 'Random text'
                }
            })
        )
        .then(cms.publishPage({ page: 'Home page', language: 'en' }))
        .run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.login()).then(cms.removePage()).then(cms.logout()).run(done);
});

casper.test.begin('Non admin user cannot open structureboard', function(test) {
    casper
        .start()
        .then(cms.logout())
        .then(
            cms.login({
                username: 'normal',
                password: 'normal'
            })
        )
        .thenOpen(globals.editUrl)
        .waitForSelector('.cms-ready', function() {
            this.mouse.doubleclick(
                // pick a div with class cms-plugin that has a p that has text "Random text"
                xPath('//*[contains(@class, "cms-plugin")][contains(text(), "Random text")]')
            );
        })
        .waitUntilVisible('.cms-modal-open')
        .withFrame(0, function() {
            casper.waitUntilVisible('body', function() {
                test.assertSelectorHasText('body', 'You do not have permission to edit this plugin');
            });
        })
        .then(function() {
            this.click('.cms-modal-open .cms-modal-item-buttons:last-child > a');
        })
        .waitWhileVisible('.cms-modal-iframe')
        .then(function() {
            // normally nothing happens on click, but we are making sure there are no regressions
            this.mouse.click(
                // pick a div with class cms-plugin that has a p that has text "Random text"
                xPath('//*[contains(@class, "cms-plugin")][contains(text(), "Random text")]')
            );
        })
        .then(function() {
            test.assertSelectorDoesntHaveText('.cms-structure', 'Placeholder_Content_1');
        })
        .then(function() {
            this.evaluate(function() {
                CMS.$(document).data('expandmode', true);
            });
            // normally nothing happens on click, but we are making sure there are no regressions
            this.mouse.click(
                // pick a div with class cms-plugin that has a p that has text "Random text"
                xPath('//*[contains(@class, "cms-plugin")][contains(text(), "Random text")]')
            );
        })
        .then(function() {
            test.assertSelectorDoesntHaveText('.cms-structure', 'Placeholder_Content_1');
        })
        .wait(3000, function() {
            test.assertSelectorDoesntHaveText('.cms-structure', 'Placeholder_Content_1');
        })
        .then(cms.logout())
        .run(function() {
            test.done();
        });
});
