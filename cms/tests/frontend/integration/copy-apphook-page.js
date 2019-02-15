'use strict';

// #############################################################################
// add a test for creating apphook and trying to copy a page with an apphook

var casperjs = require('casper');
var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers(casperjs);

casper.test.setUp(function(done) {
    casper
        .start()
        .then(cms.login())
        .then(cms.addPage({ title: 'Home' }))
        .then(cms.addPage({ title: 'apphook' }))
        .then(
            cms.addApphookToPage({
                page: 'apphook',
                apphook: 'Example1App'
            })
        )
        .run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.removePage()).then(cms.removePage()).then(cms.logout()).run(done);
});

casper.test.begin('copy page with apphook should not be copied', function(test) {
    casper
        .start()
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        .withFrame(0, function() {
            casper.waitUntilVisible('.cms-pagetree-jstree').wait(3000).then(cms.expandPageTree());
            this.then(cms.triggerCopyPage({ page: cms.getPageNodeId('apphook') }));
            this.waitUntilVisible('.messagelist', function() {
                test.assertVisible('.error', 'Message appeared');
                test.assertSelectorHasText(
                    'li.error',
                    'This page cannot be copied because an application is attached to it.'
                );
            });
        })
        .run(function() {
            test.done();
        });
});
