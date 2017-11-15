/* global window */
'use strict';

// #############################################################################
// Page tree functionality

var casperjs = require('casper');
var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers(casperjs);
var xPath = casperjs.selectXPath;

var createJSTreeXPathFromTree = cms.createJSTreeXPathFromTree;
var getPasteHelpersXPath = cms.getPasteHelpersXPath;

var closeWizard = function() {
    return function() {
        // close default wizard modal
        return this.waitUntilVisible('.cms-modal', function() {
            this.click('.cms-modal .cms-modal-close');
        }).waitWhileVisible('.cms-modal');
    };
};

casper.test.setUp(function(done) {
    casper.start().then(cms.login()).run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.logout()).run(done);
});

casper.test.begin('Shows a message when there are no pages', function(test) {
    casper
        .start(globals.baseUrl)
        .then(closeWizard())
        .then(cms.openSideframe())
        .then(function() {
            test.assertVisible('.cms-sideframe-frame', 'The sideframe has been opened');
        })
        // switch to sideframe
        .withFrame(0, function() {
            casper.waitForSelector('#changelist-form', function() {
                test.assertSelectorHasText(
                    '#changelist-form',
                    'There is no page around yet.',
                    'Shows correct message if there are not pages yet'
                );
            });
        })
        .run(function() {
            test.done();
        });
});

casper.test.begin('Correctly displays languages', function(test) {
    casper
        .start()
        .then(cms.addPage({ title: 'Homepage' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            casper.waitForSelector('.cms-pagetree-jstree').wait(3000).then(cms.expandPageTree()).then(function() {
                var pageId = cms.getPageId('Homepage');

                // check that languages look correct
                test.assertExists(
                    '.cms-tree-item-lang a[href*="' + pageId + '/en/preview/"] span',
                    'Controls for publishing in EN are visible'
                );
                test.assertExists(
                    '.cms-tree-item-lang a[href*="' + pageId + '/de/preview/"] span',
                    'Controls for publishing in DE are visible'
                );
                test.assertExists(
                    '.cms-tree-item-lang a[href*="' + pageId + '/it/preview/"] span',
                    'Controls for publishing in IT are visible'
                );
                test.assertExists(
                    '.cms-tree-item-lang a[href*="' + pageId + '/zh-cn/preview/"] span',
                    'Controls for publishing in ZH-CN are visible'
                );
            });
        })
        .then(cms.removePage())
        .run(function() {
            test.done();
        });
});

casper.test.begin('Settings and advanced settings are accessible', function(test) {
    casper
        .start()
        .then(cms.addPage({ title: 'Homepage' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            casper
                .waitForSelector('.cms-pagetree-jstree')
                .wait(3000)
                .then(cms.expandPageTree())
                .then(function() {
                    var pageId = cms.getPageId('Homepage');
                    // check that languages look correct

                    this.click('a[href*="page/' + pageId + '"].cms-icon-pencil');
                })
                .waitForUrl(/page/)
                .waitForSelector('#content')
                .then(function() {
                    test.assertExists(
                        xPath('//h1[contains(text(), "Change page")]'),
                        'Settings can be accessed from page tree'
                    );

                    this.click(xPath('//a[contains(text(), "Pages")][contains(@href, "admin/cms/page")]'));
                })
                .waitForUrl(/page/)
                .waitForSelector('.cms-pagetree-jstree')
                .wait(3000)
                .then(cms.expandPageTree())
                .thenEvaluate(function() {
                    var clickEvent = new CMS.$.Event('click', { shiftKey: true });

                    // here we cheat a bit, it works only if there's only one edit on the page
                    CMS.$('.cms-icon-pencil:visible').trigger(clickEvent);
                })
                .waitForUrl(/advanced-settings/)
                .waitForSelector('h1')
                .then(function() {
                    test.assertExists(
                        xPath('//h1[contains(text(), "Advanced Settings")]'),
                        'Advanced settings can be accessed from page tree'
                    );
                });
        })
        .then(cms.removePage())
        .run(function() {
            test.done();
        });
});

casper.test.begin('Pages can be added through the page tree', function(test) {
    casper
        .start(globals.baseUrl)
        .then(closeWizard())
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            casper
                .waitForSelector('#changelist-form', function() {
                    this.click('.cms-pagetree-header-create');
                })
                .waitForSelector('#page_form', function() {
                    this.sendKeys('#id_title', 'Homepage');
                    this.click('input[name="_save"]');
                })
                .waitUntilVisible('.success')
                .wait(2000)
                .then(function() {
                    var pageId = cms.getPageId('Homepage');
                    var pageNodeId = cms.getPageNodeId('Homepage');

                    test.assertExists(
                        xPath(createJSTreeXPathFromTree([{ name: 'Homepage' }])),
                        'Page was successfully added'
                    );
                    test.assertExists(
                        '.cms-tree-item-lang a[href*="' + pageId + '"] span.published',
                        'Page is published by default'
                    );
                    // add nested page
                    this.click('a[href*="/admin/cms/page/add/?parent_node=' + pageNodeId + '"]');
                })
                .waitForSelector('#page_form', function() {
                    this.sendKeys('#id_title', 'Nested page');
                    this.click('input[name="_save"]');
                })
                .waitUntilVisible('.success')
                .waitUntilVisible('.cms-pagetree-jstree')
                .wait(3000)
                .then(cms.waitUntilAllAjaxCallsFinish())
                .then(cms.expandPageTree())
                .then(function() {
                    var pageId = cms.getPageId('Nested page');

                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [{ name: 'Nested page' }]
                                }
                            ])
                        ),
                        'Newly created page is added'
                    );
                    test.assertExists(
                        '.cms-tree-item-lang a[href*="' + pageId + '"] span.empty',
                        'Nested page is not published'
                    );
                });
        })
        .then(cms.removePage({ title: 'Homepage' }))
        .run(function() {
            test.done();
        });
});

