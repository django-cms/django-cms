'use strict';

// #############################################################################
// User login via the admin panel

var globals = require('./settings/globals');
var messages = require('./settings/messages').page.addContent;
var randomString = require('./helpers/randomString').randomString;

// random text string for filtering and content purposes
var randomText = randomString({ length: 50, withWhitespaces: false });

casper.test.begin('User Add Content', function (test) {
    casper
        .start(globals.editUrl)
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            this.click('.cms-toolbar-item-cms-mode-switcher .cms-btn[href="?build"]');
        })
        .waitUntilVisible('.cms-structure', function () {
            this.click('.cms-submenu-add [data-tooltip="Add plugin"]');
        })

        // cancel plugin creation and ensure no empty plugin
        .waitUntilVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]', function () {
            this.click('.cms-plugin-picker .cms-submenu-item [data-rel="add"]');
        })
        .waitUntilVisible('.cms-modal-open', function () {
            this.setFilter('page.confirm', function () {
                return true;
            });
            this.click('.cms-modal-item-buttons:last-child a');
        })
        .waitWhileVisible('.cms-modal-open', function () {
            this.removeAllFilters('page.confirm');
            this.click('.cms-toolbar-item-cms-mode-switcher .cms-btn[href="?edit"]');
        })
        .waitWhileVisible('.cms-structure', function () {
            test.assertSelectorDoesntHaveText('.cms-plugin p', randomText, messages.noEmptyPlugin);
            this.click('.cms-toolbar-item-cms-mode-switcher .cms-btn[href="?build"]');
        })

        // full plugin creation process
        .waitUntilVisible('.cms-structure', function () {
            this.click('.cms-submenu-add [data-tooltip="Add plugin"]');
        })
        .waitUntilVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]', function () {
            this.sendKeys('.cms-quicksearch input', randomText);
            this.waitWhileVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]', function () {
                test.assertNotVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]',
                    messages.noFilteredResults);
                this.sendKeys('.cms-quicksearch input', 'text', { reset: true });
            });
            this.waitUntilVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]', function () {
                test.assertVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]',
                    messages.filteredPluginAvailable);
            });
            this.then(function () {
                this.click('.cms-plugin-picker .cms-submenu-item [data-rel="add"]');
            });
            // ensure previous content has been changed
            this.waitWhileVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]');
        })
        .withFrame(0, function () {
            casper
                .waitUntilVisible('#text_form', function () {
                    // explicitly put text to ckeditor
                    this.evaluate(function (contentData) {
                        CMS.CKEditor.editor.setData(contentData);
                    }, randomText);
                });
        })
        .then(function () {
            this.click('.cms-modal-buttons .cms-btn-action.default');
        })
        .then(function () {
            this.click('.cms-toolbar-item-cms-mode-switcher .cms-btn[href="?edit"]');
        })
        .waitUntilVisible('.cms-plugin', function () {
            test.assertSelectorHasText('.cms-plugin p', randomText, messages.newPluginVisible);
        })
        .run(function () {
            test.done();
        });
});
