/* global document */
'use strict';

// #############################################################################
// Edit utils page content

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var casperjs = require('casper');
var cms = helpers(casperjs);

casper.test.setUp(function(done) {
    casper
        .start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        .then(
            cms.addPlugin({
                type: 'TextPlugin',
                content: {
                    id_body: 'Test text'
                }
            })
        )
        .then(
            cms.addPlugin({
                type: 'TextPlugin',
                content: {
                    id_body: 'Another Test text'
                }
            })
        )
        .run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.clearClipboard()).then(cms.removePage()).then(cms.logout()).run(done);
});

casper.test.begin('Edit utils page content', function(test) {
    var contentNumber;

    casper
        .start(globals.editUrl)
        // go to the Structure mode
        .then(cms.switchTo('structure'))
        // CHECK COPY UTIL
        // click settings for last content plugin
        .waitUntilVisible('.cms-structure', function() {
            // save initial number of content plugins
            contentNumber = this.evaluate(function() {
                return document.querySelectorAll('.cms-structure-content .cms-draggable').length;
            });
            // click settings for last content plugin
            this.click('.cms-structure .cms-draggable:last-child .cms-submenu-settings');
        })
        // select copy button from dropdown list
        .waitUntilVisible('.cms-structure .cms-draggable:last-child .cms-submenu-item a[data-rel="copy"]', function() {
            this.click('.cms-structure .cms-draggable:last-child .cms-submenu-item a[data-rel="copy"]');
        })
        .waitForResource(/copy-plugins/)
        // click on settings bar for current structure content block
        .then(function() {
            this.click('.cms-dragarea:first-child .cms-dragbar .cms-submenu-settings');
        })
        // choose paste option inside dropdown menu
        .waitUntilVisible('.cms-submenu-dropdown', function() {
            this.click('.cms-dragbar .cms-submenu-dropdown .cms-submenu-item a[data-rel="paste"]');
        })
        // check if number of content plugins has been increased (contentNumber variable)
        .then(function() {
            test.assertElementCount(
                '.cms-structure .cms-draggables .cms-draggable',
                contentNumber + 1,
                'Copy plugin successful'
            );
        })
        // wait till the paste actually succeeds
        .waitForResource(/move\-plugin/)
        .then(function() {
            this.reload();
        })
        .then(cms.switchTo('structure'))
        // check that number of content plugins have been indeed increased
        .waitForSelector('.cms-toolbar-expanded', function() {
            test.assertElementCount(
                '.cms-structure-content .cms-draggable',
                contentNumber + 1,
                'Copy plugin successful'
            );
        })
        .wait(1000)
        // CHECK DELETE UTIL
        // click settings for last content plugin
        .then(function() {
            // save initial number of content plugins
            contentNumber = this.evaluate(function() {
                return document.querySelectorAll('.cms-structure-content .cms-draggable').length;
            });
            // click settings for last content plugin
            this.click('.cms-structure .cms-draggable:last-child .cms-submenu-settings');
        })
        // select delete button from dropdown list
        .then(function() {
            this.click('.cms-structure .cms-draggable:last-child .cms-submenu-item a[data-rel="delete"]');
        })
        // wait for modal window appearance and submit plugin deletion
        .waitUntilVisible('.cms-modal-open', function() {
            test.assertVisible('.cms-modal-open');
            this.click('.cms-modal-buttons .deletelink');
        })
        // the modal is visible until page is reloaded
        .waitWhileVisible('.cms-modal-open', function() {
            test.assertElementCount(
                '.cms-structure .cms-draggables .cms-draggable',
                contentNumber - 1,
                'Delete plugin successful'
            );
        })
        .wait(1000)
        // CHECK CUT UTIL
        // click settings for last content plugin
        .then(function() {
            // save initial number of content plugins
            contentNumber = this.evaluate(function() {
                return document.querySelectorAll('.cms-structure .cms-draggable').length;
            });
            // click settings for last content plugin
            this.click('.cms-structure .cms-draggable:last-child .cms-submenu-settings');
        })
        // select cut button from dropdown list
        .waitUntilVisible('.cms-structure .cms-draggable:last-child .cms-submenu-item a[data-rel="cut"]', function() {
            this.click('.cms-structure .cms-draggable:last-child .cms-submenu-item a[data-rel="cut"]');
        })
        // check if number of content plugins has been decreased (because of cut)
        .then(cms.waitUntilContentIsRefreshed())
        .wait(1000)
        .then(function() {
            test.assertElementCount(
                '.cms-structure .cms-draggables .cms-draggable',
                contentNumber - 1,
                'Cut plugin successful'
            );
        })
        // click on settings bar for current structure content block
        .then(function() {
            this.click('.cms-dragarea:first-child .cms-dragbar .cms-submenu-settings');
        })
        // choose paste option inside dropdown menu
        .waitUntilVisible('.cms-submenu-dropdown', function() {
            this.click('.cms-dragbar .cms-submenu-dropdown .cms-submenu-item a[data-rel="paste"]');
        })
        // check if number of content plugins has been incereased (paste previously cutted value)
        .then(function() {
            test.assertElementCount(
                '.cms-structure .cms-draggables .cms-draggable',
                contentNumber,
                'Paste after cutting plugin successful'
            );
        })
        // wait till the paste actually succeeds
        .waitForResource(/move\-plugin/)
        .wait(1000)
        .reload()
        .then(cms.switchTo('structure'))
        // check that number of content plugins has been indeed increased
        .then(function() {
            test.assertElementCount(
                '.cms-structure .cms-draggables .cms-draggable',
                contentNumber,
                'Paste after cutting plugin successful'
            );
        })
        .run(function() {
            test.done();
        });
});
