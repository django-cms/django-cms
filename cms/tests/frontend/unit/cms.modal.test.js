/* globals $ */

'use strict';

describe('CMS.Modal', function () {
    it('creates a Modal class when document is ready', function () {
        expect(CMS.Modal).toBeDefined();
    });

    it('has public API', function () {
        expect(CMS.Modal.prototype.open).toEqual(jasmine.any(Function));
        expect(CMS.Modal.prototype.close).toEqual(jasmine.any(Function));
        expect(CMS.Modal.prototype.minimize).toEqual(jasmine.any(Function));
        expect(CMS.Modal.prototype.maximize).toEqual(jasmine.any(Function));
    });

    describe('instance', function () {
        it('has ui', function (done) {
            $(function () {
                var modal = new CMS.Modal();
                expect(modal.ui).toEqual(jasmine.any(Object));
                expect(Object.keys(modal.ui)).toContain('modal');
                expect(Object.keys(modal.ui)).toContain('body');
                expect(Object.keys(modal.ui)).toContain('window');
                expect(Object.keys(modal.ui)).toContain('toolbarLeftPart');
                expect(Object.keys(modal.ui)).toContain('minimizeButton');
                expect(Object.keys(modal.ui)).toContain('maximizeButton');
                expect(Object.keys(modal.ui)).toContain('title');
                expect(Object.keys(modal.ui)).toContain('titlePrefix');
                expect(Object.keys(modal.ui)).toContain('titleSuffix');
                expect(Object.keys(modal.ui)).toContain('resize');
                expect(Object.keys(modal.ui)).toContain('breadcrumb');
                expect(Object.keys(modal.ui)).toContain('closeAndCancel');
                expect(Object.keys(modal.ui)).toContain('modalButtons');
                expect(Object.keys(modal.ui)).toContain('modalBody');
                expect(Object.keys(modal.ui)).toContain('frame');
                expect(Object.keys(modal.ui)).toContain('shim');
                expect(Object.keys(modal.ui).length).toEqual(16);
                done();
            });
        });

        it('has options', function (done) {
            $(function () {
                var modal = new CMS.Modal();
                expect(modal.options).toEqual({
                    onClose: false,
                    minHeight: 400,
                    minWidth: 800,
                    modalDuration: 200,
                    newPlugin: false,
                    resizable: true,
                    maximizable: true,
                    minimizable: true
                });

                var modal2 = new CMS.Modal({ minHeight: 300, minWidth: 100 });
                expect(modal2.options).toEqual({
                    onClose: false,
                    minHeight: 300,
                    minWidth: 100,
                    modalDuration: 200,
                    newPlugin: false,
                    resizable: true,
                    maximizable: true,
                    minimizable: true
                });

                done();
            });
        });
    });

    describe('.open()', function () {
        it('opens the modal', function (done) {
            $(function () {
                var modal = new CMS.Modal();

                done();
            });
        });
    });
});
