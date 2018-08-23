var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var casperjs = require('casper');
var cms = helpers(casperjs);

cms.addPlugin = function (opts) {
    var xPath = casperjs.selectXPath;
    var that = this;

    return function () {
        return this.then(that.waitUntilAllAjaxCallsFinish()).thenOpen(globals.editUrl)
            .then(function () {
                this.click('.cms-btn-switch-edit');
            })
            .wait(2000)
            .then(that.switchTo('structure'))
            .wait(100)
        // only add to placeholder if no parent specified
            .thenBypassIf(opts.parent, 1)
            .waitUntilVisible('.cms-structure', function () {
                this.click('.cms-structure .cms-submenu-add [data-cms-tooltip="Add plugin"]');
            })
        // if parent specified - try to add to it
            .thenBypassUnless(opts.parent, 1)
            .then(function () {
                var parentSelector;

                // if the parent is expanded - click on "Add plugin"
                if (this.visible(opts.parent)) {
                    this.click(opts.parent + ' [data-cms-tooltip="Add plugin"]');
                } else {
                    // get full selector (css3, not jquery) of the closest placeholder
                    parentSelector = this.evaluate(function (selector) {
                        return CMS.$(selector).closest('.cms-dragarea').parentsUntil('body')
                            .andSelf()
                            .map(function () {
                                return this.nodeName + ':nth-child(' + (CMS.$(this).index() + 1) + ')';
                            }).get().join('>');
                    }, opts.parent);

                    that.expandPlaceholderPlugins(parentSelector);

                    this.wait(100);
                    this.click(opts.parent + ' [data-cms-tooltip="Add plugin"]');
                }
            })
            .wait(200)
            .waitUntilVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]', function () {
                this.then(function () {
                    this.click(xPath('//a[@href="' + opts.type + '"]'));
                });
                // ensure previous content has been changed
                return this.waitWhileVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]');
            })
            .waitForResource(/add-plugin/)
            .withFrame(0, function () {
                // we cannot pass the options as object because casper js
                // treats objects/arrays in a funny way, so we stringify it
                this.waitUntilVisible('#content', function () {
                    this.evaluate(function (content) {
                        var parsedContent;

                        if (!content.length) {
                            return;
                        }

                        parsedContent = JSON.parse(content);

                        Object.keys(parsedContent).forEach(function (key) {
                            document.querySelector('#' + key).value = parsedContent[key];
                        });
                    }, JSON.stringify(opts.content));
                });
            })
            .then(function () {
                // djangocms-text-ckeditor is special
                if (opts.type === 'TextPlugin') {
                    this.withFrame(0, function () {
                        casper.waitUntilVisible('.cke_inner', function () {
                            // explicitly put text to ckeditor
                            this.evaluate(function (contentData) {
                                CMS.CKEditor.editor.setData(contentData);
                            }, opts.content.id_body);
                        });
                    });
                }
            }).then(function () {
                this.click('.cms-modal-buttons .cms-btn-action.default');
            }).waitForUrl(/.*/).then(that.waitUntilAllAjaxCallsFinish());
    };
};

casper.test.setUp(function(done) {
    casper
        .start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        .run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.removePage()).then(cms.logout()).run(done);
});

casper.test.begin('Tooltip is correct after adding multiple plugins', function(test) {
    casper
        .start(globals.editUrl)
        .then(cms.addPlugin({
            type: 'MultiWrapPlugin',
            content: {
                id_create: 1
            }
        }))
        .wait(1000, function () {
            var plugin = this.getElementBounds('.inner-wrap');

            this.mouse.move(plugin.left + plugin.width / 2, plugin.top + plugin.height / 2);
        })
        .then(function () {
            test.assertVisible('.cms-tooltip');
            test.assertSelectorHasText(
                '.cms-tooltip span',
                'Placeholder_Content_1: Wrap'
            );
        })
        .run(function() {
            test.done();
        });
});
