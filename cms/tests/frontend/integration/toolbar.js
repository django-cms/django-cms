'use strict';

// #############################################################################
// Toolbar behaviour

var globals = require('./settings/globals');
var messages = require('./settings/messages').toolbar;

casper.test.begin('Toolbar Visibility', function (test) {
    casper
        .start(globals.editUrl, function () {
            test.assertEquals(
                this.getElementAttribute('.cms-toolbar-item-logo a', 'href'), '/', messages.logoUrlCorrect
            );
        })
        .run(function () {
            test.done();
        });
});
