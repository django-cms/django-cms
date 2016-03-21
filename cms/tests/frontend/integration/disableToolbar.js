'use strict';

// #############################################################################
// Toolbar behaviour

var globals = require('./settings/globals');
var cms = require('./helpers/cms')();

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        .then(cms.addPage({ title: 'home' }))
        .run(done);
});

casper.test.tearDown(function (done) {
    casper.start()
        .then(cms.removePage())
        .then(cms.logout())
        .run(done);
});

casper.test.begin('Disable Toolbar', function (test) {
    casper
        .start(globals.editUrl)
        // click on example.com
        .waitForSelector('.cms-toolbar-expanded', function () {
            this.click('.cms-toolbar-item-navigation li:first-child a');
        })
        // click on Disable Toolbar
        .waitUntilVisible('.cms-toolbar-item-navigation-hover a', function () {
            this.click('.cms-toolbar-item-navigation-hover a[href="?toolbar_off"]');
        })
        // waits till /toolbar_off/ is added in the URL
        .waitForUrl(/toolbar_off/)

        // checks if the toolbar is gone
        .then(function () {
            test.assertDoesntExist('.cms-toolbar');
        })

        .run(function () {
            test.done();
        });
});
