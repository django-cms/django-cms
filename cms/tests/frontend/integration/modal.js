'use strict';

// #############################################################################
// Create the first page

var casperjs = require('casper');
var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers(casperjs);
var xPath = casperjs.selectXPath;
var resizeButton;

casper.test.setUp(function(done) {
    casper.start().then(cms.login()).run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.logout()).run(done);
});

casper.test.begin('Manipulate Modal', function(test) {
    var expandModal = 30;
    var standardModal = 724;

    casper
        .start(globals.editUrl)
        .waitUntilVisible('.cms-modal-open', function() {
            test.assertExist('.cms-modal-open', 'Modal is open');
            this.click('.cms-modal-maximize');
        })
        .then(function() {
            // Page size is 1280x1024
            test.assertEvalEquals(
                function() {
                    return CMS.$('.cms-modal-open').width();
                },
                1280,
                'Modal maximized to current width'
            );
            // Page size is 1280x1024
            test.assertEvalEquals(
                function() {
                    return CMS.$('.cms-modal-open').height();
                },
                1024,
                'Modal maximized to current height'
            );
        })
        // clicks on the maximize button
        .then(function() {
            test.assertExists('.cms-icon-window', 'maximize icon exists');
            this.click('.cms-modal-maximize');
        })
        // clicks on the minimize button icon
        .then(function() {
            test.assertExists('.cms-icon-minus', 'minimize icon exists');
            this.click('.cms-modal-minimize');
        })
        // checks width of the minimized windows
        .then(function() {
            // Page size is 1280x1024
            test.assertEval(function() {
                return CMS.$('.cms-modal-open').width() < 430;
            }, 'Window is minimized to current width');

            test.assertEvalEquals(
                function() {
                    return CMS.$('.cms-modal-open').height();
                },
                46,
                'Window is minimized to current height'
            );
        })
        // expands the modal by clicking on the icon
        .then(function() {
            this.click('.cms-modal-minimize');
        })
        // checks the default height of the window
        .then(function() {
            // Page size is 1280x1024
            test.assertEvalEquals(
                function() {
                    return CMS.$('.cms-modal-open').height();
                },
                724,
                'Modal opens with default height'
            );
            test.assertEvalEquals(
                function() {
                    return CMS.$('.cms-modal-open').width();
                },
                980,
                'Modal opens with default width'
            );
        })
        // Function expands
        .then(function() {
            resizeButton = this.getElementBounds('.cms-modal-resize');
            // Chose number to expand the modal with the given pixel down

            this.mouse.down('.cms-modal-resize');
            this.mouse.move(
                resizeButton.left + resizeButton.width / 2,
                resizeButton.top + resizeButton.height / 2 + expandModal / 2
            );
            this.mouse.up(
                resizeButton.left + resizeButton.width / 2,
                resizeButton.top + resizeButton.height / 2 + expandModal / 2
            );

            test.assertEvalEquals(
                function() {
                    return CMS.$('.cms-modal-open').height();
                },
                standardModal + expandModal,
                'Modal resized bigger'
            );
        })
        .then(function() {
            resizeButton = this.getElementBounds('.cms-modal-resize');
            // Reverses the height to standard height of the modal
            this.mouse.down('.cms-modal-resize');
            this.mouse.move(
                resizeButton.left + resizeButton.width / 2,
                resizeButton.top + resizeButton.height / 2 - expandModal / 2
            );
            this.mouse.up(
                resizeButton.left + resizeButton.width / 2,
                resizeButton.top + resizeButton.height / 2 - expandModal / 2
            );
            test.assertEvalEquals(
                function() {
                    return CMS.$('.cms-modal-open').height();
                },
                standardModal,
                'Modal resized to standard again'
            );
        })
        // function moves chosen element to the left
        .then(function() {
            this.click('.cms-modal-head');
            resizeButton = this.getElementBounds('.cms-modal-head');
            this.mouse.down('.cms-modal-head');
            // Choose random number to move the modal to the left
            var movingLeft = 50;
            var distanceLeft = resizeButton.left;

            this.mouse.move(
                resizeButton.left + resizeButton.width / 2 - movingLeft,
                resizeButton.top + resizeButton.height / 2
            );
            this.mouse.up(
                resizeButton.left + resizeButton.width / 2 - movingLeft,
                resizeButton.top + resizeButton.height / 2
            );
            resizeButton = this.getElementBounds('.cms-modal');
            // checks if the modal moved 50px
            test.assertEquals(resizeButton.left, distanceLeft - movingLeft, 'Modal moved');
            this.mouse.down('.cms-modal-head');
            this.mouse.move(
                resizeButton.left + resizeButton.width / 2 + movingLeft,
                resizeButton.top + resizeButton.height * 0
            );
            this.mouse.up(
                resizeButton.left + resizeButton.width / 2 + movingLeft,
                resizeButton.top + resizeButton.height * 0
            );
            resizeButton = this.getElementBounds('.cms-modal-head');
            test.assertEquals(resizeButton.left, distanceLeft, 'Modal back');
        })
        // moves the modal diagonal
        .then(function() {
            this.click('.cms-modal-head');
            resizeButton = this.getElementBounds('.cms-modal-head'); //
            this.mouse.down('.cms-modal-head');
            // Chose random numbe to move the modal to the left
            var distanceTop = resizeButton.top;
            var distanceLeft = resizeButton.left;
            var movingUp = 50;
            var movingLeft = 20;

            this.mouse.move(
                resizeButton.left + resizeButton.width / 2 - movingLeft,
                resizeButton.top - movingUp + resizeButton.height / 2
            );
            this.mouse.up(
                resizeButton.left + resizeButton.width / 2 - movingLeft,
                resizeButton.top - movingUp + resizeButton.height / 2
            );
            resizeButton = this.getElementBounds('.cms-modal-head');
            test.assertEquals(resizeButton.left, distanceLeft - movingLeft, 'Modal moved vertical');
            test.assertEquals(resizeButton.top, distanceTop - movingUp, 'Modal moved vertical');
        })
        // check that modal cannot be resized to be smaller than default minimum dimensions
        .then(function() {
            resizeButton = this.getElementBounds('.cms-modal-resize');
            // Min height is 400px. 724px - 500px < 400
            var resizeUp = 500;

            this.mouse.down('.cms-modal-resize');
            this.mouse.move(
                resizeButton.left + resizeButton.width,
                resizeButton.top + resizeButton.height / 2 - resizeUp / 2
            );
            this.mouse.up(
                resizeButton.left + resizeButton.width,
                resizeButton.top + resizeButton.height / 2 - resizeUp / 2
            );
            // takes the current modal height
            var height = this.evaluate(function() {
                return CMS.$('.cms-modal-open').height();
            });

            // checks if the current modal height didn't turn below 400
            test.assert(height !== standardModal - resizeUp, 'Modal reached min size');
            test.assert(height === 400, 'Modal reached 400px');
        })
        .run(function() {
            test.done();
        });
});

