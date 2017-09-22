/* global window, document */
'use strict';

var casperjs = require('casper');
var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers(casperjs);
var xPath = casperjs.selectXPath;
var createJSTreeXPathFromTree = cms.createJSTreeXPathFromTree;

casper.test.setUp(function(done) {
    casper.start().then(cms.login()).run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.logout()).run(done);
});

var acceptCopyingAndAssertNewTree = function(tree) {
    return function() {
        casper
            .waitForResource(/copy/)
            .waitUntilVisible('.cms-dialog', function() {
                this.test.assertVisible('.cms-dialog', 'Dialog shows up');
                this.test.assertSelectorHasText('.cms-dialog', 'Copy options', 'Copy options dialog shows up');
                this.click('.cms-dialog .default.submit');
            })
            .waitForResource(/copy-page/, function() {
                this.test.assertExists('.jstree-initial-node.jstree-loading', 'Loading tree showed up');
            })
            .waitForResource(/get-tree/)
            .wait(1000, function() {
                this.test.assertDoesntExist('.jstree-initial-node.jstree-loading', 'Loading tree hides');
            })
            .thenEvaluate(function() {
                window.location.reload();
            })
            .wait(1000)
            .waitUntilVisible('.cms-pagetree-jstree')
            .wait(1000, cms.expandPageTree())
            .then(function() {
                this.test.assertExists(
                    xPath(createJSTreeXPathFromTree(tree)),
                    'Pages are in correct order after reload'
                );
            });
    };
};

casper.test.begin('Page can be copied through drag-n-drop to a sibling', function(test) {
    casper
        .then(cms.addPage({ title: 'Homepage' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            var drop;
            casper
                .waitUntilVisible('.cms-pagetree-jstree', cms.waitUntilAllAjaxCallsFinish())
                .then(function() {
                    test.assertExists(
                        xPath(createJSTreeXPathFromTree([{ name: 'Homepage' }])),
                        'Initial state is correct'
                    );

                    // usually to drag stuff in the iframe you have to calculate the position of the frame
                    // and then the position of the thing inside frame, but here sideframe is opened at 0, 0
                    // so this should be enough
                    drop = this.getElementBounds(
                        xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]')
                    );

                    this.mouse.down(xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]'));
                    this.mouse.move(drop.left + drop.width / 2, drop.top + drop.height - 3);
                    this.evaluate(function() {
                        CMS.$(document).trigger(new CMS.$.Event('keydown', { keyCode: 17, ctrlKey: true }));
                    });
                })
                .then(function() {
                    test.assertVisible('.jstree-copy', 'Copy indicator shown');
                    // since casper cannot trigger a mouse event with ctrlKey pressed,
                    // we fake the event with jQuery
                    this.evaluate(function() {
                        CMS.$(document).trigger(new CMS.$.Event('mouseup', { ctrlKey: true }));
                    });
                })
                .then(acceptCopyingAndAssertNewTree([{ name: 'Homepage' }, { name: 'Homepage' }]));
        })
        .then(cms.removePage())
        .then(cms.removePage())
        .run(function() {
            test.done();
        });
});

casper.test.begin('Pages can be copied into itself', function(test) {
    casper
        .then(cms.addPage({ title: 'Homepage' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            var drop;
            casper
                .waitUntilVisible('.cms-pagetree-jstree', cms.waitUntilAllAjaxCallsFinish())
                .then(function() {
                    test.assertExists(
                        xPath(createJSTreeXPathFromTree([{ name: 'Homepage' }])),
                        'Initial state is correct'
                    );

                    // usually to drag stuff in the iframe you have to calculate the position of the frame
                    // and then the position of the thing inside frame, but here sideframe is opened at 0, 0
                    // so this should be enough
                    drop = this.getElementBounds(
                        xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]')
                    );

                    this.mouse.down(xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]'));
                    this.mouse.move(drop.left + drop.width / 2 + 10, drop.top + drop.height / 2);
                    this.evaluate(function() {
                        CMS.$(document).trigger(new CMS.$.Event('keydown', { keyCode: 17, ctrlKey: true }));
                    });
                })
                .then(function() {
                    test.assertVisible('.jstree-copy', 'Copy indicator shown');
                    // since casper cannot trigger a mouse event with ctrlKey pressed,
                    // we fake the event with jQuery
                    this.evaluate(function() {
                        CMS.$(document).trigger(new CMS.$.Event('mouseup', { ctrlKey: true }));
                    });
                })
                .then(
                    acceptCopyingAndAssertNewTree([
                        {
                            name: 'Homepage',
                            children: [
                                {
                                    name: 'Homepage'
                                }
                            ]
                        }
                    ])
                );
        })
        .then(cms.removePage())
        .run(function() {
            test.done();
        });
});

