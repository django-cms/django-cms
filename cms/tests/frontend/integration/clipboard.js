/* global document */
'use strict';

// #############################################################################
// Clipboard

var globals = require('./settings/globals');
var casperjs = require('casper');
var cms = require('./helpers/cms')(casperjs);
var xPath = casperjs.selectXPath;

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        .then(cms.addPlugin({
            type: 'TextPlugin',
            content: {
                id_body: 'Test text'
            }
        }))
        .then(cms.addPlugin({
            type: 'TextPlugin',
            content: {
                id_body: 'Another Test text'
            }
        }))
        .run(done);
});

casper.test.tearDown(function (done) {
    casper.start()
        .then(cms.removePage())
        .then(cms.logout())
        .run(done);
});

casper.test.begin('Copy plugin from the structure board', function (test) {
    var contentNumber;

    casper
        .start(globals.editUrl)
        // go to the Structure mode
        .then(function () {
            this.click('.cms-toolbar-item-cms-mode-switcher .cms-btn[href="?build"]');
        })
        // click settings for last content plugin
        .waitUntilVisible('.cms-structure', function () {
            // save initial number of content plugins
            contentNumber = this.evaluate(function () {
                return document.querySelectorAll('.cms-structure-content .cms-draggable').length;
            });
            // click settings for last content plugin
            this.click('.cms-structure .cms-draggable:last-child .cms-submenu-settings');
        })
        // check that there is something now in the clipboard
        .then(function () {
            test.assertElementCount('.cms-clipboard .cms-plugin', 0, 'No plugins in clipboard');
        })
        // select copy button from dropdown list
        .waitUntilVisible(
            '.cms-structure .cms-draggable:last-child .cms-submenu-item a[data-rel="copy"]',
            function () {
                this.click('.cms-structure .cms-draggable:last-child .cms-submenu-item a[data-rel="copy"]');
            }
        )
        .waitForResource(/copy-plugins/)

        // check that there is something now in the clipboard
        .then(function () {
            test.assertElementCount('.cms-clipboard .cms-plugin', 1, '1 plugin in clipboard');
        })

        .then(function () {
            // click on "Example.com" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(1) > a');
        })
        // opening "Clipboard" menu item
        .wait(10, function () {
            this.click(
                xPath('//a[.//span[text()[contains(.,"Clipboard")]]]')
            );
        })

        // wait until clipboard modal is open
        .waitUntilVisible('.cms-modal-frame .cms-clipboard-containers', function () {
            var placeholder = this.getElementBounds('.cms-dragarea:nth-child(2) .cms-draggables');

            this.evaluate(function () {
                // changing delay here because casper doesn't understand
                // that we want to wait 100 ms after "picking up" the plugin
                // for sortable to work
                CMS.API.StructureBoard.ui.sortables.nestedSortable('option', 'delay', 0);
            });

            this.mouse.down('.cms-clipboard-containers .cms-draggable');
            this.mouse.move(placeholder.left + placeholder.width / 2, placeholder.top + placeholder.height * 0);
        }).then(function () {
            this.mouse.up('.cms-dragarea:nth-child(2) .cms-draggables');
            // check before reload
            test.assertElementCount(
                '.cms-structure .cms-draggables .cms-draggable',
                contentNumber + 1,
                'Copy plugin successful'
            );
        })
        .waitForResource(/move-plugin/)
        .then(function () {
            return this.reload();
        })
        // check if number of content plugins has been increased (after reload)
        .then(function () {
            test.assertElementCount(
                '.cms-structure .cms-dragarea:nth-child(1) .cms-draggables .cms-draggable',
                contentNumber,
                'First placeholder has 2 plugins'
            );

            test.assertElementCount(
                '.cms-structure .cms-dragarea:nth-child(2) .cms-draggables .cms-draggable',
                1,
                'Second placeholder has one plugin'
            );
        })

        .then(function () {
            // click on "Example.com" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(1) > a');
        })
        // opening "Clipboard" menu item
        .wait(10, function () {
            this.click(
                xPath('//a[.//span[text()[contains(.,"Clear clipboard")]]]')
            );
        })
        .waitForResource(/clear/)
        .then(function () {
            return this.reload();
        })
        // check that there is nothing now in the clipboard
        .then(function () {
            test.assertElementCount('.cms-clipboard .cms-plugin', 0, 'Clipboard is now empty');
        })

        .run(function () {
            test.done();
        });
});
