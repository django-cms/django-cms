/* global document */
'use strict';

// #############################################################################
// Clipboard

var casperjs = require('casper');
var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers(casperjs);
var xPath = casperjs.selectXPath;

casper.test.setUp(function(done) {
    casper
        .start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        .then(
            cms.addPlugin({
                type: 'TextPlugin',
                content: {
                    id_body: 'Test text'
                }
            })
        )
        .then(
            cms.addPlugin({
                type: 'TextPlugin',
                content: {
                    id_body: 'Another Test text'
                }
            })
        )
        .run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.removePage()).then(cms.logout()).run(done);
});

casper.test.begin('Copy/paste plugin from the structure board with dnd', function(test) {
    var contentNumber;

    casper
        .start(globals.editUrl)
        // go to the Structure mode
        .then(cms.switchTo('structure'))
        // click settings for last content plugin
        .waitUntilVisible('.cms-structure', function() {
            // save initial number of content plugins
            contentNumber = this.evaluate(function() {
                return document.querySelectorAll('.cms-structure-content .cms-draggable').length;
            });
            // click settings for last content plugin
            this.click('.cms-structure .cms-draggable:last-child .cms-submenu-settings');
        })
        // check that there is something now in the clipboard
        .then(function() {
            test.assertElementCount('.cms-clipboard .cms-draggable', 0, 'No plugins in clipboard');
        })
        // select copy button from dropdown list
        .waitUntilVisible('.cms-structure .cms-draggable:last-child .cms-submenu-item a[data-rel="copy"]', function() {
            this.click('.cms-structure .cms-draggable:last-child .cms-submenu-item a[data-rel="copy"]');
        })
        .waitForResource(/copy-plugins/)
        // check that there is something now in the clipboard
        .then(function() {
            test.assertElementCount('.cms-clipboard .cms-draggable', 1, '1 plugin in clipboard');
        })
        .waitForSelector('.cms-toolbar-expanded')
        .then(function() {
            // click on "Example.com" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(1) > a');
        })
        // opening "Clipboard" menu item
        .wait(10, function() {
            this.click(xPath('//a[.//span[text()[contains(.,"Clipboard")]]]'));
        })
        // wait until clipboard modal is open
        .waitUntilVisible('.cms-modal-frame .cms-clipboard-containers', function() {
            var placeholder = this.getElementBounds('.cms-dragarea:nth-child(2) .cms-draggables');

            this.evaluate(function() {
                // changing delay here because casper doesn't understand
                // that we want to wait 100 ms after "picking up" the plugin
                // for sortable to work
                CMS.API.StructureBoard.ui.sortables.nestedSortable('option', 'delay', 0);
            });

            this.mouse.down('.cms-clipboard-containers .cms-draggable');
            this.mouse.move(placeholder.left + placeholder.width / 2, placeholder.top + 1 + placeholder.height * 0);
            this.mouse.move(placeholder.left + placeholder.width / 2 + 1, placeholder.top + 1 + placeholder.height * 0);
        })
        .wait(300)
        .then(function() {
            this.mouse.up('.cms-dragarea:nth-child(2) .cms-draggables');
            // check before reload
            test.assertElementCount(
                '.cms-structure .cms-draggables .cms-draggable',
                contentNumber + 1,
                'Copy plugin successful'
            );
        })
        .waitForResource(/move-plugin/)
        .then(function() {
            return this.reload();
        })
        // check if number of content plugins has been increased (after reload)
        .then(cms.switchTo('structure'))
        .then(function() {
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
        .then(function() {
            // click on "Example.com" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(1) > a');
        })
        // opening "Clipboard" menu item
        .wait(10, function() {
            this.click(xPath('//a[.//span[text()[contains(.,"Clear clipboard")]]]'));
        })
        .waitForResource(/clear/)
        .then(function() {
            return this.reload();
        })
        // check that there is nothing now in the clipboard
        .then(function() {
            test.assertElementCount('.cms-clipboard .cms-draggable', 0, 'Clipboard is now empty');
        })
        .run(function() {
            test.done();
        });
});

casper.test.begin('Copy/paste plugin from the structure board with paste button into a plugin', function(test) {
    var contentNumber;

    casper
        .start()
        .then(
            cms.addPlugin({
                type: 'StylePlugin'
            })
        )
        .thenOpen(globals.editUrl)
        // go to the Structure mode
        .then(cms.switchTo('structure'))
        // click settings for last content plugin
        .waitUntilVisible('.cms-structure', function() {
            // save initial number of content plugins
            contentNumber = this.evaluate(function() {
                return document.querySelectorAll('.cms-structure-content .cms-draggable').length;
            });
            // click settings for first content plugin
            this.click('.cms-structure .cms-draggable .cms-submenu-settings');
        })
        // check that there is something now in the clipboard
        .then(function() {
            test.assertElementCount('.cms-clipboard .cms-draggable', 0, 'No plugins in clipboard');
        })
        // select copy button from dropdown list
        .waitUntilVisible('.cms-structure .cms-draggable .cms-submenu-item a[data-rel="copy"]', function() {
            this.click('.cms-structure .cms-draggable .cms-submenu-item a[data-rel="copy"]');
        })
        .waitForResource(/copy-plugins/)
        // check that there is something now in the clipboard
        .then(function() {
            test.assertElementCount('.cms-clipboard .cms-draggable', 1, '1 plugin in clipboard');
        })
        .waitForSelector('.cms-toolbar-expanded')
        .then(function() {
            this.click('.cms-structure .cms-draggable:last-child .cms-submenu-settings');
        })
        // choose paste option inside dropdown menu
        .waitUntilVisible('.cms-submenu-dropdown', function() {
            this.click(
                '.cms-structure .cms-draggable:last-child .cms-submenu-dropdown ' +
                    '.cms-submenu-item a[data-rel="paste"]'
            );
        })
        .then(function() {
            test.assertElementCount(
                '.cms-structure .cms-draggables .cms-draggable',
                contentNumber + 1,
                'Paste after cutting plugin successful'
            );
        })
        // wait till the paste actually succeeds
        .waitForResource(/move\-plugin/)
        .wait(1000)
        .reload()
        .then(cms.switchTo('structure'))
        .waitUntilVisible('.cms-structure')
        // check that number of content plugins has been indeed increased
        .then(function() {
            test.assertElementCount(
                '.cms-structure .cms-draggables .cms-draggable',
                contentNumber + 1,
                'Paste after cutting plugin successful'
            );
        })
        .then(cms.clearClipboard())
        .run(function() {
            test.done();
        });
});

casper.test.begin('Copy placeholder contents from the structure board', function(test) {
    casper
        .start(globals.editUrl)
        // go to the Structure mode
        .then(cms.switchTo('structure'))
        .waitUntilVisible('.cms-structure', function() {
            // click settings for last content plugin
            this.click('.cms-structure .cms-dragarea:nth-child(2) .cms-submenu-settings');
        })
        // check that there is nothing in the clipboard
        .then(function() {
            test.assertElementCount('.cms-clipboard .cms-draggable', 0, 'No plugins in clipboard');
        })
        .waitUntilVisible('.cms-structure .cms-dragarea:nth-child(2) .cms-submenu-item a[data-rel="copy"]', function() {
            test.assertVisible(
                '.cms-structure .cms-dragarea:nth-child(2) ' +
                    '.cms-submenu-item.cms-submenu-item-disabled a[data-rel="copy"]',
                'Copy all is disabled if there are no plugins'
            );
            this.click('.cms-structure .cms-dragarea:nth-child(2) .cms-submenu-item a[data-rel="copy"]');
        })
        .then(function() {
            test.assertNotVisible(
                '.cms-structure .cms-dragarea:nth-child(2) ' +
                    '.cms-submenu-item.cms-submenu-item-disabled a[data-rel="copy"]',
                'Dropdown hides if disabled item is clicked'
            );
        })
        // try to copy contents of non-empty placeholder
        .then(function() {
            this.click('.cms-structure .cms-dragarea:nth-child(1) .cms-submenu-settings');
        })
        // check that there is still nothing in the clipboard
        .then(function() {
            test.assertElementCount('.cms-clipboard .cms-draggable', 0, 'No plugins in clipboard');
        })
        // try to copy contents of empty placeholder
        .waitUntilVisible('.cms-structure .cms-dragarea:nth-child(1) .cms-submenu-item a[data-rel="copy"]', function() {
            this.click('.cms-structure .cms-dragarea:nth-child(1) .cms-submenu-item a[data-rel="copy"]');
        })
        .waitForResource(/copy-plugins/)
        // check that there is something now in the clipboard
        .then(function() {
            test.assertElementCount('.cms-clipboard .cms-draggable', 1, '1 plugin in clipboard');
            test.assertExists('.cms-clipboard-containers [title*="Placeholder"]', '"Placeholder" plugin was copied');
        })
        // click settings for second placeholder
        .waitForSelector('.cms-toolbar-expanded', function() {
            // click settings for last content plugin
            this.click('.cms-structure .cms-dragarea:nth-child(2) .cms-submenu-settings');
        })
        // select paste button from dropdown list
        .waitUntilVisible(
            '.cms-structure .cms-dragarea:nth-child(2) .cms-submenu-item a[data-rel="paste"]',
            function() {
                this.click('.cms-structure .cms-dragarea:nth-child(2) .cms-submenu-item a[data-rel="paste"]');
            }
        )
        .waitForResource(/move-plugin/)
        .wait(2000)
        .then(cms.switchTo('structure'))
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertElementCount('.cms-structure .cms-draggable', 4, 'Four plugins present on the page');
        })
        .then(cms.clearClipboard())
        .run(function() {
            test.done();
        });
});