casper.test.begin('Pages can be copied as sibling child', function(test) {
    casper
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
                        'Initial state is correct'
                    );

                    // usually to drag stuff in the iframe you have to calculate the position of the frame
                    // and then the position of the thing inside frame, but here sideframe is opened at 0, 0
                    // so this should be enough
                    drop = this.getElementBounds(
                        xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]')
                    );

                    this.mouse.down(xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Second")]'));
                    this.mouse.move(drop.left + drop.width / 2 + 10, drop.top + drop.height / 2);
                    this.evaluate(function() {
                        CMS.$(document).trigger(new CMS.$.Event('keydown', { keyCode: 17, ctrlKey: true }));
                    });
                })
                .then(function() {
                    test.assertVisible('.jstree-copy', 'Copy indicator shown');
                    // since casper cannot trigger a mouse event with ctrlKey pressed,
                    // we fake the event with jQuery
                    this.evaluate(function() {
                        CMS.$(document).trigger(new CMS.$.Event('mouseup', { ctrlKey: true }));
                    });
                })
                .then(
                    acceptCopyingAndAssertNewTree([
                        {
                            name: 'Homepage',
                            children: [
                                {
                                    name: 'Second'
                                }
                            ]
                        },
                        {
                            name: 'Second'
                        }
                    ])
                );
        })
        .then(cms.removePage())
        .then(cms.removePage())
        .run(function() {
            test.done();
        });
});

casper.test.begin('Pages can be copied into a position between current children', function(test) {
    casper
        .then(cms.addPage({ title: 'Homepage' }))
        .then(cms.addPage({ title: 'Child 1', parent: 'Homepage' }))
        .then(cms.addPage({ title: 'Child 2', parent: 'Homepage' }))
        .then(cms.addPage({ title: 'Second' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            var drop;
            casper
                .waitUntilVisible('.cms-pagetree-jstree', cms.waitUntilAllAjaxCallsFinish())
                .then(cms.expandPageTree())
                .then(function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [{ name: 'Child 1' }, { name: 'Child 2' }]
                                },
                                { name: 'Second' }
                            ])
                        ),
                        'Initial state is correct'
                    );

                    // usually to drag stuff in the iframe you have to calculate the position of the frame
                    // and then the position of the thing inside frame, but here sideframe is opened at 0, 0
                    // so this should be enough
                    drop = this.getElementBounds(
                        xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Child 1")]')
                    );

                    this.mouse.down(xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Second")]'));
                    this.mouse.move(drop.left + drop.width / 2, drop.top + drop.height + 3);
                    this.evaluate(function() {
                        CMS.$(document).trigger(new CMS.$.Event('keydown', { keyCode: 17, ctrlKey: true }));
                    });
                })
                .then(function() {
                    test.assertVisible('.jstree-copy', 'Copy indicator shown');
                    // since casper cannot trigger a mouse event with ctrlKey pressed,
                    // we fake the event with jQuery
                    this.evaluate(function() {
                        CMS.$(document).trigger(new CMS.$.Event('mouseup', { ctrlKey: true }));
                    });
                })
                .then(
                    acceptCopyingAndAssertNewTree([
                        {
                            name: 'Homepage',
                            children: [{ name: 'Child 1' }, { name: 'Second' }, { name: 'Child 2' }]
                        },
                        { name: 'Second' }
                    ])
                );
        })
        .then(cms.removePage())
        .then(cms.removePage())
        .run(function() {
            test.done();
        });
});