casper.test.begin('Pages can be reordered', function(test) {
    casper
        .start()
        .then(cms.addPage({ title: 'Homepage' }))
        .then(cms.addPage({ title: 'Second' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            var drop;

            casper
                .waitUntilVisible('.cms-pagetree-jstree', cms.waitUntilAllAjaxCallsFinish())
                .then(function() {
                    test.assertExists(
                        xPath(createJSTreeXPathFromTree([{ name: 'Homepage' }, { name: 'Second' }])),
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
                })
                .then(function() {
                    this.mouse.up(drop.left + drop.width / 2, drop.top + drop.height - 3);
                    test.assertExists(
                        xPath(createJSTreeXPathFromTree([{ name: 'Second' }, { name: 'Homepage' }])),
                        'Pages are in correct order after move'
                    );
                })
                .waitForResource(/get-tree/)
                .wait(1000, function() {
                    test.assertDoesntExist('.jstree-initial-node.jstree-loading', 'Loading tree hides');
                })
                .thenEvaluate(function() {
                    window.location.reload();
                })
                .wait(1000)
                .waitUntilVisible('.cms-pagetree-jstree', function() {
                    test.assertExists(
                        xPath(createJSTreeXPathFromTree([{ name: 'Second' }, { name: 'Homepage' }])),
                        'Pages are in correct order after move'
                    );
                });
        })
        .then(cms.removePage({ title: 'Homepage' }))
        .then(cms.removePage({ title: 'Second' }))
        .run(function() {
            test.done();
        });
});

casper.test.begin('Pages can be nested / unnested', function(test) {
    casper
        .start()
        .then(cms.addPage({ title: 'Homepage' }))
        .then(cms.addPage({ title: 'Second' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            var drop;

            casper
                .waitUntilVisible('.cms-pagetree-jstree', function() {
                    test.assertExists(
                        xPath(createJSTreeXPathFromTree([{ name: 'Homepage' }, { name: 'Second' }])),
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
                })
                .then(function() {
                    this.mouse.up(drop.left + drop.width / 2, drop.top + drop.height / 2);

                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second'
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Second page is now nested into the Homepage'
                    );
                })
                .waitForResource(/move-page/)
                .waitForResource(/get-tree/)
                .wait(2000)
                .thenEvaluate(function() {
                    window.location.reload();
                })
                .wait(2000)
                .waitUntilVisible('.cms-pagetree-jstree', function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second'
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Second page is now nested into the Homepage after reload'
                    );
                    drop = this.getElementBounds(
                        xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]')
                    );

                    this.mouse.down(xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Second")]'));
                    this.mouse.move(drop.left + 10, drop.top + drop.height - 1);
                })
                .then(function() {
                    this.mouse.up(drop.left + 10, drop.top + drop.height - 1);
                    test.assertExists(
                        xPath(createJSTreeXPathFromTree([{ name: 'Homepage' }, { name: 'Second' }])),
                        'Pages are back in their initial order'
                    );
                })
                .waitForResource(/move-page/)
                .waitForResource(/get-tree/)
                .wait(2000)
                .thenEvaluate(function() {
                    window.location.reload();
                })
                .wait(2000)
                .waitUntilVisible('.cms-pagetree-jstree', function() {
                    test.assertExists(
                        xPath(createJSTreeXPathFromTree([{ name: 'Homepage' }, { name: 'Second' }])),
                        'Pages are back in their initial order after reload'
                    );
                });
        })
        .then(cms.removePage({ title: 'Second' }))
        .then(cms.removePage({ title: 'Homepage' }))
        .run(function() {
            test.done();
        });
});

casper.test.begin('Pages cannot be published if it does not have a title and slug', function(test) {
    var pageId;

    casper
        .start()
        .then(cms.addPage({ title: 'Homepage' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            casper
                .waitForSelector('.cms-pagetree-jstree', function() {
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
                .then(function() {
                    this.click('.cms-tree-item-lang a[href*="' + pageId + '/de/preview/"] span.empty');
                })
                .waitUntilVisible('.cms-pagetree-dropdown-menu', function() {
                    test.assertVisible('.cms-pagetree-dropdown-menu', 'Publishing dropdown is open');

                    test.assertDoesntExist('.cms-pagetree-dropdown-menu-open a[href*="/de/publish/"]');
                });
        })
        .then(cms.removePage({ title: 'Homepage' }))
        .run(function() {
            test.done();
        });
});

casper.test.begin('Pages can be published/unpublished if it does have a title and slug', function(test) {
    var pageId;

    casper
        .start()
        .then(cms.addPage({ title: 'Homepage' }))
        // this should be baseUrl, but if you never accessed /?edit the CMS doesn't know
        // that you ever been in edit mode and will redirect you to a 404 once you unpublish home page
        .thenOpen(globals.editUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            casper
                .waitForSelector('.cms-pagetree-jstree')
                .wait(1000, function() {
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
                .then(function() {
                    this.click('.js-cms-tree-advanced-settings[href*="' + pageId + '"]');
                })
                .waitUntilVisible('#page_form', function() {
                    this.click('#debutton');
                })
                .waitForSelector('#debutton.selected', function() {
                    this.sendKeys('#id_title', 'Startseite');
                    this.click('input[name="_save"]');
                })
                .waitUntilVisible('.cms-pagetree-jstree .cms-tree-item-lang', function() {
                    this.click('.cms-tree-item-lang a[href*="' + pageId + '/de/preview/"] span.unpublished');
                })
                .waitUntilVisible('.cms-pagetree-dropdown-menu', function() {
                    test.assertVisible('.cms-pagetree-dropdown-menu', 'Publishing dropdown is open');

                    this.click('.cms-pagetree-dropdown-menu-open a[href*="/de/publish/"]');
                })
                .waitForResource(/publish/)
                .waitForResource(/get-tree/)
                .wait(200);
        })
        .wait(2000)
        .withFrame(0, function() {
            casper
                .waitUntilVisible('.cms-pagetree-jstree', function() {
                    pageId = cms.getPageId('Homepage');
                    test.assertExists(
                        '.cms-tree-item-lang a[href*="' + pageId + '/de/preview/"] span.published',
                        'Page was published in German because it does have a title and slug'
                    );
                })
                .then(function() {
                    this.click('.cms-tree-item-lang a[href*="' + pageId + '/de/preview/"]');
                })
                .waitUntilVisible('.cms-pagetree-dropdown-menu', function() {
                    this.click('.cms-pagetree-dropdown-menu-open a[href*="/de/unpublish/"]');
                })
                .waitForResource(/unpublish/)
                .waitForResource(/get-tree/)
                .wait(200);
        })
        .wait(2000)
        .withFrame(0, function() {
            casper
                .waitUntilVisible('.cms-pagetree-jstree')
                .then(cms.waitUntilAllAjaxCallsFinish())
                .then(function() {
                    pageId = cms.getPageId('Homepage');
                    test.assertExists(
                        '.cms-tree-item-lang a[href*="' + pageId + '/de/preview/"] span.unpublished',
                        'Page in German was unpublished'
                    );
                })
                .waitUntilVisible('.cms-pagetree-jstree', function() {
                    test.assertExists(
                        '.cms-tree-item-lang a[href*="' + pageId + '/en/preview/"] span.published',
                        'Page is published in English'
                    );
                })
                .then(function() {
                    this.click('.cms-tree-item-lang a[href*="' + pageId + '/en/preview/"]');
                })
                .waitUntilVisible('.cms-pagetree-dropdown-menu', function() {
                    this.click('.cms-pagetree-dropdown-menu-open a[href*="/en/unpublish/"]');
                })
                .waitForResource(/unpublish/)
                .waitForResource(/get-tree/)
                .wait(200);
        })
        .wait(2000)
        .withFrame(0, function() {
            casper.waitUntilVisible('.cms-pagetree-jstree').then(cms.waitUntilAllAjaxCallsFinish()).then(function() {
                pageId = cms.getPageId('Homepage');
                test.assertExists(
                    '.cms-tree-item-lang a[href*="' + pageId + '/en/preview/"] span.unpublished',
                    'Page in English was unpublished'
                );
            });
        })
        .then(cms.removePage({ title: 'Homepage' }))
        .run(function() {
            test.done();
        });
});

casper.test.begin('Pages can be copied and pasted', function(test) {
    casper
        .start()
        .then(cms.addPage({ title: 'Homepage' }))
        .then(cms.addPage({ title: 'Second', parent: 'Homepage' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            var secondPageId;

            casper
                .waitUntilVisible('.cms-pagetree-jstree')
                .then(cms.expandPageTree())
                .then(function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second'
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Second page is nested into the Homepage'
                    );

                    secondPageId = cms.getPageNodeId('Second');

                    this.then(cms.triggerCopyPage({ page: secondPageId }));
                })
                // wait until paste buttons show up
                .then(function() {
                    test.assertElementCount(
                        xPath(
                            getPasteHelpersXPath({
                                visible: true
                            })
                        ),
                        2,
                        'Two possible paste targets, root and self'
                    );
                })
                .then(function() {
                    var firstPageId = cms.getPageNodeId('Homepage');

                    this.click('.js-cms-pagetree-options[data-node-id="' + firstPageId + '"]');
                })
                .then(cms.waitUntilActionsDropdownLoaded())
                .then(function() {
                    test.assertElementCount(
                        xPath(
                            getPasteHelpersXPath({
                                visible: true
                            })
                        ),
                        3,
                        'Three possible paste targets, root, parent and self'
                    );
                })
                // click on it again
                .then(function() {
                    this.then(cms.triggerCopyPage({ page: secondPageId }));
                })
                .then(function() {
                    test.assertElementCount(
                        xPath(
                            getPasteHelpersXPath({
                                visible: true
                            })
                        ),
                        0,
                        'Paste buttons hide when clicked on copy again'
                    );
                })
                .then(function() {
                    // open them again
                    this.then(cms.triggerCopyPage({ page: secondPageId }));
                })
                // then try to paste into itself
                .then(function() {
                    this.then(
                        cms.triggerPastePage({
                            page: secondPageId
                        })
                    );
                })
                .waitUntilVisible('.cms-dialog', function() {
                    test.assertVisible('.cms-dialog', 'Dialog shows up');
                    test.assertSelectorHasText('.cms-dialog', 'Copy options', 'Copy options dialog shows up');
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Second'
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Copy page placeholder is visible in the tree'
                    );
                    test.assertElementCount(
                        xPath(
                            getPasteHelpersXPath({
                                visible: true
                            })
                        ),
                        0,
                        'Paste buttons hide when dialog is shown up'
                    );
                    this.click('.cms-dialog .default.submit');
                })
                .waitForResource(/copy-page/)
                .waitForUrl(/page/) // need to wait for reload
                .wait(2000)
                .waitUntilVisible('.cms-pagetree-jstree')
                .then(cms.waitUntilAllAjaxCallsFinish())
                .then(function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Second'
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Second page was copied into itself'
                    );
                })
                .then(function() {
                    this.then(cms.triggerCopyPage({ page: secondPageId }));
                })
                // wait until paste buttons show up
                .then(function() {
                    this.then(
                        cms.triggerPastePage({
                            page: cms.getPageNodeId('Homepage')
                        })
                    );
                })
                .waitUntilVisible('.cms-dialog', function() {
                    test.assertVisible('.cms-dialog', 'Dialog shows up');
                    test.assertSelectorHasText('.cms-dialog', 'Copy options', 'Copy options dialog shows up');
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Second'
                                                }
                                            ]
                                        },
                                        {
                                            name: 'Second'
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Copy page placeholder is visible in the tree'
                    );
                    test.assertElementCount(
                        xPath(
                            getPasteHelpersXPath({
                                visible: true
                            })
                        ),
                        0,
                        'Paste buttons hide when dialog is shown up'
                    );
                })
                .then(function() {
                    // click on cancel - nothing should happen
                    this.click('.cms-dialog .cancel');
                })
                .waitWhileVisible('.cms-dialog', function() {
                    test.assertNotVisible('.cms-dialog', 'Dialog closed');
                    test.assertDoesntExist(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Second'
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    name: 'Second'
                                }
                            ])
                        ),
                        'Copy page placeholder is no longer visible in the tree'
                    );
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Second'
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Copy page placeholder is no longer visible in the tree'
                    );
                })
                // try to copy into parent
                .then(function() {
                    this.then(cms.triggerCopyPage({ page: secondPageId }));
                })
                // wait until paste buttons show up
                .then(function() {
                    // click on "Paste" to homepage
                    this.then(
                        cms.triggerPastePage({
                            page: cms.getPageNodeId('Homepage')
                        })
                    );
                })
                .waitUntilVisible('.cms-dialog', function() {
                    this.click('.cms-dialog .default.submit');
                })
                .waitForResource(/copy-page/)
                .waitForUrl(/page/) // need to wait for reload
                .wait(2000)
                .waitUntilVisible('.cms-pagetree-jstree', cms.expandPageTree())
                .waitUntilVisible('.cms-pagetree-jstree', function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Second'
                                                }
                                            ]
                                        },
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Second'
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Second page was copied into the homepage'
                    );
                })
                .thenEvaluate(function() {
                    window.location.reload();
                })
                .wait(2000)
                .waitUntilVisible('.cms-pagetree-jstree', cms.waitUntilAllAjaxCallsFinish())
                .then(function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Second'
                                                }
                                            ]
                                        },
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Second'
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Second page was copied into the homepage'
                    );
                })
                // try to copy into root
                .then(function() {
                    this.then(cms.triggerCopyPage({ page: secondPageId }));
                })
                // wait until paste buttons show up
                .then(function() {
                    // click on "Paste" to root
                    this.then(
                        cms.triggerPastePage({
                            page: '#root'
                        })
                    );
                })
                .waitUntilVisible('.cms-dialog', function() {
                    this.click('.cms-dialog .default.submit');
                })
                .waitForResource(/copy-page/)
                .waitForUrl(/page/) // need to wait for reload
                .wait(2000)
                .waitUntilVisible('.cms-pagetree-jstree')
                .then(cms.waitUntilAllAjaxCallsFinish())
                .then(cms.expandPageTree())
                .waitUntilVisible('.cms-pagetree-jstree', function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Second'
                                                }
                                            ]
                                        },
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Second'
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    name: 'Second',
                                    children: [
                                        {
                                            name: 'Second'
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Second page was copied into the root'
                    );
                })
                .thenEvaluate(function() {
                    window.location.reload();
                })
                .wait(2000)
                .waitUntilVisible('.cms-pagetree-jstree')
                .then(cms.waitUntilAllAjaxCallsFinish())
                .then(cms.expandPageTree())
                .then(function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Second'
                                                }
                                            ]
                                        },
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Second'
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    name: 'Second',
                                    children: [
                                        {
                                            name: 'Second'
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Second page was copied into the root'
                    );
                })
                // then try to copy sibling into a sibling (homepage into sibling "second" page)
                .then(function() {
                    this.then(cms.triggerCopyPage({ page: cms.getPageNodeId('Homepage') }));
                })
                // wait until paste buttons show up
                .then(function() {
                    // click on "Paste" to top level "second" page
                    var pages = cms._getPageNodeIds('Second');

                    this.then(
                        cms.triggerPastePage({
                            page: pages[pages.length - 2]
                        })
                    );
                })
                .waitUntilVisible('.cms-dialog', function() {
                    this.click('.cms-dialog .default.submit');
                })
                .waitForResource(/copy-page/)
                .waitForUrl(/page/) // need to wait for reload
                .wait(2000)
                .waitUntilVisible('.cms-pagetree-jstree', cms.expandPageTree())
                .waitUntilVisible('.cms-pagetree-jstree', function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Second'
                                                }
                                            ]
                                        },
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Second'
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    name: 'Second',
                                    children: [
                                        { name: 'Second' },
                                        {
                                            name: 'Homepage',
                                            children: [
                                                {
                                                    name: 'Second',
                                                    children: [
                                                        {
                                                            name: 'Second'
                                                        }
                                                    ]
                                                },
                                                {
                                                    name: 'Second',
                                                    children: [
                                                        {
                                                            name: 'Second'
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Homepage was copied into last "Second" page'
                    );
                })
                .thenEvaluate(function() {
                    window.location.reload();
                })
                .wait(2000)
                .waitUntilVisible('.cms-pagetree-jstree')
                .then(function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Second'
                                                }
                                            ]
                                        },
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Second'
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    name: 'Second',
                                    children: [
                                        { name: 'Second' },
                                        {
                                            name: 'Homepage',
                                            children: [
                                                {
                                                    name: 'Second',
                                                    children: [
                                                        {
                                                            name: 'Second'
                                                        }
                                                    ]
                                                },
                                                {
                                                    name: 'Second',
                                                    children: [
                                                        {
                                                            name: 'Second'
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Homepage was copied into last "Second" page'
                    );
                })
                // then try to copy a page into own child
                .then(function() {
                    this.then(cms.triggerCopyPage({ page: cms.getPageNodeId('Homepage') }));
                })
                // wait until paste buttons show up
                .then(function() {
                    // click on "Paste" to the Direct child of Homepage
                    this.then(
                        cms.triggerPastePage({
                            page: secondPageId
                        })
                    );
                });
        })
        // remove two top level pages
        .then(cms.removePage())
        .then(cms.removePage())
        .run(function() {
            test.done();
        });
});