casper.test.begin('Plugins with parent restriction cannot be pasted in incorrect parents (paste button)', function(
    test
) {
    casper
        .start(globals.editUrl)
        .waitForSelector('.cms-toolbar-expanded')
        // creates 3 plugins - row > col + col
        .then(
            cms.addPlugin({
                type: 'MultiColumnPlugin',
                content: {
                    id_create: 2
                }
            })
        )
        .thenOpen(globals.editUrl)
        // go to the Structure mode
        .then(cms.switchTo('structure'))
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertElementCount('.cms-structure .cms-draggable', 5, 'Five plugins present on the page');
        })
        // check that there is nothing now in the clipboard
        .then(function() {
            test.assertElementCount('.cms-clipboard .cms-draggable', 0, 'No plugins in clipboard');
        })
        // expand all plugins
        .then(cms.expandPlaceholderPlugins('.cms-dragarea:first-child'))
        // click settings for last content plugin (second column)
        .waitUntilVisible('.cms-structure', function() {
            // click settings for last content plugin
            this.click('.cms-structure .cms-draggable .cms-draggable:last-child .cms-submenu-settings');
        })
        // select copy button from dropdown list
        .waitUntilVisible(
            '.cms-structure .cms-draggable .cms-draggable:last-child .cms-submenu-item a[data-rel="copy"]',
            function() {
                this.click(
                    '.cms-structure .cms-draggable .cms-draggable:last-child .cms-submenu-item a[data-rel="copy"]'
                );
            }
        )
        .waitForResource(/copy-plugins/)
        .wait(200)
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertExists('.cms-clipboard-containers [title*="ColumnPlugin"]', 'Correct plugin was copied');
        })
        .then(function() {
            // click settings for last content plugin, cause that actually correctly refreshes
            // pasting possibility
            this.click('.cms-structure .cms-draggable:last-child .cms-submenu-settings');
        })
        .then(function() {
            test.assertEvalEquals(
                function() {
                    return CMS.$('.cms-structure .cms-submenu-item:has("[data-cms-icon=paste]")').length;
                },
                7,
                'There are 7 pasting areas'
            );

            test.assertEvalEquals(
                function() {
                    return CMS.$('.cms-structure .cms-submenu-item-disabled:has("[data-cms-icon=paste]")').length;
                },
                6,
                '6 items do not allow pasting'
            );

            test.assertEvalEquals(
                function() {
                    return CMS.$(
                        '.cms-structure .cms-submenu-item:not(.cms-submenu-item-disabled)' +
                            ':has("[data-cms-icon=paste]")'
                    ).length;
                },
                1,
                '1 item does allow pasting'
            );

            test.assertEvalEquals(
                function() {
                    return CMS.$(
                        '.cms-structure .cms-submenu-item:not(.cms-submenu-item-disabled)' +
                            ':has("[data-cms-icon=paste]")'
                    )
                        .closest('.cms-draggable')
                        .find('.cms-dragitem-text strong')
                        .eq(0)
                        .text();
                },
                'Multi Columns',
                '1 item that does allow pasting is indeed a Row plugin'
            );
        })
        // try to paste column in a column
        .then(function() {
            // click settings for last content plugin
            this.click('.cms-structure .cms-draggable .cms-draggable:last-child .cms-submenu-settings');
        })
        // click on the paste button from dropdown list
        .waitUntilVisible(
            '.cms-structure .cms-draggable .cms-draggable:last-child .cms-submenu-item a[data-rel="paste"]',
            function() {
                this.mouse.click(
                    '.cms-structure .cms-draggable .cms-draggable:last-child .cms-submenu-item a[data-rel="paste"]'
                );
            }
        )
        // nothing should happen
        .then(function() {
            test.assertVisible(
                '.cms-structure .cms-draggable .cms-draggable:last-child .cms-submenu-item a[data-rel="paste"]',
                'Nothing happens'
            );
        })
        .wait(2000, function() {
            test.assertVisible(
                '.cms-structure .cms-draggable .cms-draggable:last-child .cms-submenu-item a[data-rel="paste"]',
                'Nothing at all'
            );
        })
        .then(function() {
            // click settings for the row plugin
            this.click('.cms-dragarea > .cms-draggables > .cms-draggable:last-child .cms-submenu-settings');
        })
        // click on the paste button from dropdown list
        .waitUntilVisible(
            '.cms-dragarea > .cms-draggables > .cms-draggable:last-child .cms-submenu-item a[data-rel="paste"]',
            function() {
                this.mouse.click(
                    '.cms-dragarea > .cms-draggables > .cms-draggable:last-child ' +
                        '.cms-submenu-item a[data-rel="paste"]'
                );
            }
        )
        .waitForResource(/copy-plugins/)
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertElementCount('.cms-structure .cms-draggable', 6, 'Six plugins present on the page');
            test.assertElementCount(
                '.cms-structure .cms-draggables .cms-draggables .cms-draggable',
                3,
                'Three columns'
            );
        })
        .then(cms.clearClipboard())
        .run(function() {
            test.done();
        });
});

