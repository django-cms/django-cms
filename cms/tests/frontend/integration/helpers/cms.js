/* global document, localStorage */
'use strict';

module.exports = function (casperjs, settings) {
    var globals = typeof settings === 'undefined' ? require('../settings/globals') : settings;

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
                return this.wait(1000).thenOpen(globals.adminLogoutUrl)
                    .waitForSelector('#content');
            };
        },

        /**
         * removes a page by name, or the first encountered one
         *
         * @param {Object} opts
         * @param {String} [opts.title] Name of the page to delete
         */
        removePage: function (opts) {
            var that = this;
            return function () {
                return this.thenOpen(globals.adminPagesUrl)
                    .waitUntilVisible('.js-cms-pagetree-options')
                    .then(that.expandPageTree())
                    .then(function () {
                        var pageId;
                        if (opts && opts.title) {
                            pageId = that.getPageId(opts.title);
                        }

                        var data = pageId ? '[data-id="' + pageId + '"]' : '';
                        var href = pageId ? '[href*="' + pageId + '"]' : '';

                        return this.then(function () {
                                this.click('.js-cms-pagetree-options' + data);
                            })
                            .waitUntilVisible('.cms-pagetree-dropdown-menu-open')
                            .then(function () {
                                this.click('.cms-pagetree-jstree [href*="delete"]' + href);
                            });
                    })
                    .waitForUrl(/delete/)
                    .waitUntilVisible('input[type=submit]')
                    .then(function () {
                        this.click('input[type=submit]');
                    })
                    .wait(1000)
                    .then(that.waitUntilAllAjaxCallsFinish());
            };
        },

        /**
         * Opens dropdown and triggers copying a page
         *
         * @public
         * @param {Object} opts
         * @param {Number|String} opts.page page id
         */
        triggerCopyPage: function (opts) {
            return function () {
                return this.then(function () {
                        this.click('.js-cms-pagetree-options[data-id="' + opts.page + '"]');
                    })
                    .waitUntilVisible('.cms-pagetree-dropdown-menu-open')
                    .then(function () {
                        this.mouse.click('.js-cms-tree-item-copy[data-id="' + opts.page + '"]');
                    })
                    .wait(100);
            };
        },

        /**
         * Opens dropdown and triggers cutting a page
         *
         * @public
         * @param {Object} opts
         * @param {Number|String} opts.page page id
         */
        triggerCutPage: function (opts) {
            return function () {
                return this.then(function () {
                        this.click('.js-cms-pagetree-options[data-id="' + opts.page + '"]');
                    })
                    .waitUntilVisible('.cms-pagetree-dropdown-menu-open')
                    .then(function () {
                        this.mouse.click('.js-cms-tree-item-copy[data-id="' + opts.page + '"] ~ .js-cms-tree-item-cut');
                    })
                    .wait(100);
            };
        },

        /**
         * Opens dropdown and triggers pasting a page
         *
         * @public
         * @param {Object} opts
         * @param {Number|String} opts.page page id
         */
        triggerPastePage: function (opts) {
            return function () {
                return this.then(function () {
                        this.click('.js-cms-pagetree-options[data-id="' + opts.page + '"]');
                    })
                    .waitUntilVisible('.cms-pagetree-dropdown-menu-open')
                    .then(function () {
                        this.mouse.click('.js-cms-tree-item-paste[data-id="' + opts.page + '"]');
                    })
                    .wait(100);
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
                    return this.wait(1000).thenOpen(globals.adminPagesUrl)
                        .waitUntilVisible('.cms-pagetree-jstree')
                        .then(that.waitUntilAllAjaxCallsFinish())
                        .then(that.expandPageTree())
                        .then(function () {
                            var pageId = that.getPageId(opts.parent);
                            // add nested page
                            this.click('a[href*="/admin/cms/page/add/?target=' + pageId + '"]');
                        })
                        .waitForSelector('#page_form', function () {
                            this.sendKeys('#id_title', opts.title);
                        })
                        .waitForUrl(/add/)
                        .wait(250, function () {
                            this.click('input[name="_save"]');
                        })
                        .waitForResource(/add/)
                        .waitUntilVisible('.success')
                        .waitForUrl(/cms/)
                        .then(that.waitUntilAllAjaxCallsFinish())
                        .wait(1000);
                };
            }

            // add page as usual
            return function () {
                return this.wait(1000).thenOpen(globals.adminPagesUrl + 'add/')
                    .waitForUrl(/add/)
                    .waitUntilVisible('#id_title')
                    .then(function () {
                        this.sendKeys('#id_title', opts.title);
                    })
                    .wait(250, function () {
                        this.click('input[name="_save"]');
                    })
                    .waitForResource(/add/)
                    .waitForUrl(/cms/)
                    .waitUntilVisible('.success')
                    .then(that.waitUntilAllAjaxCallsFinish())
                    .wait(1000);
            };
        },

        /**
         * @function _modifyPageAdvancedSettings
         * @private
         * @param {Object} opts options
         * @param {String} opts.page page name (will take first one in the tree)
         * @param {Object} opts.fields { fieldName: value, ... }
         */
        _modifyPageAdvancedSettings: function _modifyPageAdvancedSettings(opts) {
            var that = this;
            return function () {
                return this.wait(1000).thenOpen(globals.adminPagesUrl)
                    .waitUntilVisible('.cms-pagetree-jstree')
                    .then(that.waitUntilAllAjaxCallsFinish())
                    .then(that.expandPageTree())
                    .then(function () {
                        var pageId = that.getPageId(opts.page);
                        this.thenOpen(globals.adminPagesUrl + pageId + '/advanced-settings/');
                    })
                    .waitForSelector('#page_form', function () {
                        this.fill('#page_form', opts.fields, true);
                    })
                    .waitForUrl(/page/)
                    .waitUntilVisible('.success')
                    .then(that.waitUntilAllAjaxCallsFinish())
                    .wait(1000);
            };
        },

        /**
         * @function addApphookToPage
         * @param {Object} opts options
         * @param {String} opts.page page name (will take first one in the tree)
         * @param {String} opts.apphook app name
         */
        addApphookToPage: function addApphookToPage(opts) {
            return this._modifyPageAdvancedSettings({
                page: opts.page,
                fields: {
                    application_urls: opts.apphook
                }
            });
        },

        /**
         * @function setPageTemplate
         * @param {Object} opts options
         * @param {String} opts.page page name (will take first one in the tree)
         * @param {String} opts.tempalte template file name (e.g. simple.html)
         */
        setPageTemplate: function setPageTemplate(opts) {
            return this._modifyPageAdvancedSettings({
                page: opts.page,
                fields: {
                    template: opts.template
                }
            });
        },

        /**
         * @function publishPage
         * @param {Object} opts options
         * @param {String} opts.page page name (will take first one in the tree)
         * @param {String} [opts.language='en'] language to publish
         */
        publishPage: function publishPage(opts) {
            var that = this;
            var language = typeof opts.language !== 'undefined' ? opts.language : 'en';

            return function () {
                var pageId;
                return this.wait(1000).thenOpen(globals.adminPagesUrl)
                    .waitUntilVisible('.cms-pagetree-jstree')
                    .then(that.waitUntilAllAjaxCallsFinish())
                    .then(that.expandPageTree())
                    .then(function () {
                        pageId = that.getPageId(opts.page);
                        this.click('.cms-tree-item-lang a[href*="' + pageId + '/' + language + '/preview/"] span');
                    })
                    .waitUntilVisible('.cms-pagetree-dropdown-menu', function () {
                        this.click('.cms-pagetree-dropdown-menu-open a[href*="/' + language + '/publish/"]');
                    })
                    .waitForResource(/publish/)
                    .waitUntilVisible('.cms-pagetree-jstree')
                    .then(that.waitUntilAllAjaxCallsFinish())
                    .then(that.expandPageTree())
                    .wait(1000);
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
                return this.then(that.waitUntilAllAjaxCallsFinish()).thenOpen(globals.editUrl)
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
                    }).waitForUrl(/.*/).then(that.waitUntilAllAjaxCallsFinish());
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
            var pos;
            if (view === 'structure') {
                pos = 'first';
            } else if (view === 'content') {
                pos = 'last';
            } else {
                throw new Error('Invalid arguments passed to cms.switchTo, should be either "structure" or "content"');
            }
            return function () {
                return this.waitForSelector('.cms-toolbar-expanded')
                    .then(function () {
                        this.click('.cms-toolbar-item-cms-mode-switcher .cms-btn:' + pos + '-child');
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
                return this.waitForSelector('.cms-toolbar-expanded', function () {
                    // open "Example.com" menu
                    this.click('.cms-toolbar-item-navigation li:first-child a');
                })
                // open "Pages"
                .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
                    this.click('.cms-toolbar-item-navigation-hover a[href*="/admin/cms/page"]');
                })
                // wait until sideframe is open
                .waitUntilVisible('.cms-sideframe-frame')
                .wait(1000);
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
                        return casper
                            .then(that.waitUntilAllAjaxCallsFinish())
                            .then(that.expandPageTree());
                    } else {
                        return casper.wait(1000)
                            .then(that.waitUntilAllAjaxCallsFinish());
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
        },

        /**
         * Wait a bit and then wait until $.active will become 0.
         * $.active is not documented, but it shows amount of ongoing
         * jQuery requests.
         *
         * @function waitUntilAllAjaxCallsFinish
         */
        waitUntilAllAjaxCallsFinish: function () {
            return function () {
                return casper.wait(200)
                    .waitFor(function () {
                        var remainingAjaxRequests = this.evaluate(function () {
                            var amount = 0;

                            try {
                                amount = CMS.$.active;
                            } catch (e) {}

                            return amount;
                        });

                        return (remainingAjaxRequests === 0);
                    }).wait(200);
            };
        },

        /**
         * @function createJSTreeXPathFromTree
         * @param {Object[]} tree tree object, see example
         * @param {Object} [opts]
         * @param {Object} [opts.topLevel=true] is it the top level?
         * @example tree
         *
         *     [
         *         {
         *             name: 'Homepage'
         *             children: [
         *                 {
         *                     name: 'Nested'
         *                 }
         *             ]
         *         },
         *         {
         *             name: 'Sibling'
         *         }
         *     ]
         */
        createJSTreeXPathFromTree: function createJSTreeXPathFromTree(tree, opts) {
            var xPath = '';
            var topLevel = opts && typeof opts.topLevel !== 'undefined' ? topLevel : true;

            tree.forEach(function (node, index) {
                if (index === 0) {
                    if (topLevel) {
                        xPath += '//';
                    } else {
                        xPath += './';
                    }
                    xPath += 'li[./a[contains(@class, "jstree-anchor")][contains(text(), "' + node.name +
                        '")]${children}]';
                } else {
                    xPath += '/following-sibling::li' +
                        '[./a[contains(@class, "jstree-anchor")][contains(text(), "' + node.name + '")]${children}]';
                }

                if (node.children) {
                    xPath = xPath.replace(
                        '${children}',
                        '/following-sibling::ul[contains(@class, "jstree-children")]' +
                        '[' + createJSTreeXPathFromTree(node.children, { topLevel: false }) + ']'
                    );
                } else {
                    xPath = xPath.replace('${children}', '');
                }
            });

            return xPath;
        },

        /**
         * @method createToolbarItemXPath
         * @param {String} name of the item
         */
        createToolbarItemXPath: function createToolbarItemXPath(name) {
            return '//*[contains(@class, "cms-toolbar-item-navigation")]/li/a[./span[contains(text(), "' +
                name + '")]]';
        },

        /**
         * @function getPasteHelpersXPath
         * @public
         * @param {Object} opts
         * @param {Boolean} visible get visible or hidden helpers
         * @param {String|Number} [pageId] optional id of the page to filter helpers
         */
        getPasteHelpersXPath: function getPasteHelpersXPath(opts) {
            var xpath = '//a[contains(@class, "js-cms-tree-item-paste")]';
            if (opts && opts.visible) {
                xpath += '[not(contains(@class, "cms-pagetree-dropdown-item-disabled"))]';
            } else {
                xpath += '[contains(@class, "cms-pagetree-dropdown-item-disabled")]';
            }
            xpath += '[./span[contains(text(), "Paste")]]';
            if (opts && opts.pageId) {
                xpath += '[contains(@data-id, "' + opts.pageId + '")]';
            }
            return xpath;
        }
    };
};
