'use strict';

describe('CMS.StructureBoard', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a StructureBoard class', function () {
        expect(CMS.StructureBoard).toBeDefined();
    });

    it('has public API', function () {
        expect(CMS.StructureBoard.prototype.show).toEqual(jasmine.any(Function));
        expect(CMS.StructureBoard.prototype.hide).toEqual(jasmine.any(Function));
        expect(CMS.StructureBoard.prototype.getId).toEqual(jasmine.any(Function));
        expect(CMS.StructureBoard.prototype.getIds).toEqual(jasmine.any(Function));
    });

    describe('instance', function () {
        var board;
        beforeEach(function (done) {
            fixture.load('plugins.html');
            CMS.settings = {
                mode: 'edit'
            };
            CMS.config = {
                mode: 'edit'
            };
            $(function () {
                board = new CMS.StructureBoard();
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('has ui', function () {
            expect(board.ui).toEqual(jasmine.any(Object));
            expect(Object.keys(board.ui)).toContain('container');
            expect(Object.keys(board.ui)).toContain('content');
            expect(Object.keys(board.ui)).toContain('doc');
            expect(Object.keys(board.ui)).toContain('window');
            expect(Object.keys(board.ui)).toContain('html');
            expect(Object.keys(board.ui)).toContain('toolbar');
            expect(Object.keys(board.ui)).toContain('sortables');
            expect(Object.keys(board.ui)).toContain('plugins');
            expect(Object.keys(board.ui)).toContain('render_model');
            expect(Object.keys(board.ui)).toContain('placeholders');
            expect(Object.keys(board.ui)).toContain('dragitems');
            expect(Object.keys(board.ui)).toContain('dragareas');
            expect(Object.keys(board.ui)).toContain('toolbarModeSwitcher');
            expect(Object.keys(board.ui)).toContain('toolbarModeLinks');
            expect(Object.keys(board.ui)).toContain('toolbarTrigger');
        });

        it('has no options', function () {
            expect(board.options).toEqual(undefined);
        });
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
