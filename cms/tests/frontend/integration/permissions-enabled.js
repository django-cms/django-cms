'use strict';

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers();

casper.test.setUp(function(done) {
    casper.start().then(cms.login()).then(cms.addPage({ title: 'Homepage' })).run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.removePage()).then(cms.logout()).run(done);
});

casper.test.begin('Permissions action is available', function(test) {
    casper
        .start()
        .thenOpen(globals.editUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            casper
                .waitForSelector('.cms-pagetree-jstree')
                .wait(3000)
                .then(cms.expandPageTree())
                .then(function() {
                    var pageId = cms.getPageId('Homepage');

                    this.click('.js-cms-pagetree-options[data-id="' + pageId + '"]');
                })
                .then(cms.waitUntilActionsDropdownLoaded())
                .then(function() {
                    test.assertExists(
                        '.cms-pagetree-dropdown-menu-open a[href*="permission-settings"]',
                        'Permission settings exist in the menu'
                    );
                });
        })
        .run(function() {
            test.done();
        });
});
