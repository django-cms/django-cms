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
                CMS.StructureBoard._initializeGlobalHandlers();
                jasmine.clock().install();
                board = new CMS.StructureBoard();
                done();
            });
        });

        afterEach(function () {
            jasmine.clock().uninstall();
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

        it('applies correct classes to empty placeholder dragareas', function () {
            $('.cms-dragarea').removeClass('cms-dragarea-empty');
            board = new CMS.StructureBoard();
            expect('.cms-dragarea-1').not.toHaveClass('cms-dragarea-empty');
            expect('.cms-dragarea-2').toHaveClass('cms-dragarea-empty');
            expect('.cms-dragarea-10').toHaveClass('cms-dragarea-empty');
        });

        it('initially shows or hides board based on settings', function () {
            spyOn(board, 'show');
            spyOn(board, 'hide');

            expect(CMS.settings.mode).toEqual('edit');
            expect(board.show).not.toHaveBeenCalled();
            expect(board.hide).not.toHaveBeenCalled();
            jasmine.clock().tick();
            expect(board.show).not.toHaveBeenCalled();
            expect(board.hide).toHaveBeenCalled();
        });

        it('initially shows or hides board based on settings 2', function () {
            spyOn(board, 'show');
            spyOn(board, 'hide');

            CMS.settings.mode = 'structure';
            expect(board.show).not.toHaveBeenCalled();
            expect(board.hide).not.toHaveBeenCalled();
            jasmine.clock().tick();
            expect(board.show).toHaveBeenCalled();
            expect(board.hide).not.toHaveBeenCalled();
        });

        // it('shows board mode switcher if there are placeholders');
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
                CMS.StructureBoard._initializeGlobalHandlers();
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
                CMS.StructureBoard._initializeGlobalHandlers();
                board = new CMS.StructureBoard();
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('hides the board', function () {
            spyOn(board, '_hideBoard').and.callThrough();
            board.show();
            expect(board.ui.container).toBeVisible();

            board.hide();
            expect(board.ui.container).not.toBeVisible();
            expect(board._hideBoard).toHaveBeenCalled();
        });

        it('does not hide the board if we are viewing published page', function () {
            CMS.config.mode = 'live';
            spyOn(board, '_hideBoard');
            expect(board.ui.container).not.toBeVisible();
            expect(board.hide()).toEqual(false);
            expect(board.ui.container).not.toBeVisible();
            expect(board._hideBoard).not.toHaveBeenCalled();
        });

        it('resets size of the toolbar if there was no scrollbar', function () {
            board.show();
            expect(board.ui.toolbar).toHaveCss({ right: '0px' });
            expect(board.ui.toolbarTrigger).toHaveCss({ right: '0px' });
            board.hide();
            expect(board.ui.toolbar).toHaveCss({ right: '0px' });
            expect(board.ui.toolbarTrigger).toHaveCss({ right: '0px' });
        });

        it('resets size of the toolbar if there was a scrollbar', function () {
            // fake window that has a scrollbar of 100px
            board.ui.window = {
                0: {
                    innerWidth: board.ui.toolbar.width() + 100
                },
                off: $.noop,
                trigger: $.noop
            };
            board.show();
            board.hide();
            expect(board.ui.toolbar).toHaveCss({ right: '0px' });
            expect(board.ui.toolbarTrigger).toHaveCss({ right: '0px' });
        });


        it('highlights correct trigger', function () {
            board.show();
            board.hide();
            expect(board.ui.toolbarModeLinks.eq(0)).not.toHaveClass('cms-btn-active');
            expect(board.ui.toolbarModeLinks.eq(1)).toHaveClass('cms-btn-active');
        });

        it('hides the clipboard', function () {
            board.show();
            board.ui.container.append(
                '<div class="cms-clipboard" style="display: block; width: 10px; height: 10px;">'
            );

            expect($('.cms-clipboard')).toBeVisible();
            board.hide();
            expect($('.cms-clipboard')).not.toBeVisible();
            expect($('.cms-clipboard').attr('style')).toMatch(/display: none/);
        });

        it('remembers the state', function () {
            board.show();
            expect(CMS.settings.mode).toEqual('structure');
            spyOn(CMS.StructureBoard.prototype, 'setSettings').and.callFake(function (input) {
                return input;
            });
            board.hide();
            expect(CMS.settings.mode).toEqual('edit');
            expect(CMS.StructureBoard.prototype.setSettings).toHaveBeenCalled();
        });

        it('hides the placeholders', function () {
            board.show();
            expect(board.ui.placeholders).toBeVisible();
            board.hide();
            expect(board.ui.placeholders).not.toBeVisible();
        });

        it('shows the plugins', function () {
            board.show();
            expect(board.ui.plugins.not(board.ui.render_model)).not.toBeVisible();
            board.hide();
            // toBeVisible doesn't work because they are display: inline and have no size
            board.ui.plugins.each(function () {
                expect($(this).css('display')).not.toEqual('none');
            });
        });

        it('removes resize event for sideframe', function () {
            board.show();
            spyOn($.fn, 'off');
            board.hide();
            expect($.fn.off).toHaveBeenCalledWith('resize.sideframe');
        });

        it('triggers `strucutreboard_hidden` event on the window', function () {
            board.show();
            spyOn($.fn, 'trigger');
            board.hide();
            expect($.fn.trigger).toHaveBeenCalledWith('structureboard_hidden.sideframe');
        });

        it('resizes the structureboard if type of structureboard is dynamic', function () {
            board.show();
            CMS.config.simpleStructureBoard = false;
            // faking document height
            board.ui.doc = {
                outerHeight: function () {
                    return 329;
                }
            };
            expect(board.ui.container.height()).not.toEqual(329);
            board.hide();
            expect(board.ui.container.height()).toEqual(329);
        });
    });

    describe('.getId()', function () {
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
                CMS.StructureBoard._initializeGlobalHandlers();
                board = new CMS.StructureBoard();
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('returns the id of passed element', function () {
            [
                {
                    from: 'cms-plugin cms-plugin-1',
                    result: '1'
                },
                {
                    from: 'cms-plugin cms-plugin-125',
                    result: '125'
                },
                {
                    from: 'cms-draggable cms-draggable-1',
                    result: '1'
                },
                {
                    from: 'cms-draggable cms-draggable-125',
                    result: '125'
                },
                {
                    from: 'cms-placeholder cms-placeholder-1',
                    result: '1'
                },
                {
                    from: 'cms-placeholder cms-placeholder-125',
                    result: '125'
                },
                {
                    from: 'cms-dragbar cms-dragbar-1',
                    result: '1'
                },
                {
                    from: 'cms-dragbar cms-dragbar-125',
                    result: '125'
                },
                {
                    from: 'cms-dragarea cms-dragarea-1',
                    result: '1'
                },
                {
                    from: 'cms-dragarea cms-dragarea-125',
                    result: '125'
                }
            ].forEach(function (obj) {
                expect(board.getId($('<div class="' + obj.from + '"></div>'))).toEqual(obj.result);
            });
        });

        it('returns null if element is of non supported "type"', function () {
            [
                {
                    from: 'cannot determine',
                    result: null
                },
                {
                    from: 'cms-not-supported cms-not-supported-1',
                    result: null
                }
            ].forEach(function (obj) {
                expect(board.getId($('<div class="' + obj.from + '"></div>'))).toEqual(obj.result);
            });
        });

        it('returns false if element does not exist', function () {
            expect(board.getId()).toEqual(false);
            expect(board.getId(null)).toEqual(false);
            expect(board.getId($('.non-existent'))).toEqual(false);
            expect(board.getId([])).toEqual(false);
        });

        it('fails if classname string is incorrect', function () {
            expect(board.getId.bind(board, $('<div class="cms-plugin"></div>'))).toThrow();
            expect(board.getId($('<div class="cms-plugin fail cms-plugin-10"></div>'))).toEqual('fail');
        });
    });

    describe('.getIds()', function () {
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
                CMS.StructureBoard._initializeGlobalHandlers();
                board = new CMS.StructureBoard();
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('returns the array of ids of passed collection', function () {
            spyOn(board, 'getId').and.callThrough();
            [
                {
                    from: ['cms-plugin cms-plugin-1'],
                    result: ['1']
                },
                {
                    from: ['cms-plugin cms-plugin-125', 'cms-plugin cms-plugin-1'],
                    result: ['125', '1']
                },
                {
                    from: ['cms-plugin cms-plugin-125', 'cms-plugin cms-plugin-1', 'cms-draggable cms-draggable-12'],
                    result: ['125', '1', '12']
                },
                {
                    from: ['non-existent', 'cms-plugin cms-plugin-1'],
                    result: [null, '1']
                }
            ].forEach(function (obj) {
                var collection = $();
                obj.from.forEach(function (className) {
                    collection = collection.add($('<div class="' + className + '"></div>'));
                });
                expect(board.getIds(collection)).toEqual(obj.result);
            });
            expect(board.getId).toHaveBeenCalled();
        });
    });
});
