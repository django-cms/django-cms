'use strict';

describe('CMS.StructureBoard', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a StructureBoard class', function () {
        expect(CMS.StructureBoard).toBeDefined();
    });

    it('has public API');

    describe('instance', function () {
        it('has ui');
        it('has options');
    });

    describe('.show()', function () {
        it('shows the board');
        it('does not show the board if we are viewing published page');
        it('resizes toolbar correctly based on scrollbar width');
        it('highlights correct trigger');
        it('remembers state');
        it('shows all placeholders');
        it('applies correct classes based on type of structureboard');
        it('reorders static placeholders to be last');
    });

    describe('.hide()', function () {
        it('hides the board');
        it('does not hide the board if we are viewing published page');
        it('resets size of the toolbar');
        it('highlights correct trigger');
        it('hides the clipboard');
        it('remembers the state');
        it('hides the placeholders');
        it('shows the plugins');
        it('removes resize event for sideframe');
        it('triggers `strucutreboard_hidden` event on the window');
        it('resizes the structureboard if type of structureboard is dynamic');
    });

    describe('.getId()', function () {
        it('returns the id of passed element');
        it('false if element does not exist');
    });

    describe('.getIds()', function () {
        it('returns the array of ids of passed collection');
    });
});