casper.test.begin('Cut helpers show up correctly', function(test) {
    casper
        .start()
        .then(cms.addPage({ title: 'Homepage' }))
        .then(cms.addPage({ title: 'Second', parent: 'Homepage' }))
        .then(cms.addPage({ title: 'Third', parent: 'Second' }))
        .then(cms.addPage({ title: 'Fourth', parent: 'Third' }))
        .then(cms.addPage({ title: 'Top sibling' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            var secondPageId;

            casper
                .waitUntilVisible('.cms-pagetree-jstree')
                .wait(1000)
                .then(cms.expandPageTree())
                .then(function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Third',
                                                    children: [
                                                        {
                                                            name: 'Fourth'
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    name: 'Top sibling'
                                }
                            ])
                        ),
                        'Second page is nested into the Homepage'
                    );

                    secondPageId = cms.getPageNodeId('Second');

                    this.then(cms.triggerCutPage({ page: secondPageId }));
                })
                // open all of the actions dropdowns
                .then(function() {
                    var pages = ['Homepage', 'Second', 'Third', 'Fourth', 'Top sibling'];

                    return this.eachThen(pages, function(page) {
                        var pageId = cms.getPageNodeId(page.data);

                        this.then(function() {
                            this.click('.js-cms-pagetree-options[data-node-id="' + pageId + '"]');
                        }).then(cms.waitUntilActionsDropdownLoaded());
                    });
                })
                // wait until all paste buttons show up
                .then(function() {
                    test.assertElementCount(
                        xPath(
                            getPasteHelpersXPath({
                                visible: true
                            })
                        ),
                        3,
                        'Three possible paste targets'
                    );
                    test.assertExists(
                        xPath(
                            getPasteHelpersXPath({
                                visible: false,
                                pageId: secondPageId
                            })
                        ),
                        'Paste target is not the page itself'
                    );
                    test.assertExists(
                        xPath(
                            getPasteHelpersXPath({
                                visible: false,
                                pageId: cms.getPageNodeId('Third')
                            })
                        ),
                        'Paste target is not the child of the page itself'
                    );
                    test.assertExists(
                        xPath(
                            getPasteHelpersXPath({
                                visible: false,
                                pageId: cms.getPageNodeId('Fourth')
                            })
                        ),
                        'Paste target is not the child of the child of the page itself'
                    );
                })
                .then(function() {
                    this.then(cms.triggerCutPage({ page: secondPageId }));
                })
                .then(function() {
                    test.assertElementCount(
                        xPath(
                            getPasteHelpersXPath({
                                visible: true
                            })
                        ),
                        0,
                        'Cut helpers hidden'
                    );
                });
        })
        // remove two top level pages
        .then(cms.removePage())
        .then(cms.removePage())
        .run(function() {
            test.done();
        });
});

