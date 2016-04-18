'use strict';

describe('CMS.PageTree', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a PageTree class', function () {
        expect(CMS.PageTree).toBeDefined();
    });

    it('has public API', function () {
        expect(CMS.PageTree.prototype.showError).toEqual(jasmine.any(Function));
    });

    describe('_getDescendantsIds', function () {
        var pagetree;

        beforeEach(function (done) {
            jasmine.Ajax.install();
            fixture.load('pagetree.html');
            $(function () {
                pagetree = new CMS.PageTree();
                done();
            });
        });

        afterEach(function () {
            jasmine.Ajax.uninstall();
            fixture.cleanup();
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
});
