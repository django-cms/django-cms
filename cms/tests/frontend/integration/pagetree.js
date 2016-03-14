'use strict';

// #############################################################################
// Page tree functionality

var globals = require('./settings/globals');
var casperjs = require('casper');
var cms = require('./helpers/cms')(casperjs);
var xPath = casperjs.selectXPath;

var closeWizard = function () {
    return function () {
        // close default wizard modal
        return this.waitUntilVisible('.cms-modal', function () {
            this.click('.cms-modal .cms-modal-close');
        })
        .waitWhileVisible('.cms-modal');
    };
};

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        .run(done);
});

casper.test.tearDown(function (done) {
    casper.start()
        .then(cms.logout())
        .run(done);
});

casper.test.begin('Shows a message when there are no pages', function (test) {
    casper
        .start(globals.baseUrl)
        .then(closeWizard())
        .then(cms.openSideframe())
        .then(function () {
            test.assertVisible('.cms-sideframe-frame', 'The sideframe has been opened');
        })
        // switch to sideframe
        .withFrame(0, function () {
            casper.waitForSelector('#changelist-form', function () {
                test.assertSelectorHasText(
                    '#changelist-form',
                    'There is no page around yet.',
                    'Shows correct message if there are not pages yet'
                );
            });
        })
        .run(function () {
            test.done();
        });
});

casper.test.begin('Pages can be added through the page tree', function (test) {
    casper
        .start(globals.baseUrl)
        .then(closeWizard())
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function () {
            casper.waitForSelector('#changelist-form', function () {
                this.click('#changelist-form .addlink');
            })
            .waitForSelector('#page_form', function () {
                this.sendKeys('#id_title', 'Homepage');
                this.click('input[name="_save"]');
            })
            .waitUntilVisible('.success')
            .then(function () {
                var pageId = cms.getPageId('Homepage');
                test.assertExists(
                    xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]'),
                    'Page was successfully added'
                );
                test.assertExists(
                    '.cms-tree-item-lang a[href*="' + pageId + '"] span.published',
                    'Page is published by default'
                );
                // add nested page
                this.click('a[href*="/admin/cms/page/add/?target=' + pageId + '"]');
            })
            .waitForSelector('#page_form', function () {
                this.sendKeys('#id_title', 'Nested page');
                this.click('input[name="_save"]');
            })
            .waitUntilVisible('.success')
            .then(cms.expandPageTree())
            .then(function () {
                var pageId = cms.getPageId('Nested page');
                test.assertExists(
                    xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Nested page")]'),
                    'Nested page was successfully added'
                );
                test.assertExists(
                    xPath('//a[contains(text(), "Homepage")]' +
                          '/following-sibling::ul[contains(@class, "jstree-children")]' +
                          '[./li/a[contains(@class, "jstree-anchor")][contains(text(), "Nested page")]]'),
                    'Newly created page is indeed nested'
                );
                test.assertExists(
                    '.cms-tree-item-lang a[href*="' + pageId + '"] span.empty',
                    'Nested page is not published'
                );
            });
        })
        .then(cms.removePage({ title: 'Homepage' }))
        .run(function () {
            test.done();
        });
});

