'use strict';

// #############################################################################
// Change Settings behaviour

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers();

casper.test.setUp(function(done) {
    casper.start().then(cms.login()).then(cms.addPage({ title: 'home' })).run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.removePage()).then(cms.logout()).run(done);
});

casper.test.begin('Change Settings', function(test) {
    casper
        .start(globals.editUrl)
        // click on example.com
        .waitForSelector('.cms-toolbar-expanded', function() {
            this.click('.cms-toolbar-item-navigation li:first-child a');
        })
        // click on User Settings
        .waitUntilVisible('.cms-toolbar-item-navigation-hover a', function() {
            this.click('.cms-toolbar-item-navigation-hover a[href$="/admin/cms/usersettings/"]');
        })
        // waits till Sideframe is open
        .waitUntilVisible('.cms-sideframe-frame')
        .withFrame(0, function() {
            casper.waitForSelector('#content-main', function() {
                test.assertExists('#id_language', 'language button exists');

                // selects German language
                this.fill(
                    '#usersettings_form',
                    {
                        language: 'de'
                    },
                    true
                );
            });
        })
        .waitForResource(/admin/)
        // have to wait for the sideframe again, cause the page reloads itself after saving the the language
        .waitUntilVisible('.cms-sideframe-frame')
        .withFrame(0, function() {
            casper
                // checks h1 tag if the language changed
                .waitForSelector('#content-main', function() {
                    test.assertEquals(
                        this.fetchText('#content h1'),
                        'Benutzer-Einstellung ändern',
                        'German language applied'
                    );
                })
                .waitForSelector('#content-main', function() {
                    test.assertExists('#id_language', 'Menu correct reloaded');

                    // changes back to english
                    this.fill(
                        '#usersettings_form',
                        {
                            language: 'en'
                        },
                        true
                    );
                });
        })
        .waitForResource(/admin/)
        // have to wait for the sideframe again, cause the page reloads itself after saving the the language
        .waitUntilVisible('.cms-sideframe-frame')
        .withFrame(0, function() {
            casper
                // checks h1 tag if the language changed
                .waitForSelector('#content-main', function() {
                    test.assertEquals(this.fetchText('#content h1'), 'Change user setting', 'English language applied');
                });
        })
        .then(function() {
            this.click('.cms-sideframe .cms-icon-close');
        })
        .run(function() {
            test.done();
        });
});