casper.test.begin('Plugins with parent restriction cannot be pasted in incorrect parents (dragndrop)', function(test) {
    var column;
    var row;

    casper
        .start(globals.editUrl)
        .waitForSelector('.cms-toolbar-expanded')
        // creates 3 plugins - row > col + col
        .then(
            cms.addPlugin({
                type: 'MultiColumnPlugin',
                content: {
                    id_create: 2
                }
            })
        )
        .thenOpen(globals.editUrl)
        // go to the Structure mode
        .then(cms.switchTo('structure'))
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertElementCount('.cms-structure .cms-draggable', 5, 'Five plugins present on the page');
        })
        // check that there is nothing now in the clipboard
        .then(function() {
            test.assertElementCount('.cms-clipboard .cms-draggable', 0, 'No plugins in clipboard');
        })
        // expand all plugins
        .then(cms.expandPlaceholderPlugins('.cms-dragarea:first-child'))
        // click settings for last content plugin (second column)
        .waitUntilVisible('.cms-structure', function() {
            // click settings for last content plugin
            this.click('.cms-structure .cms-draggable .cms-draggable:last-child .cms-submenu-settings');
        })
        // select copy button from dropdown list
        .waitUntilVisible(
            '.cms-structure .cms-draggable .cms-draggable:last-child .cms-submenu-item a[data-rel="copy"]',
            function() {
                this.click(
                    '.cms-structure .cms-draggable .cms-draggable:last-child .cms-submenu-item a[data-rel="copy"]'
                );
            }
        )
        .waitForResource(/copy-plugins/)
        .waitUntilVisible('.cms-structure', function() {
            // click settings for last content plugin
            this.click('.cms-structure .cms-draggable:last-child .cms-submenu-settings');
        })
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertExists('.cms-clipboard-containers [title*="ColumnPlugin"]', 'Correct plugin was copied');

            test.assertEvalEquals(
                function() {
                    return CMS.$('.cms-structure .cms-submenu-item:has("[data-cms-icon=paste]")').length;
                },
                7,
                'There are 7 pasting areas'
            );

            test.assertEvalEquals(
                function() {
                    return CMS.$('.cms-structure .cms-submenu-item-disabled:has("[data-cms-icon=paste]")').length;
                },
                6,
                '6 items do not allow pasting'
            );

            test.assertEvalEquals(
                function() {
                    return CMS.$(
                        '.cms-structure .cms-submenu-item:not(.cms-submenu-item-disabled)' +
                            ':has("[data-cms-icon=paste]")'
                    ).length;
                },
                1,
                '1 item does allow pasting'
            );

            test.assertEvalEquals(
                function() {
                    return CMS.$(
                        '.cms-structure .cms-submenu-item:not(.cms-submenu-item-disabled)' +
                            ':has("[data-cms-icon=paste]")'
                    )
                        .closest('.cms-draggable')
                        .find('.cms-dragitem-text strong')
                        .eq(0)
                        .text();
                },
                'Multi Columns',
                '1 item that does allow pasting is indeed a Row plugin'
            );
        })
        // try to paste column into column
        .then(function() {
            // click on "Example.com" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(1) > a');
        })
        // opening "Clipboard" menu item
        .wait(10, function() {
            this.click(xPath('//a[.//span[text()[contains(.,"Clipboard")]]]'));
        })
        // wait until clipboard modal is open
        .waitUntilVisible('.cms-modal-frame .cms-clipboard-containers', function() {
            column = this.getElementBounds('.cms-structure .cms-draggable .cms-draggable:first-child');

            this.evaluate(function() {
                // changing delay here because casper doesn't understand
                // that we want to wait 100 ms after "picking up" the plugin
                // for sortable to work
                CMS.API.StructureBoard.ui.sortables.nestedSortable('option', 'delay', 0);
            });

            this.mouse.down('.cms-clipboard-containers .cms-draggable');
            this.mouse.move(column.left + column.width / 2, column.top + column.height);
            this.mouse.move(column.left + column.width / 2 + 30, column.top + column.height);
        })
        .then(function() {
            test.assertExists('.cms-draggable-disallowed', 'Red line indicates impossibility of a drop');
            this.mouse.up(column.left + column.width / 2 + 30, column.top + column.height);
            test.assertElementCount('.cms-structure .cms-draggable', 5, 'Pasting plugin was not successful');
        })
        // try to paste plugin into row
        // wait until clipboard modal is open
        .waitUntilVisible('.cms-modal-frame .cms-clipboard-containers', function() {
            row = this.getElementBounds('.cms-dragarea > .cms-draggables > .cms-draggable:last-child > .cms-dragitem');

            this.evaluate(function() {
                // changing delay here because casper doesn't understand
                // that we want to wait 100 ms after "picking up" the plugin
                // for sortable to work
                CMS.API.StructureBoard.ui.sortables.nestedSortable('option', 'delay', 0);
            });

            this.mouse.down('.cms-clipboard-containers .cms-draggable');
            this.mouse.move(row.left + row.width / 2, row.top + row.height);
            this.mouse.move(row.left + row.width / 2 + 1, row.top + row.height);
        })
        .then(function() {
            test.assertDoesntExist('.cms-draggable-disallowed', 'No red line');
            this.mouse.up(row.left + row.width / 2, row.top + row.height);
            test.assertElementCount('.cms-structure .cms-draggable', 6, 'Pasting successful');
        })
        .waitForResource(/move-plugin/)
        .then(function() {
            return this.reload();
        })
        .then(cms.switchTo('structure'))
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertElementCount('.cms-structure .cms-draggable', 6, 'Six plugins present on the page');
            test.assertElementCount(
                '.cms-structure .cms-draggables .cms-draggables .cms-draggable',
                3,
                'Three columns'
            );
        })
        .then(cms.clearClipboard())
        .run(function() {
            test.done();
        });
});

