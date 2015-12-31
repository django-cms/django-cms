'use strict';

describe('CMS.Sideframe', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a Sideframe class', function () {
        expect(CMS.Sideframe).toBeDefined();
    });

    it('has public API');

    describe('instance', function () {
        it('has ui');
        it('has options');
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
