'use strict';

// #############################################################################
// Page control

var casperjs = require('casper');
var helpers = require('djangocms-casper-helpers');
var randomString = helpers.randomString;
var globals = helpers.settings;
var cms = helpers(casperjs);
var xPath = casperjs.selectXPath;

var SECOND_PAGE_TITLE = 'Second';
var UPDATED_TITLE = 'updated'; // shouldn't match "Second"
var pageUrl = (globals.baseUrl + SECOND_PAGE_TITLE).toLowerCase() + '/';

casper.test.setUp(function (done) {
    casper
        .start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        // adding second one because first is published by default
        .then(cms.addPage({ title: SECOND_PAGE_TITLE }))
        .run(done);
});

casper.test.tearDown(function (done) {
    casper
        .start()
        .then(cms.removePage({ title: SECOND_PAGE_TITLE }))
        .then(cms.removePage({ title: 'First page' })) // removing both pages
        .then(cms.logout())
        .run(done);
});

casper.test.begin('Page settings are accessible and can be edited from modal', function (test) {
    casper
        .start(globals.editUrl)
        // wait till toolbar is visible
        .waitForSelector('.cms-toolbar-expanded')
        .then(function () {
            this.thenOpen(pageUrl);
        })
        .then(function () {
            test.assertTitleMatch(new RegExp(SECOND_PAGE_TITLE), 'Current page is the correct one');
        })
        // wait till toolbar is visible
        .waitForSelector('.cms-toolbar-expanded')
        .then(function () {
            // click on "Page" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(2) > a');
        })
        // opening "Page settings" menu item
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click(xPath('//a[.//span[text()[contains(.,"Page settings")]]]'));
        })
        // switch to Page settings modal
        .withFrame(0, function () {
            // wait until form is loaded
            casper
                .waitUntilVisible('#page_form', function () {
                    test.assertField('title', SECOND_PAGE_TITLE, 'Page settings modal available');
                })
                .then(function () {
                    this.fill(
                        '#page_form',
                        {
                            title: UPDATED_TITLE
                        },
                        false
                    );
                });
        })
        .then(function () {
            // submit the form without closing the modal
            this.click(xPath('//a[contains(@class, "cms-btn")][text()[contains(.,"Save and continue editing")]]'));
        })
        // expect success message to appear
        .waitUntilVisible('.cms-messages-inner', function () {
            test.assertSelectorHasText(
                '.cms-messages-inner',
                'The page "' + UPDATED_TITLE + '" was changed successfully. You may edit it again below.',
                'Page settings can be edited through modal'
            );
        })
        // switch to modal again
        .withFrame(0, function () {
            casper.waitUntilVisible('#page_form', function () {
                test.assertField('title', UPDATED_TITLE, 'Title was updated');
            });
        })
        // reload the page and check that new title was applied
        .then(function () {
            this.reload();
        })
        .then(function () {
            test.assertTitleMatch(new RegExp(UPDATED_TITLE), 'Current page has correct title');
        })
        .run(function () {
            test.done();
        });
});

