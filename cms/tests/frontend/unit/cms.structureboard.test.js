'use strict';
import StructureBoard from '../../../static/cms/js/modules/cms.structureboard';
import Plugin from '../../../static/cms/js/modules/cms.plugins';
var CMS = require('../../../static/cms/js/modules/cms.base').default;
var $ = require('jquery');
var keyboard = require('../../../static/cms/js/modules/keyboard').default;
var showLoader;
var hideLoader;

window.CMS = window.CMS || CMS;
CMS.StructureBoard = StructureBoard;
CMS.Plugin = Plugin;
CMS.API = CMS.API || {};
CMS.API.Helpers = StructureBoard.__GetDependency__('Helpers');
CMS.KEYS = StructureBoard.__GetDependency__('KEYS');
CMS.$ = $;

const pluginConstructor = jasmine.createSpy();
const originalPlugin = StructureBoard.__GetDependency__('Plugin');
class FakePlugin {
    constructor(container, opts) {
        this.options = opts;
        const el = $('<div></div>');

        el.data('cms', []);
        this.ui = {
            container: el
        };
        pluginConstructor(container, opts);
    }
}
FakePlugin._updateRegistry = jasmine.createSpy();
FakePlugin._updateClipboard = jasmine.createSpy().and.callFake(() => {
    originalPlugin._updateClipboard();
});
FakePlugin.aliasPluginDuplicatesMap = {};
FakePlugin._refreshPlugins = jasmine.createSpy().and.callFake(() => {
    originalPlugin._refreshPlugins();
});
FakePlugin.prototype._setupUI = jasmine.createSpy();
FakePlugin.prototype._ensureData = jasmine.createSpy();
FakePlugin.prototype._setGeneric = jasmine.createSpy();
FakePlugin.prototype._setPlaceholder = jasmine.createSpy();
FakePlugin.prototype._collapsables = jasmine.createSpy();
FakePlugin.prototype._setPluginContentEvents = jasmine.createSpy();
FakePlugin.prototype._setPluginStructureEvents = jasmine.createSpy();

