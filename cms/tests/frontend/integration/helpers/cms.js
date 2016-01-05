'use strict';
var globals = require('../settings/globals');

module.exports = {
    login: function () {
        return this.thenOpen(globals.adminUrl).then(function () {
            this.fill('#login-form', globals.credentials, true);
        });
    },

    logout: function () {
        return this.thenOpen(globals.adminLogoutUrl);
    },

    removeFirstPage: function () {
        return this.thenOpen(globals.adminPagesUrl)
            .waitUntilVisible('.tree .deletelink')
            .then(function () {
                this.click('.tree .deletelink');
            })
            .waitUntilVisible('input[type=submit]')
            .then(function () {
                this.click('input[type=submit]');
            });
    },

    /**
     * Adds the page
     *
     * @public
     * @param {Object} opts
     * @param {String} opts.name name of the page
     */
    addPage: function (opts) {
        return function () {
            return this.thenOpen(globals.adminPagesUrl + 'add/')
                .waitUntilVisible('#id_title')
                .then(function () {
                    this.sendKeys('#id_title', opts.name);
                    this.captureSelector('test.png', 'html');
                    this.click('input[name="_save"]');
                });
        };
    }
};
