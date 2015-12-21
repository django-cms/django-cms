'use strict';

// #############################################################################
// Edit utils page content

var globals = require('./settings/globals');
var messages = require('./settings/messages').page.editUtils;


casper.test.begin('Edit utils page content', function (test) {
    var contentNumber;

    casper
        .start(globals.editUrl)

        // go to the Structure mode
        .then(function () {
            this.click('.cms-toolbar-item-cms-mode-switcher .cms-btn[href="?build"]');
        })

        // CHECK COPY UTIL
        // click settings for last content plugin
        .waitUntilVisible('.cms-structure', function () {
            // save initial number of content plugins
            contentNumber = this.evaluate(function () {
                return document.querySelectorAll('.cms-structure-content .cms-draggable').length;
            });
            // click settings for last content plugin
            this.click('.cms-draggable:last-child .cms-submenu-settings');
        })
        // select copy button from dropdown list
        .waitUntilVisible(
            '.cms-structure .cms-draggable:last-child .cms-submenu-item a[data-rel="copy"]',
            function () {
                this.click('.cms-structure .cms-draggable:last-child .cms-submenu-item a[data-rel="copy"]');
            }
        )
        // click on settings bar for current structure content block
        .waitWhileVisible('.cms-structure', function () {
            this.click('.cms-dragarea:first-child .cms-dragbar .cms-submenu-settings');
        })
        // choose paste option inside dropdown menu
        .waitUntilVisible('.cms-submenu-dropdown', function () {
            this.click('.cms-dragbar .cms-submenu-dropdown .cms-submenu-item a[data-rel="paste"]');
        })
        // check if number of content plugins has been incereased (contentNumber variable)
        .then(function () {
            test.assertElementCount('.cms-draggables .cms-draggable', contentNumber + 1, messages.copySuccessful);
        })

        // CHECK DELETE UTIL
        // click settings for last content plugin
        .then(function () {
            // save initial number of content plugins
            contentNumber = this.evaluate(function () {
                return document.querySelectorAll('.cms-structure-content .cms-draggable').length;
            });
            // click settings for last content plugin
            this.click('.cms-structure .cms-draggable:last-child .cms-submenu-settings');
        })
        // select copy button from dropdown list
        .waitUntilVisible(
            '.cms-structure .cms-draggable:last-child .cms-submenu-item a[data-rel="delete"]',
            function () {
                this.click('.cms-structure .cms-draggable:last-child .cms-submenu-item a[data-rel="delete"]');
            }
        )
        // wait for modal window appearance and submit plugin deletion
        .waitUntilVisible('.cms-modal-open', function () {
            this.click('.cms-modal-buttons .deletelink');
        })
        // check if number of content plugins decreased
        .waitWhileVisible('.cms-modal-open', function () {
            test.assertElementCount('.cms-draggables .cms-draggable', contentNumber, messages.deleteSuccessful);
        })

        // CHECK CUT UTIL
        // click settings for last content plugin
        .then(function () {
            // save initial number of content plugins
            contentNumber = this.evaluate(function () {
                return document.querySelectorAll('.cms-structure-content .cms-draggable').length;
            });
            // click settings for last content plugin
            this.click('.cms-structure .cms-draggable:last-child .cms-submenu-settings');
        })
        // select cut button from dropdown list
        .waitUntilVisible(
            '.cms-structure .cms-draggable:last-child .cms-submenu-item a[data-rel="cut"]',
            function () {
                this.click('.cms-structure .cms-draggable:last-child .cms-submenu-item a[data-rel="cut"]');
            }
        )
        // check if number of content plugins has been decreased (because of cut)
        .waitWhileVisible('.cms-structure', function () {
            test.assertElementCount(
                '.cms-structure .cms-draggables .cms-draggable',
                contentNumber - 1,
                messages.cutSuccessful
            );
        })
        // click on settings bar for current structure content block
        .then(function () {
            this.click('.cms-dragarea:first-child .cms-dragbar .cms-submenu-settings');
        })
        // choose paste option inside dropdown menu
        .waitUntilVisible('.cms-submenu-dropdown', function () {
            this.click('.cms-dragbar .cms-submenu-dropdown .cms-submenu-item a[data-rel="paste"]');
        })
        // check if number of content plugins has been incereased (paste previously cutted value)
        .then(function () {
            test.assertElementCount('.cms-draggables .cms-draggable', contentNumber, messages.pasteAfterCutSuccessful);
        })
        .run(function () {
            test.done();
        });
});
