'use strict';

var CMS = require('../../../static/cms/js/modules/cms.base').default;
var Tooltip = require('../../../static/cms/js/modules/cms.tooltip').default;
var $ = require('jquery');

window.CMS = window.CMS || CMS;
CMS.Tooltip = Tooltip;


describe('CMS.Tooltip', function () {
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

        it('delegates to show()', function (done) {
            spyOn(tooltip, 'show').and.callFake(function (e, name, id) {
                expect(e).toEqual({ event: 'yes' });
                expect(name).toEqual('AwesomePlugin');
                expect(id).toEqual(1);
                done();
            });

            tooltip.displayToggle(true, { event: 'yes' }, 'AwesomePlugin', 1);
        });

        it('delegates to hide()', function (done) {
            spyOn(tooltip, 'hide').and.callFake(function () {
                expect(arguments.length).toEqual(0);
                done();
            });

            tooltip.displayToggle(false);
        });
    });

    describe('.show()', function () {
        var tooltip;

        beforeEach(function (done) {
            fixture.load('tooltip.html');
            $(function () {
                tooltip = new CMS.Tooltip();
                done();
            });
        });

        afterEach(function () {
            tooltip.body.off('mousemove.cms.tooltip');
            fixture.cleanup();
        });

        it('shows the tooltip', function () {
            spyOn(tooltip, 'position').and.callFake(function () {});
            tooltip.show({ originalEvent: 'Event' }, 'AwesomePlugin', 1);
            expect(tooltip.domElem).toHaveCss({ visibility: 'visible' });
            expect(tooltip.domElem).toBeVisible();
            expect(tooltip.domElem.data('plugin_id')).toEqual(1);
            expect(tooltip.domElem.find('span')).toHaveText('AwesomePlugin');
        });

        it('attaches event listener to move plugin after the cursor', function () {
            spyOn(tooltip, 'position').and.callFake(function () {});
            tooltip.show({ originalEvent: 'Event' }, 'AwesomePlugin', 1);
            expect(tooltip.body).toHandle('mousemove');
            expect(tooltip.position.calls.count()).toEqual(1);
            tooltip.body.trigger('mousemove');
            expect(tooltip.position.calls.count()).toEqual(2);
        });

        it('allows touching the tooltip to edit the plugin', function () {
            tooltip._forceTouch();
            spyOn(tooltip, 'position').and.callFake(function () {});
            tooltip.show({ originalEvent: 'Event' }, 'AwesomePlugin', 1);
            expect(tooltip.body).not.toHandle('mousemove');
            expect(tooltip.position.calls.count()).toEqual(1);
            expect(tooltip.domElem).toHandle('touchstart');
            var dblclick = spyOnEvent(document, 'dblclick.cms');

            tooltip.domElem.trigger('touchstart');
            expect(dblclick).toHaveBeenTriggered();
        });

        it('allows touching the tooltip to edit the "generic"', function () {
            tooltip._forceTouch();
            spyOn(tooltip, 'position').and.callFake(function () {});
            tooltip.show({ originalEvent: 'Event' }, 'AwesomeGeneric', 33);
            expect(tooltip.body).not.toHandle('mousemove');
            expect(tooltip.position.calls.count()).toEqual(1);
            expect(tooltip.domElem).toHandle('touchstart');
            var dblclick = spyOnEvent('.cms-plugin-cms-page-changelist-33', 'dblclick.cms');

            tooltip.domElem.trigger('touchstart');
            expect(dblclick).toHaveBeenTriggered();
        });
    });

    describe('.position()', function () {
        var tooltip;

        beforeEach(function (done) {
            fixture.load('tooltip.html');
            $(function () {
                tooltip = new CMS.Tooltip();
                done();
            });
        });

        afterEach(function () {
            tooltip.body.off('mousemove.cms.tooltip');
            fixture.cleanup();
        });

        it('positions the tooltip correctly based on mouse position', function () {
            tooltip.show({
                originalEvent: {
                    pageX: 20,
                    pageY: 20
                }
            }, 'AwesomePlugin', 1);

            var parentOffset = tooltip.domElem.offsetParent().offset();

            expect(tooltip.domElem).toBeVisible();
            expect(tooltip.domElem).toHaveCss({
                left: (-parentOffset.left + 20 + 20) + 'px',
                top: (-parentOffset.top + 20 - 12) + 'px'
            });
        });

        it('position the tooltip correctly based on mouse position', function () {
            var boundary = $(window).width();
            var offset = 20;

            tooltip.show({
                originalEvent: {
                    pageX: 0,
                    pageY: 0
                }
            }, 'AwesomePlugin', 1);

            var parentOffset = tooltip.domElem.offsetParent().offset();
            var tooltipWidth = tooltip.domElem.outerWidth(true);

            // left side
            var xFromLeft = [10, 20, boundary - offset - tooltipWidth - 1];

            xFromLeft.forEach(function (x) {
                tooltip.position({
                    pageX: x,
                    pageY: 20
                }, tooltip.domElem);

                expect(tooltip.domElem).toHaveCss({
                    left: (-parentOffset.left + offset + x) + 'px',
                    top: (-parentOffset.top + 20 - 12) + 'px'
                });
            });

            // right side
            var xFromRight = [10, 20, tooltipWidth, tooltipWidth + offset - 1, tooltipWidth + offset];

            xFromRight.forEach(function (x) {
                tooltip.position({
                    pageX: boundary - x,
                    pageY: 20
                }, tooltip.domElem);

                expect(tooltip.domElem).toHaveCss({
                    left: (-parentOffset.left + (boundary - x) - tooltipWidth - offset) + 'px',
                    top: (-parentOffset.top + 20 - 12) + 'px'
                });
            });
        });
    });

    describe('.hide()', function () {
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

        it('hides the tooltip', function () {
            spyOn(tooltip, 'position').and.callFake(function () {});
            tooltip.show({ originalEvent: 'Event' }, 'AwesomePlugin', 1);
            expect(tooltip.domElem).toBeVisible();
            tooltip.hide();
            expect(tooltip.domElem).toHaveCss({ visibility: 'hidden' });
            expect(tooltip.domElem).not.toBeVisible();
        });

        it('unbinds the mousemove events', function () {
            spyOn(tooltip, 'position').and.callFake(function () {});
            tooltip.show({ originalEvent: 'Event' }, 'AwesomePlugin', 1);
            expect(tooltip.body).toHandle('mousemove');
            tooltip.hide();
            expect(tooltip.body).not.toHandle('mousemove');
        });
    });

});
