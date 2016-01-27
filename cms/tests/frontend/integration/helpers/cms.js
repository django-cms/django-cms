/* global document, localStorage */
'use strict';
var globals = require('../settings/globals');

module.exports = function (casperjs) {
    return {
        /**
         * Logs in with the given parameters
         *
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
            var that = this;
            return function () {
                return this.thenOpen(globals.adminPagesUrl)
                    .waitUntilVisible('.cms-pagetree [href*="delete"]')
                    .then(that.expandPageTree())
                    .then(function () {
                        var pageId;
                        if (opts && opts.title) {
                            pageId = that.getPageId(opts.title);
                        }

                        if (pageId) {
                            this.click('.cms-pagetree [href*="delete"][href*="' + pageId + '"]');
                        } else {
                            this.click('.cms-pagetree [href*="delete"]'); // first one
                        }
                    })
                    .waitUntilVisible('input[type=submit]')
                    .then(function () {
                        this.click('input[type=submit]');
                    });
            };
        },

        /**
        * Adds the page. Optionally added page can be nested into
        * a parent with given title (first in a list of equal titles taken).
        *
        * @public
        * @param {Object} opts
        * @param {String} opts.title name of the page
        * @param {String} [opts.title] name of the parent page
        */
        addPage: function (opts) {
            var that = this;

            if (opts.parent) {
                return function () {
                    return this.thenOpen(globals.adminPagesUrl)
                        .waitUntilVisible('.cms-pagetree')
                        .then(that.expandPageTree())
                        .then(function () {
                            var pageId = that.getPageId(opts.parent);
                            // add nested page
                            this.click('a[href*="/admin/cms/page/add/?target=' + pageId + '"]');
                        })
                        .waitForSelector('#page_form', function () {
                            this.sendKeys('#id_title', opts.title);
                            this.click('input[name="_save"]');
                        })
                        .waitUntilVisible('.success');
                };
            }

            // add page as usual
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
         * Adds the plugin. If the parent is not specified, plugin
         * is added to the first placeholder on the page.
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
            var that = this;

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

                            that.expandPlaceholderPlugins(parentSelector);

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
        },

        /**
         * Opens the sideframe. Toolbar has to be there.
         *
         * @function openSideframe
         */
        openSideframe: function () {
            return function () {
                return this.waitUntilVisible('.cms-toolbar-expanded', function () {
                    // open "Example.com" menu
                    this.click('.cms-toolbar-item-navigation li:first-child a');
                })
                // open "Administration"
                .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
                    this.click('.cms-toolbar-item-navigation-hover a[href*="/admin/cms/page"]');
                })
                // wait until sideframe is open
                .waitUntilVisible('.cms-sideframe-frame');
            };
        },

        /**
         * Recursively expands the page tree to operate on page nodes.
         *
         * @function expandPageTree
         */
        expandPageTree: function () {
            var that = this;
            return function () {
                return this.then(function () {
                    if (this.visible('.jstree-closed')) {
                        this.click('.jstree-closed > .jstree-ocl');
                        // there's no clear way to check if the page was loading
                        // or was already in the DOM
                        return casper.wait(1000).then(that.expandPageTree());
                    }
                });
            };
        },

        /**
         * Returns pageId. Page has to be visible in the page tree. See `expandPageTree`.
         *
         * @function getPageId
         * @param {String} title page title
         * @return {String|Boolean} page id as a string or false if couldn't be found
         */
        getPageId: function (title) {
            return this._getPageIds(title)[0];
        },

        /**
         * Returns pageIds of all the pages with same title.
         * Pages has to be visible in the page tree. See `expandPageTree`.
         *
         * @function _getPageIds
         * @private
         * @param {String} title page title
         * @return {String[]|Boolean} page ids as an array of strings or false if couldn't be found
         */
        _getPageIds: function (title) {
            // important to pass single param, because casper acts
            // weirdly with single key objects https://github.com/n1k0/casperjs/issues/353
            return casper.evaluate(function (title) {
                return CMS.$('.jstree-anchor').map(function () {
                    var anchor = $(this);
                    if (anchor.text().trim() === title) {
                        return anchor.parent().data('id');
                    }
                }).toArray();
            }, title);
        }
    };
};
