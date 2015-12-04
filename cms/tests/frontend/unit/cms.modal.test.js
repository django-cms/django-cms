/* globals $ */

'use strict';

describe('CMS.Modal', function () {
    it('creates a Modal class when document is ready', function (done) {
        $(function () {
            expect(CMS.Modal).toBeDefined();
            done();
        });
    });

    it('has public methods', function (done) {
        $(function () {
            expect(CMS.Modal.prototype.open).toEqual(jasmine.any(Function));
            done();
        });
    });
});
