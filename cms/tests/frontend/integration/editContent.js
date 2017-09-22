'use strict';

// #############################################################################
// Edit page content

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var randomString = helpers.randomString;
var casperjs = require('casper');
var xPath = casperjs.selectXPath;
var cms = helpers(casperjs);

// random text string for filtering and content purposes
var randomText = randomString({ length: 50, withWhitespaces: false });

casper.test.setUp(function(done) {
    casper
        .start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        .then(
            cms.addPlugin({
                type: 'TextPlugin',
                content: {
                    id_body: 'Random text'
                }
            })
        )
        .run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.removePage()).then(cms.logout()).run(done);
});

casper.test.begin('Edit content', function(test) {
    var previousContentText;

    casper
        .start(globals.editUrl)
        // make sure we are in content mode
        .then(cms.switchTo('content'))
        // check edit modal window appearance after double click in content mode
        // double click on last added plugin content
        .waitForSelector('.cms-toolbar-expanded', function() {
            this.mouse.doubleclick(
                // pick a div with class cms-plugin that has a p that has text "Random text"
                xPath('//*[contains(@class, "cms-plugin")][contains(text(), "Random text")]')
            );
        })
        .waitUntilVisible('.cms-modal-open')
        // change content inside appeared modal window
        .withFrame(0, function() {
            casper.waitUntilVisible('#text_form', function() {
                // explicitly put text to ckeditor
                previousContentText = this.evaluate(function(contentData) {
                    var previousContent = CMS.CKEditor.editor.document.getBody().getText();

                    CMS.CKEditor.editor.setData(contentData);
                    return previousContent;
                }, randomText);
            });
        })
        // submit changes in modal
        .then(function() {
            this.click('.cms-modal-buttons .cms-btn-action.default');
        })
        // check if content updated
        .then(cms.waitUntilContentIsRefreshed())
        .then(function() {
            // ensure content updated with new one
            test.assertSelectorHasText(
                '.cms-plugin',
                randomText,
                'Content has been updated by double click within the Content mode'
            );
        })
        // go to the Structure mode
        .then(cms.switchTo('structure'))
        // check edit modal window appearance after Edit button click in structure mode
        // click to Edit button for last plugin
        .waitUntilVisible('.cms-structure', function() {
            this.click('.cms-draggable:last-child .cms-submenu-edit');
        })
        // check if edit modal window appeared
        .waitUntilVisible('.cms-modal-open', function() {
            test.assertVisible('.cms-modal-open', 'Modal window appears after Edit button click in the Structure mode');
        })
        // close edit modal
        .then(function() {
            this.click('.cms-modal-open .cms-modal-item-buttons:last-child > a');
        })
        .waitWhileVisible('.cms-modal-iframe')
        // check edit modal window appearance after double click in structure mode
        // double click on last plugin
        .then(function() {
            this.mouse.doubleclick('.cms-structure .cms-draggable:last-child .cms-dragitem');
        })
        // edit content inside opened editor modal
        .waitUntilVisible('.cms-modal-open')
        .withFrame(0, function() {
            casper.waitUntilVisible('#text_form', function() {
                // explicitly put text to ckeditor
                this.evaluate(function(contentData) {
                    CMS.CKEditor.editor.setData(contentData);
                }, previousContentText);
            });
        })
        // submit changes
        .then(function() {
            this.click('.cms-modal-buttons .cms-btn-action.default');
        })
        // go to the Content mode
        .then(cms.waitUntilContentIsRefreshed())
        .then(cms.switchTo('content'))
        // check for applied changes
        .waitForSelector('.cms-toolbar-expanded', function() {
            // ensure content updated with new one
            test.assertSelectorHasText(
                '.cms-plugin',
                previousContentText,
                'Content has been updated by double click within the Content mode'
            );
        })
        .run(function() {
            test.done();
        });
});
