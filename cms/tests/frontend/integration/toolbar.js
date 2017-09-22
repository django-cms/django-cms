'use strict';

// #############################################################################
// Toolbar behaviour

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers();

casper.test.setUp(function(done) {
    casper.start().then(cms.login()).run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.logout()).run(done);
});

casper.test.begin('Toolbar Visibility', function(test) {
    casper
        .start(globals.baseUrl)
        .then(function() {
            test.assertVisible('.cms-toolbar');
        })
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertEquals(
                this.getElementAttribute('.cms-toolbar-item-logo a', 'href'),
                '/',
                'The django CMS logo redirects to homepage'
            );
        })
        .run(function() {
            test.done();
        });
});
