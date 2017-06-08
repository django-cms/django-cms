'use strict';
var CMS = require('../../../static/cms/js/modules/cms.base').default;
var Navigation = require('../../../static/cms/js/modules/cms.navigation').default;
var $ = require('jquery');

window.CMS = window.CMS || CMS;
CMS.Navigation = Navigation;

describe('CMS.Navigation', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a Navigation class', function () {
        expect(CMS.Navigation).toBeDefined();
    });

    it('has no public API', function () {
        // eslint-disable-next-line
        for (var key in CMS.Navigation.prototype) {
            expect(key[0]).not.toEqual('_');
        }
    });

    describe('instance', function () {
        var nav;

        beforeEach(function (done) {
            fixture.load('toolbar.html');
            $(function () {
                nav = new CMS.Navigation();
                // fake the resize until we have complete fixture in place
                spyOn(CMS.Navigation.prototype, '_handleResize');
                done();
            });
        });

        afterEach(function () {
            nav.ui.window.off('.cms.navigation');
            fixture.cleanup();
        });

        it('has ui', function () {
            expect(nav.ui).toEqual(jasmine.any(Object));
            expect(Object.keys(nav.ui)).toContain('window');
            expect(Object.keys(nav.ui)).toContain('toolbarLeftPart');
            expect(Object.keys(nav.ui)).toContain('toolbarRightPart');
            expect(Object.keys(nav.ui)).toContain('trigger');
            expect(Object.keys(nav.ui)).toContain('dropdown');
            expect(Object.keys(nav.ui)).toContain('toolbarTrigger');
            expect(Object.keys(nav.ui)).toContain('logo');
            expect(Object.keys(nav.ui).length).toEqual(7);
        });

        it('has no options', function () {
            expect(nav.options).toEqual(undefined);
        });

        it('sets up events to handle window resizing', function () {
            expect(nav.ui.window).toHandle('resize.cms.navigation');
        });

        it('sets up events to handle initial load', function () {
            expect(nav.ui.window).toHandle('load.cms.navigation');
        });

        it('sets up events to handle oriantation change', function () {
            expect(nav.ui.window).toHandle('orientationchange.cms.navigation');
        });

        it('has initial state', function () {
            expect(nav.leftMostItemIndex).toEqual(0);
            expect(nav.rightMostItemIndex).toEqual(2);
            expect(nav.items).toEqual({
                left: [
                    { element: jasmine.any(Object), width: jasmine.any(Number) },
                    { element: jasmine.any(Object), width: jasmine.any(Number) },
                    { element: jasmine.any(Object), width: jasmine.any(Number) }
                ],
                leftTotalWidth: jasmine.any(Number),
                right: [
                    // cannot check for actual widths since they vary browser to browser
                    { element: jasmine.any(Object), width: jasmine.any(Number) },
                    { element: jasmine.any(Object), width: jasmine.any(Number) },
                    { element: jasmine.any(Object), width: jasmine.any(Number) }
                ],
                rightTotalWidth: jasmine.any(Number),
                moreButtonWidth: jasmine.any(Number)
            });
        });
    });

    describe('._calculateAvailableWidth()', function () {
        var nav;
        var fakeWindow;

        beforeEach(function (done) {
            fixture.load('toolbar.html');
            $(function () {
                nav = new CMS.Navigation();
                fakeWindow = $('<div></div>');
                nav.ui.window = fakeWindow;
                done();
            });
        });

        afterEach(function () {
            nav.ui.window.off('.cms.navigation');
            fixture.cleanup();
        });

        it('calculates available width for the menu to fit in', function () {
            expect(nav._calculateAvailableWidth()).toEqual(jasmine.any(Number));
            // make the logo and toolbar right padding equal across browsers
            nav.ui.toolbarRightPart.css('padding-right', 10);
            nav.ui.logo.css('width', 100);

            [300, 500, 678].forEach(function (width) {
                fakeWindow.css('width', width);
                expect(nav._calculateAvailableWidth()).toEqual(width - 100 - 10);
            });
        });
    });

    describe('._showDropdown() / ._hideDropdown()', function () {
        var nav;

        beforeEach(function (done) {
            fixture.load('toolbar.html');
            $(function () {
                nav = new CMS.Navigation();
                done();
            });
        });

        afterEach(function () {
            nav.ui.window.off('.cms.navigation');
            fixture.cleanup();
        });

        it('one shows the trigger', function () {
            expect(nav.ui.trigger.css('display')).toEqual('none');
            nav._showDropdown();
            expect(nav.ui.trigger.css('display')).toEqual('list-item');
            nav._hideDropdown();
            expect(nav.ui.trigger.css('display')).toEqual('none');
        });
    });

    describe('._handleResize()', function () {
        var nav;

        beforeEach(function (done) {
            fixture.load('toolbar.html');
            $(function () {
                nav = new CMS.Navigation();
                spyOn(nav, '_calculateAvailableWidth');
                spyOn(nav, '_moveOutOfDropdown').and.callThrough();
                spyOn(nav, '_moveToDropdown').and.callThrough();
                spyOn(nav, '_showAll').and.callThrough();
                spyOn(nav, '_showAllRight').and.callThrough();
                spyOn(nav, '_showDropdown').and.callThrough();
                spyOn(nav, '_hideDropdown').and.callThrough();
                nav.items = $.extend(true, {}, {
                    left: [
                        { element: nav.items.left[0].element, width: 100 },
                        { element: nav.items.left[1].element, width: 100 },
                        { element: nav.items.left[2].element, width: 100 }
                    ],
                    leftTotalWidth: 300,
                    right: [
                        { element: nav.items.right[0].element, width: 100 },
                        { element: nav.items.right[1].element, width: 100 },
                        { element: nav.items.right[2].element, width: 100 }
                    ],
                    rightTotalWidth: 400,
                    moreButtonWidth: 50
                });
                done();
            });
        });

        afterEach(function () {
            nav.ui.window.off('.cms.navigation');
            fixture.cleanup();
        });

        it('shows every menu item in the toolbar if there is enough space', function () {
            nav._calculateAvailableWidth.and.returnValues(10000, 500, 201);
            nav.items.leftTotalWidth = 100;
            nav.items.rightTotalWidth = 100;

            nav._handleResize();
            nav._handleResize();
            nav._handleResize();

            expect(nav._showAll).toHaveBeenCalledTimes(3);
        });

        it('shows "more" dropdown if there is not enough space in the toolbar', function () {
            nav._calculateAvailableWidth.and.returnValues(300, 100);

            nav._handleResize();

            expect(nav._showAll).not.toHaveBeenCalled();
            expect(nav._showDropdown).toHaveBeenCalled();
            expect(nav._showAllRight).not.toHaveBeenCalled();
            expect(nav.rightMostItemIndex).toEqual(-1);
            expect(nav.leftMostItemIndex).toEqual(3);

            nav._handleResize();

            expect(nav._showAll).not.toHaveBeenCalledTimes(2);
            expect(nav._showDropdown).toHaveBeenCalledTimes(2);
            expect(nav._showAllRight).not.toHaveBeenCalled();
            expect(nav.rightMostItemIndex).toEqual(-1);
            expect(nav.leftMostItemIndex).toEqual(3);
        });

        it('shows "more" dropdown if there is not enough space in the toolbar', function () {
            nav._calculateAvailableWidth.and.returnValues(550, 700);

            nav._handleResize();

            expect(nav._showAll).not.toHaveBeenCalled();
            expect(nav._showDropdown).toHaveBeenCalledTimes(1);
            expect(nav._showAllRight).toHaveBeenCalledTimes(1);
            expect(nav._moveToDropdown).toHaveBeenCalledWith(2);
            expect(nav.rightMostItemIndex).toEqual(0);
            expect(nav.leftMostItemIndex).toEqual(0);

            nav._handleResize();

            expect(nav._showAll).not.toHaveBeenCalled();
            expect(nav._showDropdown).toHaveBeenCalledTimes(2);
            expect(nav._showAllRight).toHaveBeenCalledTimes(2);
            expect(nav._moveToDropdown).toHaveBeenCalledWith(2);
            expect(nav.rightMostItemIndex).toEqual(1);
            expect(nav.leftMostItemIndex).toEqual(0);
        });

        it('toggles cms-more-dropdown-full class if every toolbar item is collapsed', function () {
            nav._calculateAvailableWidth.and.returnValues(200, 500);
            expect(nav.ui.dropdown).not.toHaveClass('cms-more-dropdown-full');
            nav._handleResize();
            expect(nav.ui.dropdown).toHaveClass('cms-more-dropdown-full');
            nav._handleResize();
            expect(nav.ui.dropdown).not.toHaveClass('cms-more-dropdown-full');
        });

        it('wraps right part items into .cms-more-buttons', function () {
            nav._calculateAvailableWidth.and.returnValues(500, 300);
            nav._handleResize();
            expect(nav.ui.dropdown.find('.cms-more-buttons').length).toEqual(0);
            nav._handleResize();
            expect(nav.ui.dropdown.find('.cms-more-buttons').length).toEqual(3);
        });

        it('adds cms-toolbar-item-navigation-children class if moved item has menu', function () {
            spyOn($.fn, 'addClass');

            nav._calculateAvailableWidth.and.returnValues(500);
            nav._handleResize();

            expect($.fn.addClass).toHaveBeenCalledTimes(2);
            expect($.fn.addClass.calls.argsFor(0)).toEqual(['cms-toolbar-item-navigation-children']);
            expect($.fn.addClass.calls.argsFor(1)).toEqual(['cms-toolbar-item-navigation-children']);
        });
    });

});