casper.test.begin('Pages can be copied in between own descendants that themselves have children', function(test) {
    casper
        .then(cms.addPage({ title: 'Homepage' }))
        .then(cms.addPage({ title: 'Child 1', parent: 'Homepage' }))
        .then(cms.addPage({ title: 'Child 1-1', parent: 'Child 1' }))
        .then(cms.addPage({ title: 'Child 2', parent: 'Homepage' }))
        .then(cms.addPage({ title: 'Child 2-2', parent: 'Child 2' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            var drop;
            casper
                .waitUntilVisible('.cms-pagetree-jstree', cms.waitUntilAllAjaxCallsFinish())
                .then(cms.expandPageTree())
                .then(function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Child 1',
                                            children: [
                                                {
                                                    name: 'Child 1-1'
                                                }
                                            ]
                                        },
                                        {
                                            name: 'Child 2',
                                            children: [
                                                {
                                                    name: 'Child 2-2'
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Initial state is correct'
                    );

                    // usually to drag stuff in the iframe you have to calculate the position of the frame
                    // and then the position of the thing inside frame, but here sideframe is opened at 0, 0
                    // so this should be enough
                    drop = this.getElementBounds(
                        xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Child 1")]')
                    );

                    this.mouse.down(xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]'));
                    this.mouse.move(drop.left + drop.width / 2, drop.top + drop.height * 2 + 3);
                    this.evaluate(function() {
                        CMS.$(document).trigger(new CMS.$.Event('keydown', { keyCode: 17, ctrlKey: true }));
                    });
                })
                .then(function() {
                    test.assertVisible('.jstree-copy', 'Copy indicator shown');
                    // since casper cannot trigger a mouse event with ctrlKey pressed,
                    // we fake the event with jQuery
                    this.evaluate(function() {
                        CMS.$(document).trigger(new CMS.$.Event('mouseup', { ctrlKey: true }));
                    });
                })
                .then(
                    acceptCopyingAndAssertNewTree([
                        {
                            name: 'Homepage',
                            children: [
                                {
                                    name: 'Child 1',
                                    children: [
                                        {
                                            name: 'Child 1-1'
                                        }
                                    ]
                                },
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Child 1',
                                            children: [
                                                {
                                                    name: 'Child 1-1'
                                                }
                                            ]
                                        },
                                        {
                                            name: 'Child 2',
                                            children: [
                                                {
                                                    name: 'Child 2-2'
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    name: 'Child 2',
                                    children: [
                                        {
                                            name: 'Child 2-2'
                                        }
                                    ]
                                }
                            ]
                        }
                    ])
                );
        })
        .then(cms.removePage())
        .run(function() {
            test.done();
        });
});

casper.test.begin("Pages can be copied in between own descendant's descendants", function(test) {
    casper
        .start()
        .then(cms.addPage({ title: 'Homepage' }))
        .then(cms.addPage({ title: 'Child 1', parent: 'Homepage' }))
        .then(cms.addPage({ title: 'Child 1-1', parent: 'Child 1' }))
        .then(cms.addPage({ title: 'Child 1-1-1', parent: 'Child 1-1' }))
        .then(cms.addPage({ title: 'Child 1-1-2', parent: 'Child 1-1' }))
        .then(cms.addPage({ title: 'Child 2', parent: 'Homepage' }))
        .thenOpen(globals.baseUrl)
        .then(cms.openSideframe())
        // switch to sideframe
        .withFrame(0, function() {
            var drop;
            casper
                .waitUntilVisible('.cms-pagetree-jstree', cms.waitUntilAllAjaxCallsFinish())
                .then(cms.expandPageTree())
                .then(function() {
                    test.assertExists(
                        xPath(
                            createJSTreeXPathFromTree([
                                {
                                    name: 'Homepage',
                                    children: [
                                        {
                                            name: 'Child 1',
                                            children: [
                                                {
                                                    name: 'Child 1-1',
                                                    children: [{ name: 'Child 1-1-1' }, { name: 'Child 1-1-2' }]
                                                }
                                            ]
                                        },
                                        {
                                            name: 'Child 2'
                                        }
                                    ]
                                }
                            ])
                        ),
                        'Initial state is correct'
                    );

                    // usually to drag stuff in the iframe you have to calculate the position of the frame
                    // and then the position of the thing inside frame, but here sideframe is opened at 0, 0
                    // so this should be enough
                    drop = this.getElementBounds(
                        xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Child 1")]')
                    );

                    this.mouse.down(xPath('//a[contains(@class, "jstree-anchor")][contains(text(), "Homepage")]'));
                    this.mouse.move(drop.left + drop.width / 2, drop.top + drop.height * 3 + 3);
                    this.evaluate(function() {
                        CMS.$(document).trigger(new CMS.$.Event('keydown', { keyCode: 17, ctrlKey: true }));
                    });
                })
                .then(function() {
                    test.assertVisible('.jstree-copy', 'Copy indicator shown');
                    // since casper cannot trigger a mouse event with ctrlKey pressed,
                    // we fake the event with jQuery
                    this.evaluate(function() {
                        CMS.$(document).trigger(new CMS.$.Event('mouseup', { ctrlKey: true }));
                    });
                })
                .then(
                    acceptCopyingAndAssertNewTree([
                        {
                            name: 'Homepage',
                            children: [
                                {
                                    name: 'Child 1',
                                    children: [
                                        {
                                            name: 'Child 1-1',
                                            children: [
                                                { name: 'Child 1-1-1' },
                                                {
                                                    name: 'Homepage',
                                                    children: [
                                                        {
                                                            name: 'Child 1',
                                                            children: [
                                                                {
                                                                    name: 'Child 1-1',
                                                                    children: [
                                                                        { name: 'Child 1-1-1' },
                                                                        { name: 'Child 1-1-2' }
                                                                    ]
                                                                }
                                                            ]
                                                        },
                                                        {
                                                            name: 'Child 2'
                                                        }
                                                    ]
                                                },
                                                { name: 'Child 1-1-2' }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    name: 'Child 2'
                                }
                            ]
                        }
                    ])
                );
        })
        .then(cms.removePage())
        .run(function() {
            test.done();
        });
});
