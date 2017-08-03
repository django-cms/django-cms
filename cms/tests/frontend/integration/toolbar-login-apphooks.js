'use strict';

// #############################################################################
// User login via the CMS toolbar on apphooked pages

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers();

casper.test.setUp(function(done) {
    casper
        .start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        .then(cms.addPage({ title: 'Apphooked page' }))
        .then(
            cms.addApphookToPage({
                page: 'Apphooked page',
                apphook: 'Example1App'
            })
        )
        .then(
            cms.setPageTemplate({
                page: 'Apphooked page',
                template: 'simple.html'
            })
        )
        .then(
            cms.publishPage({
                page: 'Apphooked page'
            })
        )
        .then(cms.logout())
        .run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.removePage()).then(cms.removePage()).then(cms.logout()).run(done);
});

var apphookedPageUrl = globals.baseUrl + 'apphooked-page/?edit';

casper.test.begin('User Login (via Toolbar) through apphooked page', function(test) {
    casper
        .start(apphookedPageUrl)
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertSelectorHasText('.page_title', 'Apphooked page', 'Apphooked page was created and published');
            test.assertExists('.cms-toolbar .cms-form-login', 'The toolbar login form is available');

            this.fill('.cms-form-login', { username: 'totally', password: 'wrong' }, true);
        })
        .waitForSelector('.cms-error', function() {
            this.fill('.cms-form-login', globals.credentials, true);
        })
        .waitForSelector('.cms-ready', function() {
            test.assertExists('.cms-toolbar-item-navigation', 'Login via the toolbar done');
            test.assertExists('.cms-render-model-add', 'Apphooked page is correct');
        })
        .run(function() {
            test.done();
        });
});

casper.test.begin('User Login (via Toolbar) through apphooked object page', function(test) {
    var appObjectUrl;
    var appObjectId;

    casper
        .start()
        .then(cms.login())
        .thenOpen(apphookedPageUrl)
        // add app object
        .waitForSelector('.cms-render-model-add', function() {
            this.mouse.doubleclick('.cms-render-model-add');
        })
        .waitUntilVisible('.cms-modal')
        .withFrame(0, function() {
            casper.waitForSelector('#example1_form', function() {
                this.fill('#example1_form', {
                    char_1: '1',
                    char_2: '2',
                    char_3: '3',
                    char_4: '4',
                    date_field: this.evaluate(function() {
                        var today = new Date();
                        var date = today.getDate();
                        var month = today.getMonth() + 1;

                        if (date < 10) {
                            date = '0' + date;
                        }
                        if (month < 10) {
                            month = '0' + month;
                        }
                        return today.getFullYear() + '-' + month + '-' + date;
                    })
                });
            });
        })
        .then(function() {
            this.click('.cms-modal-buttons .cms-btn-action');
        })
        .waitForResource(/add/)
        .waitForUrl(/detail/)
        .waitForSelector('.cms-ready', function() {
            appObjectUrl = this.getCurrentUrl() + '?edit';
            appObjectId = this.getCurrentUrl().replace(globals.port, '').replace(/\D/g, '');
        })
        .then(cms.logout())
        .then(function() {
            this.open(appObjectUrl);
        })
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertSelectorHasText('.page_title', 'Apphooked page', 'Apphooked page was created and published');
            test.assertExists('.cms-toolbar .cms-form-login', 'The toolbar login form is available');

            this.fill('.cms-form-login', { username: 'totally', password: 'wrong' }, true);
        })
        .waitForSelector('.cms-error', function() {
            this.fill('.cms-form-login', globals.credentials, true);
        })
        .waitForSelector('.cms-ready', function() {
            test.assertExists('.cms-toolbar-item-navigation', 'Login via the toolbar done');
            test.assertExists('.cms-render-model-add', 'Apphook object page is correct');
        })
        .then(function() {
            this.open(globals.baseUrl + 'admin/placeholderapp/example1/' + appObjectId + '/delete/');
        })
        .waitForSelector('form input[type="submit"]', function() {
            this.click('form input[type="submit"]');
        })
        .waitForSelector('.success')
        .run(function() {
            test.done();
        });
});
