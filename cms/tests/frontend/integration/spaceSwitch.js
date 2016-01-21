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
        .waitForResource(/publish/)
        .waitWhileVisible('.cms-toolbar-expanded')
        .waitForSelector('.cms-toolbar-expanded', function () {
            test.assertExist('.cms-btn-switch-edit', 'published page');
            // clicks on edit mode
            this.click('.cms-btn-switch-edit');
        })

        .waitUntilVisible('.cms-toolbar-expanded', function () {
            test.assertElementCount(
                '.cms-dragarea:nth-child(1) > .cms-draggables > .cms-draggable',
                1,
                'second plugins gets added and shown'
            );
        })

        .then(function() {
            var e = $.Event("keydown");
            e.which = 32;
            $(this).trigger(e);
        });



        .run(function () {
            test.done();
        });
});