casper.test.begin('Plugins with child restriction cannot accept other children (paste button)', function(test) {
    casper
        .start(globals.editUrl)
        .waitForSelector('.cms-toolbar-expanded')
        // creates 3 plugins - row > col + col
        .then(
            cms.addPlugin({
                type: 'MultiColumnPlugin',
                content: {
                    id_create: 2
                }
            })
        )
        .thenOpen(globals.editUrl)
        // go to the Structure mode
        .then(cms.switchTo('structure'))
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertElementCount('.cms-structure .cms-draggable', 5, 'Five plugins present on the page');
        })
        // check that there is nothing now in the clipboard
        .then(function() {
            test.assertElementCount('.cms-clipboard .cms-draggable', 0, 'No plugins in clipboard');
        })
        // expand all plugins
        .then(cms.expandPlaceholderPlugins('.cms-dragarea:first-child'))
        // click settings for first content plugin (Test text)
        .waitUntilVisible('.cms-structure', function() {
            // click settings first content plugin (Test text)
            this.click('.cms-dragarea > .cms-draggables > .cms-draggable .cms-submenu-settings');
        })
        // select copy button from dropdown list
        .waitUntilVisible(
            '.cms-dragarea > .cms-draggables > .cms-draggable .cms-submenu-item a[data-rel="copy"]',
            function() {
                this.click('.cms-dragarea > .cms-draggables > .cms-draggable .cms-submenu-item a[data-rel="copy"]');
            }
        )
        .waitForResource(/copy-plugins/)
        .then(function() {
            this.reload();
        })
        .waitForSelector('.cms-toolbar-expanded')
        .then(cms.switchTo('structure'))
        // check that there is something now in the clipboard
        .then(function() {
            test.assertElementCount('.cms-clipboard .cms-draggable', 1, '1 plugin in clipboard');
            test.assertExists('.cms-clipboard-containers [title*="TextPlugin"]', 'Correct plugin was copied');
        })
        // check that we can't paste into a row
        .then(function() {
            test.assertEvalEquals(
                function() {
                    return CMS.$(
                        '.cms-structure .cms-draggables .cms-submenu-item:not(.cms-submenu-item-disabled)' +
                            ':has("[data-cms-icon=paste]")'
                    ).length;
                },
                2,
                '2 plugins do allow pasting'
            );

            test.assertEvalEquals(
                function() {
                    return CMS.$(
                        '.cms-structure .cms-draggables .cms-submenu-item:not(.cms-submenu-item-disabled)' +
                            ':has("[data-cms-icon=paste]")'
                    )
                        .closest('.cms-draggable')
                        .find('.cms-dragitem-text strong')
                        .eq(0)
                        .text();
                },
                'Column',
                'First item that does allow pasting is a Col plugin'
            );

            test.assertEvalEquals(
                function() {
                    return CMS.$(
                        '.cms-structure .cms-draggables .cms-submenu-item:not(.cms-submenu-item-disabled)' +
                            ':has("[data-cms-icon=paste]")'
                    )
                        .closest('.cms-draggable')
                        .find('.cms-dragitem-text strong')
                        .eq(1)
                        .text();
                },
                'Column',
                'Another item that does allow pasting is a Col plugin'
            );
        })
        // try to paste it in a row
        .then(function() {
            // click settings for the row plugin
            this.click('.cms-dragarea > .cms-draggables > .cms-draggable:last-child .cms-submenu-settings');
        })
        // click on the paste button from dropdown list
        .waitUntilVisible(
            '.cms-dragarea > .cms-draggables > .cms-draggable:last-child .cms-submenu-item a[data-rel="paste"]',
            function() {
                this.mouse.click(
                    '.cms-dragarea > .cms-draggables > .cms-draggable:last-child ' +
                        '.cms-submenu-item a[data-rel="paste"]'
                );
            }
        )
        // nothing should happen
        .then(function() {
            test.assertVisible(
                '.cms-dragarea > .cms-draggables > .cms-draggable:last-child ' +
                    '.cms-submenu-item a[data-rel="paste"]',
                'Nothing happens'
            );
        })
        .wait(2000, function() {
            test.assertVisible(
                '.cms-dragarea > .cms-draggables > .cms-draggable:last-child ' +
                    '.cms-submenu-item a[data-rel="paste"]',
                'Nothing at all'
            );
        })
        // click settings for last content plugin (second column)
        .waitUntilVisible('.cms-structure', function() {
            // click settings for last content plugin
            this.click('.cms-structure .cms-draggable .cms-draggable:last-child .cms-submenu-settings');
        })
        // select paste button from dropdown list
        .waitUntilVisible(
            '.cms-structure .cms-draggable .cms-draggable:last-child .cms-submenu-item a[data-rel="paste"]',
            function() {
                this.click(
                    '.cms-structure .cms-draggable .cms-draggable:last-child .cms-submenu-item a[data-rel="paste"]'
                );
            }
        )
        .waitForResource(/copy-plugins/)
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertElementCount('.cms-structure .cms-draggable', 6, 'Six plugins present on the page');
            test.assertElementCount(
                '.cms-structure .cms-draggables .cms-draggables .cms-draggable:last-child .cms-draggables ' +
                    '.cms-dragitem-text[title*="TextPlugin"]',
                1,
                'Text plugin is successfully pasted in the column'
            );
        })
        .then(cms.clearClipboard())
        .run(function() {
            test.done();
        });
});

