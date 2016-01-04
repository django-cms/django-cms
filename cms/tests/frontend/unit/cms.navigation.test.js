'use strict';

describe('CMS.Navigation', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a Navigation class', function () {
        expect(CMS.Navigation).toBeDefined();
    });

    it('has no public API', function () {
        var allowedKeys = Object.keys(CMS.API.Helpers).concat(['initialize']);

        for (var key in CMS.Navigation.prototype) {
            if (allowedKeys.indexOf(key) === '-1') {
                expect(key[0]).not.toEqual('_');
            }
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
            expect(nav.rightMostItemIndex).toEqual(-1);
            expect(nav.items).toEqual({
                left: [],
                leftTotalWidth: 0,
                right: [
                    // cannot check for actual widths since they vary browser to browser
                    { element: jasmine.any(Object), width: jasmine.any(Number) },
                    { element: jasmine.any(Object), width: jasmine.any(Number) },
                    { element: jasmine.any(Object), width: jasmine.any(Number) },
                    { element: jasmine.any(Object), width: jasmine.any(Number) }
                ],
                rightTotalWidth: jasmine.any(Number),
                moreButtonWidth: jasmine.any(Number)
            });
        });
    });
});
