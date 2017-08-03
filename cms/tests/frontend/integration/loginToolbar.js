'use strict';

// #############################################################################
// User login via the CMS toolbar (on all kinds of screens)

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers();

casper.test.setUp(function(done) {
    casper.start().then(cms.login()).then(cms.addPage({ title: 'First page' })).then(cms.logout()).run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.removePage()).then(cms.logout()).run(done);
});

[
    [320, 480], // mobile vertical
    [480, 320], // mobile horizontal
    [768, 1024], // tablet vertical
    [1024, 768], // tablet horizontal
    [1280, 1024] // standard - it's important that the last one resets
].forEach(function(dimensions) {
    casper.test.begin('User Login (via Toolbar) ' + JSON.stringify(dimensions), function(test) {
        casper
            .start(globals.editUrl)
            .viewport(dimensions[0], dimensions[1])
            .waitForSelector('.cms-toolbar-expanded', function() {
                test.assertExists('.cms-toolbar .cms-form-login', 'The toolbar login form is available');

                this.fill('.cms-form-login', globals.credentials, true);
            })
            .waitForSelector('.cms-ready', function() {
                test.assertExists('.cms-toolbar-item-navigation', 'Login via the toolbar done');
            })
            .run(function() {
                test.done();
            });
    });
});
