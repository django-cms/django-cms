describe('CMS.Modal', () => {
    it('is not defined at first', () => {
        expect(CMS.Modal).not.toBeDefined();
    });

    it('creates a Modal class when document is ready', (done) => {
        $(function () {
            expect(CMS.Modal).toBeDefined();
            done();
        });
    });

    it('has public methods', (done) => {
        $(function () {
            expect(CMS.Modal.prototype.open).toEqual(jasmine.any(Function));
            done();
        });
    });
});
