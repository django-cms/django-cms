'use strict';

// #############################################################################
// Drag'n'drop plugins

var casperjs = require('casper');
var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers(casperjs);

casper.test.setUp(function(done) {
    casper
        .start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        // actually creates 3 plugins - row > col + col
        .then(
            cms.addPlugin({
                type: 'MultiColumnPlugin',
                content: {
                    id_create: 2
                }
            })
        )
        .then(
            cms.addPlugin({
                type: 'TextPlugin',
                content: {
                    id_body: 'Test text'
                }
            })
        )
        .run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.removePage()).then(cms.logout()).run(done);
});

casper.test.begin('Drag plugin to another placeholder', function(test) {
    casper
        .start(globals.editUrl)
        .then(cms.switchTo('structure'))
        .then(function() {
            test.assertElementCount('.cms-structure .cms-draggable', 4);
        })
        // make sure we are in structure mode
        .then(cms.switchTo('structure'))
        .waitUntilVisible('.cms-structure')
        // check that the plugins are in correct placeholders
        .then(function() {
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
        .then(function() {
            var placeholder = this.getElementBounds('.cms-dragarea:nth-child(2) .cms-draggables');

            this.evaluate(function() {
                // changing delay here because casper doesn't understand
                // that we want to wait 100 ms after "picking up" the plugin
                // for sortable to work
                CMS.API.StructureBoard.ui.sortables.nestedSortable('option', 'delay', 0);
            });

            this.mouse.down('.cms-dragarea:first-child > .cms-draggables > .cms-draggable');
            this.mouse.move(placeholder.left + placeholder.width / 2, placeholder.top + placeholder.height * 0);
        })
        .then(function() {
            this.mouse.up('.cms-dragarea:nth-child(2) .cms-draggables');
            test.assertElementCount(
                '.cms-dragarea:nth-child(2) > .cms-draggables > .cms-draggable',
                1,
                'Plugin moved to another placeholder'
            );
        })
        .waitForResource(/move-plugin/)
        .then(function() {
            return this.reload();
        })
        // check after reload
        .then(cms.switchTo('structure'))
        .then(function() {
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
                'Multi Columns',
                'Second placeholder has MultiColumns Plugin'
            );
        })
        .run(function() {
            test.done();
        });
});

casper.test.begin('Move plugins inside a plugin', function(test) {
    var drop;

    casper
        .start(globals.editUrl)
        .then(cms.switchTo('structure'))
        .then(function() {
            test.assertElementCount('.cms-structure .cms-draggable', 4);
        })
        // make sure we are in structure mode
        .then(cms.switchTo('structure'))
        .waitUntilVisible('.cms-structure')
        // expand the multi columns plugin
        .thenBypassIf(function() {
            // if its already expanded, skip
            return this.visible('.cms-draggable > .cms-draggables .cms-dragitem-text[title*="ColumnPlugin"]');
        }, 2)
        .then(function() {
            this.mouse.click(
                '.cms-dragarea:first-child > .cms-draggables > .cms-draggable > .cms-dragitem-collapsable'
            );
        })
        // have to wait a bit because the collapse is debounced
        .wait(100)
        .then(function() {
            test.assertVisible(
                '.cms-draggable > .cms-draggables .cms-dragitem-text[title*="ColumnPlugin"]',
                'Plugin expanded'
            );
        })
        // move plugin
        .then(function() {
            // first grid column
            drop = this.getElementBounds(
                '.cms-dragarea:first-child > .cms-draggables > .cms-draggable .cms-draggable:first-child'
            );

            this.evaluate(function() {
                // changing delay here because casper doesn't understand
                // that we want to wait 100 ms after "picking up" the plugin
                // for sortable to work
                CMS.API.StructureBoard.ui.sortables.nestedSortable('option', 'delay', 0);
            });

            this.mouse.down('.cms-dragarea:first-child > .cms-draggables > .cms-draggable:last-child');
            this.mouse.move(drop.left + drop.width / 2, drop.top + drop.height);
            this.mouse.move(drop.left + drop.width / 2 + 30, drop.top + drop.height);
        })
        .then(function() {
            this.mouse.up(drop.left + drop.width / 2 + 30, drop.top + drop.height);
        })
        .waitForResource(/move-plugin/)
        .then(function() {
            this.reload();
        })
        // check after reload
        .then(cms.switchTo('structure'))
        .then(function() {
            test.assertElementCount(
                '.cms-dragarea:nth-child(1) > .cms-draggables > .cms-draggable',
                1,
                'There is only one root plugin'
            );

            test.assertEvalEquals(
                function() {
                    return CMS.$('.cms-draggable .cms-draggables .cms-dragitem-text[title*=ColumnPlugin]:first')
                        .closest('.cms-dragitem')
                        .hasClass('cms-dragitem-collapsable');
                },
                true,
                'First grid column has a child'
            );

            test.assertEvalEquals(
                function() {
                    return (
                        CMS.$('.cms-draggable .cms-draggables .cms-dragitem-text[title*=ColumnPlugin]:first')
                            .closest('.cms-draggable')
                            .find('.cms-draggables')
                            .find('.cms-dragitem-text strong')
                            .text() === 'Text'
                    );
                },
                true,
                'First grid column has TextPlugin as a child'
            );
        })
        // collapse the multi columns plugin
        .then(function() {
            this.mouse.click(
                '.cms-dragarea:first-child > .cms-draggables > .cms-draggable > .cms-dragitem-collapsable'
            );
        })
        .run(function() {
            test.done();
        });
});

casper.test.begin('Try to move a plugin to restricted area (not allowed)', function(test) {
    var drop;

    casper
        .start(globals.editUrl)
        .then(cms.switchTo('structure'))
        .then(function() {
            test.assertElementCount('.cms-structure .cms-draggable', 4);
        })
        // make sure we are in structure mode
        .then(cms.switchTo('structure'))
        .waitUntilVisible('.cms-structure')
        // expand the multi columns plugin
        .thenBypassIf(function() {
            // if its already expanded, skip
            return this.visible('.cms-draggable > .cms-draggables .cms-dragitem-text[title*="ColumnPlugin"]');
        }, 2)
        .then(function() {
            this.mouse.click(
                '.cms-dragarea:first-child > .cms-draggables > .cms-draggable > .cms-dragitem-collapsable'
            );
        })
        // have to wait a bit because the collapse is debounced
        .wait(100)
        .then(function() {
            test.assertVisible(
                '.cms-draggable > .cms-draggables .cms-dragitem-text[title*="ColumnPlugin"]',
                'Plugin expanded'
            );
        })
        // try to move plugin to restricted area
        .then(function() {
            // first grid column
            drop = this.getElementBounds(
                '.cms-dragarea:first-child > .cms-draggables > .cms-draggable .cms-draggable:first-child'
            );

            this.evaluate(function() {
                // changing delay here because casper doesn't understand
                // that we want to wait 100 ms after "picking up" the plugin
                // for sortable to work
                CMS.API.StructureBoard.ui.sortables.nestedSortable('option', 'delay', 0);
            });

            // try to move the text plugin into the row
            this.mouse.down('.cms-dragarea:first-child > .cms-draggables > .cms-draggable:last-child');
            this.mouse.move(drop.left, drop.top + drop.height);
        })
        .then(function() {
            test.assertExists('.cms-draggable-disallowed', 'Red line indicates impossibility of a drop');
            this.mouse.up(drop.left, drop.top + drop.height);
        })
        .then(function() {
            test.assertElementCount(
                '.cms-dragarea:nth-child(1) > .cms-draggables > .cms-draggable',
                2,
                'There are still 2 root plugins'
            );

            test.assertEvalEquals(
                function() {
                    return CMS.$('.cms-draggable .cms-draggables .cms-dragitem-text[title*=ColumnPlugin]:first')
                        .closest('.cms-dragitem')
                        .hasClass('cms-dragitem-collapsable');
                },
                false,
                'First grid column has no children'
            );

            test.assertEvalEquals(
                function() {
                    return CMS.$('.cms-draggable .cms-draggables .cms-dragitem-text[title*=ColumnPlugin]:last')
                        .closest('.cms-dragitem')
                        .hasClass('cms-dragitem-collapsable');
                },
                false,
                'Second grid column has no children'
            );

            test.assertEvalEquals(
                function() {
                    return CMS.$('.cms-dragitem-text[title*=MultiColumnPlugin]:last')
                        .closest('.cms-draggable')
                        .find('.cms-draggables')
                        .children().length;
                },
                2,
                'Row has only two children'
            );
        })
        .run(function() {
            test.done();
        });
});
