'use strict';

// #############################################################################
// User login via the admin panel

var globals = require('./settings/globals');
var randomString = require('./helpers/randomString').randomString;
var casperjs = require('casper');
var xPath = casperjs.selectXPath;
var cms = require('./helpers/cms')(casperjs);
// random text string for filtering and content purposes
var randomText = randomString({ length: 50, withWhitespaces: false });

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        .run(done);
});

casper.test.tearDown(function (done) {
    casper.start()
        .then(cms.removePage())
        .then(cms.logout())
        .run(done);
});

casper.test.begin('User Add Content', function (test) {
    casper
        .start(globals.editUrl)
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            this.click('.cms-toolbar-item-cms-mode-switcher .cms-btn[href="?build"]');
        })
        .waitUntilVisible('.cms-structure', function () {
            this.click('.cms-submenu-add [data-cms-tooltip="Add plugin"]');
        })

        // cancel plugin creation and ensure no empty plugin
        .waitUntilVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]', function () {
            this.click('.cms-plugin-picker .cms-submenu-item [data-rel="add"]');
        })
        .waitUntilVisible('.cms-modal-morphing')
        .withFrame(0, function () {
            // wait until modal fully loads
            return this.waitUntilVisible('#content');
        })
        .then(function () {
            this.setFilter('page.confirm', function () {
                return true;
            });
            // click on the "Cancel" button
            this.click('.cms-modal-item-buttons:last-child a');
        })
        .waitWhileVisible('.cms-modal-open', function () {
            this.removeAllFilters('page.confirm');
            this.click('.cms-toolbar-item-cms-mode-switcher .cms-btn[href="?edit"]');
        })
        .waitWhileVisible('.cms-structure', function () {
            test.assertSelectorDoesntHaveText('.cms-plugin p', randomText, 'Empty plugin hasn\'t been created');
            this.click('.cms-toolbar-item-cms-mode-switcher .cms-btn[href="?build"]');
        })

        // full plugin creation process
        .waitUntilVisible('.cms-structure', function () {
            this.click('.cms-submenu-add [data-cms-tooltip="Add plugin"]');
        })
        .waitUntilVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]', function () {
            this.sendKeys('.cms-quicksearch input', randomText);
            this.waitWhileVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]', function () {
                test.assertNotVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]',
                    'No filtered results for random string');
                this.sendKeys('.cms-quicksearch input', 'text', { reset: true });
            });
            this.waitUntilVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]', function () {
                this.waitFor(function () {
                    return this.evaluate(function () {
                        return $('.cms-submenu-item [data-rel="add"]:visible').length === 1;
                    });
                }).then(function () {
                    test.assertVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]',
                        'There is text plugin available by the filter: text');
                });
            });
            this.then(function () {
                this.click(xPath('//a[@data-rel="add"]/text()[normalize-space(.)="Text"]'));
            });
            // ensure previous content has been changed
            this.waitWhileVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]');
        })
        .withFrame(0, function () {
            casper
                .waitUntilVisible('.cke_inner', function () {
                    // explicitly put text to ckeditor
                    this.evaluate(function (contentData) {
                        CMS.CKEditor.editor.setData(contentData);
                    }, randomText);
                });
        })
        .then(function () {
            this.click('.cms-modal-buttons .cms-btn-action.default');
        })
        .waitForResource(/edit-plugin/)
        .waitUntilVisible('.cms-toolbar-expanded')
        .then(function () {
            this.click('.cms-toolbar-item-cms-mode-switcher .cms-btn[href="?edit"]');
        })
        .waitUntilVisible('.cms-plugin', function () {
            test.assertSelectorHasText('.cms-plugin p', randomText, 'Newly created text plugin can be seen on page');
        })
        .run(function () {
            test.done();
        });
});

casper.test.begin('Can switch mode by triggering space', function (test) {
    casper
        .start(globals.editUrl)
        .then(cms.addPlugin({
            type: 'TextPlugin',
            content: {
                id_body: 'sample text'
            }
        }))
        .then(function () {
            // triggers space
            this.sendKeys('html', casper.page.event.key.Space);
            // checks the name of the page which gets shown only on content mode
            test.assertNotVisible('.cms-structure',  'switch via space worked');
        })
        .then(function () {
            // triggers space again
            this.sendKeys('html', casper.page.event.key.Space);
            test.assertVisible('.cms-structure',  'switch via space worked');
        })
        .run(function () {
            test.done();
        });
});