casper.test.begin('Pages can be reordered', function (test) {
    casper.start()
        .then(cms.addPage({ title: 'Homepage' }))
        .then(cms.addPage({ title: 'Second' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function () {
            var drop;
            casper.waitUntilVisible('.cms-pagetree', function () {
                test.assertExists(
                    xPath('//li[./a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]]' +
                          '/following-sibling::li[./a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]'),
                    'Pages are in correct order initially'
                );

                // usually to drag stuff in the iframe you have to calculate the position of the frame
                // and then the position of the thing inside frame, but here sideframe is opened at 0, 0
                // so this should be enough
                drop = this.getElementBounds(
                    xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Second")]')
                );

                this.mouse.down(xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]'));
                this.mouse.move(drop.left + drop.width / 2, drop.top + drop.height - 3);
            }).then(function () {
                this.mouse.up(drop.left + drop.width / 2, drop.top + drop.height - 3);
                test.assertExists(
                    xPath('//li[./a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]' +
                          '/following-sibling::li' +
                          '[./a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]]'),
                    'Pages are in correct order after move'
                );
            }).waitForResource(/move-page/, function () {
                test.assertExists('.jstree-initial-node.jstree-loading', 'Loading tree showed up');
            }).waitForResource(/get-tree/, function () {
                test.assertDoesntExist('.jstree-initial-node.jstree-loading', 'Loading tree hides');
            }).then(function () {
                this.reload();
            }).waitUntilVisible('.cms-pagetree', function () {
                test.assertExists(
                    xPath('//li[./a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]' +
                          '/following-sibling::li' +
                          '[./a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]]'),
                    'Pages are in correct order after move'
                );
            });
        })
        .then(cms.removePage({ title: 'Homepage' }))
        .then(cms.removePage({ title: 'Second' }))
        .run(function () {
            test.done();
        });
});

casper.test.begin('Pages can be nested / unnested', function (test) {
    casper.start()
        .then(cms.addPage({ title: 'Homepage' }))
        .then(cms.addPage({ title: 'Second' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function () {
            var drop;
            casper.waitUntilVisible('.cms-pagetree', function () {
                test.assertExists(
                    xPath('//li[./a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]]' +
                          '/following-sibling::li[./a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]'),
                    'Pages are in correct order initially'
                );

                // usually to drag stuff in the iframe you have to calculate the position of the frame
                // and then the position of the thing inside frame, but here sideframe is opened at 0, 0
                // so this should be enough
                drop = this.getElementBounds(
                    xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]')
                );

                this.mouse.down(xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Second")]'));
                this.mouse.move(drop.left + drop.width / 2, drop.top + drop.height / 2);
            }).then(function () {
                this.mouse.up(drop.left + drop.width / 2, drop.top + drop.height / 2);

                test.assertExists(
                    xPath('//a[contains(text(), "Homepage")]' +
                          '/following-sibling::ul[contains(@class, "jstree-children")]' +
                          '[./li/a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]'),
                    'Second page is now nested into the Homepage'
                );
            })
            .waitForResource(/move-page/)
            .waitForResource(/get-tree/)
            .then(function () {
                this.reload();
            })
            .waitUntilVisible('.cms-pagetree', function () {
                test.assertExists(
                    xPath('//a[contains(text(), "Homepage")]' +
                          '/following-sibling::ul[contains(@class, "jstree-children")]' +
                          '[./li/a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]'),
                    'Second page is now nested into the Homepage after reload'
                );
                drop = this.getElementBounds(
                    xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]')
                );

                this.mouse.down(xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Second")]'));
                this.mouse.move(drop.left + 10, drop.top + drop.height - 1);
            }).then(function () {
                this.mouse.up(drop.left + 10, drop.top + drop.height - 1);
                test.assertExists(
                    xPath('//li[./a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]]' +
                          '/following-sibling::li[./a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]'),
                    'Pages are back in their initial order'
                );
            })
            .waitForResource(/move-page/)
            .waitForResource(/get-tree/)
            .then(function () {
                this.reload();
            })
            .waitUntilVisible('.cms-pagetree', function () {
                test.assertExists(
                    xPath('//li[./a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]]' +
                          '/following-sibling::li[./a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]'),
                    'Pages are back in their initial order after reload'
                );
            });
        })
        .then(cms.removePage({ title: 'Second' }))
        .then(cms.removePage({ title: 'Homepage' }))
        .run(function () {
            test.done();
        });
});

casper.test.begin('Pages cannot be published if it does not have a title and slug', function (test) {
    var pageId;
    casper
        .start()
        .then(cms.addPage({ title: 'Homepage' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function () {
            casper.waitForSelector('.cms-pagetree', function () {
                pageId = cms.getPageId('Homepage');
                test.assertExists(
                    '.cms-tree-item-lang a[href*="' + pageId + '/en/preview/"] span.published',
                    'Page is published by default in main lang'
                );
                test.assertExists(
                    '.cms-tree-item-lang a[href*="' + pageId + '/de/preview/"] span.empty',
                    'Page is not published by default in another language'
                );
            })
            .then(function () {
                this.click('.cms-tree-item-lang a[href*="' + pageId + '/de/preview/"] span.empty');
            })
            .waitUntilVisible('.cms-tree-tooltip-container', function () {
                test.assertVisible('.cms-tree-tooltip-container', 'Publishing dropdown is open');

                test.assertDoesntExist('.cms-tree-tooltip-container-open a[href*="/de/publish/"]');
            })
        })
        .then(cms.removePage({ title: 'Homepage' }))
        .run(function () {
            test.done();
        });
});

casper.test.begin('Pages can be published/unpublished if it does have a title and slug', function (test) {
    var pageId;
    casper
        .start()
        .then(cms.addPage({ title: 'Homepage' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function () {
            casper.waitForSelector('.cms-pagetree', function () {
                pageId = cms.getPageId('Homepage');
                test.assertExists(
                    '.cms-tree-item-lang a[href*="' + pageId + '/en/preview/"] span.published',
                    'Page is published by default in main lang'
                );
                test.assertExists(
                    '.cms-tree-item-lang a[href*="' + pageId + '/de/preview/"] span.empty',
                    'Page is not published by default in another language'
                );
            })
            // then edit the page to have german translation
            .then(function () {
                this.click('.js-cms-tree-advanced-settings[href*="' + pageId + '"]');
            })
            .waitUntilVisible('#page_form', function () {
                this.click('#debutton');
            })
            .waitForSelector('#debutton.selected', function () {
                this.sendKeys('#id_title', 'Startseite');
                this.click('input[name="_save"]');
            })
            .waitUntilVisible('.cms-pagetree', function () {
                this.click('.cms-tree-item-lang a[href*="' + pageId + '/de/preview/"] span.unpublished');
            })
            .waitUntilVisible('.cms-tree-tooltip-container', function () {
                test.assertVisible('.cms-tree-tooltip-container', 'Publishing dropdown is open');

                this.click('.cms-tree-tooltip-container-open a[href*="/de/publish/"]');
            })
            .waitForResource(/publish/)
            .waitForResource(/get-tree/);
        })
        .wait(1000)
        .withFrame(0, function () {
            casper.waitUntilVisible('.cms-pagetree', function () {
                pageId = cms.getPageId('Homepage');
                test.assertExists(
                    '.cms-tree-item-lang a[href*="' + pageId + '/de/preview/"] span.published',
                    'Page was published in German because it does have a title and slug'
                );
            })
            .then(function () {
                this.click('.cms-tree-item-lang a[href*="' + pageId + '/de/preview/"]');
            })
            .waitUntilVisible('.cms-tree-tooltip-container', function () {
                this.click('.cms-tree-tooltip-container-open a[href*="/de/unpublish/"]');
            })
            .waitForResource(/unpublish/)
            .waitForResource(/get-tree/);
        })
        .wait(1000)
        .withFrame(0, function () {
            casper.waitUntilVisible('.cms-pagetree', function () {
                pageId = cms.getPageId('Homepage');
                test.assertExists(
                    '.cms-tree-item-lang a[href*="' + pageId + '/de/preview/"] span.unpublished',
                    'Page in German was unpublished'
                );
            })
            .waitUntilVisible('.cms-pagetree', function () {
                test.assertExists(
                    '.cms-tree-item-lang a[href*="' + pageId + '/en/preview/"] span.published',
                    'Page is published in English'
                );
            })
            .then(function () {
                this.click('.cms-tree-item-lang a[href*="' + pageId + '/en/preview/"]');
            })
            .waitUntilVisible('.cms-tree-tooltip-container', function () {
                this.click('.cms-tree-tooltip-container-open a[href*="/en/unpublish/"]');
            })
            .waitForResource(/unpublish/)
            .waitForResource(/get-tree/);
        })
        .wait(1000)
        .withFrame(0, function () {
            casper.waitUntilVisible('.cms-pagetree', function () {
                pageId = cms.getPageId('Homepage');
                test.assertExists(
                    '.cms-tree-item-lang a[href*="' + pageId + '/en/preview/"] span.unpublished',
                    'Page in English was unpublished'
                );
            });
        })
        .then(cms.removePage({ title: 'Homepage' }))
        .run(function () {
            test.done();
        });
});

casper.test.begin('Pages can be copied and pasted', function (test) {
    casper.start()
        .then(cms.addPage({ title: 'Homepage' }))
        .then(cms.addPage({ title: 'Second', parent: 'Homepage' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function () {
            var secondPageId;
            casper.waitUntilVisible('.cms-pagetree')
                .then(cms.expandPageTree())
                .then(function () {
                    test.assertExists(
                        xPath('//a[contains(text(), "Homepage")]' +
                            '/following-sibling::ul[contains(@class, "jstree-children")]' +
                            '[./li/a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]'),
                        'Second page is nested into the Homepage'
                    );

                    secondPageId = cms.getPageId('Second');

                    this.click('.js-cms-tree-item-copy[data-id="' + secondPageId + '"]');
                })
                // wait until paste buttons show up
                .waitUntilVisible('.cms-tree-item-helpers', function () {
                    test.assertElementCount(
                        xPath('//*[self::div or self::span]' +
                              '[contains(@class, "cms-tree-item-helpers")]' +
                              '[not(contains(@class, "cms-hidden"))]' +
                              '[./a[contains(text(), "Paste")]]'),
                        3,
                        'Three possible paste targets'
                    );
                })
                // click on it again
                .then(function () {
                    this.click('.js-cms-tree-item-copy[data-id="' + secondPageId + '"]');
                    test.assertElementCount(
                        xPath('//*[self::div or self::span]' +
                              '[contains(@class, "cms-tree-item-helpers")]' +
                              '[not(contains(@class, "cms-hidden"))]' +
                              '[./a[contains(text(), "Paste")]]'),
                        0,
                        'Paste buttons hide when clicked on copy again'
                    );
                    // open them again
                    this.click('.js-cms-tree-item-copy[data-id="' + secondPageId + '"]');
                })
                // then try to paste into itself
                .then(function () {
                    this.click('.cms-tree-item-helpers a[data-id="' + secondPageId + '"]');
                })
                // FIXME should be possible
                .then(function () {
                    test.assertVisible('.error', 'Error shown');
                })
                .then(function () {
                    this.click('.js-cms-tree-item-copy[data-id="' + secondPageId + '"]');
                })
                // wait until paste buttons show up
                .waitUntilVisible('.cms-tree-item-helpers', function () {
                    this.click('.cms-tree-item-helpers a[data-id="' + cms.getPageId('Homepage') + '"]');
                })
                .waitUntilVisible('.cms-dialog', function () {
                    test.assertVisible('.cms-dialog', 'Dialog shows up');
                    test.assertSelectorHasText('.cms-dialog', 'Copy options', 'Copy options dialog shows up');
                    test.assertExists(
                        xPath('//a[contains(text(), "Homepage")]' +
                            '/following-sibling::ul[contains(@class, "jstree-children")]' +
                            '[./li[./a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]' +
                            '/following-sibling::li/a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]'),
                        'Copy page placeholder is visible in the tree'
                    );
                    test.assertElementCount(
                        xPath('//*[self::div or self::span]' +
                              '[contains(@class, "cms-tree-item-helpers")]' +
                              '[not(contains(@class, "cms-hidden"))]' +
                              '[./a[contains(text(), "Paste")]]'),
                        0,
                        'Paste buttons hide when dialog is shown up'
                    );
                })
                .then(function () {
                    // click on cancel - nothing should happen
                    this.click('.cms-dialog .cancel');
                })
                .waitWhileVisible('.cms-dialog', function () {
                    test.assertNotVisible('.cms-dialog', 'Dialog closed');
                    test.assertDoesntExist(
                        xPath('//a[contains(text(), "Homepage")]' +
                            '/following-sibling::ul[contains(@class, "jstree-children")]' +
                            '[./li[./a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]' +
                            '/following-sibling::li/a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]'),
                        'Copy page placeholder is no longer visible in the tree'
                    );
                })
                // try to copy into parent
                .then(function () {
                    this.click('.js-cms-tree-item-copy[data-id="' + secondPageId + '"]');
                })
                // wait until paste buttons show up
                .waitUntilVisible('.cms-tree-item-helpers', function () {
                    // click on "Paste" to homepage
                    this.click('.cms-tree-item-helpers a[data-id="' + cms.getPageId('Homepage') + '"]');
                })
                .waitUntilVisible('.cms-dialog', function () {
                    this.click('.cms-dialog .default.submit');
                })
                .waitForResource(/copy-page/)
                .waitForUrl(/page/) // need to wait for reload
                .waitUntilVisible('.cms-pagetree', function () {
                    test.assertExists(
                        xPath('//a[contains(text(), "Homepage")]' +
                            '/following-sibling::ul[contains(@class, "jstree-children")]' +
                            '[./li[./a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]' +
                            '/following-sibling::li/a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]'),
                        'Second page was copied into the homepage'
                    );
                })
                // FIXME doesn't work
                .thenBypass(2)
                .then(function () {
                    this.reload();
                })
                .waitUntilVisible('.cms-pagetree', function () {
                    test.assertExists(
                        xPath('//a[contains(text(), "Homepage")]' +
                            '/following-sibling::ul[contains(@class, "jstree-children")]' +
                            '[./li[./a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]' +
                            '/following-sibling::li/a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]'),
                        'Second page was copied into the homepage'
                    );
                })
                // FIXME should be removed
                .then(function () {
                    // click on cancel - nothing should happen
                    this.click('.cms-dialog .cancel');
                })
                // try to copy into root
                .then(function () {
                    this.click('.js-cms-tree-item-copy[data-id="' + secondPageId + '"]');
                })
                // wait until paste buttons show up
                .waitUntilVisible('.cms-tree-item-helpers', function () {
                    // click on "Paste" to root
                    this.click('.cms-tree-item-helpers a[href="#root"]');
                })
                .waitUntilVisible('.cms-dialog', function () {
                    this.click('.cms-dialog .default.submit');
                })
                .waitForResource(/copy-page/)
                .waitForUrl(/page/) // need to wait for reload
                .waitUntilVisible('.cms-pagetree', function () {
                    test.assertExists(
                        xPath(
                            '//li[./a[contains(text(), "Homepage")]' +
                            '/following-sibling::ul[contains(@class, "jstree-children")]' +
                            '[./li[./a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]]]' +
                            '/following-sibling::li/a[contains(@class, "jstree-anchor")][contains(text(), "Second")]'
                        ),
                        'Second page was copied into the root'
                    );
                })
                .then(function () {
                    this.reload();
                })
                .waitUntilVisible('.cms-pagetree')
                .then(cms.expandPageTree())
                .then(function () {
                    test.assertExists(
                        xPath(
                            '//li[./a[contains(text(), "Homepage")]' +
                            '/following-sibling::ul[contains(@class, "jstree-children")]' +
                            '[./li[./a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]]]' +
                            '/following-sibling::li/a[contains(@class, "jstree-anchor")][contains(text(), "Second")]'
                        ),
                        'Second page was copied into the root'
                    );
                })
                // then try to copy sibling into a sibling (homepage into sibling "second" page)
                .then(function () {
                    this.click('.js-cms-tree-item-copy[data-id="' + cms.getPageId('Homepage') + '"]');
                })
                // wait until paste buttons show up
                .waitUntilVisible('.cms-tree-item-helpers', function () {
                    // click on "Paste" to last sibling
                    var pages = cms._getPageIds('Second');
                    this.click('.cms-tree-item-helpers a[data-id="' + pages[pages.length - 1] + '"]');
                })
                .waitUntilVisible('.cms-dialog', function () {
                    this.click('.cms-dialog .default.submit');
                })
                .waitForResource(/copy-page/)
                .waitForUrl(/page/) // need to wait for reload
                .waitUntilVisible('.cms-pagetree')
                .then(cms.expandPageTree())
                .then(function () {
                    test.assertExists(
                        // check that tree looks like this
                        // - Homepage
                        //     - Second
                        // - Second
                        //     - Homepage
                        //         - Second
                        xPath(
                            '//li[./a[contains(text(), "Homepage")]' +
                            '/following-sibling::ul[contains(@class, "jstree-children")]' +
                            '[./li[./a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]]]' +
                            '/following-sibling::li/a[contains(text(), "Second")]' +
                            '/following-sibling::ul/li/a[contains(text(), "Homepage")]' +
                            '/following-sibling::ul/li/a[contains(text(), "Second")]'
                        ),
                        'Homepage was copied into last "Second" page'
                    );
                })
                .then(function () {
                    this.reload();
                })
                .waitUntilVisible('.cms-pagetree')
                .then(function () {
                    test.assertExists(
                        xPath(
                            '//li[./a[contains(text(), "Homepage")]' +
                            '/following-sibling::ul[contains(@class, "jstree-children")]' +
                            '[./li[./a[contains(@class, "jstree-anchor")][contains(text(), "Second")]]]]' +
                            '/following-sibling::li/a[contains(text(), "Second")]' +
                            '/following-sibling::ul/li/a[contains(text(), "Homepage")]' +
                            '/following-sibling::ul/li/a[contains(text(), "Second")]'
                        ),
                        'Homepage was copied into last "Second" page'
                    );
                });
        })
        // remove two top level pages
        .then(cms.removePage())
        .then(cms.removePage())
        .run(function () {
            test.done();
        });
});