casper.test.begin('Plugins with child restriction cannot accept other children (dragndrop)', function(test) {
    var row;
    var column;

    casper
        .start(globals.editUrl)
        .waitForSelector('.cms-toolbar-expanded')
        // creates 3 plugins - row > col + col
        .then(
            cms.addPlugin({
                type: 'MultiColumnPlugin',
                content: {
                    id_create: 2
                }
            })
        )
        .thenOpen(globals.editUrl)
        // go to the Structure mode
        .then(cms.switchTo('structure'))
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertElementCount('.cms-structure .cms-draggable', 5, 'Five plugins present on the page');
        })
        // check that there is nothing now in the clipboard
        .then(function() {
            test.assertElementCount('.cms-clipboard .cms-draggable', 0, 'No plugins in clipboard');
        })
        // expand all plugins
        .then(cms.expandPlaceholderPlugins('.cms-dragarea:first-child'))
        // click settings for first content plugin (Test text)
        .waitUntilVisible('.cms-structure', function() {
            // click settings first content plugin (Test text)
            this.click('.cms-dragarea > .cms-draggables > .cms-draggable .cms-submenu-settings');
        })
        // select copy button from dropdown list
        .waitUntilVisible(
            '.cms-dragarea > .cms-draggables > .cms-draggable .cms-submenu-item a[data-rel="copy"]',
            function() {
                this.click('.cms-dragarea > .cms-draggables > .cms-draggable .cms-submenu-item a[data-rel="copy"]');
            }
        )
        .waitForResource(/copy-plugins/)
        .waitForSelector('.cms-toolbar-expanded')
        // check that there is something now in the clipboard
        .then(function() {
            test.assertElementCount('.cms-clipboard .cms-draggable', 1, '1 plugin in clipboard');
            test.assertExists('.cms-clipboard-containers [title*="TextPlugin"]', 'Correct plugin was copied');
        })
        .then(function() {
            this.reload();
        })
        .then(cms.switchTo('structure'))
        // check that we can't paste into a row
        .then(function() {
            test.assertEvalEquals(
                function() {
                    return CMS.$(
                        '.cms-structure .cms-draggables .cms-submenu-item:not(.cms-submenu-item-disabled)' +
                            ':has("[data-cms-icon=paste]")'
                    ).length;
                },
                2,
                '2 plugins do allow pasting'
            );

            test.assertEvalEquals(
                function() {
                    return CMS.$(
                        '.cms-structure .cms-draggables .cms-submenu-item:not(.cms-submenu-item-disabled)' +
                            ':has("[data-cms-icon=paste]")'
                    )
                        .closest('.cms-draggable')
                        .find('.cms-dragitem-text strong')
                        .eq(0)
                        .text();
                },
                'Column',
                'First item that does allow pasting is a Col plugin'
            );

            test.assertEvalEquals(
                function() {
                    return CMS.$(
                        '.cms-structure .cms-draggables .cms-submenu-item:not(.cms-submenu-item-disabled)' +
                            ':has("[data-cms-icon=paste]")'
                    )
                        .closest('.cms-draggable')
                        .find('.cms-dragitem-text strong')
                        .eq(1)
                        .text();
                },
                'Column',
                'Another item that does allow pasting is a Col plugin'
            );
        })
        // try to paste text into row
        .then(function() {
            // click on "Example.com" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(1) > a');
        })
        // opening "Clipboard" menu item
        .wait(10, function() {
            this.click(xPath('//a[.//span[text()[contains(.,"Clipboard")]]]'));
        })
        // wait until clipboard modal is open
        .waitUntilVisible('.cms-modal-frame .cms-clipboard-containers', function() {
            row = this.getElementBounds('.cms-dragarea > .cms-draggables > .cms-draggable:last-child > .cms-dragitem');

            this.evaluate(function() {
                // changing delay here because casper doesn't understand
                // that we want to wait 100 ms after "picking up" the plugin
                // for sortable to work
                CMS.API.StructureBoard.ui.sortables.nestedSortable('option', 'delay', 0);
            });

            this.mouse.down('.cms-clipboard-containers .cms-draggable');
            this.mouse.move(row.left + row.width / 2, row.top + row.height);
            this.mouse.move(row.left + row.width / 2 + 1, row.top + row.height);
            test.assertExists('.cms-draggable-disallowed', 'Red line indicates impossibility of a drop');
        })
        .then(function() {
            this.mouse.up(row.left + row.width / 2, row.top + row.height);
            test.assertElementCount('.cms-structure .cms-draggable', 5, 'Pasting plugin was not successful');
        })
        // try to paste into a column
        .waitUntilVisible('.cms-modal-frame .cms-clipboard-containers', function() {
            column = this.getElementBounds('.cms-structure .cms-draggable .cms-draggable:first-child');

            this.evaluate(function() {
                // changing delay here because casper doesn't understand
                // that we want to wait 100 ms after "picking up" the plugin
                // for sortable to work
                CMS.API.StructureBoard.ui.sortables.nestedSortable('option', 'delay', 0);
            });

            this.mouse.down('.cms-clipboard-containers .cms-draggable');
            this.mouse.move(column.left + column.width / 2, column.top + column.height);
            this.mouse.move(column.left + column.width / 2 + 1, column.top + column.height);
        })
        .then(function() {
            test.assertDoesntExist('.cms-draggable-disallowed', 'No red line');
            this.mouse.up(column.left + column.width / 2, column.top + column.height);
            test.assertElementCount('.cms-structure .cms-draggable', 6, 'Pasting successful');
        })
        .waitForResource(/move-plugin/)
        .then(function() {
            return this.reload();
        })
        .waitForSelector('.cms-toolbar-expanded')
        .then(cms.switchTo('structure'))
        .then(function() {
            test.assertElementCount('.cms-structure .cms-draggable', 6, 'Six plugins present on the page');
            test.assertElementCount(
                '.cms-structure .cms-draggables .cms-draggables .cms-draggable:first-child .cms-draggables ' +
                    '.cms-dragitem-text[title*="TextPlugin"]',
                1,
                'Text plugin is successfully pasted in the column'
            );
        })
        .then(cms.clearClipboard())
        .run(function() {
            test.done();
        });
});
