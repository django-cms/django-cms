'use strict';

// #############################################################################
// Toolbar behaviour

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers();

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        .run(done);
});

casper.test.tearDown(function (done) {
    casper.start()
        .then(cms.logout())
        .run(done);
});

casper.test.begin('Toolbar Visibility', function (test) {
    var toolbarOffset = 0;
    var transitionTime = 200;

    // The toolbar is hidden with negative margin and casper considers it visible at all times
    // in order to check visibility the suite has to grab margin value
    casper
        .start(globals.baseUrl)
        .waitForSelector('.cms-toolbar-expanded', function () {
            test.assertEquals(
                this.getElementAttribute('.cms-toolbar-item-logo a', 'href'), '/',
                'The django CMS logo redirects to homepage'
            );

            this.click('.cms-toolbar-trigger');
        })
        .wait(transitionTime, function () {
            toolbarOffset = this.evaluate(function () {
                return parseInt(CMS.$('.cms-toolbar').css('marginTop'), 10);
            });

            test.assertTruthy(toolbarOffset < 0, 'Toolbar can be closed on trigger click');

            this.click('.cms-toolbar-trigger');
        })
        .wait(transitionTime, function () {
            toolbarOffset = this.evaluate(function () {
                return parseInt(CMS.$('.cms-toolbar').css('marginTop'), 10);
            });

            test.assertTruthy(toolbarOffset === 0, 'Toolbar can be opened on trigger click');
        })
        .run(function () {
            test.done();
        });
});
