/* global window */
'use strict';

var casperjs = require('casper');
var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers(casperjs);
var xPath = casperjs.selectXPath;

var createJSTreeXPathFromTree = cms.createJSTreeXPathFromTree;
var getPasteHelpersXPath = cms.getPasteHelpersXPath;

casper.test.setUp(function(done) {
    casper.start().then(cms.login()).run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.logout()).run(done);
});

casper.test.begin('Pages can be copied and pasted when CMS_PERMISSION=False', function(test) {
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
                .waitForResource(/copy-page/)
                .waitForUrl(/page/) // need to wait for reload
                .wait(1000)
                .waitUntilVisible('.cms-pagetree-jstree')
                .wait(3000)
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
                .then(cms.expandPageTree())
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
                .waitForResource(/copy-page/)
                .waitForUrl(/page/) // need to wait for reload
                .wait(1000)
                .waitUntilVisible('.cms-pagetree-jstree', cms.expandPageTree())
                .wait(3000)
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
                .wait(1000)
                .waitUntilVisible('.cms-pagetree-jstree', cms.waitUntilAllAjaxCallsFinish())
                .wait(3000)
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
                .waitForResource(/copy-page/)
                .waitForUrl(/page/) // need to wait for reload
                .wait(1000)
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
                .wait(1000)
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
                .waitForResource(/copy-page/)
                .waitForUrl(/page/) // need to wait for reload
                .wait(1000)
                .waitUntilVisible('.cms-pagetree-jstree', cms.expandPageTree())
                .wait(3000)
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
                .wait(1000)
                .waitUntilVisible('.cms-pagetree-jstree')
                .wait(3000)
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