casper.test.begin('Shortcuts modal', function(test) {
    casper
        .start()
        .then(cms.addPage({ title: 'Home' }))
        .thenOpen(globals.editUrl)
        .waitForSelector('.cms-toolbar-expanded')
        .then(function() {
            // click on "Example.com" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(1) > a');
        })
        // opening "Clipboard" menu item
        .wait(10, function() {
            this.click(xPath('//a[.//span[text()[contains(.,"Shortcuts")]]]'));
        })
        .waitUntilVisible('.cms-modal-open')
        .then(function() {
            test.assertSelectorHasText('.cms-modal-title-prefix', 'Shortcuts', 'Shortcuts window was opened');
        })
        .then(function() {
            this.click('.cms-modal-close');
        })
        .waitWhileVisible('.cms-modal-open')
        .then(cms.switchTo('structure'))
        .then(function() {
            // click on "Example.com" menu item
            this.click('.cms-toolbar-item-navigation > li:nth-child(1) > a');
        })
        // opening "Clipboard" menu item
        .wait(10, function() {
            this.click(xPath('//a[.//span[text()[contains(.,"Shortcuts")]]]'));
        })
        .waitUntilVisible('.cms-modal-open')
        .then(function() {
            test.assertSelectorHasText('.cms-modal-title-prefix', 'Shortcuts', 'Shortcuts window was opened');
        })
        .then(cms.removePage())
        .run(function() {
            test.done();
        });
});
