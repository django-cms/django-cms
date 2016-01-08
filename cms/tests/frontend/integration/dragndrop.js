'use strict';

// #############################################################################
// Drag'n'drop plugins

var globals = require('./settings/globals');
var casperjs = require('casper');
var cms = require('./helpers/cms')(casperjs);

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        // actually creates 3 plugins - row > col + col
        .then(cms.addPlugin({
            type: 'GridPlugin',
            content: {
                id_create: 2,
                id_create_size: 12
            }
        }))
        .then(cms.addPlugin({
            type: 'TextPlugin',
            content: {
                id_body: 'Test text'
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

casper.test.begin('Drag plugin to another placeholder', function (test) {
    casper.start(globals.editUrl)
        .then(function () {
            test.assertElementCount('.cms-structure .cms-draggable', 4);
        })
        // make sure we are in structure mode
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            this.click('.cms-toolbar-item-cms-mode-switcher .cms-btn[href="?build"]');
        })
        .waitUntilVisible('.cms-structure')
        // check that the plugins are in correct placeholders
        .then(function () {
            test.assertElementCount(
                '.cms-dragarea:nth-child(1) > .cms-draggables > .cms-draggable',
                2,
                'Both plugins are in first placeholder'
            );
            test.assertElementCount(
                '.cms-dragarea:nth-child(2) > .cms-draggables > .cms-draggable',
                0,
                'Plugin is not yet moved to another placeholder'
            );
        })
        // move plugin
        .then(function () {
            var placeholder = this.getElementBounds('.cms-dragarea:nth-child(2) .cms-draggables');

            this.evaluate(function () {
                // changing delay here because casper doesn't understand
                // that we want to wait 100 ms after "picking up" the plugin
                // for sortable to work
                CMS.API.StructureBoard.ui.sortables.nestedSortable('option', 'delay', 0);
            });

            this.mouse.down('.cms-dragarea:first-child > .cms-draggables > .cms-draggable');
            this.mouse.move(placeholder.left + placeholder.width / 2, placeholder.top + placeholder.height * 0);
        }).then(function () {
            this.mouse.up('.cms-dragarea:nth-child(2) .cms-draggables');
            test.assertElementCount(
                '.cms-dragarea:nth-child(2) > .cms-draggables > .cms-draggable',
                1,
                'Plugin moved to another placeholder'
            );
        })
        .waitForResource(/move-plugin/)
        .then(function () {
            return this.reload();
        })
        // check after reload
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            this.click('.cms-toolbar-item-cms-mode-switcher .cms-btn[href="?build"]');
        })
        .then(function () {
            test.assertElementCount(
                '.cms-dragarea:nth-child(1) > .cms-draggables > .cms-draggable',
                1,
                'One plugin is in the first placeholder'
            );
            test.assertSelectorHasText(
                '.cms-dragarea:nth-child(1) > .cms-draggables > .cms-draggable',
                'Text',
                'First placeholder has Text Plugin'
            );
            test.assertElementCount(
                '.cms-dragarea:nth-child(2) > .cms-draggables > .cms-draggable',
                1,
                'Another plugin is in the second placeholder'
            );
            test.assertSelectorHasText(
                '.cms-dragarea:nth-child(2) > .cms-draggables > .cms-draggable',
                'Multi Columns (grid)',
                'Second placeholder has MultiColumns Plugin'
            );
        })
        .run(function () {
            test.done();
        });
});
