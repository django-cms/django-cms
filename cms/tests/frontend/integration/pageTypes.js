'use strict';

// #############################################################################
// Page types and templates

var casperjs = require('casper');
var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers(casperjs);
var xPath = casperjs.selectXPath;

var SECOND_PAGE_TITLE = 'Second';

casper.test.setUp(function(done) {
    casper
        .start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        // adding second one because first is published by default
        .then(cms.addPage({ title: SECOND_PAGE_TITLE }))
        .run(done);
});

casper.test.tearDown(function(done) {
    casper
        .start()
        .then(cms.removePage({ title: SECOND_PAGE_TITLE }))
        .then(cms.removePage({ title: 'First page' })) // removing both pages
        .then(cms.logout())
        .run(done);
});

casper.test.begin('Different page template can be applied', function(test) {
    casper
        .start(globals.editUrl)
        .waitForSelector('.cms-toolbar-expanded')
        // wait more for the logo to finish loading?
        .wait(300, function() {
            test.assertDoesntExist('h1', 'Page is "fullwidth.html"');
            // click on "Page" menu item
            this.click('.cms-toolbar-item-navigation > li + li > a');
        })
        // expand "Templates" menu item
        .wait(10, function() {
            var position = this.getElementBounds(xPath('//a[.//span[text()[contains(.,"Templates")]]]'));

            // simulating mouseenter event
            this.mouse.move(position.left + 1, position.top - 1);
            this.mouse.move(position.left + 1, position.top + 1);
            this.wait(10);
        })
        // wait till it expands
        .waitForSelector('.cms-toolbar-item-navigation-hover .cms-toolbar-item-navigation-hover', function() {
            // move right
            this.mouse.move(xPath('//a[.//span[text()[contains(.,"Fullwidth")]]]'));
            // move down
            this.mouse.move(xPath('//a[.//span[text()[contains(.,"Standard page")]]]'));
            this.click(xPath('//a[.//span[text()[contains(.,"Standard page")]]]'));
        })
        .waitForResource(/change-template/)
        .waitForSelector('.cms-ready', function() {
            test.assertSelectorHasText(
                '.cms-toolbar-item-navigation-active',
                'Standard page',
                'Correct template is highlighted in the menu'
            );
            test.assertExists('h1', 'Page is "page.html"');
            test.assertSelectorHasText('h1', 'This is a custom page template', 'Page is "page.html"');
        })
        .run(function() {
            test.done();
        });
});

casper.test.begin('PageType can be created and used', function(test) {
    casper
        .start()
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
                    id_body: 'Left column'
                },
                parent: '.cms-dragarea:first-child .cms-draggable .cms-draggable:first-child'
            })
        )
        .then(
            cms.addPlugin({
                type: 'TextPlugin',
                content: {
                    id_body: 'Right column'
                },
                parent: '.cms-dragarea:first-child .cms-draggable .cms-draggable:last-child'
            })
        )
        .thenOpen(globals.editUrl)
        .waitForSelector('.cms-toolbar-expanded', function() {
            // click on "Page" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(2) > a');
        })
        // opening "Save as Page Type" menu item
        .wait(10, function() {
            this.click(xPath('//a[.//span[text()[contains(.,"Save as Page Type")]]]'));
        })
        // switch to "Add Page Type" modal
        .withFrame(0, function() {
            // wait until form is loaded
            casper
                .waitUntilVisible('#page_form', function() {
                    test.assertField('title', '', 'Page type modal available');
                })
                .then(function() {
                    this.sendKeys('input[name="title"]', 'Two column layout');
                })
                .then(function() {
                    test.assertField('slug', 'two-column-layout', 'Slug generated correctly');
                });
        })
        // submit the modal
        .then(function() {
            this.click('.cms-modal-item-buttons .cms-btn-action');
        })
        .waitForResource(/cms\/pagetype\/add/)
        .waitForUrl(/page_types/)
        .then(function() {
            test.assertUrlMatch(/page_types\/two-column-layout/, 'Page Type created');
        })
        .thenOpen(globals.editUrl)
        // create new page through Page > Create Page > New Page
        .waitForSelector('.cms-toolbar-expanded', function() {
            this.click('.cms-toolbar-item-navigation > li:nth-child(2) > a');
        })
        // expand "Page" menu item
        .wait(10, function() {
            var position = this.getElementBounds(xPath('//a[.//span[text()[contains(.,"Create Page")]]]'));

            // simulating mouseenter event
            this.mouse.move(position.left + 1, position.top - 1);
            this.mouse.move(position.left + 1, position.top + 1);
            this.wait(10);
        })
        // wait till it expands
        .wait(10, function() {
            // move right
            this.mouse.move(xPath('//a[.//span[text()[contains(.,"New Page")]]]'));
            this.click(xPath('//a[.//span[text()[contains(.,"New Page")]]]'));
        })
        // then with modal
        .withFrame(0, function() {
            casper.waitUntilVisible('#page_form', function() {
                // need to get the value of correct option
                var pageType = this.getElementAttribute(
                    xPath('//option[text()[contains(.,"Two column layout")]]'),
                    'value'
                );

                // fill the form
                this.fill(
                    '#page_form',
                    {
                        title: 'New Shiny Page',
                        slug: 'new-shiny-page',
                        source: pageType
                    },
                    false
                );
            });
        })
        // submit the page creation form
        .then(function() {
            this.click('.cms-modal-item-buttons .cms-btn-action');
        })
        // wait till it succeeds
        .waitForResource(/cms\/page\/add/)
        // and we are redirected to a newly created page
        .waitForUrl(/new-shiny-page/)
        .waitForSelector('.cms-toolbar-expanded')
        .then(function() {
            test.assertUrlMatch(/new-shiny-page/, 'Page was created');
            test.assertSelectorHasText(
                '.multicolumn2 .column:first-child',
                'Left column',
                'Correct page type was used'
            );
            test.assertSelectorHasText(
                '.multicolumn2 .column:last-child',
                'Right column',
                'Correct page type was used'
            );
        })
        // cleanup before teardown
        // TODO remove page type
        .thenOpen(globals.adminPagesUrl.replace('page', 'pagetype'))
        .waitUntilVisible('.js-cms-pagetree-options')
        .then(cms.expandPageTree())
        .then(function () {
            var data = '';
            var href = '';

            return this.then(function () {
                this.click('.cms-pagetree-jstree .js-cms-pagetree-options' + data);
            })
            .then(cms.waitUntilActionsDropdownLoaded())
            .then(function () {
                this.click('.cms-pagetree-jstree [href*="delete"]' + href);
            });
        })
        .waitForUrl(/delete/)
        .waitUntilVisible('input[type=submit]')
        .then(function () {
            this.click('input[type=submit]');
        })
        .wait(1000)
        .then(cms.waitUntilAllAjaxCallsFinish())

        .then(cms.removePage({ title: 'New Shiny Page' }))
        .run(function() {
            test.done();
        });
});
