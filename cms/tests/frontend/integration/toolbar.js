'use strict';

// #############################################################################
// Toolbar behaviour

var globals = require('./settings/globals');
var messages = require('./settings/messages').toolbar;

casper.test.begin('Toolbar Visibility', function (test) {
    casper
        .start(globals.editUrl, function () {
            test.assertEquals(
                casper.getElementAttribute('.cms-toolbar-item-logo a', 'href'), '/', messages.logoUrlCorrect
            );

            casper.click('.cms-toolbar-trigger');
        })
        .wait(1000, function () {
            // TODO test hidden toolbar with screenshots match
            casper.click('.cms-toolbar-trigger');
        })
        .wait(1000, function () {
            // TODO test visible toolbar with screenshots match
        })
        .run(function () {
            test.done();
        });
});
