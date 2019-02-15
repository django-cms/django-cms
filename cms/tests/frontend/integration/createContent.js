'use strict';

// #############################################################################
// User login via the admin panel

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var randomString = helpers.randomString;
var casperjs = require('casper');
var xPath = casperjs.selectXPath;
var cms = helpers(casperjs);
// random text string for filtering and content purposes
var randomText = randomString({ length: 50, withWhitespaces: false });

casper.test.setUp(function(done) {
    casper.start().then(cms.login()).then(cms.addPage({ title: 'First page' })).run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.removePage()).then(cms.logout()).run(done);
});

casper.test.begin('User Add Content', function(test) {
    casper
        .start(globals.editUrl)
        .then(cms.switchTo('structure'))
        .waitUntilVisible('.cms-structure', function() {
            this.click('.cms-submenu-add [data-cms-tooltip="Add plugin"]');
        })
        // cancel plugin creation and ensure no empty plugin
        .waitUntilVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]', function() {
            this.click('.cms-plugin-picker .cms-submenu-item [data-rel="add"]');
        })
        .waitForResource(/add-plugin/)
        .wait(2000)
        .withFrame(0, function() {
            // wait until modal fully loads
            return this.waitUntilVisible('#content');
        })
        .then(function() {
            // click on the "Cancel" button
            this.click('.cms-modal-item-buttons:last-child a');
        })
        .waitWhileVisible('.cms-modal-open')
        .then(cms.switchTo('content'))
        .waitWhileVisible('.cms-structure', function() {
            test.assertSelectorDoesntHaveText('.cms-plugin', randomText, "Empty plugin hasn't been created");
        })
        .then(cms.switchTo('structure'))
        // full plugin creation process
        .waitUntilVisible('.cms-structure', function() {
            this.click('.cms-submenu-add [data-cms-tooltip="Add plugin"]');
        })
        .waitUntilVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]', function() {
            this.sendKeys('.cms-quicksearch input', randomText);
            this.waitWhileVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]', function() {
                test.assertNotVisible(
                    '.cms-plugin-picker .cms-submenu-item [data-rel="add"]',
                    'No filtered results for random string'
                );
                this.sendKeys('.cms-quicksearch input', 'text', { reset: true });
            });
            this.waitUntilVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]', function() {
                this.waitFor(function() {
                    return this.evaluate(function() {
                        return CMS.$('.cms-submenu-item [data-rel="add"]:visible').length === 1;
                    });
                }).then(function() {
                    test.assertVisible(
                        '.cms-plugin-picker .cms-submenu-item [data-rel="add"]',
                        'There is text plugin available by the filter: text'
                    );
                });
            });
            this.then(function() {
                this.click(
                    xPath('//div[contains(@class, "cms-modal")]//a[@data-rel="add"]/text()[normalize-space(.)="Text"]')
                );
            });
            // ensure previous content has been changed
            this.waitWhileVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]');
        })
        .withFrame(0, function() {
            casper.waitUntilVisible('.cke_inner', function() {
                // explicitly put text to ckeditor
                this.evaluate(function(contentData) {
                    CMS.CKEditor.editor.setData(contentData);
                }, randomText);
            });
        })
        .then(function() {
            this.click('.cms-modal-buttons .cms-btn-action.default');
        })
        .then(cms.waitUntilContentIsRefreshed())
        .then(cms.switchTo('content'))
        .then(function() {
            test.assertSelectorHasText('p.cms-plugin', randomText, 'Newly created text plugin can be seen on page');
        })
        .run(function() {
            test.done();
        });
});

casper.test.begin('Can switch mode by triggering space', function(test) {
    casper
        .start(globals.editUrl)
        .then(
            cms.addPlugin({
                type: 'TextPlugin',
                content: {
                    id_body: 'sample text'
                }
            })
        )
        .then(function() {
            // triggers space
            this.sendKeys('html', casper.page.event.key.Space);
            test.assertDoesntExist('.cms-structure-mode-structure', 'switch via space worked');
        })
        .then(function() {
            // triggers space again
            this.sendKeys('html', casper.page.event.key.Space);
        })
        .wait(100, function() {
            test.assertExists('.cms-structure-mode-structure', 'switch via space worked');
        })
        .run(function() {
            test.done();
        });
});
