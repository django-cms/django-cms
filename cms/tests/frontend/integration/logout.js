'use strict';

// #############################################################################
// User logout

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers();

casper.test.setUp(function(done) {
    casper.start().then(cms.login()).then(cms.addPage({ title: 'First page' })).run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.login()).then(cms.removePage()).then(cms.logout()).run(done);
});

casper.test.begin('User Logout', function(test) {
    casper
        .start(globals.editUrl)
        .waitForSelector('.cms-toolbar-expanded', function() {
            this.click('.cms-toolbar-item-navigation li:first-child a');
        })
        .waitForSelector('.cms-toolbar-item-navigation-hover', function() {
            this.click('.cms-toolbar-item-navigation-hover a[href$="/admin/logout/"]');
        })
        .waitForResource(/logout/)
        .waitForSelector('.nav', function() {
            test.assertDoesntExist('.cms-toolbar', 'Logout via the toolbar done');
        })
        .run(function() {
            test.done();
        });
});
