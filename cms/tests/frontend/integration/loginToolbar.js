'use strict';

// #############################################################################
// User login via the CMS toolbar

var globals = require('./settings/globals');
var cms = require('./helpers/cms')();

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        .then(cms.logout())
        .run(done);
});

casper.test.tearDown(function (done) {
    casper.start()
        .then(cms.removePage())
        .then(cms.logout())
        .run(done);
});

casper.test.begin('User Login (via Toolbar)', function (test) {
    casper
        .start(globals.editUrl)
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            test.assertExists('.cms-toolbar .cms-form-login', 'The toolbar login form is available');

            this.fill('.cms-form-login', globals.credentials, true);
        })
        .waitForSelector('.cms-ready', function () {
            test.assertExists('.cms-toolbar-item-navigation', 'Login via the admin form done');
        })
        .run(function () {
            test.done();
        });
});
