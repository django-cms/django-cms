/* globals $ */

'use strict';

describe('CMS.Messages', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a Tooltip class', function () {
        expect(CMS.Tooltip).toBeDefined();
    });

    it('has public API');

    describe('instance', function () {
        it('does not have options');
        it('has ui');
        it('picks correct dom node to show if touch enabled device');
    });

    describe('.displayToggle()', function () {
        it('delegates to show()');
        it('delegates to hide()');
    });

    describe('.show()', function () {
        it('shows the tooltip');
        it('attaches event listener to move plugin after the cursor');
        it('allows touching the tooltip to edit the plugin');
    });

    describe('.position()', function () {
        it('positions the tooltip correctly based on mouse position');
    });

    describe('.hide()', function () {
        it('hides the tooltip');
        it('unbinds the mousemove events');
    });

});
