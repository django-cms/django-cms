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
                }).waitForSelector('#content');
            };
        },

        logout: function () {
            return function () {
                return this.thenEvaluate(function () {
                    localStorage.clear();
                }).thenOpen(globals.adminLogoutUrl);
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
                    });
            };
        },

        /**
         * Adds the plugin (currently to the first placeholder)
         *
         * @param {Object} opts
         * @param {String} opts.type type of the plugin to add
         * @param {Object} opts.content object containing fields and values
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
                    .waitUntilVisible('.cms-structure', function () {
                        this.click('.cms-structure .cms-submenu-add [data-tooltip="Add plugin"]');
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
                    });
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
        }
    };
};
