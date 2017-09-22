'use strict';

// #############################################################################
// Edit page content

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var casperjs = require('casper');
var cms = helpers(casperjs);

casper.test.setUp(function(done) {
    casper
        .start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        .then(
            cms.addPlugin({
                type: 'LinkPlugin',
                content: {
                    id_name: 'Link Plugin',
                    id_external_link: 'http://google.com'
                }
            })
        )
        .run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.removePage()).then(cms.logout()).run(done);
});

casper.test.begin('Doubleclick on plugins with links handled correctly', function(test) {
    casper
        .start(globals.editUrl)
        .then(cms.switchTo('content'))
        .waitForSelector('.cms-toolbar-expanded', function() {
            this.mouse.doubleclick('a.cms-plugin');
        })
        .wait(5000, function() {
            test.assertUrlMatch(/\/\/(?!google)/, 'We did not go to google');
            test.assertVisible('.cms-modal');
        })
        .run(function() {
            test.done();
        });
});