casper.test.begin('Page advanced settings are accessible from modal and can be edited', function (test) {
    var random = randomString();

    casper
        .start(globals.editUrl)
        // wait till toolbar is visible
        .waitForSelector('.cms-toolbar-expanded')
        .then(function () {
            this.thenOpen(pageUrl);
        })
        // wait till toolbar is visible
        .waitForSelector('.cms-toolbar-expanded')
        .then(function () {
            // click on "Page" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(2) > a');
        })
        // opening "Page settings" menu item
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click(xPath('//a[.//span[text()[contains(.,"Page settings")]]]'));
        })
        // switch to Page settings modal
        .withFrame(0, function () {
            // wait until form is loaded
            casper.waitUntilVisible('#page_form', function () {
                test.assertField('title', SECOND_PAGE_TITLE, 'Page settings modal available');
            });
        })
        // switch to "Advanced settings"
        .then(function () {
            this.click(xPath('//a[contains(@class, "cms-btn")][text()[contains(.,"Advanced Settings")]]'));
        })
        // then with modal
        .withFrame(0, function () {
            casper
                .waitUntilVisible('#page_form', function () {
                    test.assertField('overwrite_url', '', 'Advanced settings are available from modal');
                })
                .then(function () {
                    this.fill(
                        '#page_form',
                        {
                            overwrite_url: '/overwritten-url-' + random
                        },
                        false
                    );
                });
        })
        // submit the advanced settings form
        .then(function () {
            this.click('.cms-modal-item-buttons .cms-btn-action');
        })
        // wait until we are redirected to updated page
        .waitForUrl(/overwritten-url/, function () {
            test.assertUrlMatch(/overwritten-url/, 'Url have been overwritten');
            test.assertTitleMatch(new RegExp(SECOND_PAGE_TITLE), 'Title is still the same');
        })
        .waitForSelector('.cms-toolbar-expanded')
        .then(function () {
            // click on "Page" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(2) > a');
        })
        // opening "Page settings" menu item
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click(xPath('//a[.//span[text()[contains(.,"Advanced settings")]]]'));
        })
        // then with modal
        .withFrame(0, function () {
            casper
                .waitUntilVisible('#page_form', function () {
                    test.assertField(
                        'overwrite_url',
                        'overwritten-url-' + random,
                        'Advanced settings are available from modal'
                    );
                })
                .then(function () {
                    this.fill(
                        '#page_form',
                        {
                            overwrite_url: ''
                        },
                        false
                    );
                });
        })
        // submit the advanced settings form
        .then(function () {
            this.click('.cms-modal-item-buttons .cms-btn-action');
        })
        // wait until we are redirected to updated page
        .waitForUrl(new RegExp(SECOND_PAGE_TITLE.toLowerCase()))
        // check that the page was edited correctly
        .then(function () {
            test.assertUrlMatch(new RegExp(SECOND_PAGE_TITLE.toLowerCase()), 'Url have been overwritten');
            test.assertTitleMatch(new RegExp(SECOND_PAGE_TITLE), 'Title is still the same');
        })
        .run(function () {
            test.done();
        });
});

casper.test.begin('Page can be deleted', function (test) {
    casper
        .start(globals.editUrl)
        // wait till toolbar is visible
        .waitForSelector('.cms-toolbar-expanded')
        .then(function () {
            this.thenOpen(pageUrl);
        })
        // wait till toolbar is visible
        .waitForSelector('.cms-toolbar-expanded')
        .then(function () {
            // click on "Page" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(2) > a');
        })
        // opening "Page settings" menu item
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click(xPath('//a[.//span[text()[contains(.,"Delete page")]]]'));
        })
        // wait for modal window appearance and submit page deletion
        .waitUntilVisible('.cms-modal-open', function () {
            test.assertVisible('.cms-modal-open');
            this.click('.cms-modal-buttons .deletelink');
        })
        .waitForUrl(/en\//)
        // check that we were redirected to the root
        // .then(function() {
        //     test.assertUrlMatch(/en\/$/, 'Page was removed and user was redirected');
        //     test.assertTitleMatch(/First page/, 'Title is still the same');
        // })
        // try to open the page that we deleted
        .thenOpen(pageUrl)
        .then(function () {
            test.assertTitleMatch(/Page not found/, 'The page is not available');
        })
        // have to add the page back so tearDown runs correctly
        .then(cms.addPage({ title: SECOND_PAGE_TITLE }))
        .run(function () {
            test.done();
        });
});

