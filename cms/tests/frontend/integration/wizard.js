'use strict';

// #############################################################################
// Wizard

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers();

casper.test.setUp(function(done) {
    casper.start().then(cms.login()).run(done);
});

casper.test.tearDown(function(done) {
    casper
        .start()
        .then(cms.removePage()) // remove root page
        .then(cms.logout())
        .run(done);
});

casper.test.begin('Add first page with a wizard (doubleclick)', function(test) {
    casper
        .start(globals.editUrl)
        // wait till wizard modal show up automatically (since we don't have any pages)
        .waitUntilVisible('.cms-modal', function() {
            // switch to modal
            var framePosition = this.getElementBounds('.cms-modal-frame');

            casper.withFrame(0, function() {
                this.waitUntilVisible('.cms-content-wizard', function() {
                    // doubleclick on the "new page"
                    var choicePosition = this.getElementBounds('.choice.active');
                    var coordinates = [
                        framePosition.left + choicePosition.left + choicePosition.width / 2,
                        framePosition.top + choicePosition.top + choicePosition.height / 2
                    ];

                    this.mouse.doubleclick.apply(this, coordinates);
                })
                    .waitForResource(/cms_wizard\/create/)
                    // wait until next step loads
                    .waitUntilVisible('#cke_id_1-content', function() {
                        // ckeditor textarea has to be done like this
                        this.evaluate(function() {
                            CMS.CKEditor.editor.setData('Some text');
                        });

                        // submit the form from inside the modal
                        this.fill(
                            '.cms-content-wizard form',
                            {
                                '1-title': 'Homepage'
                            },
                            true
                        );
                    });
            });
        })
        .waitForResource(/cms_wizard\/create/)
        .waitForSelector('.cms-ready', function() {
            test.assertSelectorHasText(
                '.cms-plugin',
                'Some text',
                'The new page has been created and its content is correct'
            );
        })
        .run(function() {
            test.done();
        });
});

casper.test.begin('Add sub page with a wizard (click on next button)', function(test) {
    casper
        .start()
        .then(cms.addPage({ title: 'Homepage' }))
        .thenOpen(globals.editUrl)
        .waitForSelector('.cms-toolbar-expanded', function() {
            this.click('.cms-btn[href*="cms_wizard/create"]');
        })
        // wait till wizard modal show up
        .waitUntilVisible('.cms-modal', function() {
            // switch to modal
            casper.withFrame(0, function() {
                this.waitUntilVisible('.cms-content-wizard', function() {
                    test.assertSelectorHasText(
                        '.choice.active',
                        'New page',
                        '"New page" is available and active by default'
                    );
                    test.assertSelectorHasText(
                        '.choice:not(.active)',
                        'New sub page',
                        '"New sub page" is available and not active by default'
                    );

                    this.click('.choice:not(.active)');
                });
            });
        })
        .then(function() {
            this.click('.cms-modal-buttons .cms-btn-action');
        })
        .waitForResource(/cms_wizard\/create/)
        .then(function() {
            casper.withFrame(0, function() {
                // wait until next step loads
                this.waitUntilVisible('#cke_id_1-content', function() {
                    // ckeditor textarea has to be done like this
                    this.evaluate(function() {
                        CMS.CKEditor.editor.setData('Some subpage text');
                    });
                    // fill, but do not submit form from inside the modal
                    this.fill('.cms-content-wizard form', {
                        '1-title': 'Subpage'
                    });
                });
            });
        })
        .then(function() {
            this.click('.cms-modal-buttons .cms-btn-action');
        })
        .waitForResource(/cms_wizard\/create/)
        .waitForSelector('.cms-ready', function() {
            test.assertSelectorHasText(
                '.cms-plugin',
                'Some subpage text',
                'The new page has been created and its content is correct'
            );
            test.assertTitleMatch(/Subpage/, 'The new page has been created and its title is correct');
            test.assertEval(function() {
                var selectedChild = CMS.$('.nav .selected');

                return (
                    selectedChild.find('> a').text() === 'Subpage' &&
                    // have to use parents, because closest li is selectedChild itself
                    selectedChild.parents('li').eq(0) &&
                    selectedChild.parents('li').eq(0).find('> a').text() === 'Homepage'
                );
            }, 'Subpage appears in the menu correctly');
        })
        .run(function() {
            test.done();
        });
});

casper.test.begin('Can go back in wizard', function(test) {
    casper
        .start(globals.editUrl)
        // wait till wizard modal show up automatically (since we don't have any pages)
        .waitUntilVisible('.cms-modal', function() {
            // switch to modal
            casper.withFrame(0, function() {
                this.waitUntilVisible('.cms-content-wizard', function() {
                    test.assertVisible('.choice', 'First step is visible');
                });
            });
        })
        .then(function() {
            this.click('.cms-modal-buttons .cms-btn-action');
        })
        .waitForResource(/cms_wizard\/create/)
        .then(function() {
            casper.withFrame(0, function() {
                this.waitUntilVisible('.cms-content-wizard', function() {
                    test.assertVisible('#id_1-title', 'Second step is visible');
                });
            });
        })
        .then(function() {
            this.click('.cms-modal-item-buttons-left .cms-btn');
        })
        .waitForResource(/cms_wizard\/create/)
        .then(function() {
            casper.withFrame(0, function() {
                this.waitUntilVisible('.cms-content-wizard', function() {
                    test.assertVisible('.choice', 'First step is visible again');
                });
            });
        })
        // have to create a page to tear down correctly
        .then(cms.addPage({ title: 'whatever' }))
        .run(function() {
            test.done();
        });
});
