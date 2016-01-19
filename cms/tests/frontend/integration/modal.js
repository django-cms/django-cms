'use strict';

// #############################################################################
// Create the first page

var globals = require('./settings/globals');
var content = require('./settings/globals').content.page;
var cms = require('./helpers/cms')();
var moveMouse;

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        .run(done);
});

casper.test.tearDown(function (done) {
    casper.start()
        .then(cms.logout())
        .run(done);
});

casper.test.begin('Manipulate Modal', function (test) {
    casper
        .start(globals.editUrl)
        .waitUntilVisible('.cms-modal-open', function () {
            test.assertExist('.cms-modal-open', 'Modal is open');
            this.click('.cms-icon-window');
        })
        .then(function () {
            // Page size is 1280x1024
            test.assertEvalEquals(function () {
            return $('.cms-modal-maximized').width();
            }, 1280, 'Modal maximized');
        })
        // clicks on the window icon
        .then(function () {
           this.click('.cms-icon-window');
        })
        // clicks on the minimize window icon
        .then(function () {
           this.click('.cms-icon-minus');
        })
        // checks width of the minimized windows
        .then(function () {
            // Page size is 1280x1024
            test.assertEvalEquals(function () {
            return $('.cms-modal-open').width();
            }, 396, 'Window is minimized');
        })
        // epands the window by clicking on the icon
        .then(function () {
           this.click('.cms-icon-minus');
        })
        // checks the default width of the windo
        .then(function () {
            // Page size is 1280x1024
            test.assertEvalEquals(function () {
            return $('.cms-modal-open').height();
            }, 724, 'Modal opens with default width');
        })
        // Function expands
        .then(function () {
            moveMouse = this.getElementBounds('.cms-modal-resize');
             // Chose random numbe to expand the modal down
            var expandModal = 30;
            var standardModal = 724;
            this.mouse.down('.cms-modal-resize');
            this.mouse.move(moveMouse.left + moveMouse.width, moveMouse.top + (moveMouse.height / 2) + expandModal / 2);
            this.mouse.up(moveMouse.left + moveMouse.width, moveMouse.top + (moveMouse.height / 2) + expandModal / 2);
            test.assertEvalEquals(function () {
                return $('.cms-modal-open').height();
            }, standardModal + expandModal, 'Modal resized bigger');
            // Reverses the height to standard height of the modal
            this.mouse.down('.cms-modal-resize');
            this.mouse.move(moveMouse.left + moveMouse.width, moveMouse.top + (moveMouse.height / 2) - expandModal / 2);
            this.mouse.up(moveMouse.left + moveMouse.width, moveMouse.top + (moveMouse.height / 2) - expandModal / 2);
            test.assertEvalEquals(function () {
                return $('.cms-modal-open').height();
            }, standardModal - expandModal, 'Modal resized to standard again');
        })
        // function moves chosen element to the left
        .then(function () {
            this.click('.cms-modal-head');
            moveMouse = this.getElementBounds('.cms-modal-head'); // moveMouse.left = 138px
            this.mouse.down('.cms-modal-head');
            // Chose random numbe to move the modal to the left
            var movingLeft = 50;
            this.mouse.move(moveMouse.left + moveMouse.width/ 2 - movingLeft, moveMouse.top + moveMouse.height / 2);
            this.mouse.up(moveMouse.left + moveMouse.width/ 2 - movingLeft, moveMouse.top + moveMouse.height / 2);
            moveMouse = this.getElementBounds('.cms-modal');
            // checks if the modal moved 50px to the left from 138px
            test.assertEquals(moveMouse.left, 138 - movingLeft, 'Modal moved');
        })
        // function checks min height of modal
        .then(function () {
            moveMouse = this.getElementBounds('.cms-modal-resize');
             // Min height is 400px. 724px - 500px < 400
            var resizeUp = 500;
            var standardModal = 724;
            this.mouse.down('.cms-modal-resize');
            this.mouse.move(moveMouse.left + moveMouse.width, moveMouse.top + (moveMouse.height / 2) - resizeUp / 2);
            this.mouse.up(moveMouse.left + moveMouse.width, moveMouse.top + (moveMouse.height / 2) - resizeUp / 2);
            // takes the current modal height
            var height = this.evaluate(function () {
                return $('.cms-modal-open').height();
            })
            // checks if the current modal height didn't turn below 400
            test.assert(height !== standardModal - resizeUp, 'Modal reached min size' );
        })
        .run(function () {
            test.done();
        });
});
