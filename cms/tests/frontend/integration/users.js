'use strict';

// #############################################################################
// Users managed via the admin panel

var globals = require('./settings/globals');
var messages = require('./settings/messages').users;

casper.test.begin('Users Creation', function (test) {
    casper
        .start(globals.baseUrl, function () {
            this.click('.cms-toolbar-item-navigation li:first-child a');
        })
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click('.cms-toolbar-item-navigation-hover a[href$="/admin/"]');
        })
        .waitUntilVisible('.cms-sideframe-frame')
        .withFrame(0, function () {
            casper
                .waitForSelector('.cms-admin-sideframe', function(){
                    test.assertExists('.model-user', messages.adminPanelOpened);

                    this.click('.model-user .changelink');
                })
                .waitForSelector('#changelist-form', function () {
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
        .run(function () {
            test.done();
        });
});
