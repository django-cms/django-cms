'use strict';

// #############################################################################
// Page types and templates

var globals = require('./settings/globals');
var randomString = require('./helpers/randomString').randomString;
var casperjs = require('casper');
var cms = require('./helpers/cms')(casperjs);
var xPath = casperjs.selectXPath;

var SECOND_PAGE_TITLE = 'Second';

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        // .then(cms.addPage({ title: 'First page' }))
        // adding second one because first is published by default
        // .then(cms.addPage({ title: SECOND_PAGE_TITLE }))
        .run(done);
});

casper.test.tearDown(function (done) {
    casper.start()
        // .then(cms.removePage({ title: SECOND_PAGE_TITLE }))
        // .then(cms.removePage({ title: 'First page' })) // removing both pages
        .then(cms.logout())
        .run(done);
});

0 && casper.test.begin('Different page template can be applied', function (test) {
    casper.start(globals.editUrl)
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            test.assertDoesntExist('h1', 'Page is "fullwidth.html"');
            // click on "Page" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(2) > a');
        })
        // expand "Templates" menu item
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            var position = this.getElementBounds(xPath('//a[.//span[text()[contains(.,"Templates")]]]'));
            // simulating mouseenter event
            this.mouse.move(position.left + 1, position.top - 1);
            this.mouse.move(position.left + 1, position.top + 1);
            this.wait(10);
        })
        // wait till it expands
        .waitForSelector('.cms-toolbar-item-navigation-hover .cms-toolbar-item-navigation-hover', function () {
            // move right
            this.mouse.move(
                xPath('//a[.//span[text()[contains(.,"Fullwidth")]]]')
            );
            // move down
            this.mouse.move(
                xPath('//a[.//span[text()[contains(.,"Standard page")]]]')
            );
            this.click(
                xPath('//a[.//span[text()[contains(.,"Standard page")]]]')
            );
        })
        .waitForResource(/change_template/)
        .waitForSelector('.cms-ready', function () {
            test.assertSelectorHasText(
                '.cms-toolbar-item-navigation-active',
                'Standard page',
                'Correct template is highlighted in the menu'
            );
            test.assertExists('h1', 'Page is "page.html"');
            test.assertSelectorHasText('h1', 'This is a custom page template', 'Page is "page.html"');
        })
        .run(function () {
            test.done();
        });
});

casper.test.begin('PageType can be created and used', function (test) {
    casper.start(globals.editUrl)
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
                id_body: 'Left column'
            },
            parent: '.cms-dragarea:first-child .cms-draggable .cms-draggable:first-child'
        }))
        .then(cms.addPlugin({
            type: 'TextPlugin',
            content: {
                id_body: 'Right column'
            },
            parent: '.cms-dragarea:first-child .cms-draggable .cms-draggable:last-child'
        }))
        .run(function () {
            test.done();
        });
});
