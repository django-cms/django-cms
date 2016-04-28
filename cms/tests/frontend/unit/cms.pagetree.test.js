'use strict';

describe('CMS.PageTree', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    beforeEach(function () {
        fixture.load('pagetree.html');
        jasmine.Ajax.install();
        spyOn(CMS.PageTreeDropdowns.prototype, 'initialize').and.returnValue({
            closeAllDropdowns: jasmine.createSpy()
        });
    });
    afterEach(function () {
        fixture.cleanup();
        jasmine.Ajax.uninstall();
    });

    it('creates a PageTree class', function () {
        expect(CMS.PageTree).toBeDefined();
    });

    it('has options', function () {
        expect(CMS.PageTree.prototype.options).toEqual({
            pasteSelector: '.js-cms-tree-item-paste'
        });
    });

    it('has public API', function () {
        expect(CMS.PageTree.prototype.showError).toEqual(jasmine.any(Function));
    });

    describe('_getDescendantsIds()', function () {
        var pagetree;

        beforeEach(function (done) {
            $(function () {
                pagetree = new CMS.PageTree();
                done();
            });
        });

        it('returns array of descendant ids', function () {
            spyOn($.jstree.core.prototype, 'get_node').and.callFake(function (pick) {
                return {
                    full: {
                        children_d: [1, 2, 3]
                    },
                    empty: {
                        children_d: []
                    }
                }[pick];
            });

            expect(pagetree._getDescendantsIds('full')).toEqual([1, 2, 3]);
            expect(pagetree._getDescendantsIds('empty')).toEqual([]);
        });
    });

    describe('_setupPageView()', function () {
        var pagetree;

        beforeEach(function (done) {
            spyOn(CMS.API.Helpers, 'setSettings');
            spyOn(CMS.API.Helpers, '_getWindow').and.returnValue({
                CMS: CMS
            });
            $(function () {
                pagetree = new CMS.PageTree();
                pagetree.ui.container.off(pagetree.click);
                done();
            });
        });

        it('sets up event handler to hide sideframe', function () {
            pagetree._setupPageView();
            expect(pagetree.ui.container).toHandle(pagetree.click);
        });

        it('that event handler hides sideframe', function () {
            var link = $('<span class="js-cms-pagetree-page-view"></span>');
            link.appendTo(pagetree.ui.container);

            pagetree._setupPageView();
            link.trigger(pagetree.click);
            expect(CMS.API.Helpers.setSettings).toHaveBeenCalledTimes(1);
            expect(CMS.API.Helpers.setSettings).toHaveBeenCalledWith({
                sideframe: {
                    url: null,
                    hidden: true
                }
            });
        });

        it('tries to use parent window', function () {
            var spy = jasmine.createSpy();
            CMS.API.Helpers._getWindow.and.returnValue({
                parent: {
                    CMS: {
                        API: {
                            Helpers: {
                                setSettings: spy
                            }
                        }
                    }
                }
            });

            var link = $('<span class="js-cms-pagetree-page-view"></span>');
            link.appendTo(pagetree.ui.container);

            pagetree._setupPageView();
            link.trigger(pagetree.click);
            expect(spy).toHaveBeenCalledTimes(1);
            expect(spy).toHaveBeenCalledWith({
                sideframe: {
                    url: null,
                    hidden: true
                }
            });
        });
    });

    describe('_enablePaste()', function () {
        var pagetree;
        var paste1;
        var paste2;

        beforeEach(function (done) {
            $(function () {
                paste1 = $('<div class="paste-1 js-cms-tree-item-paste cms-pagetree-dropdown-item-disabled"></div>');
                paste2 = $('<div class="paste-2 js-cms-tree-item-paste cms-pagetree-dropdown-item-disabled"></div>');
                pagetree = new CMS.PageTree();
                pagetree.ui.container.append(paste1);
                pagetree.ui.container.append(paste2);
                done();
            });
        });

        it('removes disabled class from "Paste" actions', function () {
            expect(paste1).toHaveClass('cms-pagetree-dropdown-item-disabled');
            expect(paste2).toHaveClass('cms-pagetree-dropdown-item-disabled');
            pagetree._enablePaste();
            expect(paste1).not.toHaveClass('cms-pagetree-dropdown-item-disabled');
            expect(paste2).not.toHaveClass('cms-pagetree-dropdown-item-disabled');
        });

        it('accepts optional selector', function () {
            expect(paste1).toHaveClass('cms-pagetree-dropdown-item-disabled');
            expect(paste2).toHaveClass('cms-pagetree-dropdown-item-disabled');
            pagetree._enablePaste('.paste-1');
            expect(paste1).not.toHaveClass('cms-pagetree-dropdown-item-disabled');
            expect(paste2).toHaveClass('cms-pagetree-dropdown-item-disabled');
        });
    });

    describe('_disablePaste()', function () {
        var pagetree;
        var paste1;
        var paste2;

        beforeEach(function (done) {
            $(function () {
                paste1 = $('<div class="paste-1 js-cms-tree-item-paste"></div>');
                paste2 = $('<div class="paste-2 js-cms-tree-item-paste"></div>');
                pagetree = new CMS.PageTree();
                pagetree.ui.container.append(paste1);
                pagetree.ui.container.append(paste2);
                done();
            });
        });

        it('adds disabled class to "Paste" actions', function () {
            expect(paste1).not.toHaveClass('cms-pagetree-dropdown-item-disabled');
            expect(paste2).not.toHaveClass('cms-pagetree-dropdown-item-disabled');
            pagetree._disablePaste();
            expect(paste1).toHaveClass('cms-pagetree-dropdown-item-disabled');
            expect(paste2).toHaveClass('cms-pagetree-dropdown-item-disabled');
        });

        it('accepts optional selector', function () {
            expect(paste1).not.toHaveClass('cms-pagetree-dropdown-item-disabled');
            expect(paste2).not.toHaveClass('cms-pagetree-dropdown-item-disabled');
            pagetree._disablePaste('.paste-1');
            expect(paste1).toHaveClass('cms-pagetree-dropdown-item-disabled');
            expect(paste2).not.toHaveClass('cms-pagetree-dropdown-item-disabled');
        });
    });

    describe('_updatePasteHelpersState()', function () {
        var pagetree;

        beforeEach(function (done) {
            $(function () {
                pagetree = new CMS.PageTree();
                spyOn(pagetree, '_enablePaste');
                spyOn(pagetree, '_disablePaste');
                spyOn(pagetree, '_getDescendantsIds');
                done();
            });
        });

        it('does not do anything if there is nothing in the clipboard', function () {
            pagetree._updatePasteHelpersState();
            expect(pagetree._enablePaste).not.toHaveBeenCalled();
            expect(pagetree._disablePaste).not.toHaveBeenCalled();
            expect(pagetree._getDescendantsIds).not.toHaveBeenCalled();
        });

        it('enables "Paste" action if there is something in the clipboard', function () {
            pagetree.clipboard = {
                type: 'copy',
                id: 123
            };

            pagetree._updatePasteHelpersState();
            expect(pagetree._enablePaste).toHaveBeenCalledTimes(1);
            expect(pagetree._disablePaste).not.toHaveBeenCalled();
            expect(pagetree._getDescendantsIds).not.toHaveBeenCalled();
        });

        it('enables "Paste" action only where needed if action is "cut"', function () {
            pagetree.clipboard = {
                type: 'cut',
                id: 123,
                origin: true
            };

            pagetree._updatePasteHelpersState();
            expect(pagetree._enablePaste).toHaveBeenCalledTimes(1);
            expect(pagetree._getDescendantsIds).toHaveBeenCalledTimes(1);
            expect(pagetree._disablePaste).toHaveBeenCalledTimes(1);
            expect(pagetree._disablePaste).toHaveBeenCalledWith('.jsgrid_123_col .js-cms-tree-item-paste');
        });

        it('enables "Paste" action only where needed if action is "cut"', function () {
            pagetree.clipboard = {
                type: 'cut',
                id: 123,
                origin: true
            };
            pagetree._getDescendantsIds.and.returnValues([111, 104]);

            pagetree._updatePasteHelpersState();
            expect(pagetree._enablePaste).toHaveBeenCalledTimes(1);
            expect(pagetree._getDescendantsIds).toHaveBeenCalledTimes(1);
            expect(pagetree._disablePaste).toHaveBeenCalledTimes(3);
            expect(pagetree._disablePaste).toHaveBeenCalledWith('.jsgrid_123_col .js-cms-tree-item-paste');
            expect(pagetree._disablePaste).toHaveBeenCalledWith('.jsgrid_111_col .js-cms-tree-item-paste');
            expect(pagetree._disablePaste).toHaveBeenCalledWith('.jsgrid_104_col .js-cms-tree-item-paste');
        });
    });

    describe('showMessage()', function () {
        it('does not do anything if message was not provided');
        it('shows message');
        it('replaces existing message if one is already shown');
        it('can show error message');
        it('can provide a "reload" link');
    });
});