casper.test.begin('Page can be hidden / shown in navigation', function (test) {
    casper
        .start(globals.editUrl)
        // wait till toolbar is visible
        .waitForSelector('.cms-toolbar-expanded')
        .then(function () {
            this.thenOpen(pageUrl);
        })
        .then(function () {
            test.assertExists(
                xPath(
                    '//ul[@class="nav"]/li/a[contains(@href,"' +
                        SECOND_PAGE_TITLE.toLowerCase() +
                        '")]' +
                        '[contains(text(),"' +
                        SECOND_PAGE_TITLE +
                        '")]'
                ),
                'Page is in navigation'
            );
        })
        // wait till toolbar is visible
        .waitForSelector('.cms-toolbar-expanded')
        .then(function () {
            // click on "Page" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(2) > a');
        })
        // in the dropdown click on "hide in navigation"
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click(xPath('//a[.//span[text()[contains(.,"Hide in navigation")]]]'));
        })
        .waitForResource(/change-navigation/)
        // wait for reload
        .waitForUrl(new RegExp(SECOND_PAGE_TITLE.toLowerCase()))
        // wait until we have the navigation displayed again
        .waitForSelector('.nav', function () {
            test.assertDoesntExist(
                xPath(
                    '//ul[@class="nav"]/li/a[contains(@href,"' +
                        SECOND_PAGE_TITLE.toLowerCase() +
                        '")]' +
                        '[contains(text(),"' +
                        SECOND_PAGE_TITLE +
                        '")]'
                ),
                'Page is not in navigation anymore'
            );
            test.assertExists(
                // here we don't check for url because it's root
                xPath('//ul[@class="nav"]/li/a[contains(text(),"First page")]'),
                'While the first one still is'
            );
        })
        .waitForSelector('.cms-toolbar-expanded', function () {
            // click on "Page" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(2) > a');
        })
        // in the dropdown click on "display in navigation"
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click(xPath('//a[.//span[text()[contains(.,"Display in navigation")]]]'));
        })
        .waitForResource(/change-navigation/)
        // wait for reload
        .wait(100)
        .waitForUrl(new RegExp(SECOND_PAGE_TITLE.toLowerCase()))
        // wait until we have the navigation displayed again
        .wait(1000)
        .waitUntilVisible('.nav', function () {
            test.assertExists(
                xPath(
                    '//ul[@class="nav"]/li/a[contains(@href,"' +
                        SECOND_PAGE_TITLE.toLowerCase() +
                        '")]' +
                        '[contains(text(),"' +
                        SECOND_PAGE_TITLE +
                        '")]'
                ),
                'Page is again in the navigation'
            );
            test.assertExists(
                // here we don't check for url because it's root
                xPath('//ul[@class="nav"]/li/a[contains(text(),"First page")]'),
                'And the first one still is'
            );
        })
        .run(function () {
            test.done();
        });
});

casper.test.begin('Page can be published / unpublished', function (test) {
    casper
        .start(globals.editUrl)
        // wait till toolbar is visible
        .waitForSelector('.cms-toolbar-expanded')
        .then(function () {
            this.thenOpen(pageUrl);
        })
        // check if publish button is available
        .waitForSelector('.cms-toolbar-expanded', function () {
            test.assertSelectorHasText('.cms-publish-page', 'Publish page now', 'Page is unpublished');
        })
        .wait(300)
        .then(cms.logout())
        // check that the page is 404
        .thenOpen(pageUrl, function () {
            test.assertTitleMatch(/Page not found/, 'The page is not yet available');
        })
        .then(cms.login())
        .thenOpen(pageUrl + '?edit')
        // wait till toolbar is visible
        .waitForSelector('.cms-toolbar-expanded')
        .then(function () {
            // click on "Page" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(2) > a');
        })
        // in the dropdown click on "Publish page"
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click(xPath('//a[.//span[text()[contains(.,"Publish page")]]]'));
        })
        // wait until it successfully publishes
        .waitForResource(/publish/)
        // have to wait a bit longer here because .thenOpen doesn't play well with page reloads
        .wait(2000)
        .then(cms.logout())
        // open a page and check if it's published for non-logged in user
        .thenOpen(pageUrl, function () {
            // test.assertTitleMatch(new RegExp(SECOND_PAGE_TITLE), 'The page is published and available');
        })
        .then(cms.login())
        .thenOpen(pageUrl + '?edit')
        .waitForSelector('.cms-toolbar-expanded')
        .then(function () {
            // click on "Page" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(2) > a');
        })
        // in the dropdown click on "Unpublish page"
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click(xPath('//a[.//span[text()[contains(.,"Unpublish page")]]]'));
        })
        // wait until it successfully unpublishes
        .waitForResource(/publish/)
        .waitForResource(/admin\/cms\/page/)
        .waitForSelector('.cms-toolbar-expanded')
        .then(cms.logout())
        // check that the page is 404 again
        .thenOpen(pageUrl, function () {
            test.assertTitleMatch(/Page not found/, 'The page is not longer available');
        })
        // then login again so teardown finishes correctly
        .then(cms.login())
        .run(function () {
            test.done();
        });
});
