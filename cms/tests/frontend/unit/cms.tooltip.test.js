/* globals $ */

'use strict';

describe('CMS.Messages', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a Tooltip class', function () {
        expect(CMS.Tooltip).toBeDefined();
    });

    it('has public API', function () {
        expect(CMS.Tooltip.prototype.displayToggle).toEqual(jasmine.any(Function));
        expect(CMS.Tooltip.prototype.show).toEqual(jasmine.any(Function));
        expect(CMS.Tooltip.prototype.position).toEqual(jasmine.any(Function));
        expect(CMS.Tooltip.prototype.hide).toEqual(jasmine.any(Function));
    });

    describe('instance', function () {
        var tooltip;
        beforeEach(function (done) {
            fixture.load('tooltip.html');
            $(function () {
                tooltip = new CMS.Tooltip();
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('does not have options', function () {
            expect(tooltip.options).not.toBeDefined();
        });

        it('has ui', function () {
            expect(tooltip.body).toBeDefined();
            expect(tooltip.domElem).toBeDefined();
        });

        it('picks correct dom node to show if touch enabled device', function () {
            expect(tooltip.domElem).toBeMatchedBy('.cms-tooltip');
            expect(tooltip.isTouch).toEqual(false);

            tooltip.body.trigger('touchstart');

            expect(tooltip.isTouch).toEqual(true);
            expect(tooltip.domElem).not.toBeMatchedBy('.cms-tooltip');
            expect(tooltip.domElem).toBeMatchedBy('.cms-tooltip-touch');
        });
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
