'use strict';

// #############################################################################
// Users managed via the admin panel

var globals = require('./settings/globals');
var messages = require('./settings/messages').users;

casper.test.begin('Users Management', function (test) {
    casper
        .start(globals.baseUrl)
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            this.click('.cms-toolbar-item-navigation li:first-child a');
        })
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click('.cms-toolbar-item-navigation-hover a[href$="/admin/auth/user/"]');
        })
        .waitUntilVisible('.cms-sideframe-frame')
        .withFrame(0, function () {
            casper
                .waitForSelector('#changelist-form', function () {
                    test.assertExists('.column-first_name', messages.usersListOpened);

                    this.click('.field-username a[href$="/user/1/"]');
                })
                .waitForSelector('#user_form', function () {
                    test.assertExists('#user_form', messages.editPageOpened);

                    this.fill('#user_form', { first_name: globals.user.firstName }, true);
                })
                .waitForSelector('#changelist-form', function () {
                    test.assertSelectorHasText(
                        '#changelist-form .field-first_name',
                        globals.user.firstName,
                        messages.firstNameChanged
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
