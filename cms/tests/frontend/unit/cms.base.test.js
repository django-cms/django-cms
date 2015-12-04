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
            it('should set csrf token on ajax requests', function () {
                var token = 'csrf';
                var request;

                jasmine.Ajax.install();
                $.ajax('/test');
                request = jasmine.Ajax.requests.mostRecent();
                expect(request.requestHeaders['X-CSRFToken']).toEqual(undefined);

                spyOn($, 'ajaxSetup').and.callThrough();
                CMS.API.Helpers.csrf(token);
                expect($.ajaxSetup).toHaveBeenCalled();
                expect($.ajaxSetup.calls.count()).toEqual(1);

                $.ajax('/test');
                request = jasmine.Ajax.requests.mostRecent();
                expect(request.requestHeaders['X-CSRFToken']).toEqual(token);
                jasmine.Ajax.uninstall();
            });
        });

        describe('.setSettings()', function () {

        });

        describe('.getSettings()', function () {

        });

        describe('.makeURL()', function () {
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
            it('debounces the function', function (done) {
                var count = 0;
                var fn = function () {
                    count++;
                };

                var debounced = CMS.API.Helpers.debounce(fn, 10);

                debounced();
                debounced();
                debounced();

                setTimeout(function () {
                    expect(count).toEqual(1);
                    done();
                }, 20);
            });

            it('should support `immediate` option', function (done) {
                var withImmediateCount = 0;
                var withoutImmediateCount = 0;
                var withImmediate = CMS.API.Helpers.debounce(function () {
                    withImmediateCount++;
                }, 10, { immediate: true });
                var withoutImmediate = CMS.API.Helpers.debounce(function () {
                    withoutImmediateCount++;
                }, 10, { immediate: false });

                withImmediate();
                withImmediate();
                expect(withImmediateCount).toEqual(1);

                withoutImmediate();
                withoutImmediate();

                setTimeout(function () {
                    expect(withImmediateCount).toEqual(1);
                    expect(withoutImmediateCount).toEqual(1);
                    withImmediate();
                    expect(withImmediateCount).toEqual(2);

                    done();
                }, 20);
            });

            it('should use correct `this` value', function (done) {
                var actual = [];
                var object = {
                    method: CMS.API.Helpers.debounce(function () {
                        actual.push(this);
                    }, 10)
                };

                object.method();
                object.method();

                setTimeout(function () {
                    expect([object]).toEqual(actual);
                    done();
                }, 20);
            });
        });

        describe('.throttle()', function () {
            it('should throttle a function', function (done) {
                var count = 0;
                var fn = function () {
                    count++;
                };

                var throttled = CMS.API.Helpers.throttle(fn, 10);

                throttled();
                throttled();
                throttled();

                expect(count).toEqual(1);
                setTimeout(function () {
                    expect(count).toEqual(2);
                    done();
                }, 35);
            });

            it('subsequent calls should return the result of the first call', function () {
                var fn = function (param) {
                    return param;
                };

                var throttled = CMS.API.Helpers.throttle(fn, 10);
                var result = [throttled('a'), throttled('b')];

                expect(result).toEqual(['a', 'a']);
            });

            it('should not trigger a trailing call when invoked once', function (done) {
                var count = 0;
                var fn = function () {
                    count++;
                };

                var throttled = CMS.API.Helpers.throttle(fn, 10);

                throttled();

                expect(count).toEqual(1);
                setTimeout(function () {
                    expect(count).toEqual(1);
                    done();
                }, 35);
            });

            it('should support a leading option', function () {
                var fn = function (param) {
                    return param;
                };
                var withLeading = CMS.API.Helpers.throttle(fn, 10, { leading: true });
                var withoutLeading = CMS.API.Helpers.throttle(fn, 10, { leading: false });
                expect(withLeading('a')).toEqual('a');
                expect(withoutLeading('a')).toEqual(undefined);
            });

            it('should support a trailing option', function (done) {
                var withCount = 0;
                var withoutCount = 0;
                var withTrailing = CMS.API.Helpers.throttle(function (param) {
                    withCount++;
                    return param;
                }, 10, { trailing: true });
                var withoutTrailing = CMS.API.Helpers.throttle(function (param) {
                    withoutCount++;
                    return param;
                }, 10, { trailing: false });

                expect(withTrailing('a')).toEqual('a');
                expect(withTrailing('b')).toEqual('a');

                expect(withoutTrailing('a')).toEqual('a');
                expect(withoutTrailing('b')).toEqual('a');

                setTimeout(function () {
                    expect(withCount).toEqual(2);
                    expect(withoutCount).toEqual(1);
                    done();
                }, 20);
            });

            it('should use correct `this` value', function () {
                var actual = [];
                var object = {
                    method: CMS.API.Helpers.throttle(function () {
                        actual.push(this);
                    }, 10)
                };

                object.method();
                object.method();

                expect([object]).toEqual(actual);
            });
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