casper.test.begin('Pages can be cut and pasted', function(test) {
    casper
        .start()
        .then(cms.addPage({ title: 'Homepage' }))
        .then(cms.addPage({ title: 'Second', parent: 'Homepage' }))
        .then(cms.addPage({ title: 'Third', parent: 'Second' }))
        .then(cms.addPage({ title: 'Fourth', parent: 'Third' }))
        .then(cms.addPage({ title: 'Top sibling' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            var secondPageId;

            casper
                .waitUntilVisible('.cms-pagetree-jstree')
                .wait(1000)
                .then(cms.expandPageTree())
                .then(function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Third',
                                                    children: [
                                                        {
                                                            name: 'Fourth'
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    name: 'Top sibling'
                                }
                            ])
                        ),
                        'Initial page structure is correct'
                    );

                    secondPageId = cms.getPageNodeId('Second');

                    this.then(cms.triggerCutPage({ page: secondPageId }));
                })
                // wait until paste buttons show up
                .then(function() {
                    test.assertDoesntExist('.cms-dialog', 'Dialog does not show up');
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Third',
                                                    children: [
                                                        {
                                                            name: 'Fourth'
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    name: 'Top sibling'
                                }
                            ])
                        ),
                        'Tree stays the same'
                    );

                    this.then(
                        cms.triggerPastePage({
                            page: '#root'
                        })
                    );
                })
                .then(function() {
                    test.assertElementCount(xPath(getPasteHelpersXPath({ visible: true })), 0, 'Cut helpers hidden');
                })
                .waitForResource(/move-page/)
                .waitForResource(/get-tree/)
                .wait(2000)
                .then(cms.expandPageTree())
                .then(function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage'
                                },
                                {
                                    name: 'Top sibling'
                                },
                                {
                                    name: 'Second',
                                    children: [
                                        {
                                            name: 'Third',
                                            children: [
                                                {
                                                    name: 'Fourth'
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Page was moved into root'
                    );
                })
                .thenEvaluate(function() {
                    window.location.reload();
                })
                .wait(2000)
                .waitUntilVisible('.cms-pagetree-jstree', function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage'
                                },
                                {
                                    name: 'Top sibling'
                                },
                                {
                                    name: 'Second',
                                    children: [
                                        {
                                            name: 'Third',
                                            children: [
                                                {
                                                    name: 'Fourth'
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Page was moved into root'
                    );
                })
                // then try to cut the page and paste it into sibling
                .then(function() {
                    this.then(cms.triggerCutPage({ page: secondPageId }));
                })
                .then(function() {
                    this.then(
                        cms.triggerPastePage({
                            page: cms.getPageNodeId('Top sibling')
                        })
                    );
                })
                .waitForResource(/move-page/)
                .waitForResource(/get-tree/)
                .wait(2000)
                .then(cms.expandPageTree())
                .then(function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage'
                                },
                                {
                                    name: 'Top sibling',
                                    children: [
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Third',
                                                    children: [
                                                        {
                                                            name: 'Fourth'
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Page was moved into sibling'
                    );
                })
                .thenEvaluate(function() {
                    window.location.reload();
                })
                .wait(2000)
                .waitUntilVisible('.cms-pagetree-jstree', function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage'
                                },
                                {
                                    name: 'Top sibling',
                                    children: [
                                        {
                                            name: 'Second',
                                            children: [
                                                {
                                                    name: 'Third',
                                                    children: [
                                                        {
                                                            name: 'Fourth'
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Page was moved into sibling'
                    );
                });
        })
        // remove two top level pages
        .then(cms.removePage())
        .then(cms.removePage())
        .run(function() {
            test.done();
        });
});

casper.test.begin('Pagetree remembers which nodes are opened and which ones are closed', function(test) {
    casper
        .start()
        .then(cms.addPage({ title: 'Homepage' }))
        .then(cms.addPage({ title: 'Second', parent: 'Homepage' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            casper
                .waitUntilVisible('.cms-pagetree-jstree')
                .then(function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage'
                                }
                            ])
                        ),
                        'At first nested page is not visible'
                    );
                })
                .then(function() {
                    this.click('.jstree-closed[data-node-id="' + cms.getPageNodeId('Homepage') + '"] > .jstree-ocl');
                })
                .waitForResource(/get-tree/)
                .wait(2000)
                .then(function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second'
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Page nodes can be expanded'
                    );
                })
                .thenEvaluate(function() {
                    window.location.reload();
                })
                .waitUntilVisible('.cms-pagetree-jstree')
                .wait(2000, function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second'
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Expanded state was restored after reload'
                    );
                })
                .then(function() {
                    this.click('.jstree-open[data-node-id="' + cms.getPageNodeId('Homepage') + '"] > .jstree-ocl');
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage'
                                }
                            ])
                        ),
                        'Nested page is no longer visible'
                    );
                    test.assertDoesntExist(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second'
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Markup is for nested page is removed'
                    );
                })
                .thenEvaluate(function() {
                    window.location.reload();
                })
                .waitUntilVisible('.cms-pagetree-jstree')
                .wait(2000, function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage'
                                }
                            ])
                        ),
                        'Collapsed state was restored'
                    );
                    test.assertDoesntExist(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second'
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Nested page is not in the markup'
                    );
                });
        })
        .then(cms.removePage())
        .run(function() {
            test.done();
        });
});

