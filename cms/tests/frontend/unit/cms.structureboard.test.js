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
        var board;
        beforeEach(function (done) {
            fixture.load('plugins.html');
            CMS.settings = {
                mode: 'edit'
            };
            CMS.config = {
                mode: 'edit',
                simpleStructureBoard: true
            };
            $(function () {
                board = new CMS.StructureBoard();
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('shows the board', function () {
            spyOn(board, '_showBoard').and.callThrough();
            expect(board.ui.container).not.toBeVisible();
            board.show();
            expect(board.ui.container).toBeVisible();
            expect(board._showBoard).toHaveBeenCalled();
        });

        it('does not show the board if we are viewing published page', function () {
            CMS.config.mode = 'live';
            spyOn(board, '_showBoard').and.callThrough();
            expect(board.ui.container).not.toBeVisible();
            expect(board.show()).toEqual(false);
            expect(board.ui.container).not.toBeVisible();
            expect(board._showBoard).not.toHaveBeenCalled();
        });

        it('resizes toolbar correctly if there is no scrollbar', function () {
            board.show();
            expect(board.ui.toolbar).toHaveCss({ right: '0px' });
            expect(board.ui.toolbarTrigger).toHaveCss({ right: '0px' });
        });

        it('resizes toolbar correctly based if there is a scrollbar', function () {
            // fake window that has a scrollbar of 20px
            board.ui.window = {
                0: {
                    innerWidth: board.ui.toolbar.width() + 20
                },
                off: $.noop,
                trigger: $.noop
            };
            board.show();
            expect(board.ui.toolbar).toHaveCss({ right: '20px' });
            expect(board.ui.toolbarTrigger).toHaveCss({ right: '20px' });
        });

        it('highlights correct trigger', function () {
            expect(board.ui.toolbarModeLinks.eq(0)).not.toHaveClass('cms-btn-active');
            board.show();
            expect(board.ui.toolbarModeLinks.eq(0)).toHaveClass('cms-btn-active');
            expect(board.ui.toolbarModeLinks.eq(1)).not.toHaveClass('cms-btn-active');
        });

        it('adds correct classes to the root of the document', function () {
            board.ui.html.removeClass('cms-structure-mode-structure');
            expect(board.ui.html).not.toHaveClass('cms-structure-mode-structure');
            board.show();
            expect(board.ui.html).toHaveClass('cms-structure-mode-structure');
        });

        it('remembers state', function () {
            spyOn(CMS.StructureBoard.prototype, 'setSettings').and.callFake(function (input) {
                return input;
            });
            expect(CMS.settings.mode).toEqual('edit');
            board.show();
            expect(CMS.settings.mode).toEqual('structure');
            expect(CMS.StructureBoard.prototype.setSettings).toHaveBeenCalled();
        });

        it('shows all placeholders', function () {
            expect(board.ui.dragareas).not.toBeVisible();
            expect(board.ui.dragareas).not.toHaveAttr('style');
            board.show(true);
            expect(board.ui.dragareas).toBeVisible();
            // browsers report different strings
            expect(board.ui.dragareas.attr('style')).toMatch(/opacity: 1/);
        });

        it('applies correct classes based on type of structureboard 1', function () {
            expect(board.ui.content).not.toHaveClass('cms-structure-content-simple');
            expect(board.ui.dragareas).not.toHaveClass('cms-dragarea-simple');
            expect(board.ui.container).not.toHaveClass('cms-structure-dynamic');
            board.show();
            expect(board.ui.content).toHaveClass('cms-structure-content-simple');
            expect(board.ui.container).not.toHaveClass('cms-structure-dynamic');
            expect(board.ui.dragareas).toHaveClass('cms-dragarea-simple');
        });

        it('applies correct classes based on type of structureboard 2', function () {
            spyOn(board, '_resizeBoard').and.callFake($.noop);
            CMS.config.simpleStructureBoard = false;
            expect(board.ui.content).not.toHaveClass('cms-structure-content-simple');
            expect(board.ui.dragareas).not.toHaveClass('cms-dragarea-simple');
            expect(board.ui.container).not.toHaveClass('cms-structure-dynamic');
            board.show();
            expect(board.ui.content).not.toHaveClass('cms-structure-content-simple');
            expect(board.ui.container).toHaveClass('cms-structure-dynamic');
            expect(board.ui.dragareas).not.toHaveClass('cms-dragarea-simple');
            CMS.config.simpleStructureBoard = true;
        });

        it('reorders static placeholders to be last', function () {
            expect($('.cms-dragarea-static')).toEqual($('.cms-dragarea:first'));
            board.show();
            expect($('.cms-dragarea-static')).toEqual($('.cms-dragarea:last'));
        });
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
