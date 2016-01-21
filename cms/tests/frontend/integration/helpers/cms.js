/* global document, localStorage */
'use strict';
var globals = require('../settings/globals');

module.exports = function (casperjs) {
    return {
        /**
         * Logs in with the given parameters
         *
         * @public
         * @param {Object} [credentials=globals.credentials]
         * @param {String} credentials.username
         * @param {String} credentials.password
         */
        login: function (credentials) {
            return function () {
                return this.thenOpen(globals.adminUrl).then(function () {
                    this.fill('#login-form', credentials ||  globals.credentials, true);
                }).waitForResource(/login/).thenEvaluate(function () {
                    localStorage.clear();
                });
            };
        },

        logout: function () {
            return function () {
                return this.thenOpen(globals.adminLogoutUrl)
                    .waitForSelector('#content');
            };
        },

        /**
         * removes a page by name, or the first encountered one
         *
         * @public
         * @param {Object} opts
         * @param {String} [opts.title] Name of the page to delete
         */
        removePage: function (opts) {
            return function () {
                return this.thenOpen(globals.adminPagesUrl)
                    .waitUntilVisible('.tree .deletelink')
                    .then(function () {
                        var pageId;
                        if (opts && opts.title) {
                            // important to pass single param, because casper acts
                            // weirdly with single key objects https://github.com/n1k0/casperjs/issues/353
                            pageId = this.evaluate(function (title) {
                                return CMS.$('.col1 a > span').map(function () {
                                    var span = $(this);
                                    if (span.text().trim() === title) {
                                        return span.closest('li').attr('id').split('_')[1];
                                    }
                                }).get()[0];
                            }, opts.title);
                        }
                        if (pageId) {
                            this.click('.tree .deletelink[href*="' + pageId + '"]');
                        } else {
                            this.click('.tree .deletelink'); // first one
                        }
                    })
                    .waitUntilVisible('input[type=submit]')
                    .then(function () {
                        this.click('input[type=submit]');
                    });
            };
        },

        /**
        * Adds the page
        *
        * @public
        * @param {Object} opts
        * @param {String} opts.title name of the page
        */
        addPage: function (opts) {
            return function () {
                return this.thenOpen(globals.adminPagesUrl + 'add/')
                    .waitUntilVisible('#id_title')
                    .then(function () {
                        this.sendKeys('#id_title', opts.title);
                        this.click('input[name="_save"]');
                    })
                    .waitUntilVisible('.success');
            };
        },

        /**
         * Adds the plugin (currently to the first placeholder)
         *
         * @param {Object} opts
         * @param {String} opts.type type of the plugin to add
         * @param {Object} opts.content object containing fields and values
         * @param {Object} [opts.parent] selector of the parent cms-draggable
         * @example
         *
         *     cms.addPlugin({
         *         type: 'TextPlugin',
         *         content: {
         *             id_body: 'Some text'
         *         }
         *     });
         */
        addPlugin: function (opts) {
            var xPath = casperjs.selectXPath;

            return function () {
                return this.thenOpen(globals.editUrl)
                    .waitUntilVisible('.cms-toolbar-expanded', function () {
                        this.click('.cms-toolbar-item-cms-mode-switcher .cms-btn[href="?build"]');
                    })
                    // only add to placeholder if no parent specified
                    .thenBypassIf(opts.parent, 1)
                    .waitUntilVisible('.cms-structure', function () {
                        this.click('.cms-structure .cms-submenu-add [data-cms-tooltip="Add plugin"]');
                    })
                    // if parent specified - try to add to it
                    .thenBypassUnless(opts.parent, 1)
                    .then(function () {
                        // if the parent is expanded - click on "Add plugin"
                        if (this.visible(opts.parent)) {
                            this.click(opts.parent + ' [data-cms-tooltip="Add plugin"]');
                        } else {
                            // get full selector (css3, not jquery) of the closest placeholder
                            var parentSelector = this.evaluate(function (selector) {
                                return $(selector).closest('.cms-dragarea').parentsUntil('body')
                                    .andSelf()
                                    .map(function () {
                                        return this.nodeName + ':nth-child(' + ($(this).index() + 1) + ')';
                                    }).get().join('>');
                            }, opts.parent);

                            // check if "Expand all" is visible
                            if (this.visible(parentSelector + ' .cms-dragbar-expand-all')) {
                                this.click(parentSelector + ' .cms-dragbar-expand-all');
                            } else {
                                // if not visible, then first "Collapse all"
                                this.click(parentSelector + ' .cms-dragbar-collapse-all');
                                this.wait(100);
                                this.click(parentSelector + ' .cms-dragbar-expand-all');
                            }

                            this.wait(100);
                            this.click(opts.parent + ' [data-cms-tooltip="Add plugin"]');
                        }
                    })
                    .waitUntilVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]', function () {
                        this.then(function () {
                            this.click(xPath('//a[@href="' + opts.type + '"]'));
                        });
                        // ensure previous content has been changed
                        return this.waitWhileVisible('.cms-plugin-picker .cms-submenu-item [data-rel="add"]');
                    })
                    .withFrame(0, function () {
                        // we cannot pass the options as object because casper js
                        // treats objects/arrays in a funny way, so we stringify it
                        this.waitUntilVisible('#content', function () {
                            this.evaluate(function (content) {
                                if (!content.length) {
                                    return;
                                }

                                content = JSON.parse(content);

                                Object.keys(content).forEach(function (key) {
                                    document.querySelector('#' + key).value = content[key];
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
                    }).waitForResource(/edit-plugin/);
            };
        },

        clearClipboard: function () {
            return function () {
                return this.thenOpen(globals.editUrl)
                    .then(function () {
                        this.click('.cms-clipboard-empty a');
                    })
                    .waitForResource(/clear/);
            };
        },

        /**
         * Switches structureboard to a specific mode.
         *
         * @function switchTo
         * @param {String} view 'structure' or 'content'
         */
        switchTo: function (view) {
            var url;
            if (view === 'structure') {
                url = 'build';
            } else if (view === 'content') {
                url = 'edit';
            } else {
                throw new Error('Invalid arguments passed to cms.switchTo, should be either "structure" or "content"');
            }
            return function () {
                return this.waitUntilVisible('.cms-toolbar-expanded')
                    .then(function () {
                        this.click('.cms-toolbar-item-cms-mode-switcher .cms-btn[href="?' + url + '"]');
                    });
            };
        },

        /**
         * Expands all plugins in the given placeholder.
         *
         * @function expandPlaceholderPlugins
         * @param {String} selector placeholder selector
         */
        expandPlaceholderPlugins: function (selector) {
            return function () {
                return this.then(function () {
                    // if "Expand all" is visible then
                    if (this.visible(selector + ' .cms-dragbar-expand-all')) {
                        this.click(selector + ' .cms-dragbar-expand-all');
                    } else if (this.visible(selector + ' .cms-dragbar-collapse-all')) {
                        // if not visible, then first "Collapse all"
                        this.click(selector + ' .cms-dragbar-collapse-all');
                        this.wait(100);
                        this.click(selector + ' .cms-dragbar-expand-all');
                    } else {
                        throw new Error('Given placeholder has no plugins');
                    }
                });
            };
        }
    };
};
