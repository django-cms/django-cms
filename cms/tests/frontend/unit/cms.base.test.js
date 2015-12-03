describe('cms.base.js', function () {
    it('creates CMS namespace', function () {
        expect(CMS).toBeDefined();
        expect(CMS).toEqual(jasmine.any(Object));
        expect(CMS.API).toEqual(jasmine.any(Object));
        expect(CMS.KEYS).toEqual(jasmine.any(Object));
        expect(CMS.BREAKPOINTS).toEqual(jasmine.any(Object));
        expect(CMS.$).toEqual(jQuery);
        expect(CMS.Class).toEqual(Class);
    });

    describe('CMS.API', function () {
        it('exists', function () {
            expect(CMS.API.Helpers).toEqual(jasmine.any(Object));
            // this expectation is here so no one ever forgets to add a test
            expect(Object.keys(CMS.API.Helpers).length).toEqual(16);
        });

        describe('.reloadBrowser()', function () {

        });

        describe('.preventSubmit()', function () {

        });

        describe('.csrf()', function () {

        });

        describe('.setSettings()', function () {

        });

        describe('.getSettings()', function () {

        });

        describe('.makeURL()', function () {

        });

        describe('.debounce()', function () {

        });

        describe('.throttle()', function () {

        });

        describe('.secureConfirm()', function () {

        });

        describe('.addEventListener()', function () {

        });

        describe('.removeEventListener()', function () {

        });

        describe('.dispatchEvent()', function () {

        });

        describe('.once()', function () {

        });

        describe('.preventTouchScrolling()', function () {

        });

        describe('.allowTouchScrolling()', function () {

        });
    });
});
