'use strict';

// #############################################################################
// Users managed via the admin panel

var globals = require('./settings/globals');
var messages = require('./settings/messages').users;

casper.test.begin('New Page Creation', function (test) {
    casper
        .start(globals.editUrl)
        .wait(globals.toolbarTransitionTime, function () {

        })
        .run(function () {
            test.done();
        });
});
