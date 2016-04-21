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
});
