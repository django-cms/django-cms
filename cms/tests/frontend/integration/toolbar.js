'use strict';

// #############################################################################
// Toolbar behaviour

var globals = require('./settings/globals');
var messages = require('./settings/messages').toolbar;

casper.test.begin('Toolbar Visibility', function (test) {
    var toolbarOffset = 0;
    var transitionTime = 200;

    // The toolbar is hidden with negative margin and casper considers it visible at all times
    // in order to check visibility the suite has to grab margin value
    casper
        .start(globals.baseUrl, function () {
            test.assertEquals(
                this.getElementAttribute('.cms-toolbar-item-logo a', 'href'), '/', messages.logoUrlCorrect
            );

            this.click('.cms-toolbar-trigger');
        })
        .wait(transitionTime, function () {
            toolbarOffset = this.evaluate(function () {
                return parseInt($('.cms-toolbar').css('marginTop'), 10);
            });

            test.assertTruthy(toolbarOffset < 0, messages.toolbarClosed);

            this.click('.cms-toolbar-trigger');
        })
        .wait(transitionTime, function () {
            toolbarOffset = this.evaluate(function () {
                return parseInt($('.cms-toolbar').css('marginTop'), 10);
            });

            test.assertTruthy(toolbarOffset === 0, messages.toolbarOpened);
        })
        .run(function () {
            test.done();
        });
});
