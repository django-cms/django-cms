'use strict';

// #############################################################################
// Users managed via the admin panel

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers();

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        .run(done);
});

casper.test.tearDown(function (done) {
    casper.start()
        .then(cms.removePage())
        .then(cms.logout())
        .run(done);
});

casper.test.begin('Users Management', function (test) {
    casper
        .start(globals.baseUrl)
        .waitForSelector('.cms-toolbar-expanded', function () {
            this.click('.cms-toolbar-item-navigation li:first-child a');
        })
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click('.cms-toolbar-item-navigation-hover a[href$="/admin/auth/user/"]');
        })
        .waitUntilVisible('.cms-sideframe-frame')
        .withFrame(0, function () {
            casper
                .waitForSelector('#changelist-form', function () {
                    test.assertExists('.column-first_name', 'Admin panel with the list of users opened in sideframe');

                    this.click('.field-username a[href$="/user/1/"]');
                })
                .waitForSelector('#user_form', function () {
                    test.assertExists('#user_form', 'The admin profile edit page has been opened');

                    this.fill('#user_form', { first_name: globals.user.firstName }, true);
                })
                .waitForSelector('#changelist-form', function () {
                    test.assertSelectorHasText(
                        '#changelist-form .field-first_name',
                        globals.user.firstName,
                        'The admin first name has been updated'
                    );
                });
        })
        .then(function () {
            this.click('.cms-sideframe .cms-icon-close');
        })
        .run(function () {
            test.done();
        });
});
