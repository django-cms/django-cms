'use strict';

describe('CMS.Sideframe', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a Sideframe class', function () {
        expect(CMS.Sideframe).toBeDefined();
    });

    it('has public API', function () {
        expect(CMS.Sideframe.prototype.open).toEqual(jasmine.any(Function));
        expect(CMS.Sideframe.prototype.close).toEqual(jasmine.any(Function));
    });

    describe('instance', function () {
        var sideframe;
        beforeEach(function (done) {
            $(function () {
                sideframe = new CMS.Sideframe();
                done();
            });
        });

        it('has ui', function () {
            expect(sideframe.ui).toEqual(jasmine.any(Object));
            expect(Object.keys(sideframe.ui)).toContain('sideframe');
            expect(Object.keys(sideframe.ui)).toContain('body');
            expect(Object.keys(sideframe.ui)).toContain('window');
            expect(Object.keys(sideframe.ui)).toContain('dimmer');
            expect(Object.keys(sideframe.ui)).toContain('close');
            expect(Object.keys(sideframe.ui)).toContain('resize');
            expect(Object.keys(sideframe.ui)).toContain('frame');
            expect(Object.keys(sideframe.ui)).toContain('shim');
            expect(Object.keys(sideframe.ui)).toContain('historyBack');
            expect(Object.keys(sideframe.ui)).toContain('historyForward');
            expect(Object.keys(sideframe.ui).length).toEqual(10);
        });

        it('has options', function () {
            expect(sideframe.options).toEqual({
                onClose: false,
                sideframeDuration: 300,
                sideframeWidth: 0.8
            });

            sideframe = new CMS.Sideframe({
                onClose: 'something',
                sideframeDuration: 310,
                sideframeWidth: 0.9,
                something: 'else'
            });

            expect(sideframe.options).toEqual({
                onClose: 'something',
                sideframeDuration: 310,
                sideframeWidth: 0.9,
                something: 'else'
            });
        });
    });

    describe('.open()', function () {
        it('throws an error if no url was passed');
        it('shows the dimmer');
        it('shows the toolbar loader');
        it('shows the loader on the sideframe');
        it('correctly modifies the url');
        it('animates the sideframe to correct width');
        it('does not animate sideframe if sideframe was already open');
        it('opens the toolbar');
        it('locks the toolbar');
        it('hides the toolbar loader');
        it('prevents scrolling of the outer body for mobile devices');
        it('is chainable');
    });

    describe('.close()', function () {
        it('hides the dimmer');
        it('sets correct state');
        it('checks if page requires reloading');
        it('unlocks the toolbar');
        it('removes the loader from sideframe');
        it('restores scrolling of the outer body for mobile devices');
    });
});
