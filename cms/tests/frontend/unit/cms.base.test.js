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
            it('exists', function () {
                expect(CMS.API.Helpers.makeURL).toEqual(jasmine.any(Function));
            });

            it('outputs the same url when no additional params passed', function () {
                var url = CMS.API.Helpers.makeURL('test');
                expect(url).toEqual('test');
            });

            it('outputs new url when additional params passed', function () {
                var url;

                url = CMS.API.Helpers.makeURL('test', ['param=1']);
                expect(url).toEqual('test?param=1');
            });

            it('outputs new url when there are multiple additional params', function () {
                var url;

                url = CMS.API.Helpers.makeURL('test', ['param=1', 'another=2']);
                expect(url).toEqual('test?param=1&amp;another=2');

                url = CMS.API.Helpers.makeURL('test?param=1', ['another=2']);
                expect(url).toEqual('test?param=1&amp;another=2');

                url = CMS.API.Helpers.makeURL('test?param=1&another=2', ['different=3']);
                expect(url).toEqual('test?param=1&amp;another=2&amp;different=3');

                url = CMS.API.Helpers.makeURL('test?param=1&amp;another=2', ['different=3']);
                expect(url).toEqual('test?param=1&amp;another=2&amp;different=3');

                url = CMS.API.Helpers.makeURL('test?param=1&another=2&amp;again=3', ['different=3']);
                expect(url).toEqual('test?param=1&amp;another=2&amp;again=3&amp;different=3');
            });

            it('replaces param values with new ones if they match', function () {
                var url;

                url = CMS.API.Helpers.makeURL('test?param=1&amp;another=2', ['another=3']);
                expect(url).toEqual('test?param=1&amp;another=3');

                url = CMS.API.Helpers.makeURL('test?param=1&amp;another=2', ['another=3', 'param=4']);
                expect(url).toEqual('test?param=4&amp;another=3');
            });
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
