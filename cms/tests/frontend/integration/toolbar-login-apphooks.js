'use strict';

// #############################################################################
// User login via the CMS toolbar on apphooked pages

var globals = require('./settings/globals');
var cms = require('./helpers/cms')();

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        .then(cms.addPage({ title: 'Apphooked page' }))
        .then(cms.addApphookToPage({
            page: 'Apphooked page',
            apphook: 'Example1App'
        }))
        .then(cms.setPageTemplate({
            page: 'Apphooked page',
            template: 'simple.html'
        }))
        .then(cms.publishPage({
            page: 'Apphooked page'
        }))
        .then(cms.logout())
        .run(done);
});

casper.test.tearDown(function (done) {
    casper.start()
        .then(cms.removePage())
        .then(cms.removePage())
        .then(cms.logout())
        .run(done);
});

var apphookedPageUrl = globals.baseUrl + 'apphooked-page/?edit';

casper.test.begin('User Login (via Toolbar) through apphooked page', function (test) {
    casper
        .start(apphookedPageUrl)
        .waitForSelector('.cms-toolbar-expanded', function () {
            test.assertSelectorHasText(
                '.page_title',
                'Apphooked page',
                'Apphooked page was created and published'
            );
            test.assertExists('.cms-toolbar .cms-form-login', 'The toolbar login form is available');

            this.fill('.cms-form-login', { username: 'totally', password: 'wrong' }, true);
        })
        .waitForSelector('.cms-error')
        .waitUntilVisible('.cms-messages', function () {
            test.assertSelectorHasText(
                '.cms-messages',
                'Please check your credentials and try again.',
                'Error is displayed'
            );

            this.fill('.cms-form-login', globals.credentials, true);
        })
        .waitForSelector('.cms-ready', function () {
            test.assertExists('.cms-toolbar-item-navigation', 'Login via the toolbar done');
            test.assertExists('.cms-render-model-add', 'Apphooked page is correct');
        })
        .run(function () {
            test.done();
        });
});
