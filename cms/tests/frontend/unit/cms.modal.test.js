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