describe('CMS.StructureBoard', function() {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    beforeEach(() => {
        CMS.API.Clipboard = {
            populate: jasmine.createSpy()
        };
        showLoader = jasmine.createSpy();
        hideLoader = jasmine.createSpy();
        StructureBoard.__Rewire__('showLoader', showLoader);
        StructureBoard.__Rewire__('hideLoader', hideLoader);
    });

    afterEach(() => {
        FakePlugin.aliasPluginDuplicatesMap = {};
        FakePlugin.prototype._setupUI.calls.reset();
        FakePlugin.prototype._ensureData.calls.reset();
        FakePlugin.prototype._setGeneric.calls.reset();
        FakePlugin.prototype._setPlaceholder.calls.reset();
        FakePlugin.prototype._collapsables.calls.reset();
        FakePlugin.prototype._setPluginContentEvents.calls.reset();
        FakePlugin.prototype._setPluginStructureEvents.calls.reset();
        FakePlugin._refreshPlugins.calls.reset();
        StructureBoard.__ResetDependency__('showLoader');
        StructureBoard.__ResetDependency__('hideLoader');
    });

    it('creates a StructureBoard class', function() {
        expect(CMS.StructureBoard).toBeDefined();
    });

    it('has public API', function() {
        expect(CMS.StructureBoard.prototype.show).toEqual(jasmine.any(Function));
        expect(CMS.StructureBoard.prototype.hide).toEqual(jasmine.any(Function));
        expect(CMS.StructureBoard.prototype.getId).toEqual(jasmine.any(Function));
        expect(CMS.StructureBoard.prototype.getIds).toEqual(jasmine.any(Function));
    });

    describe('instance', function() {
        var board;
        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.settings = {
                mode: 'edit'
            };
            CMS.config = {
                settings: {
                    mode: 'edit',
                    structure: 'structure'
                },
                mode: 'edit'
            };
            $(function() {
                CMS.StructureBoard._initializeGlobalHandlers();
                jasmine.clock().install();
                board = new CMS.StructureBoard();
                done();
            });
        });

        afterEach(function() {
            jasmine.clock().uninstall();
            fixture.cleanup();
        });

        it('has ui', function() {
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
            expect(Object.keys(board.ui).length).toEqual(14);
        });

        it('has no options', function() {
            expect(board.options).not.toBeDefined();
        });

        it('applies correct classes to empty placeholder dragareas', function() {
            $('.cms-dragarea').removeClass('cms-dragarea-empty');
            board = new CMS.StructureBoard();
            expect('.cms-dragarea-1').not.toHaveClass('cms-dragarea-empty');
            expect('.cms-dragarea-2').toHaveClass('cms-dragarea-empty');
            expect('.cms-dragarea-10').toHaveClass('cms-dragarea-empty');
        });

        it('initially shows or hides board based on settings', function() {
            spyOn(CMS.StructureBoard.prototype, 'show');
            spyOn(CMS.StructureBoard.prototype, 'hide');

            expect(CMS.config.settings.mode).toEqual('edit');
            board = new CMS.StructureBoard();
            expect(board.show).not.toHaveBeenCalled();
            expect(board.hide).toHaveBeenCalled();
        });

        it('initially shows or hides board based on settings 2', function() {
            spyOn(CMS.StructureBoard.prototype, 'show');
            spyOn(CMS.StructureBoard.prototype, 'hide');

            CMS.config.settings.mode = 'structure';
            board = new CMS.StructureBoard();
            expect(board.show).toHaveBeenCalled();
            expect(board.hide).not.toHaveBeenCalled();
        });

        it('does not show or hide structureboard if there are no dragareas', function() {
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

        it('does not show or hide structureboard if there is no board mode switcher', function() {
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

        it('enables board mode switcher if there are placeholders', function() {
            expect(board.ui.placeholders.length > 0).toEqual(true);
            board.ui.toolbarModeSwitcher.find('.cms-btn').addClass('cms-btn-disabled');

            new CMS.StructureBoard();

            jasmine.clock().tick(100);

            expect(board.ui.toolbarModeSwitcher.find('.cms-btn')).not.toHaveClass('cms-btn-disabled');
        });

        it('does not enable board mode switcher if there are no placeholders', function() {
            expect(board.ui.placeholders.length > 0).toEqual(true);
            expect(board.ui.dragareas.length > 0).toEqual(true);

            board.ui.placeholders.remove();
            board.ui.dragareas.remove();
            board.ui.toolbarModeSwitcher.find('.cms-btn').addClass('cms-btn-disabled');

            board = new CMS.StructureBoard();
            expect(board.ui.placeholders.length).toEqual(0);
            expect(board.ui.dragareas.length).toEqual(0);

            jasmine.clock().tick(100);

            expect(board.ui.toolbarModeSwitcher.find('.cms-btn')).toHaveClass('cms-btn-disabled');
        });

        it('sets loaded content and structure flags if it is a legacy renderer', () => {
            CMS.config.settings.legacy_mode = true;
            board = new CMS.StructureBoard();
            expect(board._loadedStructure).toEqual(true);
            expect(board._loadedContent).toEqual(true);
        });
    });

    describe('.show()', function() {
        var board;
        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.settings = {
                mode: 'edit'
            };
            CMS.API.Toolbar = {
                _refreshMarkup: jasmine.createSpy()
            };
            CMS.config = {
                settings: {
                    mode: 'edit',
                    structure: 'structure'
                },
                mode: 'edit'
            };
            $(function() {
                spyOn(CMS.API.Helpers, 'setSettings').and.callFake(function(input) {
                    return input;
                });
                CMS.StructureBoard._initializeGlobalHandlers();
                board = new CMS.StructureBoard();
                spyOn(board, '_loadStructure').and.returnValue(Promise.resolve());
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it('shows the board', function(done) {
            spyOn(board, '_showBoard').and.callThrough();
            expect(board.ui.container).not.toBeVisible();
            board.show().then(function() {
                expect(board.ui.container).toBeVisible();
                expect(board._showBoard).toHaveBeenCalled();
                done();
            });
        });

        it('does not show the board if we are viewing published page', function(done) {
            CMS.config.mode = 'live';
            spyOn(board, '_showBoard').and.callThrough();
            expect(board.ui.container).not.toBeVisible();
            board.show().then(r => {
                expect(r).toEqual(false);
                expect(board.ui.container).not.toBeVisible();
                expect(board._showBoard).not.toHaveBeenCalled();
                done();
            });
        });

        it('highlights correct trigger', function(done) {
            expect(board.ui.toolbarModeLinks).not.toHaveClass('cms-btn-active');
            board.show().then(() => {
                expect(board.ui.toolbarModeLinks).toHaveClass('cms-btn-active');
                done();
            });
        });

        it('adds correct classes to the root of the document', function(done) {
            board.ui.html.removeClass('cms-structure-mode-structure');
            expect(board.ui.html).not.toHaveClass('cms-structure-mode-structure');
            board.show().then(() => {
                expect(board.ui.html).toHaveClass('cms-structure-mode-structure');
                done();
            });
        });

        it('does set state through settings', function(done) {
            CMS.API.Helpers.setSettings.and.callFake(function(input) {
                return input;
            });
            expect(CMS.settings.mode).toEqual('edit');
            board.show().then(() => {
                expect(CMS.settings.mode).toEqual('structure');
                expect(CMS.API.Helpers.setSettings).toHaveBeenCalled();
                done();
            });
        });

        it('saves the state in the url');
    });

    describe('highlights', function() {
        var board;
        beforeEach(function(done) {
            fixture.load('plugins.html', 'clipboard.html');
            CMS.settings = {
                mode: 'edit'
            };
            CMS.config = {
                settings: {
                    mode: 'edit',
                    structure: 'structure'
                },
                mode: 'edit'
            };
            $(function() {
                spyOn(CMS.API.Helpers, 'setSettings').and.callFake(function(input) {
                    return input;
                });
                CMS.API.Tooltip = {
                    domElem: {
                        is: function() {
                            return true;
                        },
                        data: function() {
                            return 1;
                        }
                    }
                };
                CMS.StructureBoard._initializeGlobalHandlers();
                board = new CMS.StructureBoard();
                spyOn(board, 'show').and.returnValue(Promise.resolve());
                spyOn(board, 'hide').and.returnValue(Promise.resolve());
                spyOn(Plugin, '_highlightPluginStructure');
                spyOn(Plugin, '_highlightPluginContent');
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        describe('._showAndHighlightPlugin()', function() {
            it('returns false if tooltip does not exist', function(done) {
                CMS.API.Tooltip = false;
                board._showAndHighlightPlugin().then(r => {
                    expect(r).toEqual(false);
                    expect(board.show).not.toHaveBeenCalled();
                    done();
                });
            });

            it('returns false if in live mode', function(done) {
                CMS.config.mode = 'live';
                board._showAndHighlightPlugin().then(r => {
                    expect(r).toEqual(false);
                    expect(board.show).not.toHaveBeenCalled();
                    done();
                });
            });

            it('returns false if no plugin is hovered', function(done) {
                CMS.API.Tooltip.domElem.is = function() {
                    return false;
                };

                board._showAndHighlightPlugin().then(r => {
                    expect(r).toEqual(false);
                    expect(board.show).not.toHaveBeenCalled();
                    done();
                });
            });

            it('shows board if plugin is hovered', function(done) {
                jasmine.clock().install();
                board._showAndHighlightPlugin().then(() => {
                    expect(board.show).toHaveBeenCalledTimes(1);
                    expect(Plugin._highlightPluginStructure).not.toHaveBeenCalled();
                    jasmine.clock().tick(201);
                    expect(Plugin._highlightPluginStructure).toHaveBeenCalledTimes(1);
                    jasmine.clock().uninstall();
                    done();
                });
            });
        });
    });

    describe('.hide()', function() {
        var board;
        beforeEach(function(done) {
            fixture.load('plugins.html');
            $(function() {
                CMS.settings = {
                    mode: 'edit'
                };
                CMS.config = {
                    settings: {
                        mode: 'edit',
                        structure: 'structure'
                    },
                    mode: 'edit'
                };
                spyOn(CMS.API.Helpers, 'setSettings').and.callFake(function(input) {
                    return input;
                });
                CMS.StructureBoard._initializeGlobalHandlers();
                board = new CMS.StructureBoard();
                spyOn(board, '_loadContent').and.returnValue(Promise.resolve());
                spyOn(board, '_loadStructure').and.returnValue(Promise.resolve());
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it('hides the board', function(done) {
            spyOn(board, '_hideBoard').and.callThrough();
            board
                .show()
                .then(() => {
                    expect(board.ui.container).toBeVisible();

                    return board.hide();
                })
                .then(() => {
                    expect(board.ui.container).not.toBeVisible();
                    expect(board._hideBoard).toHaveBeenCalled();
                    done();
                });
        });

        it('does not hide the board if we are viewing published page', function() {
            CMS.config.mode = 'live';
            spyOn(board, '_hideBoard');
            expect(board.ui.container).not.toBeVisible();
            expect(board.hide()).toEqual(false);
            expect(board.ui.container).not.toBeVisible();
            expect(board._hideBoard).not.toHaveBeenCalled();
        });

        it('deactivates the button', function(done) {
            board.hide().then(() => {
                expect(board.ui.toolbarModeLinks).not.toHaveClass('cms-btn-active');
                done();
            });
        });

        it('does not remember the state in localstorage', function() {
            board.show();
            expect(CMS.settings.mode).toEqual('structure');
            CMS.API.Helpers.setSettings.and.callFake(function(input) {
                return input;
            });
            CMS.API.Helpers.setSettings.calls.reset();
            board.hide();
            expect(CMS.settings.mode).toEqual('edit');
            expect(CMS.API.Helpers.setSettings).not.toHaveBeenCalled();
        });

        it('remembers the state in the url');

        it('triggers `resize` event on the window', function(done) {
            var spy = jasmine.createSpy();

            board
                .show()
                .then(() => {
                    $(window).on('resize', spy);
                    return board.hide();
                })
                .then(() => {
                    expect(spy).toHaveBeenCalledTimes(1);
                    $(window).off('resize', spy);
                    done();
                });
        });
    });

    describe('.getId()', function() {
        var board;
        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.settings = {
                mode: 'edit'
            };
            CMS.config = {
                settings: {
                    mode: 'edit',
                    structure: 'structure'
                },
                mode: 'edit'
            };
            $(function() {
                CMS.StructureBoard._initializeGlobalHandlers();
                board = new CMS.StructureBoard();
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it('returns the id of passed element', function() {
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
            ].forEach(function(obj) {
                expect(board.getId($('<div class="' + obj.from + '"></div>'))).toEqual(obj.result);
            });
        });

        it('returns null if element is of non supported "type"', function() {
            [
                {
                    from: 'cannot determine',
                    result: null
                },
                {
                    from: 'cms-not-supported cms-not-supported-1',
                    result: null
                }
            ].forEach(function(obj) {
                expect(board.getId($('<div class="' + obj.from + '"></div>'))).toEqual(obj.result);
            });
        });

        it('returns false if element does not exist', function() {
            expect(board.getId()).toEqual(false);
            expect(board.getId(null)).toEqual(false);
            expect(board.getId($('.non-existent'))).toEqual(false);
            expect(board.getId([])).toEqual(false);
        });

        it('fails if classname string is incorrect', function() {
            expect(board.getId.bind(board, $('<div class="cms-plugin"></div>'))).toThrow();
            expect(board.getId($('<div class="cms-plugin fail cms-plugin-10"></div>'))).toEqual('fail');
        });
    });

    describe('.getIds()', function() {
        var board;
        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.settings = {
                mode: 'edit'
            };
            CMS.config = {
                settings: {
                    mode: 'edit',
                    structure: 'structure'
                },
                mode: 'edit'
            };
            $(function() {
                CMS.StructureBoard._initializeGlobalHandlers();
                board = new CMS.StructureBoard();
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it('returns the array of ids of passed collection', function() {
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
            ].forEach(function(obj) {
                var collection = $();
                obj.from.forEach(function(className) {
                    collection = collection.add($('<div class="' + className + '"></div>'));
                });
                expect(board.getIds(collection)).toEqual(obj.result);
            });
            expect(board.getId).toHaveBeenCalled();
        });
    });

    describe('._setupModeSwitcher()', function() {
        var board;
        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.settings = {
                mode: 'edit'
            };
            CMS.config = {
                settings: {
                    mode: 'edit',
                    structure: 'structure'
                },
                mode: 'edit'
            };
            $(function() {
                spyOn(keyboard, 'bind');
                CMS.StructureBoard._initializeGlobalHandlers();
                board = new CMS.StructureBoard();
                spyOn(board, 'show').and.callFake(function() {
                    CMS.settings.mode = 'structure';
                });
                spyOn(board, 'hide').and.callFake(function() {
                    CMS.settings.mode = 'edit';
                });
                done();
            });
        });

        afterEach(function() {
            board.ui.doc.off('keydown.cms.structureboard.switcher');
            fixture.cleanup();
        });

        it('sets up click handler to show board', function() {
            var showTrigger = board.ui.toolbarModeLinks;
            expect(showTrigger).toHandle(board.click);

            CMS.settings.mode = 'structure';

            showTrigger.trigger(board.click);

            expect(board.show).not.toHaveBeenCalled();

            CMS.settings.mode = 'edit';

            showTrigger.trigger(board.click);
            expect(board.show).toHaveBeenCalledTimes(1);
        });

        it('sets up click handler to hide board', function() {
            var hideTrigger = board.ui.toolbarModeLinks;
            expect(hideTrigger).toHandle(board.click);

            CMS.settings.mode = 'edit';

            hideTrigger.trigger(board.click);

            expect(board.hide).not.toHaveBeenCalled();

            CMS.settings.mode = 'structure';

            hideTrigger.trigger(board.click);
            expect(board.hide).toHaveBeenCalledTimes(1);
        });

        it('sets up shortcuts to toggle board', function() {
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

        it('does not setup key binds if toggler is not availabe', function() {
            keyboard.bind.calls.reset();
            board.ui.toolbarModeSwitcher.remove();

            CMS.StructureBoard._initializeGlobalHandlers();
            board = new CMS.StructureBoard();
            spyOn(board, 'show').and.callFake(function() {
                CMS.settings.mode = 'structure';
            });
            spyOn(board, 'hide').and.callFake(function() {
                CMS.settings.mode = 'edit';
            });

            expect(keyboard.bind).not.toHaveBeenCalled();
        });

        it('does not setup key binds if toggler is not visible (there are no placeholders)', function() {
            keyboard.bind.calls.reset();

            board.ui.placeholders.remove();
            board.ui.dragareas.remove();
            board.ui.toolbarModeSwitcher.find('.cms-btn').addClass('cms-btn-disabled');
            CMS.StructureBoard._initializeGlobalHandlers();
            board = new CMS.StructureBoard();

            spyOn(board, 'show').and.callFake(function() {
                CMS.settings.mode = 'structure';
            });
            spyOn(board, 'hide').and.callFake(function() {
                CMS.settings.mode = 'edit';
            });

            expect(keyboard.bind).not.toHaveBeenCalled();
        });
    });

    describe('._toggleStructureBoard()', function() {
        var board;
        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.settings = {
                mode: 'edit'
            };
            CMS.config = {
                settings: {
                    mode: 'edit',
                    structure: 'structure'
                },
                mode: 'edit'
            };
            $(function() {
                spyOn(keyboard, 'bind');
                CMS.StructureBoard._initializeGlobalHandlers();
                board = new CMS.StructureBoard();
                spyOn(board, 'show').and.callFake(function() {
                    CMS.settings.mode = 'structure';
                });
                spyOn(board, 'hide').and.callFake(function() {
                    CMS.settings.mode = 'edit';
                });
                spyOn(board, '_showAndHighlightPlugin').and.returnValue({
                    then() {}
                });
                done();
            });
        });

        it('shows structureboard', function() {
            board._toggleStructureBoard();
            expect(board.show).toHaveBeenCalledTimes(1);
            expect(board.hide).not.toHaveBeenCalled();
        });

        it('hides strucrueboard', function() {
            CMS.settings.mode = 'structure';
            board._toggleStructureBoard();
            expect(board.show).not.toHaveBeenCalled();
            expect(board.hide).toHaveBeenCalledTimes(1);
        });

        it('shows structureboard and highlights plugin', function() {
            CMS.settings.mode = 'edit';
            board._toggleStructureBoard({ useHoveredPlugin: true });
            expect(board._showAndHighlightPlugin).toHaveBeenCalledTimes(1);
        });

        it('does not show structureboard and highlights plugin if it is open already', function() {
            CMS.settings.mode = 'structure';
            board._toggleStructureBoard({ useHoveredPlugin: true });
            expect(board._showAndHighlightPlugin).not.toHaveBeenCalled();
        });
    });

    describe('._drag()', function() {
        var board;
        var options;
        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.settings = {
                mode: 'structure'
            };
            CMS.config = {
                settings: {
                    mode: 'structure',
                    structure: 'structure'
                },
                mode: 'structure'
            };
            $(function() {
                CMS.StructureBoard._initializeGlobalHandlers();
                board = new CMS.StructureBoard();
                board._drag();
                options = board.ui.sortables.nestedSortable('option');
                board.show().then(() => {
                    done();
                });
            });
        });

        afterEach(function() {
            board.ui.doc.off('keyup.cms.interrupt');
            fixture.cleanup();
        });

        it('initializes nested sortable', function() {
            options = board.ui.sortables.nestedSortable('option');
            expect(options).toEqual(
                jasmine.objectContaining({
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
                })
            );
        });

        it('adds event handler for cms-structure-update to actualize empty placeholders', function() {
            if (!CMS.$._data(board.ui.sortables[0]).events['cms-structure-update'][0].handler.name) {
                pending();
            }
            expect(board.ui.sortables).toHandle('cms-structure-update');
            // cheating here a bit
            expect(CMS.$._data(board.ui.sortables[0]).events['cms-structure-update'][0].handler.name).toEqual(
                'actualizePlaceholders'
            );
        });

        it('defines how draggable helper is created', function() {
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

        describe('start', function() {
            it('sets data-touch-action attribute', function() {
                expect(board.ui.content).toHaveAttr('data-touch-action', 'pan-y');
                options.start({}, { item: $('<div></div>'), helper: $('<div></div>') });
                expect(board.ui.content).toHaveAttr('data-touch-action', 'none');
            });

            it('sets dragging state', function() {
                expect(board.dragging).toEqual(false);
                options.start({}, { item: $('<div></div>'), helper: $('<div></div>') });
                expect(board.dragging).toEqual(true);
            });

            it('actualizes empty placeholders', function() {
                var firstPlaceholder = board.ui.dragareas.eq(0);
                var firstPlaceholderCopyAll = firstPlaceholder.find(
                    '.cms-dragbar .cms-submenu-item:has(a[data-rel="copy"]):first'
                );
                var secondPlaceholder = board.ui.dragareas.eq(1);
                var secondPlaceholderCopyAll = secondPlaceholder.find(
                    '.cms-dragbar .cms-submenu-item:has(a[data-rel="copy"]):first'
                );

                expect(firstPlaceholder).toHaveClass('cms-dragarea-empty');
                expect(firstPlaceholderCopyAll).toHaveClass('cms-submenu-item-disabled');
                expect(secondPlaceholder).not.toHaveClass('cms-dragarea-empty');
                expect(secondPlaceholderCopyAll).not.toHaveClass('cms-submenu-item-disabled');

                secondPlaceholder
                    .find('> .cms-draggables')
                    .contents()
                    .appendTo(firstPlaceholder.find('> .cms-draggables'));

                options.start({}, { item: $('<div></div>'), helper: $('<div></div>') });

                expect(firstPlaceholder).not.toHaveClass('cms-dragarea-empty');
                expect(firstPlaceholderCopyAll).not.toHaveClass('cms-submenu-item-disabled');
                expect(secondPlaceholder).toHaveClass('cms-dragarea-empty');
                expect(secondPlaceholderCopyAll).toHaveClass('cms-submenu-item-disabled');

                // now check that the plugin currently being dragged does not count
                // towards "plugins count"
                firstPlaceholder
                    .find('> .cms-draggables')
                    .contents()
                    .appendTo(secondPlaceholder.find('> .cms-draggables'));
                firstPlaceholder
                    .find('> .cms-draggables')
                    .append($('<div class="cms-draggable cms-draggable-is-dragging"></div>'));

                options.start({}, { item: $('<div></div>'), helper: $('<div></div>') });

                expect(firstPlaceholder).toHaveClass('cms-dragarea-empty');
                expect(firstPlaceholderCopyAll).toHaveClass('cms-submenu-item-disabled');
                expect(secondPlaceholder).not.toHaveClass('cms-dragarea-empty');
                expect(secondPlaceholderCopyAll).not.toHaveClass('cms-submenu-item-disabled');
            });

            it('hides settings menu', function() {
                spyOn(CMS.Plugin, '_hideSettingsMenu');
                options.start({}, { item: $('<div></div>'), helper: $('<div></div>') });
                expect(CMS.Plugin._hideSettingsMenu).toHaveBeenCalledTimes(1);
            });

            it('shows all the empty sortables', function() {
                expect($('.cms-draggables.cms-hidden').length).toEqual(1);
                options.start({}, { item: $('<div></div>'), helper: $('<div></div>') });
                expect($('.cms-draggables.cms-hidden').length).toEqual(0);
            });

            it('adds appropriate classes on item without children and helper', function() {
                var item = $('<div class="cms-draggable"><div class="cms-dragitem">Some plugin</div></div>');
                var helper = options.helper(null, item);

                options.start(
                    {},
                    {
                        item: item,
                        helper: helper
                    }
                );

                expect(item).toHaveClass('cms-is-dragging');
                expect(helper).toHaveClass('cms-draggable-is-dragging');
            });

            it('adds appropriate classes on item with children', function() {
                var item = $(
                    '<div class="cms-draggable">' +
                        '<div class="cms-dragitem">Some plugin</div>' +
                        '<div class="cms-draggables">' +
                        '<div></div>' +
                        '</div>' +
                        '</div>'
                );
                var helper = options.helper(null, item);

                options.start(
                    {},
                    {
                        item: item,
                        helper: helper
                    }
                );

                expect(helper).toHaveClass('cms-draggable-stack');
            });

            it('sets up a handler for interrupting dragging with keyboard', function() {
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

        describe('beforeStop', function() {
            it('sets dragging state to false', function() {
                board.dragging = true;
                options.beforeStop(null, { item: $('<div></div>') });
                expect(board.dragging).toEqual(false);
            });

            it('removes classes', function() {
                var item = $('<div class="cms-is-dragging cms-draggable-stack"></div>');
                options.beforeStop(null, { item: item });
                expect(item).not.toHaveClass('cms-is-dragging');
                expect(item).not.toHaveClass('cms-draggable-stack');
            });

            it('unbinds interrupt event', function() {
                var spy = jasmine.createSpy();
                board.ui.doc.on('keyup.cms.interrupt', spy);
                options.beforeStop(null, { item: $('<div></div>') });
                board.ui.doc.trigger('keyup.cms.interrupt');
                expect(spy).not.toHaveBeenCalled();
                expect(board.ui.doc).not.toHandle('keyup.cms.interrupt');
            });

            it('resets data-touch-action attribute', function() {
                board.ui.content.removeAttr('data-touch-action');
                options.beforeStop(null, { item: $('<div></div>') });
                expect(board.ui.content).toHaveAttr('data-touch-action', 'pan-y');
            });
        });

        describe('update', function() {
            it('returns false if it is not possible to update', function() {
                board.state = false;
                expect(options.update()).toEqual(false);
            });

            it('actualizes collapsible status', function() {
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

            it('returns false if we moved plugin inside same container and the event is fired on the container', () => {
                var textPlugin = $('.cms-draggable-1');
                var helper = options.helper(null, textPlugin);
                var placeholderDraggables = $('.cms-dragarea-1').find('> .cms-draggables');

                // and one more time
                options.start(null, { item: textPlugin, helper: helper });
                board.state = true;

                textPlugin.prependTo(placeholderDraggables);
                expect(options.update.bind(textPlugin)(null, { item: textPlugin, helper: helper })).toEqual(false);
            });

            it('triggers event on the plugin when necessary', function() {
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

            it('triggers event on the plugin in clipboard', function() {
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

            it('actualizes empty placeholders', function() {
                var firstPlaceholder = board.ui.dragareas.eq(0);
                var firstPlaceholderCopyAll = firstPlaceholder.find(
                    '.cms-dragbar .cms-submenu-item:has(a[data-rel="copy"]):first'
                );
                var secondPlaceholder = board.ui.dragareas.eq(1);
                var secondPlaceholderCopyAll = secondPlaceholder.find(
                    '.cms-dragbar .cms-submenu-item:has(a[data-rel="copy"]):first'
                );

                expect(firstPlaceholder).toHaveClass('cms-dragarea-empty');
                expect(firstPlaceholderCopyAll).toHaveClass('cms-submenu-item-disabled');
                expect(secondPlaceholder).not.toHaveClass('cms-dragarea-empty');
                expect(secondPlaceholderCopyAll).not.toHaveClass('cms-submenu-item-disabled');

                options.start({}, { item: $('<div></div>'), helper: $('<div></div>') });

                secondPlaceholder
                    .find('> .cms-draggables')
                    .contents()
                    .appendTo(firstPlaceholder.find('> .cms-draggables'));

                board.state = true;
                options.update({}, { item: $('<div class="cms-plugin-1"></div>'), helper: $('<div></div>') });

                expect(firstPlaceholder).not.toHaveClass('cms-dragarea-empty');
                expect(firstPlaceholderCopyAll).not.toHaveClass('cms-submenu-item-disabled');
                expect(secondPlaceholder).toHaveClass('cms-dragarea-empty');
                expect(secondPlaceholderCopyAll).toHaveClass('cms-submenu-item-disabled');

                // now check that the plugin currently being dragged does not count
                // towards "plugins count"
                firstPlaceholder
                    .find('> .cms-draggables')
                    .contents()
                    .appendTo(secondPlaceholder.find('> .cms-draggables'));
                firstPlaceholder
                    .find('> .cms-draggables')
                    .append($('<div class="cms-draggable cms-draggable-is-dragging"></div>'));

                options.update({}, { item: $('<div class="cms-plugin-1"></div>'), helper: $('<div></div>') });

                expect(firstPlaceholder).toHaveClass('cms-dragarea-empty');
                expect(firstPlaceholderCopyAll).toHaveClass('cms-submenu-item-disabled');
                expect(secondPlaceholder).not.toHaveClass('cms-dragarea-empty');
                expect(secondPlaceholderCopyAll).not.toHaveClass('cms-submenu-item-disabled');
            });

            it('hides empty sortables', function() {
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

        describe('isAllowed', function() {
            it('returns false if CMS.API is locked', function() {
                CMS.API.locked = true;
                board.state = 'mock';
                expect(options.isAllowed()).toEqual(false);
                expect(board.state).toEqual('mock');
            });

            it('returns false if there is no item', function() {
                CMS.API.locked = false;
                board.state = 'mock';
                expect(options.isAllowed()).toEqual(false);
                expect(board.state).toEqual('mock');
            });

            it('returns false if item has no settings', function() {
                board.state = 'mock';
                expect(options.isAllowed(null, null, $('.cms-draggable-1'))).toEqual(false);
                expect(board.state).toEqual('mock');
            });

            it('returns false if parent cannot have children', function() {
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

            it('returns false if parent is a clipboard', function() {
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

            describe('bounds of a place we put current plugin in', function() {
                it('uses placeholder bounds', function() {
                    board.state = 'mock';
                    var pluginStructure = $('.cms-draggable-1');
                    var placeholder = $('.cms-dragarea-1 > .cms-draggables');
                    var placeholderEdit = $('.cms-placeholder-1');
                    pluginStructure.data('cms', { plugin_parent_restriction: [] });
                    placeholderEdit.data('cms', { plugin_restriction: ['OnlyThisPlugin'] });

                    expect(options.isAllowed(placeholder, null, pluginStructure)).toEqual(false);
                    expect(board.state).toEqual(false);
                });

                it('uses placeholder bounds', function() {
                    board.state = 'mock';
                    var pluginStructure = $('.cms-draggable-1');
                    var placeholder = $('.cms-dragarea-1 > .cms-draggables');
                    var placeholderEdit = $('.cms-placeholder-1');
                    pluginStructure.data('cms', { plugin_parent_restriction: [], plugin_type: 'OnlyThisPlugin' });
                    placeholderEdit.data('cms', { plugin_restriction: ['OnlyThisPlugin'] });

                    expect(options.isAllowed(placeholder, null, pluginStructure)).toEqual(true);
                    expect(board.state).toEqual(true);
                });

                it('uses plugin bounds if pasted into the plugin', function() {
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

                it('uses plugin bounds if pasted into the plugin', function() {
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

                it('uses plugin bounds if pasted into the plugin', function() {
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

                it('uses placeholderParent bounds', function() {
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

            describe('parent bonds of the plugin', function() {
                it('respects parent bounds of the plugin', function() {
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

                it('respects parent bounds of the plugin', function() {
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

                it('works around "0" parent restriction for PlaceholderPlugin', function() {
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

    describe('invalidateState', () => {
        let board;

        beforeEach(done => {
            fixture.load('plugins.html');
            board = new CMS.StructureBoard();
            StructureBoard.__Rewire__('Plugin', FakePlugin);
            spyOn(StructureBoard, 'actualizePluginCollapseStatus');
            spyOn(StructureBoard, 'actualizePlaceholders');
            spyOn(StructureBoard, 'actualizePluginsCollapsibleStatus');
            spyOn(Plugin, '_updateClipboard');
            spyOn(board, '_drag');
            setTimeout(() => {
                done();
            }, 20);
        });

        afterEach(() => {
            fixture.cleanup();
            StructureBoard.__ResetDependency__('Plugin');
        });

        describe('itself', () => {
            beforeEach(() => {
                spyOn(CMS.API.Helpers, 'reloadBrowser');
                CMS.API.Toolbar = {
                    _refreshMarkup: jasmine.createSpy()
                };
                spyOn(board, 'handleAddPlugin');
                spyOn(board, 'handleEditPlugin');
                spyOn(board, 'handleDeletePlugin');
                spyOn(board, 'handleClearPlaceholder');
                spyOn(board, 'handleCopyPlugin');
                spyOn(board, 'handleMovePlugin');
                spyOn(board, 'handleCutPlugin');
                spyOn(board, '_loadToolbar').and.returnValue({
                    done() {
                        return {
                            fail() {}
                        };
                    }
                });
                spyOn(board, '_requestMode').and.returnValue({
                    done() {
                        return {
                            fail() {}
                        };
                    }
                });
                spyOn(board, 'refreshContent');
            });

            it('delegates to correct methods', () => {
                board.invalidateState('ADD', { randomData: 1 });
                expect(board.handleAddPlugin).toHaveBeenCalledWith({ randomData: 1 });

                board.invalidateState('MOVE', { randomData: 1 });
                expect(board.handleMovePlugin).toHaveBeenCalledWith({ randomData: 1 });

                board.invalidateState('COPY', { randomData: 1 });
                expect(board.handleCopyPlugin).toHaveBeenCalledWith({ randomData: 1 });

                board.invalidateState('PASTE', { randomData: 1 });
                expect(board.handleMovePlugin).toHaveBeenCalledWith({ randomData: 1 });

                board.invalidateState('CUT', { randomData: 1 });
                expect(board.handleCutPlugin).toHaveBeenCalledWith({ randomData: 1 });

                board.invalidateState('EDIT', { randomData: 1 });
                expect(board.handleEditPlugin).toHaveBeenCalledWith({ randomData: 1 });

                board.invalidateState('DELETE', { randomData: 1 });
                expect(board.handleDeletePlugin).toHaveBeenCalledWith({ randomData: 1 });

                board.invalidateState('CLEAR_PLACEHOLDER', { randomData: 1 });
                expect(board.handleClearPlaceholder).toHaveBeenCalledWith({ randomData: 1 });

                expect(board.handleAddPlugin).toHaveBeenCalledTimes(1);
                expect(board.handleCopyPlugin).toHaveBeenCalledTimes(1);
                expect(board.handleMovePlugin).toHaveBeenCalledTimes(2);
                expect(board.handleCutPlugin).toHaveBeenCalledTimes(1);
                expect(board.handleEditPlugin).toHaveBeenCalledTimes(1);
                expect(board.handleDeletePlugin).toHaveBeenCalledTimes(1);
                expect(board.handleClearPlaceholder).toHaveBeenCalledTimes(1);
            });

            it('reloads browser if there was no action', () => {
                board.invalidateState();
                expect(CMS.API.Helpers.reloadBrowser).toHaveBeenCalledWith();
                expect(board._loadToolbar).not.toHaveBeenCalled();
            });

            it('reloads toolbar if there is an action', () => {
                board.invalidateState('ADD', { randomData: 1 });
                board.invalidateState('MOVE', { randomData: 1 });
                board.invalidateState('COPY', { randomData: 1 });
                board.invalidateState('PASTE', { randomData: 1 });
                board.invalidateState('CUT', { randomData: 1 });
                board.invalidateState('EDIT', { randomData: 1 });
                board.invalidateState('DELETE', { randomData: 1 });
                board.invalidateState('CLEAR_PLACEHOLDER', { randomData: 1 });

                expect(board._loadToolbar).toHaveBeenCalledTimes(8);

                board.invalidateState('x');
                expect(board._loadToolbar).toHaveBeenCalledTimes(9);
            });

            it('refreshes markup if loading markup succeeds', () => {
                board._loadToolbar.and.returnValue({
                    done(fn) {
                        fn();
                        return {
                            fail() {}
                        };
                    }
                });

                board.invalidateState('x');
                expect(CMS.API.Toolbar._refreshMarkup).toHaveBeenCalled();
            });

            it('reloads if fails', () => {
                board._loadToolbar.and.returnValue({
                    done() {
                        return {
                            fail(fn) {
                                fn();
                            }
                        };
                    }
                });

                board.invalidateState('x');
                expect(CMS.API.Helpers.reloadBrowser).toHaveBeenCalled();
            });

            it('resets the requested content', () => {
                const args = ['random', 'stuff'];
                expect(CMS.settings.mode).toEqual('structure');
                board._loadedContent = false;
                board._requestMode.and.callFake(mode => {
                    expect(mode).toEqual('content');
                    return {
                        done(fn) {
                            fn(...args);
                            return { fail() {} };
                        }
                    };
                });

                board._requestcontent = '1';
                board.invalidateState('x');
                expect(board._requestcontent).toEqual(null);
                expect(board.refreshContent).not.toHaveBeenCalled();
            });

            it('refreshes content mode if needed', () => {
                const args = ['random', 'stuff'];
                expect(CMS.settings.mode).toEqual('structure');
                board._loadedContent = true;
                board._requestMode.and.callFake(mode => {
                    expect(mode).toEqual('content');
                    return {
                        done(fn) {
                            fn(...args);
                            return { fail() {} };
                        }
                    };
                });

                board.invalidateState('x');
                expect(board.refreshContent).toHaveBeenCalledWith('random');
            });

            it('reloads if it cannot refresh content', () => {
                const args = ['random', 'stuff'];
                expect(CMS.settings.mode).toEqual('structure');
                board._loadedContent = true;
                board._requestMode.and.callFake(mode => {
                    expect(mode).toEqual('content');
                    return {
                        done() {
                            return {
                                fail(fn) {
                                    fn(...args);
                                }
                            };
                        }
                    };
                });

                board.invalidateState('x');
                expect(CMS.API.Helpers.reloadBrowser).toHaveBeenCalledWith();
            });

            it('refreshes content if in content mode', () => {
                const args = ['random', 'stuff'];
                CMS.settings.mode = 'edit';
                board._loadedContent = true;
                board._requestMode.and.callFake(mode => {
                    expect(mode).toEqual('content');
                    expect(board._requestcontent).toEqual(null);
                    return {
                        done(fn) {
                            fn(...args);
                            return {
                                fail() {}
                            };
                        }
                    };
                });

                board.invalidateState('x');
                expect(board._requestMode).toHaveBeenCalledWith('content');
                expect(board.refreshContent).toHaveBeenCalledWith('random');
            });

            it('reloads if cant refresh content when in content mode', () => {
                const args = ['random', 'stuff'];
                CMS.settings.mode = 'edit';
                board._loadedContent = false;
                board._requestMode.and.callFake(mode => {
                    expect(mode).toEqual('content');
                    expect(board._requestcontent).toEqual(null);
                    return {
                        done() {
                            return {
                                fail(fn) {
                                    fn(...args);
                                }
                            };
                        }
                    };
                });

                board.invalidateState('x');
                expect(board._requestMode).toHaveBeenCalledWith('content');
                expect(CMS.API.Helpers.reloadBrowser).toHaveBeenCalledWith();
            });
        });

        describe('handleMovePlugin', () => {
            it('replaces markup with given one', () => {
                const data = {
                    plugin_parent: false,
                    plugin_id: 1,
                    html: '<div class="new-draggable"><div class="cms-draggables"></div></div>',
                    plugins: [{ plugin_id: 1, otherStuff: true }]
                };
                board.handleMovePlugin(data);

                expect($('.cms-draggable-1')).not.toExist();
                expect($('.new-draggable')).toExist();
                expect(StructureBoard.actualizePlaceholders).toHaveBeenCalled();
                expect(FakePlugin._updateRegistry).toHaveBeenCalledWith(data.plugins);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledTimes(1);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledWith(1);
                expect(board._drag).toHaveBeenCalled();
                expect(board.ui.sortables.filter('.new-draggable .cms-draggables')).toExist();
            });

            it('replaces markup with given one when parent is also provided', () => {
                const data = {
                    plugin_parent: 2,
                    plugin_id: 1,
                    html: `
                        <div class="new-draggable ">
                            <div class="cms-draggables"><div class="cms-draggable-1"></div></div>
                        </div>
                    `,
                    plugins: [{ plugin_id: 1, otherStuff: true }]
                };
                board.handleMovePlugin(data);

                expect($('.cms-draggable-1')).toExist();
                expect($('.cms-draggable-2')).not.toExist();
                expect($('.new-draggable')).toExist();
                expect(StructureBoard.actualizePlaceholders).toHaveBeenCalled();
                expect(FakePlugin._updateRegistry).toHaveBeenCalledWith(data.plugins);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledTimes(1);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledWith(1);
                expect(board._drag).toHaveBeenCalled();
                expect(board.ui.sortables.filter('.new-draggable .cms-draggables')).toExist();
            });

            it('replaces markup with given one when it is copying from language', () => {
                const data = {
                    target_placeholder_id: 2,
                    html: '<div class="new-draggable"><div class="cms-draggables"></div></div>',
                    plugins: [{ plugin_id: 1, otherStuff: true }]
                };
                board.handleMovePlugin(data);

                expect($('.cms-draggable-1')).toExist();
                expect($('.cms-draggable-2')).toExist();
                expect($('.new-draggable')).toExist();
                expect(StructureBoard.actualizePlaceholders).toHaveBeenCalled();
                expect(FakePlugin._updateRegistry).toHaveBeenCalledWith(data.plugins);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledTimes(1);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledWith(1);
                expect(board._drag).toHaveBeenCalled();
                expect(board.ui.sortables.filter('.cms-dragarea-2 .new-draggable .cms-draggables')).toExist();
            });

            it('handles top level move update when in same placeholder', () => {
                const data = {
                    placeholder_id: 1,
                    plugin_id: 2,
                    plugin_order: ['2', '1'],
                    html: `
                        <div class="cms-draggable cms-draggable-2 new-cms-draggable-2">
                        </div>
                    `,
                    plugins: [{ plugin_id: 2, otherStuff: true }, { plugin_id: 1, otherStuff: true }]
                };

                board.handleMovePlugin(data);

                expect($('.cms-draggable-1')).toExist();
                expect($('.cms-draggable-2')).toExist();
                expect(StructureBoard.actualizePlaceholders).toHaveBeenCalled();
                expect(FakePlugin._updateRegistry).toHaveBeenCalledWith(data.plugins);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledTimes(2);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledWith(1);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledWith(2);
                expect(board._drag).toHaveBeenCalled();
                expect($('.new-cms-draggable-2')).toExist();
                expect($('.cms-draggable-2').index()).toEqual(0); // account for "empty" message
                expect($('.cms-draggable-1').index()).toEqual(2);
            });

            it('handles top level move update when in same placeholder', () => {
                const data = {
                    placeholder_id: 1,
                    plugin_id: 1,
                    plugin_order: ['2', '1'],
                    html: `
                        <div class="cms-draggable cms-draggable-1 new-cms-draggable-1">
                        </div>
                    `,
                    plugins: [{ plugin_id: 2, otherStuff: true }, { plugin_id: 1, otherStuff: true }]
                };

                board.handleMovePlugin(data);

                expect($('.cms-draggable-1')).toExist();
                expect($('.cms-draggable-2')).toExist();
                expect(StructureBoard.actualizePlaceholders).toHaveBeenCalled();
                expect(FakePlugin._updateRegistry).toHaveBeenCalledWith(data.plugins);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledTimes(2);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledWith(1);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledWith(2);
                expect(board._drag).toHaveBeenCalled();
                expect($('.new-cms-draggable-1')).toExist();
                expect($('.cms-draggable-2').index()).toEqual(1);
                expect($('.cms-draggable-1').index()).toEqual(2);
            });
        });

        describe('handleAddPlugin', () => {
            it('replaces parent if provided', () => {
                const data = {
                    plugin_parent: 2,
                    plugin_id: 3,
                    structure: {
                        html: `
                            <div class="cms-draggable-2 new">
                                <div class="cms-draggables">
                                    <div class="cms-draggable-3 new-draggable">
                                        <div class="cms-draggables"></div>
                                    </div>
                                </div>
                            </div>
                        `,
                        plugins: [{ plugin_id: 2, otherStuff: true }, { plugin_id: 3, other_stuff: false }]
                    }
                };
                board.handleAddPlugin(data);

                expect($('.cms-draggable-2')).toHaveClass('new');
                expect($('.new-draggable')).toExist();
                expect(StructureBoard.actualizePlaceholders).toHaveBeenCalled();
                expect(FakePlugin._updateRegistry).toHaveBeenCalledWith(data.structure.plugins);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledTimes(2);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledWith(2);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledWith(3);
                expect(board._drag).toHaveBeenCalled();
                expect(board.ui.sortables.filter('.new-draggable .cms-draggables')).toExist();
            });

            it('appends to placeholder if no parent', () => {
                const data = {
                    plugin_parent: null,
                    placeholder_id: 2,
                    plugin_id: 3,
                    structure: {
                        html: `
                            <div class="cms-draggable-3 new-draggable">
                                <div class="cms-draggables"></div>
                            </div>
                        `,
                        plugins: [{ plugin_id: 3, other_stuff: false }]
                    }
                };
                board.handleAddPlugin(data);

                expect($('.cms-draggable-2')).not.toHaveClass('new');
                expect($('.cms-dragarea-2 > .cms-draggables > .new-draggable')).toBeInDOM();
                expect(StructureBoard.actualizePlaceholders).toHaveBeenCalled();
                expect(FakePlugin._updateRegistry).toHaveBeenCalledWith(data.structure.plugins);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledTimes(1);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledWith(3);
                expect(board._drag).toHaveBeenCalled();
                expect(board.ui.sortables.filter('.new-draggable .cms-draggables')).toExist();
            });
        });

        describe('handleEditPlugin', () => {
            it('replaces edited plugin with new markup', () => {
                const data = {
                    plugin_parent: null,
                    plugin_id: 2,
                    structure: {
                        html: `
                            <div class="cms-draggable-3 new-draggable">
                                <div class="cms-draggables"></div>
                            </div>
                        `,
                        plugins: [{ plugin_id: 3, other_stuff: false }]
                    }
                };
                board.handleEditPlugin(data);

                expect($('.cms-draggable-2')).not.toExist();
                expect($('.new-draggable')).toBeInDOM();
                expect(StructureBoard.actualizePlaceholders).not.toHaveBeenCalled();
                expect(FakePlugin._updateRegistry).toHaveBeenCalledWith(data.structure.plugins);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledTimes(1);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledWith(3);
                expect(board._drag).toHaveBeenCalled();
                expect(board.ui.sortables.filter('.new-draggable .cms-draggables')).toExist();
            });

            it('replaces parent of edited plugin if it was passed', () => {
                const data = {
                    plugin_parent: 2,
                    plugin_id: 3,
                    structure: {
                        html: `
                            <div class="cms-draggable-3 new-draggable">
                                <div class="cms-draggables"></div>
                            </div>
                        `,
                        plugins: [{ plugin_id: 3, other_stuff: false }]
                    }
                };
                board.handleEditPlugin(data);

                expect($('.cms-draggable-2')).not.toExist();
                expect($('.new-draggable')).toBeInDOM();
                expect(StructureBoard.actualizePlaceholders).not.toHaveBeenCalled();
                expect(FakePlugin._updateRegistry).toHaveBeenCalledWith(data.structure.plugins);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledTimes(1);
                expect(StructureBoard.actualizePluginCollapseStatus).toHaveBeenCalledWith(3);
                expect(board._drag).toHaveBeenCalled();
                expect(board.ui.sortables.filter('.new-draggable .cms-draggables')).toExist();
            });
        });

        describe('handleDeletePlugin', () => {
            it('removes plugin', () => {
                CMS._plugins = [['cms-plugin-1', { plugin_id: 1 }], ['cms-plugin-2']];
                CMS._instances = [{ options: { plugin_id: 1 } }, { options: { plugin_id: 2 } }];
                board.handleDeletePlugin({ plugin_id: 1 });
                expect($('.cms-draggable-1')).not.toBeInDOM();
                expect(StructureBoard.actualizePluginsCollapsibleStatus).toHaveBeenCalledWith(
                    $('.cms-dragarea-1 > .cms-draggables')
                );
                expect(CMS._plugins).toEqual([['cms-plugin-2']]);
                expect(CMS._instances).toEqual([{ options: { plugin_id: 2 } }]);
            });

            it('removes plugin and its children', () => {
                CMS._plugins = [['cms-plugin-3', { plugin_id: 3 }], ['cms-plugin-4']];
                CMS._instances = [{ options: { plugin_id: 3 } }, { options: { plugin_id: 4 } }];
                $('.cms-draggable-2').find('.cms-draggables').append(`
                    <div class="cms-draggable cms-draggable-3">
                        <div class="cms-draggables">
                            <div class="cms-draggable cms-draggable-4">
                            </div>
                        </div>
                    </div>
                `);
                expect($('.cms-draggable-3')).toBeInDOM();
                expect($('.cms-draggable-4')).toBeInDOM();
                board.handleDeletePlugin({ plugin_id: 3 });
                expect($('.cms-draggable-3')).not.toBeInDOM();
                expect($('.cms-draggable-4')).not.toBeInDOM();
                expect(StructureBoard.actualizePluginsCollapsibleStatus).toHaveBeenCalledWith(
                    $('.cms-draggable-2 > .cms-draggables')
                );
                expect(CMS._plugins).toEqual([]);
                expect(CMS._instances).toEqual([]);
            });
        });

        describe('handleClearPlaceholder', () => {
            it('clears placeholder', () => {
                CMS._plugins = [
                    ['cms-plugin-3'],
                    ['cms-plugin-1', { plugin_id: 1, placeholder_id: 1 }],
                    ['cms-plugin-2', { plugin_id: '2', placeholder_id: 1 }]
                ];
                CMS._instances = [
                    { options: { plugin_id: 3 } },
                    { options: { plugin_id: 1, placeholder_id: 1 } },
                    { options: { plugin_id: '2', placeholder_id: '1' } }
                ];
                expect($('.cms-draggable-1')).toBeInDOM();
                expect($('.cms-draggable-2')).toBeInDOM();

                board.handleClearPlaceholder({ placeholder_id: 1 });

                expect($('.cms-draggable-1')).not.toBeInDOM();
                expect($('.cms-draggable-2')).not.toBeInDOM();
                expect(StructureBoard.actualizePluginsCollapsibleStatus).not.toHaveBeenCalled();
                expect(StructureBoard.actualizePlaceholders).toHaveBeenCalled();
                expect(CMS._plugins).toEqual([['cms-plugin-3']]);
                expect(CMS._instances).toEqual([{ options: { plugin_id: 3 } }]);
            });
        });

        describe('handleCopyPlugin', () => {
            const clipboardConstructor = jasmine.createSpy();
            const close = jasmine.createSpy();
            class FakeClipboard {
                constructor(...args) {
                    clipboardConstructor(...args);
                }
            }
            FakeClipboard.prototype = Object.assign(FakeClipboard.prototype, {
                _isClipboardModalOpen: jasmine.createSpy(),
                modal: {
                    close: jasmine.createSpy()
                },
                populate: jasmine.createSpy(),
                _enableTriggers: jasmine.createSpy()
            });
            beforeEach(() => {
                CMS.API.Clipboard = {
                    _isClipboardModalOpen: jasmine.createSpy(),
                    modal: {
                        close
                    },
                    populate: jasmine.createSpy(),
                    _enableTriggers: jasmine.createSpy()
                };
                StructureBoard.__Rewire__('Clipboard', FakeClipboard);
                StructureBoard.__Rewire__('Plugin', FakePlugin);
                fixture.load('clipboard.html');
            });
            afterEach(() => {
                StructureBoard.__ResetDependency__('Clipboard');
                StructureBoard.__ResetDependency__('Plugin');
            });

            it('updates the clipboard', () => {
                const data = {
                    plugins: [{ plugin_id: 10, stuff: true }],
                    html: '<div class="new-clipboard-draggable cms-draggable-from-clipboard"></div>'
                };
                CMS._plugins = [];
                CMS._instances = [];
                board.handleCopyPlugin(data);

                expect(CMS._plugins).toEqual([['cms-plugin-10', data.plugins[0]]]);
                expect(CMS._instances).toEqual([jasmine.any(FakePlugin)]);

                expect(FakePlugin._updateClipboard).toHaveBeenCalled();
                expect(clipboardConstructor).toHaveBeenCalled();
                expect(FakeClipboard.prototype.populate).toHaveBeenCalled();
                expect(FakeClipboard.prototype._enableTriggers).toHaveBeenCalled();
                expect(board.ui.sortables.find('.new-clipboard-draggable')).toExist();
                expect(board._drag).toHaveBeenCalled();
                expect(pluginConstructor).toHaveBeenCalledWith('cms-plugin-10', data.plugins[0]);
                expect(CMS.API.Clipboard.modal.close).not.toHaveBeenCalled();
            });

            it('closes clipboard modal if needed', () => {
                CMS.API.Clipboard._isClipboardModalOpen.and.returnValue(true);

                const data = {
                    plugins: [{ plugin_id: 10, stuff: true }],
                    html: '<div class="new-clipboard-draggable cms-draggable-from-clipboard"></div>'
                };

                board.handleCopyPlugin(data);
                expect(close).toHaveBeenCalled();
            });
        });

        describe('handleCutPlugin', () => {
            it('calls delete and copy', () => {
                spyOn(board, 'handleDeletePlugin');
                spyOn(board, 'handleCopyPlugin');

                board.handleCutPlugin({ randomData: true });

                expect(board.handleDeletePlugin).toHaveBeenCalledWith({ randomData: true });
                expect(board.handleCopyPlugin).toHaveBeenCalledWith({ randomData: true });
            });
        });
    });

    describe('_loadToolbar', () => {
        it('loads toolbar url', () => {
            const board = new StructureBoard();

            spyOn($, 'ajax');
            CMS.config.request = {
                toolbar: 'TOOLBAR_URL',
                pk: 100,
                model: 'cms.page'
            };

            board._loadToolbar();

            expect($.ajax).toHaveBeenCalledWith({
                url: jasmine.stringMatching(
                    /TOOLBAR_URL\?obj_id=100&obj_type=cms.page&cms_path=%2Fcontext.html.*/
                )
            });
        });
    });

    describe('_requestMode', () => {
        let board;
        let request;
        const preloadImages = jasmine.createSpy();

        beforeEach(() => {
            board = new StructureBoard();
            StructureBoard.__Rewire__('preloadImagesFromMarkup', preloadImages);
        });

        afterEach(() => {
            StructureBoard.__ResetDependency__('preloadImagesFromMarkup');
            preloadImages.calls.reset();
        });

        it('requests content', () => {
            request = {
                then(fn) {
                    fn('markup');
                    return request;
                }
            };
            spyOn($, 'ajax').and.callFake(req => {
                expect(req.method).toEqual('GET');
                expect(req.url).toMatch(/\?edit/);
                return request;
            });

            expect(board._requestcontent).not.toBeDefined();

            board._requestMode('content');
            expect(preloadImages).toHaveBeenCalledWith('markup');
            expect(board._requestcontent).toBe(request);
        });

        it('requests structure', () => {
            request = {
                then(fn) {
                    fn('markup');
                    return request;
                }
            };
            spyOn($, 'ajax').and.callFake(req => {
                expect(req.method).toEqual('GET');
                expect(req.url).toMatch(/\?structure/);
                return request;
            });

            expect(board._requeststructure).not.toBeDefined();

            board._requestMode('structure');
            expect(preloadImages).toHaveBeenCalledWith('markup');
            expect(board._requeststructure).toBe(request);
        });

        it('reuses same promise if it was not reset', () => {
            request = {
                then(fn) {
                    fn('markup');
                    return request;
                }
            };
            spyOn($, 'ajax').and.callFake(req => {
                expect(req.method).toEqual('GET');
                expect(req.url).toMatch(/\?edit/);
                return request;
            });

            expect(board._requestcontent).not.toBeDefined();

            board._requestMode('content');
            expect(preloadImages).toHaveBeenCalledWith('markup');
            expect(board._requestcontent).toBe(request);

            board._requestMode('content');
            expect(preloadImages).toHaveBeenCalledTimes(1);
            expect(board._requestcontent).toBe(request);
        });
    });

    describe('_loadContent', () => {
        let board;
        let response = '';
        let requestSucceeded;
        beforeEach(() => {
            requestSucceeded = jasmine.createSpy();
            CMS.API.Toolbar = {
                _refreshMarkup: jasmine.createSpy()
            };
            board = new StructureBoard();
            CMS.config = {
                settings: {
                    mode: 'structure'
                }
            };

            spyOn(board, '_requestMode').and.returnValue({
                done(fn) {
                    requestSucceeded();
                    fn(response);
                    return {
                        fail() {
                            return {
                                then(callback) {
                                    callback();
                                }
                            };
                        }
                    };
                }
            });
            StructureBoard.__Rewire__('Plugin', FakePlugin);
            Plugin.__Rewire__('Plugin', FakePlugin);
        });
        afterEach(() => {
            StructureBoard.__ResetDependency__('Plugin');
            Plugin.__ResetDependency__('Plugin', FakePlugin);
        });

        it('resolves immediately when content mode is already loaded', done => {
            CMS.config.settings.mode = 'edit';
            board._loadContent().then(() => {
                expect(requestSucceeded).not.toHaveBeenCalled();
                done();
            });

            CMS.config.settings.mode = 'structure';
        });
        it('resolves immediately when content mode is already loaded', done => {
            board._loadedContent = true;
            board._loadContent().then(() => {
                expect(requestSucceeded).not.toHaveBeenCalled();
                done();
            });

            CMS.config.settings.mode = 'structure';
        });

        it('requests content', done => {
            response = `
                <html attr0="a" attr1="b">
                    <head>
                        <title>i am a new title</title>
                    </head>
                    <body attr2="x" attr3="y">
                        <p class="new-content">New body content yay</p>
                    </body>
                </html>
            `;
            CMS._instances = [
                new FakePlugin('cms-plugin-1', { plugin_id: 1, type: 'plugin' }),
                new FakePlugin('cms-placeholder-1', { placeholder_id: 1, type: 'placeholder' }),
                new FakePlugin('cms-plugin-existing-generic-1', { plugin_id: '1', type: 'generic' })
            ];
            CMS._plugins = [
                ['cms-plugin-1', { plugin_id: 1, type: 'plugin' }],
                ['cms-plugin-1', { plugin_id: 1, type: 'plugin' }],
                ['cms-placeholder-1', { placeholder_id: 1, type: 'placeholder' }],
                ['cms-plugin-existing-generic-1', { plugin_id: 1, type: 'generic' }],
                ['cms-plugin-new-generic-2', { plugin_id: 2, type: 'generic' }]
            ];

            expect(board._loadedContent).not.toBeDefined();
            pluginConstructor.calls.reset();
            board._loadContent().then(() => {
                expect(showLoader).toHaveBeenCalled();
                expect(hideLoader).toHaveBeenCalled();
                expect(CMS.API.Toolbar._refreshMarkup).toHaveBeenCalled();
                expect($('html').attr('attr0')).toEqual('a');
                expect($('html').attr('attr1')).toEqual('b');
                expect($('body').attr('attr2')).toEqual('x');
                expect($('body').attr('attr3')).toEqual('y');
                expect($('.new-content')).toBeInDOM();

                expect(FakePlugin.prototype._ensureData).toHaveBeenCalledTimes(3);
                expect(FakePlugin.prototype._setGeneric).toHaveBeenCalledTimes(1);
                expect(FakePlugin.prototype._setPluginContentEvents).toHaveBeenCalledTimes(1);
                expect(pluginConstructor).toHaveBeenCalledTimes(1);

                $('.new-content').remove();
                expect(board._loadedContent).toBe(true);
                done();
            });
        });
    });

    describe('_loadStructure', () => {
        let board;
        let response = '';
        let requestSucceeded;
        beforeEach(() => {
            requestSucceeded = jasmine.createSpy();
            CMS.API.Toolbar = {
                _refreshMarkup: jasmine.createSpy()
            };
            board = new StructureBoard();
            CMS.config = {
                settings: {
                    mode: 'edit'
                }
            };

            spyOn(StructureBoard, '_initializeGlobalHandlers');
            spyOn(StructureBoard, 'actualizePlaceholders');
            spyOn(StructureBoard, '_initializeDragItemsStates');
            spyOn(board, '_drag');

            spyOn(board, '_requestMode').and.returnValue({
                done(fn) {
                    requestSucceeded();
                    fn(response);
                    return {
                        fail() {
                            return {
                                then(callback) {
                                    callback();
                                }
                            };
                        }
                    };
                }
            });
            StructureBoard.__Rewire__('Plugin', FakePlugin);
        });
        afterEach(() => {
            StructureBoard.__ResetDependency__('Plugin');
        });

        it('resolves immediately when structure mode is already loaded', done => {
            CMS.config.settings.mode = 'structure';
            board._loadStructure().then(() => {
                expect(requestSucceeded).not.toHaveBeenCalled();
                done();
            });

            CMS.config.settings.mode = 'edit';
        });

        it('resolves immediately when structure mode is already loaded', done => {
            board._loadedStructure = true;
            board._loadStructure().then(() => {
                expect(requestSucceeded).not.toHaveBeenCalled();
                done();
            });

            CMS.config.settings.mode = 'edit';
        });

        it('requests structure', done => {
            response = `
                <html attr0="a" attr1="b">
                    <head>
                        <title>i am a new title</title>
                    </head>
                    <body attr2="x" attr3="y">
                        <p class="new-content">New body content yay</p>
                    </body>
                </html>
            `;
            CMS._instances = [
                new FakePlugin('cms-plugin-1', { plugin_id: 1, type: 'plugin' }),
                new FakePlugin('cms-placeholder-1', { placeholder_id: 1, type: 'placeholder' }),
                new FakePlugin('cms-plugin-existing-generic-1', { plugin_id: '1', type: 'generic' })
            ];

            expect(board._loadedStructure).not.toBeDefined();
            pluginConstructor.calls.reset();
            board._loadStructure().then(() => {
                expect(showLoader).toHaveBeenCalled();
                expect(hideLoader).toHaveBeenCalled();
                expect(CMS.API.Toolbar._refreshMarkup).toHaveBeenCalled();

                expect(FakePlugin.prototype._setPlaceholder).toHaveBeenCalledTimes(1);
                expect(FakePlugin.prototype._setPluginStructureEvents).toHaveBeenCalledTimes(1);
                expect(FakePlugin.prototype._setGeneric).not.toHaveBeenCalled();
                expect(pluginConstructor).not.toHaveBeenCalled();
                expect(board._drag).toHaveBeenCalled();

                expect(StructureBoard._initializeDragItemsStates).toHaveBeenCalled();
                expect(StructureBoard._initializeGlobalHandlers).toHaveBeenCalled();
                expect(StructureBoard.actualizePlaceholders).toHaveBeenCalled();
                expect(board._loadedStructure).toBe(true);
                done();
            });
        });
    });

    describe('_getPluginDataFromMarkup()', () => {
        [
            {
                args: ['', [1, 2, 3]],
                expected: []
            },
            {
                args: ['whatever', []],
                expected: []
            },
            {
                args: ['CMS._plugins.push(["cms-plugin-4",{"plugin_id":"4"}]);', [1, 2, 3]],
                expected: []
            },
            {
                args: ['CMS._plugins.push(["cms-plugin-4",{"plugin_id":"4"}]);', [1, 2, 4]],
                expected: [['cms-plugin-4', { plugin_id: '4' }]]
            },
            {
                args: [
                    `CMS._plugins.push(["cms-plugin-4",{"plugin_id":"4"}]);
                    CMS._plugins.push(["cms-plugin-10", { "plugin_id": "meh"}]);`, [1, 2, 10]],
                expected: [['cms-plugin-10', { plugin_id: 'meh' }]]
            },
            {
                args: ['CMS._plugins.push(["cms-plugin-4",{plugin_id:"4"}])', [4]],
                expected: []
            },
            {
                args: ['CMS._plugins.push(["cms-plugin-4",not a json :(]);', [4]],
                expected: []
            },
            {
                args: [`CMS._plugins.push(["cms-plugin-4", {
                    "something": 1
                }])`, [4]],
                expected: [['cms-plugin-4', { something: 1 }]]
            }
        ].forEach((test, i) => {
            it(`extracts plugin data from markup ${i}`, () => {
                expect(StructureBoard._getPluginDataFromMarkup(...test.args)).toEqual(test.expected);
            });
        });
    });

    describe('_extractMessages()', () => {
        let board;

        beforeEach(() => {
            board = new StructureBoard();
        });

        it('extracts messages', () => {
            expect(
                board._extractMessages(
                    $(`
                <div>
                    <div data-cms-messages-container>
                        <div data-cms-message data-cms-message-tags="error">
                            Error
                        </div>
                        <div data-cms-message data-cms-message-tags="invalid">
                            Normal
                        </div>
                        <div data-cms-message>

                        </div>
                    </div>
                </div>
            `)
                )
            ).toEqual([{ message: 'Error', error: true }, { message: 'Normal', error: false }]);

            expect(
                board._extractMessages(
                    $(`
                <div>
                    <ul class="messagelist"></ul>
                    <div data-cms-messages-container>
                        <div data-cms-message data-cms-message-tags="error">
                            Error1
                        </div>
                        <div data-cms-message data-cms-message-tags="invalid">
                            Normal1
                        </div>
                    </div>
                </div>
            `)
                )
            ).toEqual([{ message: 'Error1', error: true }, { message: 'Normal1', error: false }]);

            expect(
                board._extractMessages(
                    $(`
                <div>
                    <ul class="messagelist">
                        <li class="whatever">normal message</li>
                        <li class="error">error message</li>
                    </ul>
                </div>
            `)
                )
            ).toEqual([{ message: 'normal message', error: false }, { message: 'error message', error: true }]);

            expect(
                board._extractMessages(
                    $(`
                <div>
                </div>
            `)
                )
            ).toEqual([]);
        });
    });

    describe('_refreshContent()', () => {
        let board;
        const diffDOMConstructor = jasmine.createSpy();
        const newDoc = `
            <!DOCTYPE html>
            <html>
                <head>
                </head>
                <body>
                    <div class="new-markup">new markup</div>
                </body>
            </html>
        `;

        class DiffDOM {
            constructor() {
                diffDOMConstructor();
            }
        }
        DiffDOM.prototype.diff = jasmine.createSpy();
        DiffDOM.prototype.apply = jasmine.createSpy();

        class FakeDOMParser {}
        FakeDOMParser.prototype.parseFromString = jasmine.createSpy().and.returnValue({
            head: 'fakeNewHead',
            body: 'fakeNewBody'
        });

        beforeEach(() => {
            StructureBoard.__Rewire__('DiffDOM', DiffDOM);
            StructureBoard.__Rewire__('DOMParser', FakeDOMParser);

            board = new StructureBoard();

            spyOn(StructureBoard, '_replaceBodyWithHTML');

            CMS.API.Messages = {
                open: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                _refreshMarkup: jasmine.createSpy()
            };
        });

        afterEach(() => {
            StructureBoard.__ResetDependency__('DiffDOM');
            StructureBoard.__ResetDependency__('DOMParser');
        });

        it('resets loaded content flag', () => {
            CMS._instances = [];
            board._requestcontent = {};
            board._loadedContent = false;
            board.refreshContent(newDoc);
            expect(board._requestcontent).toBe(null);
            expect(board._loadedContent).toBe(true);
        });

        it('shows messages', done => {
            CMS._instances = [];
            spyOn(board, '_extractMessages').and.returnValue([{ message: 'hello' }]);
            board.refreshContent(newDoc);
            setTimeout(() => {
                expect(CMS.API.Messages.open).toHaveBeenCalledWith({ message: 'hello' });
                done();
            }, 20);
        });

        it('resets plugin instances', () => {
            CMS._instances = [
                new FakePlugin('cms-plugin-1', { plugin_id: 1, type: 'plugin' }),
                new FakePlugin('cms-placeholder-1', { placeholder_id: 1, type: 'placeholder' })
            ];

            board.refreshContent(newDoc);
            expect(FakePlugin.prototype._setupUI).toHaveBeenCalledTimes(2);
            expect(FakePlugin.prototype._setupUI).toHaveBeenCalledWith('cms-plugin-1');
            expect(FakePlugin.prototype._setupUI).toHaveBeenCalledWith('cms-placeholder-1');
            expect(FakePlugin.prototype._ensureData).toHaveBeenCalledTimes(2);
            expect(FakePlugin.prototype._setPlaceholder).toHaveBeenCalledTimes(1);
            expect(FakePlugin.prototype._setPluginContentEvents).toHaveBeenCalledTimes(1);
        });
    });

    describe('_preloadOppositeMode', () => {
        ['content', 'structure'].forEach(mode => {
            it(`preloads the opposite mode (${mode})`, () => {
                const div = document.createElement('div');
                const _getWindow = jasmine.createSpy().and.returnValue(div);

                StructureBoard.__Rewire__('Helpers', {
                    _getWindow
                });

                const board = new StructureBoard();

                spyOn(board, '_requestMode');

                jasmine.clock().install();

                if (mode === 'content') {
                    board._loadedStructure = false;
                } else {
                    board._loadedStructure = true;
                }

                board._preloadOppositeMode();
                expect(board._requestMode).not.toHaveBeenCalled();
                $(div).trigger('load');
                expect(board._requestMode).not.toHaveBeenCalled();
                jasmine.clock().tick(2001);
                expect(board._requestMode).toHaveBeenCalledTimes(1);
                expect(board._requestMode).toHaveBeenCalledWith(mode === 'content' ? 'structure' : 'content');

                jasmine.clock().uninstall();

                StructureBoard.__ResetDependency__('Helpers');
            });
        });

        it('does not preload the opposite mode (legacy renderer)', () => {
            const div = document.createElement('div');
            const _getWindow = jasmine.createSpy().and.returnValue(div);

            StructureBoard.__Rewire__('Helpers', {
                _getWindow
            });

            const board = new StructureBoard();

            spyOn(board, '_requestMode');

            jasmine.clock().install();

            CMS.config.settings.legacy_mode = true;
            board._loadedContent = true;
            board._loadedStructure = true;

            board._preloadOppositeMode();
            expect(board._requestMode).not.toHaveBeenCalled();
            $(div).trigger('load');
            expect(board._requestMode).not.toHaveBeenCalled();
            jasmine.clock().tick(2001);
            expect(board._requestMode).not.toHaveBeenCalled();

            jasmine.clock().uninstall();

            StructureBoard.__ResetDependency__('Helpers');
        });
    });

    describe('actualizePluginCollapseStatus', () => {
        it('works', () => {
            $('#fixture_container').append(`
                <div class="cms-draggable-1">
                    <div class="cms-collapsable-container cms-hidden"></div>
                    <div class="cms-dragitem"></div>
                    <div class="cms-draggables"></div>
                </div>
            `);

            CMS.settings = {
                states: ['1\n']
            };

            StructureBoard.actualizePluginCollapseStatus(1);

            expect('.cms-draggable-1 .cms-collapsable-container').not.toHaveClass('cms-hidden');
            expect('.cms-draggable-1 .cms-dragitem').toHaveClass('cms-dragitem-expanded');

            $('#fixture_container').empty();
        });
    });
});
