'use strict';
var CMS = require('../../../static/cms/js/modules/cms.base');
var StructureBoard = require('../../../static/cms/js/modules/cms.structureboard');
var Plugin = require('../../../static/cms/js/modules/cms.plugins');
var $ = require('jquery');
var keyboard = require('../../../static/cms/js/modules/keyboard');

window.CMS = window.CMS || CMS;
CMS.StructureBoard = StructureBoard;
CMS.Plugin = Plugin;

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
            expect(Object.keys(board.ui).length).toEqual(15);
        });

        it('has no options', function () {
            expect(board.options).not.toBeDefined();
        });

        it('applies correct classes to empty placeholder dragareas', function () {
            $('.cms-dragarea').removeClass('cms-dragarea-empty');
            board = new CMS.StructureBoard();
            expect('.cms-dragarea-1').not.toHaveClass('cms-dragarea-empty');
            expect('.cms-dragarea-2').toHaveClass('cms-dragarea-empty');
            expect('.cms-dragarea-10').toHaveClass('cms-dragarea-empty');
        });

        it('initially shows or hides board based on settings', function () {
            spyOn(CMS.StructureBoard.prototype, 'show');
            spyOn(CMS.StructureBoard.prototype, 'hide');

            expect(CMS.settings.mode).toEqual('edit');
            board = new CMS.StructureBoard();
            expect(board.show).not.toHaveBeenCalled();
            expect(board.hide).toHaveBeenCalled();
        });

        it('initially shows or hides board based on settings 2', function () {
            spyOn(CMS.StructureBoard.prototype, 'show');
            spyOn(CMS.StructureBoard.prototype, 'hide');

            CMS.settings.mode = 'structure';
            board = new CMS.StructureBoard();
            expect(board.show).toHaveBeenCalled();
            expect(board.hide).not.toHaveBeenCalled();
        });

        it('does not show or hide structureboard if there are no dragareas', function () {
            board.ui.dragareas.remove();
            board = new CMS.StructureBoard();

            spyOn(board, 'show');
            spyOn(board, 'hide');

            expect(board.show).not.toHaveBeenCalled();
            expect(board.hide).not.toHaveBeenCalled();
            jasmine.clock().tick(200);
            expect(board.show).not.toHaveBeenCalled();
            expect(board.hide).not.toHaveBeenCalled();
        });

        it('does not show or hide structureboard if there is no board mode switcher', function () {
            board.ui.toolbarModeSwitcher.remove();
            board = new CMS.StructureBoard();

            spyOn(board, 'show');
            spyOn(board, 'hide');

            expect(board.show).not.toHaveBeenCalled();
            expect(board.hide).not.toHaveBeenCalled();
            jasmine.clock().tick(200);
            expect(board.show).not.toHaveBeenCalled();
            expect(board.hide).not.toHaveBeenCalled();
        });

        it('shows board mode switcher if there are placeholders', function () {
            expect(board.ui.placeholders.length > 0).toEqual(true);
            board.ui.toolbarModeSwitcher.hide();
            expect(board.ui.toolbarModeSwitcher).not.toBeVisible();

            new CMS.StructureBoard();

            expect(board.ui.toolbarModeSwitcher).toBeVisible();
        });

        it('does not show board mode switcher if there are no placeholders', function () {
            expect(board.ui.placeholders.length > 0).toEqual(true);
            board.ui.placeholders.remove();

            board.ui.toolbarModeSwitcher.hide();
            expect(board.ui.toolbarModeSwitcher).not.toBeVisible();

            board = new CMS.StructureBoard();
            expect(board.ui.placeholders.length).toEqual(0);

            expect(board.ui.toolbarModeSwitcher).not.toBeVisible();
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
                mode: 'edit'
            };
            $(function () {
                spyOn(CMS.API.Helpers, 'setSettings').and.callFake(function (input) {
                    return input;
                });
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
            CMS.API.Helpers.setSettings.and.callFake(function (input) {
                return input;
            });
            expect(CMS.settings.mode).toEqual('edit');
            board.show();
            expect(CMS.settings.mode).toEqual('structure');
            expect(CMS.API.Helpers.setSettings).toHaveBeenCalled();
        });

        it('shows all placeholders', function () {
            expect(board.ui.dragareas).not.toBeVisible();
            expect(board.ui.dragareas).not.toHaveAttr('style');
            board.show(true);
            expect(board.ui.dragareas).toBeVisible();
            // browsers report different strings
            expect(board.ui.dragareas.attr('style')).toMatch(/opacity: 1/);
        });

        it('reorders static placeholders to be last', function () {
            expect($('.cms-dragarea-static')).toEqual($('.cms-dragarea:first'));
            board.show();
            expect($('.cms-dragarea-static')).toEqual($('.cms-dragarea:last'));
        });
    });

    describe('highlights', function () {
        var board;
        beforeEach(function (done) {
            fixture.load('plugins.html', 'clipboard.html');
            CMS.settings = {
                mode: 'edit'
            };
            CMS.config = {
                mode: 'edit'
            };
            $(function () {
                spyOn(CMS.API.Helpers, 'setSettings').and.callFake(function (input) {
                    return input;
                });
                CMS.API.Tooltip = {
                    domElem: {
                        is: function () {
                            return true;
                        },
                        data: function () {
                            return 1;
                        }
                    }
                };
                CMS.StructureBoard._initializeGlobalHandlers();
                board = new CMS.StructureBoard();
                spyOn(board, 'show');
                spyOn(board, 'hide');
                spyOn(Plugin, '_highlightPluginStructure');
                spyOn(Plugin, '_highlightPluginContent');
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        describe('._showAndHighlightPlugin()', function () {
            it('returns false if tooltip does not exist', function () {
                CMS.API.Tooltip = false;
                expect(board._showAndHighlightPlugin()).toEqual(false);
                expect(board.show).not.toHaveBeenCalled();
            });

            it('returns false if in live mode', function () {
                CMS.config.mode = 'live';
                expect(board._showAndHighlightPlugin()).toEqual(false);
                expect(board.show).not.toHaveBeenCalled();
            });

            it('returns false if no plugin is hovered', function () {
                CMS.API.Tooltip.domElem.is = function () {
                    return false;
                };

                expect(board._showAndHighlightPlugin()).toEqual(false);
                expect(board.show).not.toHaveBeenCalled();
            });

            it('shows board if plugin is hovered', function () {
                jasmine.clock().install();
                expect(board._showAndHighlightPlugin()).not.toBeDefined();
                expect(board.show).toHaveBeenCalledTimes(1);
                expect(Plugin._highlightPluginStructure).not.toHaveBeenCalled();
                jasmine.clock().tick(201);
                expect(Plugin._highlightPluginStructure).toHaveBeenCalledTimes(1);
                jasmine.clock().uninstall();
            });
        });

        describe('._hideAndHighlightPlugin()', function () {
            beforeEach(function (done) {
                $(function () {
                    CMS.settings.mode = 'structure';
                    done();
                });
            });

            it('returns false if no plugin is hovered', function () {
                expect(board._hideAndHighlightPlugin()).toEqual(false);
                expect(board.hide).not.toHaveBeenCalled();
            });

            it('returns false if in live mode', function () {
                CMS.config.mode = 'live';
                expect(board._hideAndHighlightPlugin()).toEqual(false);
                expect(board.hide).not.toHaveBeenCalled();
            });

            it('returns false if hovered plugin is inside clipboard', function () {
                var clipboardDraggable = $('.cms-draggable-from-clipboard');

                spyOn($.fn, 'init').and.returnValue(clipboardDraggable);

                expect(board._hideAndHighlightPlugin()).toEqual(false);
                expect(board.hide).not.toHaveBeenCalled();
            });

            it('hides board if plugin is hovered', function () {
                jasmine.clock().install();
                var draggable = $('.cms-draggable-1');

                spyOn($.fn, 'init').and.returnValue(draggable);
                spyOn($.fn, 'closest').and.returnValue([]);
                spyOn(board, 'getId').and.returnValue(999);

                expect(board._hideAndHighlightPlugin()).not.toBeDefined();
                expect(board.hide).toHaveBeenCalledTimes(1);
                expect(Plugin._highlightPluginContent).not.toHaveBeenCalled();

                jasmine.clock().tick(201);

                expect(Plugin._highlightPluginContent).toHaveBeenCalledTimes(1);
                expect(Plugin._highlightPluginContent).toHaveBeenCalledWith(999);
                jasmine.clock().uninstall();
            });
        });
    });

    describe('.hide()', function () {
        var board;
        beforeEach(function (done) {
            fixture.load('plugins.html');
            $(function () {
                CMS.settings = {
                    mode: 'edit'
                };
                CMS.config = {
                    mode: 'edit'
                };
                spyOn(CMS.API.Helpers, 'setSettings').and.callFake(function (input) {
                    return input;
                });
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

        it('remembers the state', function () {
            board.show();
            expect(CMS.settings.mode).toEqual('structure');
            CMS.API.Helpers.setSettings.and.callFake(function (input) {
                return input;
            });
            board.hide();
            expect(CMS.settings.mode).toEqual('edit');
            expect(CMS.API.Helpers.setSettings).toHaveBeenCalled();
        });

        it('triggers `resize` event on the window', function () {
            board.show();
            var spy = jasmine.createSpy();
            $(window).on('resize', spy);
            board.hide();
            expect(spy).toHaveBeenCalledTimes(1);
            $(window).off('resize', spy);
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
                mode: 'edit'
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
                mode: 'edit'
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

    describe('._setupModeSwitcher()', function () {
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
                spyOn(keyboard, 'bind');
                CMS.StructureBoard._initializeGlobalHandlers();
                board = new CMS.StructureBoard();
                spyOn(board, 'show').and.callFake(function () {
                    CMS.settings.mode = 'structure';
                });
                spyOn(board, 'hide').and.callFake(function () {
                    CMS.settings.mode = 'edit';
                });
                done();
            });
        });

        afterEach(function () {
            board.ui.doc.off('keydown.cms.structureboard.switcher');
            fixture.cleanup();
        });

        it('sets up click handler to show board', function () {
            var showTrigger = board.ui.toolbarModeLinks.eq(0);
            expect(showTrigger).toHandle(board.click);
            expect(showTrigger).toHandle(board.pointerUp);

            CMS.settings.mode = 'structure';

            showTrigger.trigger(board.click);
            showTrigger.trigger(board.pointerUp);

            expect(board.show).not.toHaveBeenCalled();

            CMS.settings.mode = 'edit';

            showTrigger.trigger(board.click);
            expect(board.show).toHaveBeenCalledTimes(1);
            showTrigger.trigger(board.pointerUp);
            expect(board.show).toHaveBeenCalledTimes(1);

            CMS.settings.mode = 'edit';
            showTrigger.trigger(board.pointerUp);
            expect(board.show).toHaveBeenCalledTimes(2);
            showTrigger.trigger(board.click);
            expect(board.show).toHaveBeenCalledTimes(2);
        });

        it('sets up click handler to hide board', function () {
            var hideTrigger = board.ui.toolbarModeLinks.eq(1);
            expect(hideTrigger).toHandle(board.click);
            expect(hideTrigger).toHandle(board.pointerUp);

            CMS.settings.mode = 'edit';

            hideTrigger.trigger(board.click);
            hideTrigger.trigger(board.pointerUp);

            expect(board.hide).not.toHaveBeenCalled();

            CMS.settings.mode = 'structure';

            hideTrigger.trigger(board.click);
            expect(board.hide).toHaveBeenCalledTimes(1);
            hideTrigger.trigger(board.pointerUp);
            expect(board.hide).toHaveBeenCalledTimes(1);

            CMS.settings.mode = 'structure';
            hideTrigger.trigger(board.pointerUp);
            expect(board.hide).toHaveBeenCalledTimes(2);
            hideTrigger.trigger(board.click);
            expect(board.hide).toHaveBeenCalledTimes(2);
        });

        it('sets up shortcuts to toggle board', function () {
            spyOn(board, '_toggleStructureBoard');
            var preventDefaultSpySpace = jasmine.createSpy();
            var preventDefaultSpyShiftSpace = jasmine.createSpy();

            expect(keyboard.bind).toHaveBeenCalledTimes(2);
            expect(keyboard.bind).toHaveBeenCalledWith('space', jasmine.any(Function));
            expect(keyboard.bind).toHaveBeenCalledWith('shift+space', jasmine.any(Function));

            var calls = keyboard.bind.calls.all();

            calls[0].args[1]({ preventDefault: preventDefaultSpySpace });
            expect(board._toggleStructureBoard).toHaveBeenCalledTimes(1);
            expect(board._toggleStructureBoard).toHaveBeenCalledWith();
            expect(preventDefaultSpySpace).toHaveBeenCalledTimes(1);
            expect(preventDefaultSpyShiftSpace).not.toHaveBeenCalled();

            calls[1].args[1]({ preventDefault: preventDefaultSpyShiftSpace });
            expect(board._toggleStructureBoard).toHaveBeenCalledTimes(2);
            expect(board._toggleStructureBoard).toHaveBeenCalledWith({
                useHoveredPlugin: true
            });
            expect(preventDefaultSpySpace).toHaveBeenCalledTimes(1);
            expect(preventDefaultSpyShiftSpace).toHaveBeenCalledTimes(1);
        });

        it('does not setup key binds if toggler is not availabe', function () {
            keyboard.bind.calls.reset();
            board.ui.toolbarModeSwitcher.remove();

            CMS.StructureBoard._initializeGlobalHandlers();
            board = new CMS.StructureBoard();
            spyOn(board, 'show').and.callFake(function () {
                CMS.settings.mode = 'structure';
            });
            spyOn(board, 'hide').and.callFake(function () {
                CMS.settings.mode = 'edit';
            });

            expect(keyboard.bind).not.toHaveBeenCalled();
        });

        it('does not setup key binds if toggler is not visible (there are no placeholders)', function () {
            keyboard.bind.calls.reset();

            board.ui.placeholders.remove();
            board.ui.toolbarModeSwitcher.hide();
            CMS.StructureBoard._initializeGlobalHandlers();
            board = new CMS.StructureBoard();

            spyOn(board, 'show').and.callFake(function () {
                CMS.settings.mode = 'structure';
            });
            spyOn(board, 'hide').and.callFake(function () {
                CMS.settings.mode = 'edit';
            });

            expect(keyboard.bind).not.toHaveBeenCalled();
            expect(board.ui.toolbarModeSwitcher).not.toBeVisible();
        });
    });

    describe('._toggleStructureBoard()', function () {
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
                spyOn(keyboard, 'bind');
                CMS.StructureBoard._initializeGlobalHandlers();
                board = new CMS.StructureBoard();
                spyOn(board, 'show').and.callFake(function () {
                    CMS.settings.mode = 'structure';
                });
                spyOn(board, 'hide').and.callFake(function () {
                    CMS.settings.mode = 'edit';
                });
                spyOn(board, '_showAndHighlightPlugin');
                spyOn(board, '_hideAndHighlightPlugin');
                done();
            });
        });

        it('shows structureboard', function () {
            board._toggleStructureBoard();
            expect(board.show).toHaveBeenCalledTimes(1);
            expect(board.hide).not.toHaveBeenCalled();
        });

        it('hides strucrueboard', function () {
            CMS.settings.mode = 'structure';
            board._toggleStructureBoard();
            expect(board.show).not.toHaveBeenCalled();
            expect(board.hide).toHaveBeenCalledTimes(1);
        });

        it('shows structureboard and highlights plugin', function () {
            board._toggleStructureBoard({ useHoveredPlugin: true });
            expect(board._showAndHighlightPlugin).toHaveBeenCalledTimes(1);
            expect(board._hideAndHighlightPlugin).not.toHaveBeenCalled();
        });

        it('hides structureboard and highlights plugin', function () {
            CMS.settings.mode = 'structure';
            board._toggleStructureBoard({ useHoveredPlugin: true });
            expect(board._showAndHighlightPlugin).not.toHaveBeenCalled();
            expect(board._hideAndHighlightPlugin).toHaveBeenCalledTimes(1);
        });
    });

    describe('._drag()', function () {
        var board;
        var options;
        beforeEach(function (done) {
            fixture.load('plugins.html');
            CMS.settings = {
                mode: 'structure'
            };
            CMS.config = {
                mode: 'structure'
            };
            $(function () {
                CMS.StructureBoard._initializeGlobalHandlers();
                board = new CMS.StructureBoard();
                options = board.ui.sortables.nestedSortable('option');
                done();
            });
        });

        afterEach(function () {
            board.ui.doc.off('keyup.cms.interrupt');
            fixture.cleanup();
        });

        it('initializes nested sortable', function () {
            options = board.ui.sortables.nestedSortable('option');
            expect(options).toEqual(jasmine.objectContaining({
                items: '> .cms-draggable:not(.cms-draggable-disabled .cms-draggable)',
                placeholder: 'cms-droppable',
                connectWith: '.cms-draggables:not(.cms-hidden)',
                appendTo: '.cms-structure-content',
                listType: 'div.cms-draggables',
                doNotClear: true,
                toleranceElement: '> div',
                disableNestingClass: 'cms-draggable-disabled',
                errorClass: 'cms-draggable-disallowed',
                start: jasmine.any(Function),
                helper: jasmine.any(Function),
                beforeStop: jasmine.any(Function),
                update: jasmine.any(Function),
                isAllowed: jasmine.any(Function)
            }));
        });

        it('adds event handler for cms-structure-update to actualize empty placeholders', function () {
            if (!CMS.$._data(board.ui.sortables[0]).events['cms-structure-update'][0].handler.name) {
                pending();
            }
            expect(board.ui.sortables).toHandle('cms-structure-update');
            // cheating here a bit
            expect(CMS.$._data(board.ui.sortables[0]).events['cms-structure-update'][0].handler.name)
                .toEqual('actualizeEmptyPlaceholders');
        });

        it('defines how draggable helper is created', function () {
            options = board.ui.sortables.nestedSortable('option');
            var helper = options.helper;

            var item = $(
                '<div class="some class string">' +
                    '<div class="cms-dragitem">Only this will be cloned</div>' +
                    '<div class="cms-draggables">' +
                        '<div class="cms-dragitem">This will not</div>' +
                    '</div>' +
                '</div>'
            );

            var result = helper(null, item);

            expect(result).toHaveClass('some');
            expect(result).toHaveClass('class');
            expect(result).toHaveClass('string');

            expect(result).toHaveText('Only this will be cloned');
            expect(result).not.toHaveText('This will not');
        });

        describe('start', function () {
            it('sets data-touch-action attribute', function () {
                expect(board.ui.content).toHaveAttr('data-touch-action', 'pan-y');
                options.start({}, { item: $('<div></div>'), helper: $('<div></div>') });
                expect(board.ui.content).toHaveAttr('data-touch-action', 'none');
            });

            it('sets dragging state', function () {
                expect(board.dragging).toEqual(false);
                options.start({}, { item: $('<div></div>'), helper: $('<div></div>') });
                expect(board.dragging).toEqual(true);
            });

            it('actualizes empty placeholders', function () {
                var firstPlaceholder = board.ui.dragareas.eq(0);
                var firstPlaceholderCopyAll = firstPlaceholder
                    .find('.cms-dragbar .cms-submenu-item:has(a[data-rel="copy"]):first');
                var secondPlaceholder = board.ui.dragareas.eq(1);
                var secondPlaceholderCopyAll = secondPlaceholder
                    .find('.cms-dragbar .cms-submenu-item:has(a[data-rel="copy"]):first');

                expect(firstPlaceholder).toHaveClass('cms-dragarea-empty');
                expect(firstPlaceholderCopyAll).toHaveClass('cms-submenu-item-disabled');
                expect(secondPlaceholder).not.toHaveClass('cms-dragarea-empty');
                expect(secondPlaceholderCopyAll).not.toHaveClass('cms-submenu-item-disabled');

                secondPlaceholder.find('> .cms-draggables').contents()
                    .appendTo(firstPlaceholder.find('> .cms-draggables'));

                options.start({}, { item: $('<div></div>'), helper: $('<div></div>') });

                expect(firstPlaceholder).not.toHaveClass('cms-dragarea-empty');
                expect(firstPlaceholderCopyAll).not.toHaveClass('cms-submenu-item-disabled');
                expect(secondPlaceholder).toHaveClass('cms-dragarea-empty');
                expect(secondPlaceholderCopyAll).toHaveClass('cms-submenu-item-disabled');

                // now check that the plugin currently being dragged does not count
                // towards "plugins count"
                firstPlaceholder.find('> .cms-draggables').contents()
                    .appendTo(secondPlaceholder.find('> .cms-draggables'));
                firstPlaceholder.find('> .cms-draggables').append(
                    $('<div class="cms-draggable cms-draggable-is-dragging"></div>')
                );

                options.start({}, { item: $('<div></div>'), helper: $('<div></div>') });

                expect(firstPlaceholder).toHaveClass('cms-dragarea-empty');
                expect(firstPlaceholderCopyAll).toHaveClass('cms-submenu-item-disabled');
                expect(secondPlaceholder).not.toHaveClass('cms-dragarea-empty');
                expect(secondPlaceholderCopyAll).not.toHaveClass('cms-submenu-item-disabled');
            });

            it('hides settings menu', function () {
                spyOn(CMS.Plugin, '_hideSettingsMenu');
                options.start({}, { item: $('<div></div>'), helper: $('<div></div>') });
                expect(CMS.Plugin._hideSettingsMenu).toHaveBeenCalledTimes(1);
            });

            it('shows all the empty sortables', function () {
                expect($('.cms-draggables.cms-hidden').length).toEqual(1);
                options.start({}, { item: $('<div></div>'), helper: $('<div></div>') });
                expect($('.cms-draggables.cms-hidden').length).toEqual(0);
            });

            it('adds appropriate classes on item without children and helper', function () {
                var item = $('<div class="cms-draggable"><div class="cms-dragitem">Some plugin</div></div>');
                var helper = options.helper(null, item);

                options.start({}, {
                    item: item,
                    helper: helper
                });

                expect(item).toHaveClass('cms-is-dragging');
                expect(helper).toHaveClass('cms-draggable-is-dragging');
            });

            it('adds appropriate classes on item with children', function () {
                var item = $(
                    '<div class="cms-draggable">' +
                        '<div class="cms-dragitem">Some plugin</div>' +
                        '<div class="cms-draggables">' +
                            '<div></div>' +
                        '</div>' +
                    '</div>'
                );
                var helper = options.helper(null, item);

                options.start({}, {
                    item: item,
                    helper: helper
                });

                expect(helper).toHaveClass('cms-draggable-stack');
            });

            it('sets up a handler for interrupting dragging with keyboard', function () {
                expect(board.ui.doc).not.toHandle('keyup.cms.interrupt');

                options.start({}, { item: $('<div></div>'), helper: $('<div></div>') });

                expect(board.ui.doc).toHandle('keyup.cms.interrupt');

                var spy = jasmine.createSpy();

                board.ui.sortables.on('mouseup', spy);
                spyOn($.ui.sortable.prototype, '_mouseStop');

                var wrongEvent = new $.Event('keyup.cms.interrupt', { keyCode: 1287926834 });
                var correctEvent = new $.Event('keyup.cms.interrupt', { keyCode: CMS.KEYS.ESC });

                board.state = 'mock';
                board.ui.doc.trigger(wrongEvent);
                expect(board.state).toEqual('mock');
                expect($.ui.sortable.prototype._mouseStop).not.toHaveBeenCalled();
                expect(spy).not.toHaveBeenCalled();

                board.state = 'mock';
                board.ui.doc.trigger(wrongEvent, [true]);
                expect(board.state).toEqual(false);
                expect($.ui.sortable.prototype._mouseStop).toHaveBeenCalledTimes(1);
                expect(spy).toHaveBeenCalledTimes(1 + board.ui.sortables.length);

                board.ui.doc.off('keyup.cms.interrupt');

                options.start({}, { item: $('<div></div>'), helper: $('<div></div>') });

                board.state = 'mock';
                board.ui.doc.trigger(correctEvent);
                expect(board.state).toEqual(false);
                expect($.ui.sortable.prototype._mouseStop).toHaveBeenCalledTimes(2);
                expect(spy).toHaveBeenCalledTimes((1 + board.ui.sortables.length) * 2);
            });
        });

        describe('beforeStop', function () {
            it('sets dragging state to false', function () {
                board.dragging = true;
                options.beforeStop(null, { item: $('<div></div>') });
                expect(board.dragging).toEqual(false);
            });

            it('removes classes', function () {
                var item = $('<div class="cms-is-dragging cms-draggable-stack"></div>');
                options.beforeStop(null, { item: item });
                expect(item).not.toHaveClass('cms-is-dragging');
                expect(item).not.toHaveClass('cms-draggable-stack');
            });

            it('unbinds interrupt event', function () {
                var spy = jasmine.createSpy();
                board.ui.doc.on('keyup.cms.interrupt', spy);
                options.beforeStop(null, { item: $('<div></div>') });
                board.ui.doc.trigger('keyup.cms.interrupt');
                expect(spy).not.toHaveBeenCalled();
                expect(board.ui.doc).not.toHandle('keyup.cms.interrupt');
            });

            it('resets data-touch-action attribute', function () {
                board.ui.content.removeAttr('data-touch-action');
                options.beforeStop(null, { item: $('<div></div>') });
                expect(board.ui.content).toHaveAttr('data-touch-action', 'pan-y');
            });
        });

        describe('update', function () {
            it('returns false if it is not possible to update', function () {
                board.state = false;
                expect(options.update()).toEqual(false);
            });

            it('actualizes collapsible status', function () {
                var textPlugin = $('.cms-draggable-1');
                var randomPlugin = $('.cms-draggable-2');
                var helper = options.helper(null, textPlugin);

                // we need to start first to set a private variable original container
                options.start(null, { item: textPlugin, helper: helper });
                board.state = true;

                expect(randomPlugin.find('> .cms-dragitem')).not.toHaveClass('cms-dragitem-collapsable');
                expect(randomPlugin.find('> .cms-dragitem')).not.toHaveClass('cms-dragitem-expanded');

                textPlugin.appendTo(randomPlugin.find('.cms-draggables'));
                options.update(null, { item: textPlugin, helper: helper });

                expect(randomPlugin.find('> .cms-dragitem')).toHaveClass('cms-dragitem-collapsable');
                expect(randomPlugin.find('> .cms-dragitem')).toHaveClass('cms-dragitem-expanded');

                // and back

                options.start(null, { item: textPlugin, helper: helper });
                board.state = true;

                textPlugin.appendTo($('.cms-dragarea-1').find('> .cms-draggables'));
                options.update(null, { item: textPlugin, helper: helper });

                expect(randomPlugin.find('> .cms-dragitem')).not.toHaveClass('cms-dragitem-collapsable');
                expect(randomPlugin.find('> .cms-dragitem')).toHaveClass('cms-dragitem-expanded');
            });

            it('returns false if we moved plugin inside same container ' +
               'and the event is fired on the container', function () {
                var textPlugin = $('.cms-draggable-1');
                var helper = options.helper(null, textPlugin);
                var placeholderDraggables = $('.cms-dragarea-1').find('> .cms-draggables');

                // and one more time
                options.start(null, { item: textPlugin, helper: helper });
                board.state = true;

                textPlugin.prependTo(placeholderDraggables);
                expect(
                    options.update.bind(textPlugin)(null, { item: textPlugin, helper: helper })
                ).toEqual(false);
            });

            it('triggers event on the plugin when necessary', function () {
                var textPlugin = $('.cms-draggable-1');
                var randomPlugin = $('.cms-draggable-2');
                var helper = options.helper(null, textPlugin);
                var placeholderDraggables = $('.cms-dragarea-1').find('> .cms-draggables');

                var spy = jasmine.createSpy();
                textPlugin.on('cms-plugins-update', spy);

                // we need to start first to set a private variable original container
                options.start(null, { item: textPlugin, helper: helper });
                board.state = true;

                textPlugin.appendTo(randomPlugin.find('.cms-draggables'));
                options.update(null, { item: textPlugin, helper: helper });

                expect(spy).toHaveBeenCalledTimes(1);


                // and back
                options.start(null, { item: textPlugin, helper: helper });
                board.state = true;

                textPlugin.appendTo($('.cms-dragarea-1').find('> .cms-draggables'));
                options.update(null, { item: textPlugin, helper: helper });

                expect(spy).toHaveBeenCalledTimes(2);


                // and one more time
                options.start(null, { item: textPlugin, helper: helper });
                board.state = true;

                textPlugin.prependTo(placeholderDraggables);
                options.update.bind(placeholderDraggables)(null, { item: textPlugin, helper: helper });

                expect(spy).toHaveBeenCalledTimes(3);
            });

            it('triggers event on the plugin in clipboard', function () {
                $(fixture.el).prepend(
                    '<div class="cms-clipboard">' +
                    '<div class="cms-clipboard-containers cms-draggables"></div>' +
                    '</div>'
                );

                var textPlugin = $('.cms-draggable-1');
                var randomPlugin = $('.cms-draggable-2');
                var helper = options.helper(null, textPlugin);

                textPlugin.prependTo('.cms-clipboard-containers');

                var pluginSpy = jasmine.createSpy();
                var clipboardSpy = jasmine.createSpy();

                textPlugin.on('cms-plugins-update', pluginSpy);
                textPlugin.on('cms-paste-plugin-update', clipboardSpy);

                // we need to start first to set a private variable original container
                options.start(null, { item: textPlugin, helper: helper });
                board.state = true;

                textPlugin.appendTo(randomPlugin.find('.cms-draggables'));
                options.update(null, { item: textPlugin, helper: helper });

                expect(pluginSpy).not.toHaveBeenCalled();
                expect(clipboardSpy).toHaveBeenCalledTimes(1);
            });

            it('actualizes empty placeholders', function () {
                var firstPlaceholder = board.ui.dragareas.eq(0);
                var firstPlaceholderCopyAll = firstPlaceholder
                    .find('.cms-dragbar .cms-submenu-item:has(a[data-rel="copy"]):first');
                var secondPlaceholder = board.ui.dragareas.eq(1);
                var secondPlaceholderCopyAll = secondPlaceholder
                    .find('.cms-dragbar .cms-submenu-item:has(a[data-rel="copy"]):first');

                expect(firstPlaceholder).toHaveClass('cms-dragarea-empty');
                expect(firstPlaceholderCopyAll).toHaveClass('cms-submenu-item-disabled');
                expect(secondPlaceholder).not.toHaveClass('cms-dragarea-empty');
                expect(secondPlaceholderCopyAll).not.toHaveClass('cms-submenu-item-disabled');

                options.start({}, { item: $('<div></div>'), helper: $('<div></div>') });

                secondPlaceholder.find('> .cms-draggables').contents()
                    .appendTo(firstPlaceholder.find('> .cms-draggables'));

                board.state = true;
                options.update({}, { item: $('<div class="cms-plugin-1"></div>'), helper: $('<div></div>') });

                expect(firstPlaceholder).not.toHaveClass('cms-dragarea-empty');
                expect(firstPlaceholderCopyAll).not.toHaveClass('cms-submenu-item-disabled');
                expect(secondPlaceholder).toHaveClass('cms-dragarea-empty');
                expect(secondPlaceholderCopyAll).toHaveClass('cms-submenu-item-disabled');

                // now check that the plugin currently being dragged does not count
                // towards "plugins count"
                firstPlaceholder.find('> .cms-draggables').contents()
                    .appendTo(secondPlaceholder.find('> .cms-draggables'));
                firstPlaceholder.find('> .cms-draggables').append(
                    $('<div class="cms-draggable cms-draggable-is-dragging"></div>')
                );

                options.update({}, { item: $('<div class="cms-plugin-1"></div>'), helper: $('<div></div>') });

                expect(firstPlaceholder).toHaveClass('cms-dragarea-empty');
                expect(firstPlaceholderCopyAll).toHaveClass('cms-submenu-item-disabled');
                expect(secondPlaceholder).not.toHaveClass('cms-dragarea-empty');
                expect(secondPlaceholderCopyAll).not.toHaveClass('cms-submenu-item-disabled');
            });

            it('hides empty sortables', function () {
                var textPlugin = $('.cms-draggable-1');
                var randomPlugin = $('.cms-draggable-2');
                var helper = options.helper(null, textPlugin);

                options.start(null, { item: textPlugin, helper: helper });
                board.state = true;

                expect($('.cms-draggables.cms-hidden').length).toEqual(0);

                textPlugin.appendTo(randomPlugin.find('.cms-draggables'));
                options.update(null, { item: textPlugin, helper: helper });

                expect($('.cms-draggables.cms-hidden').length).toEqual(0);

                options.start(null, { item: textPlugin, helper: helper });
                board.state = true;

                expect($('.cms-draggables.cms-hidden').length).toEqual(0);

                textPlugin.appendTo($('.cms-dragarea-1').find('> .cms-draggables'));
                options.update(null, { item: textPlugin, helper: helper });

                expect($('.cms-draggables.cms-hidden').length).toEqual(1);
            });
        });

        describe('isAllowed', function () {
            it('returns false if CMS.API is locked', function () {
                CMS.API.locked = true;
                board.state = 'mock';
                expect(options.isAllowed()).toEqual(false);
                expect(board.state).toEqual('mock');
            });

            it('returns false if there is no item', function () {
                CMS.API.locked = false;
                board.state = 'mock';
                expect(options.isAllowed()).toEqual(false);
                expect(board.state).toEqual('mock');
            });

            it('returns false if item has no settings', function () {
                board.state = 'mock';
                expect(options.isAllowed(null, null, $('.cms-draggable-1'))).toEqual(false);
                expect(board.state).toEqual('mock');
            });

            it('returns false if parent cannot have children', function () {
                board.state = 'mock';
                var pluginStructure = $('.cms-draggable-1');
                var pluginEdit = $('.cms-plugin-1');
                var placeholder = $('.cms-draggables').eq(0);
                placeholder.parent().addClass('cms-draggable-disabled');
                $('.cms-placeholder-1').remove();
                pluginEdit.data('cms', { plugin_parent_restriction: [] });

                expect(options.isAllowed(placeholder, null, pluginStructure)).toEqual(false);
                expect(board.state).toEqual('mock');
            });

            it('returns false if parent is a clipboard', function () {
                board.state = 'mock';
                var pluginStructure = $('.cms-draggable-1');
                var pluginEdit = $('.cms-plugin-1');
                var placeholder = $('.cms-draggables').eq(0);
                placeholder.parent().addClass('cms-clipboard-containers');
                $('.cms-placeholder-1').remove();
                pluginEdit.data('cms', { plugin_parent_restriction: [] });

                expect(options.isAllowed(placeholder, null, pluginStructure)).toEqual(false);
                expect(board.state).toEqual('mock');
            });

            describe('bounds of a place we put current plugin in', function () {
                it('uses placeholder bounds', function () {
                    board.state = 'mock';
                    var pluginStructure = $('.cms-draggable-1');
                    var placeholder = $('.cms-dragarea-1 > .cms-draggables');
                    var placeholderEdit = $('.cms-placeholder-1');
                    pluginStructure.data('cms', { plugin_parent_restriction: [] });
                    placeholderEdit.data('cms', { plugin_restriction: ['OnlyThisPlugin'] });

                    expect(options.isAllowed(placeholder, null, pluginStructure)).toEqual(false);
                    expect(board.state).toEqual(false);
                });

                it('uses placeholder bounds', function () {
                    board.state = 'mock';
                    var pluginStructure = $('.cms-draggable-1');
                    var placeholder = $('.cms-dragarea-1 > .cms-draggables');
                    var placeholderEdit = $('.cms-placeholder-1');
                    pluginStructure.data('cms', { plugin_parent_restriction: [], plugin_type: 'OnlyThisPlugin' });
                    placeholderEdit.data('cms', { plugin_restriction: ['OnlyThisPlugin'] });

                    expect(options.isAllowed(placeholder, null, pluginStructure)).toEqual(true);
                    expect(board.state).toEqual(true);
                });

                it('uses plugin bounds if pasted into the plugin', function () {
                    board.state = 'mock';
                    var pluginStructure = $('.cms-draggable-1');
                    var parentPluginStructure = $('.cms-draggable-2');
                    var placeholder = $('.cms-draggable-2 > .cms-draggables');
                    var placeholderEdit = $('.cms-placeholder-1');

                    pluginStructure.appendTo(parentPluginStructure.find('> .cms-draggables'));

                    pluginStructure.data('cms', { plugin_parent_restriction: [], plugin_type: 'OtherPlugin' });
                    parentPluginStructure.data('cms', { plugin_restriction: ['OnlyThisPlugin'] });
                    placeholderEdit.data('cms', { plugin_restriction: ['OnlyThisPlugin'] });

                    expect(options.isAllowed(placeholder, null, $('.cms-draggable-1'))).toEqual(false);
                    expect(board.state).toEqual(false);
                });

                it('uses plugin bounds if pasted into the plugin', function () {
                    board.state = 'mock';
                    var pluginStructure = $('.cms-draggable-1');
                    var parentPluginStructure = $('.cms-draggable-2');
                    var placeholder = $('.cms-draggable-2 > .cms-draggables');
                    var placeholderEdit = $('.cms-placeholder-1');

                    pluginStructure.appendTo(parentPluginStructure.find('> .cms-draggables'));

                    pluginStructure.data('cms', { plugin_parent_restriction: [], plugin_type: 'OtherPlugin' });
                    parentPluginStructure.data('cms', { plugin_restriction: ['OnlyThisPlugin'] });
                    placeholderEdit.data('cms', { plugin_restriction: ['OtherPlugin'] });

                    expect(options.isAllowed(placeholder, null, $('.cms-draggable-1'))).toEqual(false);
                    expect(board.state).toEqual(false);
                });

                it('uses plugin bounds if pasted into the plugin', function () {
                    board.state = 'mock';
                    var pluginStructure = $('.cms-draggable-1');
                    var parentPluginStructure = $('.cms-draggable-2');
                    var placeholder = $('.cms-draggable-2 > .cms-draggables');
                    var placeholderEdit = $('.cms-placeholder-1');

                    pluginStructure.appendTo(parentPluginStructure.find('> .cms-draggables'));

                    pluginStructure.data('cms', { plugin_parent_restriction: [], plugin_type: 'OtherPlugin' });
                    parentPluginStructure.data('cms', { plugin_restriction: [] });
                    placeholderEdit.data('cms', { plugin_restriction: ['OnlyThisPlugin'] });

                    expect(options.isAllowed(placeholder, null, $('.cms-draggable-1'))).toEqual(true);
                    expect(board.state).toEqual(true);
                });

                it('uses placeholderParent bounds', function () {
                    board.state = 'mock';
                    var pluginStructure = $('.cms-draggable-1');
                    var parentPluginStructure = $('.cms-draggable-2');
                    var placeholder = $('.cms-draggable-2 > .cms-draggables');
                    var placeholderEdit = $('.cms-placeholder-1');

                    pluginStructure.appendTo(parentPluginStructure.find('> .cms-draggables'));

                    pluginStructure.data('cms', { plugin_parent_restriction: [], plugin_type: 'OtherPlugin' });
                    parentPluginStructure.data('cms', { plugin_restriction: [] });
                    placeholderEdit.data('cms', { plugin_restriction: ['OnlyThisPlugin'] });

                    // it's important that placeholder is used, and not .cms-draggable-1
                    expect(options.isAllowed($('.cms-draggable-1'), placeholder, $('.cms-draggable-1'))).toEqual(true);
                    expect(board.state).toEqual(true);
                });
            });

            describe('parent bonds of the plugin', function () {
                it('respects parent bounds of the plugin', function () {
                    board.state = 'mock';
                    var pluginStructure = $('.cms-draggable-1');
                    var parentPluginStructure = $('.cms-draggable-2');
                    var placeholder = $('.cms-draggable-2 > .cms-draggables');
                    var placeholderEdit = $('.cms-placeholder-1');

                    pluginStructure.appendTo(parentPluginStructure.find('> .cms-draggables'));

                    pluginStructure.data('cms', {
                        plugin_parent_restriction: ['TestPlugin'],
                        plugin_type: 'OtherPlugin'
                    });
                    parentPluginStructure.data('cms', { plugin_restriction: [], plugin_type: 'TestPlugin' });
                    placeholderEdit.data('cms', { plugin_restriction: ['OnlyThisPlugin'] });

                    expect(options.isAllowed(placeholder, null, $('.cms-draggable-1'))).toEqual(true);
                    expect(board.state).toEqual(true);
                });

                it('respects parent bounds of the plugin', function () {
                    board.state = 'mock';
                    var pluginStructure = $('.cms-draggable-1');
                    var parentPluginStructure = $('.cms-draggable-2');
                    var placeholder = $('.cms-draggable-2 > .cms-draggables');
                    var placeholderEdit = $('.cms-placeholder-1');

                    pluginStructure.appendTo(parentPluginStructure.find('> .cms-draggables'));

                    pluginStructure.data('cms', {
                        plugin_parent_restriction: ['TestPlugin'],
                        plugin_type: 'OtherPlugin'
                    });
                    parentPluginStructure.data('cms', { plugin_restriction: [], plugin_type: 'OtherType' });
                    placeholderEdit.data('cms', { plugin_restriction: ['OnlyThisPlugin'] });

                    expect(options.isAllowed(placeholder, null, $('.cms-draggable-1'))).toEqual(false);
                    expect(board.state).toEqual(false);
                });

                it('works around "0" parent restriction for PlaceholderPlugin', function () {
                    board.state = 'mock';
                    var pluginStructure = $('.cms-draggable-1');
                    var parentPluginStructure = $('.cms-draggable-2');
                    var placeholder = $('.cms-draggable-2 > .cms-draggables');
                    var placeholderEdit = $('.cms-placeholder-1');

                    pluginStructure.appendTo(parentPluginStructure.find('> .cms-draggables'));

                    pluginStructure.data('cms', { plugin_parent_restriction: ['0'], plugin_type: 'OtherPlugin' });
                    parentPluginStructure.data('cms', { plugin_restriction: [], plugin_type: 'OtherType' });
                    placeholderEdit.data('cms', { plugin_restriction: ['OnlyThisPlugin'] });

                    expect(options.isAllowed(placeholder, null, $('.cms-draggable-1'))).toEqual(true);
                    expect(board.state).toEqual(true);
                });
            });
        });
    });
});
