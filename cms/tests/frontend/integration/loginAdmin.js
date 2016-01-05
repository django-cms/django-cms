/* globals localStorage */
'use strict';

// #############################################################################
// User login via the admin panel

var globals = require('./settings/globals');
var messages = require('./settings/messages').login.admin;
var cms = require('./helpers/cms');

casper.test.tearDown(function (done) {
    casper.start().then(cms.logout).run(done);
});

casper.test.begin('User Login (via Admin Panel)', function (test) {
    casper
        .start(globals.adminUrl, function () {
            // we explicitly kill the session id cookie to reset the login state
            // and localstorage data to reset the ui state (sideframe, toolbar, etc)
            this.page.deleteCookie('sessionid');
            this.evaluate(function () {
                localStorage.clear();
            });

            this.echo('The currently set cookies are: ' + JSON.stringify(this.page.cookies), 'INFO');
        })
        .then(function () {
            var titleRegExp = new RegExp(globals.adminTitle, 'g');

            test.assertTitleMatch(titleRegExp, messages.cmsTitleOk);
            test.assertExists('#login-form', messages.adminAvailable);

            this.fill('#login-form', {
                username: 'fake',
                password: 'credentials'
            }, true);
        })
        .waitForSelector('.errornote', function () {
            test.assertExists('.errornote', messages.loginFail);

            this.fill('#login-form', globals.credentials, true);
        })
        .thenOpen(globals.baseUrl, function () {
            test.assertExists('.cms-toolbar', messages.loginOk);
        })
        .run(function () {
            test.done();
        });
});
