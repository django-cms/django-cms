'use strict';

describe('CMS.Toolbar', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a Toolbar class', function () {
        expect(CMS.Toolbar).toBeDefined();
    });

    it('has public API', function () {
        expect(CMS.Toolbar.prototype.toggle).toEqual(jasmine.any(Function));
        expect(CMS.Toolbar.prototype.open).toEqual(jasmine.any(Function));
        expect(CMS.Toolbar.prototype.close).toEqual(jasmine.any(Function));
        expect(CMS.Toolbar.prototype.showLoader).toEqual(jasmine.any(Function));
        expect(CMS.Toolbar.prototype.hideLoader).toEqual(jasmine.any(Function));
        expect(CMS.Toolbar.prototype.openAjax).toEqual(jasmine.any(Function));
    });

    describe('instance', function () {
        var toolbar;
        beforeEach(function (done) {
            fixture.load('toolbar.html');

            $(function () {
                spyOn(CMS.Navigation.prototype, 'initialize').and.callFake(function () {
                    return {};
                });
                toolbar = new CMS.Toolbar();
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('has ui', function () {
            expect(toolbar.ui).toEqual(jasmine.any(Object));
            expect(Object.keys(toolbar.ui)).toContain('container');
            expect(Object.keys(toolbar.ui)).toContain('body');
            expect(Object.keys(toolbar.ui)).toContain('window');
            expect(Object.keys(toolbar.ui)).toContain('document');
            expect(Object.keys(toolbar.ui)).toContain('toolbar');
            expect(Object.keys(toolbar.ui)).toContain('toolbarTrigger');
            expect(Object.keys(toolbar.ui)).toContain('navigations');
            expect(Object.keys(toolbar.ui)).toContain('buttons');
            expect(Object.keys(toolbar.ui)).toContain('messages');
            expect(Object.keys(toolbar.ui)).toContain('screenBlock');
            expect(Object.keys(toolbar.ui)).toContain('structureBoard');
            expect(Object.keys(toolbar.ui).length).toEqual(11);
        });

        it('has options', function () {
            expect(toolbar.options).toEqual({
                toolbarDuration: 200
            });

            var toolbar2 = new CMS.Toolbar({ toolbarDuration: 250, nonExistent: true });
            expect(toolbar2.options).toEqual({
                toolbarDuration: 250,
                nonExistent: true
            });
        });

        // this spec can be thoroughly expanded, but for the moment just checking for the
        // class and event is sufficient
        it('initializes the states', function (done) {
            spyOn(CMS.Toolbar.prototype, '_initialStates').and.callThrough();
            CMS.settings = { sideframe: {}, version: 'fake' };
            CMS.config = { settings: { version: 'fake' }, auth: true };
            jasmine.clock().install();
            toolbar = new CMS.Toolbar();
            toolbar.ui.document.on('cms-ready', function () {
                // expect this to happen
                jasmine.clock().uninstall();
                done();
            });
            expect(toolbar._initialStates).not.toHaveBeenCalled();
            jasmine.clock().tick(200);
            expect(toolbar._initialStates).toHaveBeenCalled();
            expect(toolbar.ui.body).toHaveClass('cms-ready');
        });

        it('sets the "ready" data on the toolbar ui', function () {
            expect(toolbar.ui.toolbar.data('ready')).toEqual(true);

            toolbar.ui.toolbar.data('ready', false);
            var toolbar1 = new CMS.Toolbar();
            expect(toolbar.ui.toolbar.data('ready')).toEqual(true);
        });
    });

    describe('.toggle()', function () {
        var toolbar;
        beforeEach(function (done) {
            fixture.load('toolbar.html');
            $(function () {
                CMS.settings = {
                    toolbar: 'collapsed'
                };
                spyOn(CMS.Navigation.prototype, 'initialize').and.callFake(function () {
                    return {};
                });
                toolbar = new CMS.Toolbar();
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('delegates to `open()`', function () {
            spyOn(toolbar, 'open');
            spyOn(toolbar, 'close');
            toolbar.toggle();
            expect(toolbar.open).toHaveBeenCalled();
            expect(toolbar.close).not.toHaveBeenCalled();
        });

        it('delegates to `close()`', function () {
            CMS.settings.toolbar = 'expanded';
            spyOn(toolbar, 'open');
            spyOn(toolbar, 'close');
            toolbar.toggle();
            expect(toolbar.open).not.toHaveBeenCalled();
            expect(toolbar.close).toHaveBeenCalled();
        });
    });

    describe('.open', function () {
        var toolbar;
        beforeEach(function (done) {
            fixture.load('toolbar.html');
            CMS.config = {};
            CMS.settings = {
                toolbar: 'collapsed'
            };
            spyOn(CMS.Navigation.prototype, 'initialize').and.callFake(function () {
                return {};
            });
            $(function () {
                toolbar = new CMS.Toolbar();
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('opens toolbar and remembers the state', function () {
            expect(CMS.settings.toolbar).toEqual('collapsed');
            spyOn(toolbar, '_show');
            toolbar.open();
            expect(toolbar._show).toHaveBeenCalled();
            expect(CMS.settings.toolbar).toEqual('expanded');
        });

        it('animates toolbar with correct duration', function () {
            spyOn($.fn, 'css').and.callThrough();
            toolbar.open();
            expect($.fn.css).toHaveBeenCalledWith({
                'transition': 'margin-top 200ms',
                'margin-top': 0
            });

            toolbar.open({ duration: 10 });
            expect($.fn.css).toHaveBeenCalledWith({
                'transition': 'margin-top 10ms',
                'margin-top': 0
            });
        });

        it('animates toolbar and body to correct position', function () {
            spyOn($.fn, 'css').and.callThrough();
            spyOn($.fn, 'animate').and.callThrough();

            toolbar.open();
            expect($.fn.css).toHaveBeenCalledWith({
                'transition': 'margin-top 200ms',
                'margin-top': 0
            });
            expect($.fn.animate).toHaveBeenCalledWith(
                jasmine.any(Object),
                200,
                'linear',
                jasmine.any(Function)
            );
            // here we have to use toBeCloseTo because different browsers report different values
            // e.g. FF reports 45.16666
            expect($.fn.animate.calls.mostRecent().args[0]['margin-top']).toBeCloseTo(45, 0);
        });

        it('animates toolbar and body to correct position if debug is true', function () {
            spyOn($.fn, 'css').and.callThrough();
            spyOn($.fn, 'animate').and.callThrough();

            $('<div class="cms-debug-bar"></div>').css({
                height: '15px'
            }).prependTo('#cms-top');

            toolbar.open();
            expect($.fn.css).toHaveBeenCalledWith({
                'transition': 'margin-top 200ms',
                'margin-top': 0
            });
            expect($.fn.animate).toHaveBeenCalledWith(
                jasmine.any(Object),
                200,
                'linear',
                jasmine.any(Function)
            );
            // here we have to use toBeCloseTo because different browsers report different values
            // e.g. FF reports 45.16666
            expect($.fn.animate.calls.mostRecent().args[0]['margin-top']).toBeCloseTo(60, 0);
        });

        it('turns the disclosure triangle into correct position', function (done) {
            spyOn($.fn, 'animate').and.callFake(function (opts, timeout, easing, callback) {
                expect(toolbar.ui.body).not.toHaveClass('cms-toolbar-expanded');
                callback();
                expect(toolbar.ui.body).toHaveClass('cms-toolbar-expanded');
                done();
            });
            toolbar.ui.toolbarTrigger.removeClass('cms-toolbar-trigger-expanded');
            toolbar.ui.body.removeClass('cms-toolbar-expanded');
            toolbar.open();
            expect(toolbar.ui.toolbarTrigger).toHaveClass('cms-toolbar-trigger-expanded');
        });
    });

    describe('.close()', function () {
        var toolbar;
        beforeEach(function (done) {
            fixture.load('toolbar.html');
            CMS.config = {};
            CMS.settings = {
                toolbar: 'expanded'
            };
            spyOn(CMS.Navigation.prototype, 'initialize').and.callFake(function () {
                return {};
            });
            $(function () {
                toolbar = new CMS.Toolbar();
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('closes toolbar and remembers state', function () {
            expect(CMS.settings.toolbar).toEqual('expanded');
            spyOn(toolbar, '_hide');
            toolbar.close();
            expect(toolbar._hide).toHaveBeenCalled();
            expect(CMS.settings.toolbar).toEqual('collapsed');
        });

        it('does not close toolbar if it is locked', function () {
            spyOn($.fn, 'animate').and.callFake(function (opts, timeout, easing, callback) {
                callback();
            });
            toolbar.open();
            toolbar._lock(true);
            // can only check it this way, since we don't propagate
            // this value to `.close()`
            expect(toolbar._hide()).toEqual(false);
            toolbar.close();
            expect(toolbar.ui.body).toHaveClass('cms-toolbar-expanded');
            expect(toolbar.ui.toolbarTrigger).toHaveClass('cms-toolbar-trigger-expanded');

            toolbar._lock(false);
            expect(toolbar._hide()).toEqual(undefined);
            toolbar.close();
            expect(toolbar.ui.body).not.toHaveClass('cms-toolbar-expanded');
            expect(toolbar.ui.toolbarTrigger).not.toHaveClass('cms-toolbar-trigger-expanded');
        });

        it('animates toolbar and body to correct position', function () {
            toolbar.open();

            spyOn($.fn, 'css').and.callThrough();
            spyOn($.fn, 'animate').and.callThrough();

            toolbar.close();
            expect($.fn.css).toHaveBeenCalledWith(
                'transition', 'margin-top 200ms'
            );
            expect($.fn.css).toHaveBeenCalledWith(
                'margin-top', jasmine.any(Number)
            );

            expect($.fn.animate).toHaveBeenCalledWith(
                { 'margin-top': 0 },
                200,
                'linear',
                jasmine.any(Function)
            );
            // here we have to use toBeCloseTo because different browsers report different values
            // e.g. FF reports -55.16666
            expect($.fn.css.calls.argsFor(1)[1]).toBeCloseTo(-55, 0);
        });

        it('animates toolbar and body to correct position if debug is true', function () {
            CMS.config = CMS.config || {};
            CMS.config.debug = true;
            $('<div class="cms-debug-bar"></div>').css({
                height: '15px'
            }).prependTo('#cms-top');

            toolbar.open();

            spyOn($.fn, 'animate').and.callThrough();

            toolbar.close();

            expect($.fn.animate).toHaveBeenCalledWith(
                { 'margin-top': 5 },
                200,
                'linear',
                jasmine.any(Function)
            );
        });

        it('turns the disclosure triangle into correct position', function (done) {
            spyOn($.fn, 'animate').and.callFake(function (opts, timeout, easing, callback) {
                expect(toolbar.ui.toolbarTrigger).toHaveClass('cms-toolbar-trigger-expanded');
                callback()
                expect(toolbar.ui.body).toHaveClass('cms-toolbar-expanded');
            });

            toolbar.open();

            $.fn.animate.and.callFake(function (opts, timeout, easing, callback) {
                expect(toolbar.ui.body).toHaveClass('cms-toolbar-expanded');
                callback();
                expect(toolbar.ui.body).not.toHaveClass('cms-toolbar-expanded');
                done();
            });

            toolbar.close();
            expect(toolbar.ui.toolbarTrigger).not.toHaveClass('cms-toolbar-trigger-expanded');
        });
    });

    describe('.showLoader() / hideLoader()', function () {
        var toolbar;
        beforeEach(function (done) {
            fixture.load('toolbar.html');
            CMS.config = {};
            CMS.settings = {
                toolbar: 'expanded'
            };
            spyOn(CMS.Navigation.prototype, 'initialize').and.callFake(function () {
                return {};
            });
            $(function () {
                toolbar = new CMS.Toolbar();
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('shows the loader', function () {
            expect(toolbar.ui.toolbarTrigger).not.toHaveClass('cms-toolbar-loader');
            toolbar.showLoader();
            expect(toolbar.ui.toolbarTrigger).toHaveClass('cms-toolbar-loader');
        });
        it('hides the loader', function () {
            toolbar.showLoader();
            expect(toolbar.ui.toolbarTrigger).toHaveClass('cms-toolbar-loader');
            toolbar.hideLoader();
            expect(toolbar.ui.toolbarTrigger).not.toHaveClass('cms-toolbar-loader');
        });
    });

    describe('.openAjax()', function () {
        var toolbar;
        beforeEach(function (done) {
            fixture.load('toolbar.html');
            CMS.config = {};
            CMS.settings = {
                toolbar: 'expanded'
            };
            spyOn(CMS.Navigation.prototype, 'initialize').and.callFake(function () {
                return {};
            });
            jasmine.Ajax.install();
            $(function () {
                toolbar = new CMS.Toolbar();
                done();
            });
        });

        afterEach(function () {
            jasmine.Ajax.uninstall();
            fixture.cleanup();
        });

        it('makes the request', function () {
            expect(toolbar.openAjax({ url: '/url' })).toEqual(jasmine.any(Object));
            var request = jasmine.Ajax.requests.mostRecent();
            expect(request.url).toEqual('/url');
        });

        it('does not make the request if there is a confirmation that is not succeeded', function () {
            spyOn(CMS.API.Helpers, 'secureConfirm').and.callFake(function (question) {
                expect(question).toEqual('Are you sure?');
                return false;
            });
            expect(toolbar.openAjax({ url: '/url', text: 'Are you sure?' })).toEqual(false);
        });

        it('shows the loader before making the request', function () {
            spyOn(toolbar, 'showLoader');
            expect(toolbar.openAjax({ url: '/url' })).toEqual(jasmine.any(Object));
            expect(toolbar.showLoader).toHaveBeenCalled();
        });

        it('uses custom callback after request succeeds and hides the loader', function () {
            spyOn($, 'ajax').and.callFake(function () {
                return {
                    done: function (callback) {
                        callback('response');
                        return { fail: $.noop };
                    }
                };
            });
            spyOn(toolbar, 'hideLoader');

            var callback = jasmine.createSpy();

            toolbar.openAjax({
                url: '/url',
                callback: callback
            });

            expect(callback).toHaveBeenCalled();
            expect(callback).toHaveBeenCalledWith(toolbar, 'response');
            expect(toolbar.hideLoader).toHaveBeenCalled();
        });

        it('does not hide the loader if no callback provided', function () {
            spyOn($, 'ajax').and.callFake(function () {
                return {
                    done: function (callback) {
                        callback('response');
                        return { fail: $.noop };
                    }
                };
            });

            spyOn(CMS.API.Helpers, 'reloadBrowser');
            spyOn(toolbar, 'showLoader');
            spyOn(toolbar, 'hideLoader');

            toolbar.openAjax({
                url: '/url',
                onSuccess: '/another-url'
            });

            expect(toolbar.showLoader).toHaveBeenCalled();
            expect(toolbar.hideLoader).not.toHaveBeenCalled();
        });

        it('uses custom onSuccess url after request succeeds', function () {
            spyOn($, 'ajax').and.callFake(function () {
                return {
                    done: function (callback) {
                        callback('response');
                        return { fail: $.noop };
                    }
                };
            });

            spyOn(CMS.API.Helpers, 'reloadBrowser');

            toolbar.openAjax({
                url: '/url',
                onSuccess: '/another-url'
            });

            expect(CMS.API.Helpers.reloadBrowser).toHaveBeenCalledWith('/another-url', false, true);
        });

        it('reloads the page if no callback or onSuccess passed', function () {
            spyOn($, 'ajax').and.callFake(function () {
                return {
                    done: function (callback) {
                        callback('response');
                        return { fail: $.noop };
                    }
                };
            });

            spyOn(CMS.API.Helpers, 'reloadBrowser');

            toolbar.openAjax({
                url: '/url'
            });

            expect(CMS.API.Helpers.reloadBrowser).toHaveBeenCalledWith(false, false, true);
        });

        it('handles parameters', function () {
            spyOn($, 'ajax').and.callFake(function (param) {
                expect(param.data).toEqual({ param1: true, param2: false, param3: 150, param4: 'alala' });
                return {
                    done: function () {
                        return { fail: $.noop };
                    }
                };
            });

            toolbar.openAjax({
                url: '/whatever',
                post: JSON.stringify({ param1: true, param2: false, param3: 150, param4: 'alala' })
            });
        });

        it('opens an error message if request failed', function () {
            CMS.API.Messages = new CMS.Messages();
            spyOn(CMS.API.Messages, 'open');

            spyOn($, 'ajax').and.callFake(function () {
                return {
                    done: function () {
                        return {
                            fail: function (callback) {
                                callback({
                                    responseText: 'An error occured',
                                    status: 418,
                                    statusText: "I'm a teapot"
                                });
                            }
                        };
                    }
                };
            });

            toolbar.openAjax({
                url: '/whatever'
            });

            expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                message: "An error occured | 418 I'm a teapot",
                error: true
            });
        });

        it('unlocks the toolbar if request succeeds', function () {
            spyOn($, 'ajax').and.callFake(function () {
                return {
                    done: function (callback) {
                        callback('response');
                        return { fail: $.noop };
                    }
                };
            });

            spyOn(CMS.API.Helpers, 'reloadBrowser');
            CMS.API.locked = true;

            toolbar.openAjax({
                url: '/url'
            });

            expect(CMS.API.locked).toEqual(false);

            CMS.API.locked = true;

            toolbar.openAjax({
                url: '/url',
                callback: $.noop
            });

            expect(CMS.API.locked).toEqual(false);

            CMS.API.locked = true;

            toolbar.openAjax({
                url: '/url',
                onSuccess: '/another-url'
            });

            expect(CMS.API.locked).toEqual(false);
        });

        it('unlocks the toolbar if request fails', function () {
            CMS.API.Messages = new CMS.Messages();
            spyOn(CMS.API.Messages, 'open');

            spyOn($, 'ajax').and.callFake(function () {
                return {
                    done: function () {
                        return {
                            fail: function (callback) {
                                callback({
                                    responseText: 'An error occured',
                                    status: 418,
                                    statusText: "I'm a teapot"
                                });
                            }
                        };
                    }
                };
            });

            CMS.API.locked = true;

            toolbar.openAjax({
                url: '/whatever'
            });

            expect(CMS.API.locked).toEqual(false);
        });
    });
});