casper.test.begin('Pages can be filtered and cannot be dragged if pagetree is filtered', function(test) {
    casper
        .start()
        .then(cms.addPage({ title: 'Homepage' }))
        .then(cms.addPage({ title: 'Second', parent: 'Homepage' }))
        .then(cms.addPage({ title: 'Second but top-level' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            var drop;

            casper
                .waitUntilVisible('.cms-pagetree-jstree')
                .wait(3000)
                .then(cms.expandPageTree())
                .then(function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Second'
                                        }
                                    ]
                                },
                                {
                                    name: 'Second but top-level'
                                }
                            ])
                        ),
                        'Initial structure is correct'
                    );
                })
                .then(function() {
                    this.fill(
                        '.js-cms-pagetree-header-search',
                        {
                            q: 'seco'
                        },
                        true
                    );
                })
                .waitUntilVisible('.cms-pagetree-jstree')
                .wait(3000)
                .then(cms.expandPageTree())
                .then(function() {
                    test.assertExists(
                        xPath(createJSTreeXPathFromTree([{ name: 'Second' }, { name: 'Second but top-level' }])),
                        'Correct pages are shown after filtering'
                    );
                })
                .then(function() {
                    // usually to drag stuff in the iframe you have to calculate the position of the frame
                    // and then the position of the thing inside frame, but here sideframe is opened at 0, 0
                    // so this should be enough
                    drop = this.getElementBounds(
                        xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Second")]')
                    );

                    this.mouse.down(
                        xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Second but top-level")]')
                    );
                    this.mouse.move(drop.left + drop.width / 2, drop.top + drop.height - 3);
                })
                .then(function() {
                    this.mouse.up(drop.left + drop.width / 2, drop.top + drop.height - 3);
                    test.assertExists(
                        xPath(createJSTreeXPathFromTree([{ name: 'Second' }, { name: 'Second but top-level' }])),
                        'Pages order was not changed'
                    );
                });
        })
        .then(cms.removePage())
        .then(cms.removePage())
        .run(function() {
            test.done();
        });
});
