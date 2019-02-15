'use strict';
var CMS = require('../../../static/cms/js/modules/cms.base').default;
var PageTree = require('../../../static/cms/js/modules/cms.pagetree').default;
var PageTreeDropdowns = require('../../../static/cms/js/modules/cms.pagetree.dropdown').default;
var $ = require('jquery');

window.CMS = window.CMS || CMS;
CMS.PageTree = PageTree;
CMS.PageTreeDropdowns = PageTreeDropdowns;


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
                CMS.settings = {};
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

        it('retains existing state', function () {
            CMS.settings = {
                whatever: 'set',
                sideframe: {
                    url: 'something'
                }
            };
            var link = $('<span class="js-cms-pagetree-page-view"></span>');
            link.appendTo(pagetree.ui.container);

            pagetree._setupPageView();
            link.trigger(pagetree.click);
            expect(CMS.API.Helpers.setSettings).toHaveBeenCalledTimes(1);
            expect(CMS.API.Helpers.setSettings).toHaveBeenCalledWith({
                whatever: 'set',
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
        var paste1wrapper;

        beforeEach(function (done) {
            $(function () {
                paste1 = $('<div class="paste-1 js-cms-tree-item-paste cms-pagetree-dropdown-item-disabled"></div>');
                paste2 = $('<div class="paste-2 js-cms-tree-item-paste cms-pagetree-dropdown-item-disabled"></div>');
                paste1wrapper = paste1.wrap('<div class="wrapper"></div>').parent();
                pagetree = new CMS.PageTree();
                pagetree.ui.container.append(paste1wrapper);
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
            pagetree._enablePaste('.wrapper');
            expect(paste1).not.toHaveClass('cms-pagetree-dropdown-item-disabled');
            expect(paste2).toHaveClass('cms-pagetree-dropdown-item-disabled');
        });
    });

    describe('_disablePaste()', function () {
        var pagetree;
        var paste1;
        var paste2;
        var paste1wrapper;

        beforeEach(function (done) {
            $(function () {
                paste1 = $('<div class="paste-1 js-cms-tree-item-paste"></div>');
                paste2 = $('<div class="paste-2 js-cms-tree-item-paste"></div>');
                paste1wrapper = paste1.wrap('<div class="wrapper"></div>').parent();
                pagetree = new CMS.PageTree();
                pagetree.ui.container.append(paste1wrapper);
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
            pagetree._disablePaste('.wrapper');
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
                id: 123,
                source_site: 1
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
                origin: true,
                source_site: 1
            };

            pagetree._updatePasteHelpersState();
            expect(pagetree._enablePaste).toHaveBeenCalledTimes(1);
            expect(pagetree._getDescendantsIds).toHaveBeenCalledTimes(1);
            expect(pagetree._disablePaste).toHaveBeenCalledTimes(1);
            expect(pagetree._disablePaste).toHaveBeenCalledWith('.jsgrid_123_col');
        });

        it('enables "Paste" action only where needed if action is "cut"', function () {
            pagetree.clipboard = {
                type: 'cut',
                id: 123,
                origin: true,
                source_site: 1
            };
            pagetree._getDescendantsIds.and.returnValues([111, 104]);

            pagetree._updatePasteHelpersState();
            expect(pagetree._enablePaste).toHaveBeenCalledTimes(1);
            expect(pagetree._getDescendantsIds).toHaveBeenCalledTimes(1);
            expect(pagetree._disablePaste).toHaveBeenCalledTimes(3);
            expect(pagetree._disablePaste).toHaveBeenCalledWith('.jsgrid_123_col');
            expect(pagetree._disablePaste).toHaveBeenCalledWith('.jsgrid_111_col');
            expect(pagetree._disablePaste).toHaveBeenCalledWith('.jsgrid_104_col');
        });
    });

    describe('_getNodeId()', function () {
        var pagetree;
        var node;
        var rootNode;

        beforeEach(function (done) {
            $(function () {
                node = $('<div class="jstree-grid-cell jsgrid_j125_col test"></div>');
                rootNode = $('<div class="root node"></div>');
                pagetree = new CMS.PageTree();
                pagetree.ui.container.append(node);
                pagetree.ui.container.append(rootNode);
                done();
            });
        });

        it('finds the id of the of the closest pagetree node', function () {
            expect(pagetree._getNodeId(node)).toEqual('j125');
        });

        it('handles root node', function () {
            expect(pagetree._getNodeId(rootNode)).toEqual('#');
        });
    });

    describe('_paste()', function () {
        var pagetree;

        beforeEach(function (done) {
            $(function () {
                pagetree = new CMS.PageTree();
                spyOn(pagetree, '_getNodeId').and.returnValues('FROM', 'TO');
                spyOn(pagetree, '_disablePaste');
                done();
            });
        });

        it('disables pasting', function () {
            pagetree._paste({ currentTarget: 'MOCK' });
            expect(pagetree._disablePaste).toHaveBeenCalledTimes(1);
        });

        it('triggers cut event if necessary', function () {
            spyOn($.fn, 'jstree');
            pagetree.clipboard.type = 'cut';
            pagetree._paste({ currentTarget: 'MOCK' });
            expect($.fn.jstree).toHaveBeenCalledTimes(3);

            expect($.fn.jstree).toHaveBeenCalledWith('create_node', 'TO', 'Loading', 'last');
            expect($.fn.jstree).toHaveBeenCalledWith('cut', undefined);
            expect($.fn.jstree).toHaveBeenCalledWith('paste', 'TO', 'last');
        });

        it('triggers copy event if necessary', function () {
            spyOn($.fn, 'jstree');
            pagetree.clipboard.type = 'copy';
            pagetree._paste({ currentTarget: 'MOCK' });
            expect($.fn.jstree).toHaveBeenCalledTimes(3);

            expect($.fn.jstree).toHaveBeenCalledWith('create_node', 'TO', 'Loading', 'last');
            expect($.fn.jstree).toHaveBeenCalledWith('cut', undefined);
            expect($.fn.jstree).toHaveBeenCalledWith('paste', 'TO', 'last');
        });

        it('triggers paste event with specific state', function () {
            spyOn($.fn, 'jstree').and.callFake(function (type) {
                if (type === 'paste') {
                    expect(pagetree.clipboard.isPasting).toEqual(true);
                }
            });

            pagetree._paste({ currentTarget: 'MOCK' });
        });

        it('unsets the clipboard', function () {
            spyOn($.fn, 'jstree');
            pagetree.clipboard = {
                id: 1,
                type: 2,
                origin: 3
            };
            pagetree._paste({ currentTarget: 'MOCK' });
            expect(pagetree.clipboard).toEqual({
                id: null,
                type: null,
                origin: null,
                isPasting: false
            });
        });
    });
});
