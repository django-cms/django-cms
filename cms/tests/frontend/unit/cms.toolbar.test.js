'use strict';
var CMS = require('../../../static/cms/js/modules/cms.base');
var Toolbar = require('../../../static/cms/js/modules/cms.toolbar');
var $ = require('jquery');

window.CMS = window.CMS || CMS;
CMS.Toolbar = Toolbar;


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
                spyOn(CMS.Toolbar.prototype, '_initialStates');
                toolbar = new CMS.Toolbar();
                spyOn(toolbar, 'setSettings').and.callFake(function (input) {
                    return $.extend(true, CMS.settings, input);
                });
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
            expect(Object.keys(toolbar.ui)).toContain('structureBoard');
            expect(Object.keys(toolbar.ui).length).toEqual(10);
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
            CMS.Toolbar.prototype._initialStates.and.callThrough();
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
            new CMS.Toolbar();
            expect(toolbar.ui.toolbar.data('ready')).toEqual(true);
        });
    });

    describe('.toggle()', function () {
        var toolbar;
        beforeEach(function (done) {
            fixture.load('toolbar.html');
            $(function () {
                CMS.settings = $.extend(CMS.settings, {
                    toolbar: 'collapsed'
                });
                spyOn(CMS.Navigation.prototype, 'initialize').and.callFake(function () {
                    return {};
                });
                spyOn(CMS.Toolbar.prototype, '_initialStates');
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
            CMS.settings = $.extend(CMS.settings, {
                toolbar: 'collapsed'
            });
            spyOn(CMS.Navigation.prototype, 'initialize').and.callFake(function () {
                return {};
            });
            spyOn(CMS.Toolbar.prototype, '_initialStates');
            $(function () {
                toolbar = new CMS.Toolbar();
                spyOn(toolbar, 'setSettings').and.callFake(function (input) {
                    return $.extend(true, CMS.settings, input);
                });
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
            // have to cleanup here because previous test `animate` call isn't finished yet
            toolbar.ui.body.removeClass('cms-toolbar-collapsing cms-toolbar-expanded cms-toolbar-expanding');
            // eslint-disable-next-line max-params
            spyOn($.fn, 'animate').and.callFake(function (opts, timeout, easing, callback) {
                expect(toolbar.ui.toolbarTrigger).toHaveClass('cms-toolbar-trigger-expanded');
                expect(toolbar.ui.body).not.toHaveClass('cms-toolbar-collapsing');
                expect(toolbar.ui.body).not.toHaveClass('cms-toolbar-expanded');
                expect(toolbar.ui.body).toHaveClass('cms-toolbar-expanding');
                callback();
                expect(toolbar.ui.body).not.toHaveClass('cms-toolbar-collapsing');
                expect(toolbar.ui.body).not.toHaveClass('cms-toolbar-expanding');
                expect(toolbar.ui.body).toHaveClass('cms-toolbar-expanded');
                done();
            });
            toolbar.ui.toolbarTrigger.removeClass('cms-toolbar-trigger-expanded');
            toolbar.ui.body.removeClass('cms-toolbar-expanded');
            toolbar.open();
        });
    });

    describe('.close()', function () {
        var toolbar;
        beforeEach(function (done) {
            fixture.load('toolbar.html');
            CMS.config = {};
            CMS.settings = $.extend(CMS.settings, {
                toolbar: 'expanded'
            });
            spyOn(CMS.Navigation.prototype, 'initialize').and.callFake(function () {
                return {};
            });
            $(function () {
                spyOn(CMS.Toolbar.prototype, '_initialStates');
                toolbar = new CMS.Toolbar();
                spyOn(toolbar, 'setSettings').and.callFake(function (input) {
                    return $.extend(true, CMS.settings, input);
                });
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
            // eslint-disable-next-line max-params
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
            expect(toolbar._hide()).not.toBeDefined();
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
            // eslint-disable-next-line max-params
            spyOn($.fn, 'animate').and.callFake(function (opts, timeout, easing, callback) {
                expect(toolbar.ui.toolbarTrigger).toHaveClass('cms-toolbar-trigger-expanded');
                callback();
                expect(toolbar.ui.body).toHaveClass('cms-toolbar-expanded');
            });

            toolbar.open();

            // eslint-disable-next-line max-params
            $.fn.animate.and.callFake(function (opts, timeout, easing, callback) {
                expect(toolbar.ui.toolbarTrigger).not.toHaveClass('cms-toolbar-trigger-expanded');
                expect(toolbar.ui.body).toHaveClass('cms-toolbar-expanded');
                expect(toolbar.ui.body).not.toHaveClass('cms-toolbar-expanding');
                expect(toolbar.ui.body).toHaveClass('cms-toolbar-collapsing');
                callback();
                expect(toolbar.ui.body).not.toHaveClass('cms-toolbar-expanded');
                expect(toolbar.ui.body).not.toHaveClass('cms-toolbar-collapsing');
                expect(toolbar.ui.body).not.toHaveClass('cms-toolbar-expanding');
                done();
            });

            toolbar.close();
        });
    });

    describe('.showLoader() / hideLoader()', function () {
        var toolbar;
        beforeEach(function (done) {
            fixture.load('toolbar.html');
            CMS.config = {};
            CMS.settings = $.extend(CMS.settings, {
                toolbar: 'expanded'
            });
            spyOn(CMS.Navigation.prototype, 'initialize').and.callFake(function () {
                return {};
            });
            $(function () {
                spyOn(CMS.Toolbar.prototype, '_initialStates');
                toolbar = new CMS.Toolbar();
                spyOn(toolbar, 'setSettings').and.callFake(function (input) {
                    return $.extend(true, CMS.settings, input);
                });
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
            CMS.settings = $.extend(CMS.settings, {
                toolbar: 'expanded'
            });
            spyOn(CMS.Navigation.prototype, 'initialize').and.callFake(function () {
                return {};
            });
            jasmine.Ajax.install();
            $(function () {
                spyOn(CMS.Toolbar.prototype, '_initialStates');
                toolbar = new CMS.Toolbar();
                spyOn(toolbar, 'setSettings').and.callFake(function (input) {
                    return $.extend(true, CMS.settings, input);
                });
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

    describe('._events()', function () {
        var toolbar;
        beforeEach(function (done) {
            fixture.load('toolbar.html');
            CMS.config = {
                lang: {
                    publish: 'publish?'
                }
            };
            CMS.settings = $.extend(CMS.settings, {
                toolbar: 'expanded'
            });
            spyOn(CMS.Navigation.prototype, 'initialize').and.callFake(function () {
                return {};
            });
            $(function () {
                spyOn(CMS.Toolbar.prototype, '_initialStates');
                toolbar = new CMS.Toolbar();
                spyOn(toolbar, 'setSettings').and.callFake(function (input) {
                    return $.extend(true, CMS.settings, input);
                });
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('attaches event handlers to toolbar trigger', function () {
            toolbar.ui.toolbarTrigger.off(toolbar.pointerUp);
            toolbar.ui.toolbarTrigger.off(toolbar.click);

            toolbar._events();

            expect(toolbar.ui.toolbarTrigger).toHandle(toolbar.pointerUp);
            expect(toolbar.ui.toolbarTrigger).toHandle(toolbar.click);

            spyOn(toolbar, 'toggle');

            toolbar.ui.document.off(toolbar.click);
            toolbar.ui.document.on(toolbar.click, function () {
                expect(toolbar.toggle).toHaveBeenCalled();
            });

            toolbar.ui.toolbarTrigger.trigger(toolbar.pointerUp);
            toolbar.ui.toolbarTrigger.trigger(toolbar.click);
        });

        it('attaches event handlers to navigation menu links', function () {
            spyOn(toolbar, '_delegate');

            var emptyLink = $(toolbar.ui.navigations[0]).find('a').eq(0);
            var pagesLink = $(toolbar.ui.navigations[0]).find('a').eq(1);

            emptyLink.trigger('click');
            expect(toolbar._delegate).not.toHaveBeenCalled();

            pagesLink.trigger('click');

            expect(toolbar._delegate).toHaveBeenCalledTimes(1);
            expect(toolbar._delegate).toHaveBeenCalledWith(pagesLink);
        });

        it('attaches event handlers to navigation menu links (to open in new window)', function () {
            var fakeWindow = {
                open: jasmine.createSpy()
            };
            spyOn(toolbar, '_delegate');
            spyOn(CMS.API.Helpers, '_getWindow').and.callFake(function () {
                return fakeWindow;
            });

            var emptyLink = $(toolbar.ui.navigations[0]).find('a').eq(0);
            var pagesLink = $(toolbar.ui.navigations[0]).find('a').eq(1);

            emptyLink.trigger(new $.Event('keydown', { keyCode: CMS.KEYS.CTRL }));
            emptyLink.trigger('click');
            expect(toolbar._delegate).not.toHaveBeenCalled();
            expect(fakeWindow.open).not.toHaveBeenCalled();

            emptyLink.trigger(new $.Event('keydown', { keyCode: CMS.KEYS.CTRL }));
            pagesLink.trigger('click');
            expect(toolbar._delegate).not.toHaveBeenCalledTimes(1);
            expect(fakeWindow.open).toHaveBeenCalledWith(jasmine.stringMatching('cms/page'), '_blank');

            pagesLink.trigger('keyup');
        });

        it('attaches event handlers to navigation menu lists', function () {
            var firstMenuItem = $(toolbar.ui.navigations.find('> li')[0]);
            toolbar.ui.structureBoard = $('<div></div>');

            expect(toolbar.ui.document).not.toHandle(toolbar.click);
            expect(toolbar.ui.structureBoard).not.toHandle(toolbar.click);
            expect(toolbar.ui.toolbar).not.toHandle(toolbar.click);
            expect(toolbar.ui.window).not.toHandle(toolbar.resize + '.menu.reset');
            firstMenuItem.trigger('click');
            expect(toolbar.ui.document).toHandle(toolbar.click);
            expect(toolbar.ui.structureBoard).toHandle(toolbar.click);
            expect(toolbar.ui.toolbar).toHandle(toolbar.click);
            expect(toolbar.ui.window).toHandle(toolbar.resize + '.menu.reset');
        });


        it('handles mousemove over top level toolbar items', function () {
            var firstMenuItem = $(toolbar.ui.navigations.find('> li')[0]);
            var secondMenuItem = $(toolbar.ui.navigations.find('> li')[1]);
            var thirdMenuItem = $(toolbar.ui.navigations.find('> li')[2]);

            firstMenuItem.trigger('click');

            var clickFirstMenuItem = spyOnEvent(firstMenuItem, toolbar.click);
            var clickSecondMenuItem = spyOnEvent(secondMenuItem, toolbar.click);
            var clickThirdMenuItem = spyOnEvent(thirdMenuItem, toolbar.click);

            firstMenuItem.trigger('mouseenter');
            expect(clickFirstMenuItem).not.toHaveBeenTriggered();

            secondMenuItem.trigger('mouseenter');
            expect(clickSecondMenuItem).toHaveBeenTriggered();

            thirdMenuItem.trigger('mouseenter');
            expect(clickThirdMenuItem).toHaveBeenTriggered();
        });

        it('does not care for mouse over top level items if touch is enabled', function () {
            var firstMenuItem = $(toolbar.ui.navigations.find('> li')[0]);
            var secondMenuItem = $(toolbar.ui.navigations.find('> li')[1]);

            firstMenuItem.find('a').trigger('touchstart');
            firstMenuItem.trigger('click');

            var clickFirstMenuItem = spyOnEvent(firstMenuItem, toolbar.click);
            var clickSecondMenuItem = spyOnEvent(secondMenuItem, toolbar.click);

            firstMenuItem.trigger('mouseenter');
            expect(clickFirstMenuItem).not.toHaveBeenTriggered();
            secondMenuItem.trigger('mouseenter');
            expect(clickSecondMenuItem).not.toHaveBeenTriggered();
        });

        it('closes the menu item if it is open', function () {
            var firstMenuItem = $(toolbar.ui.navigations.find('> li')[0]);

            firstMenuItem.trigger('click');
            expect(firstMenuItem).toHaveClass('cms-toolbar-item-navigation-hover');

            firstMenuItem.trigger('click');
            expect(firstMenuItem).not.toHaveClass('cms-toolbar-item-navigation-hover');
        });

        it('handles mousemove over nested toolbar items', function () {
            var menuItem = $(toolbar.ui.navigations.find('> li')[1]);
            var subMenu = menuItem.find('> ul');
            var childrenSubMenuItem = subMenu.find('> li').eq(0);

            spyOn($.fn, 'show').and.callThrough();

            expect(childrenSubMenuItem.find('> ul')).not.toBeVisible();
            childrenSubMenuItem.trigger('pointerover');
            expect($.fn.show).toHaveBeenCalledTimes(1);
            expect($.fn.show.calls.mostRecent().object).toEqual(childrenSubMenuItem.find('> ul'));
        });

        it('attaches event handlers to buttons with data-rel', function () {
            spyOn(toolbar, '_delegate');
            var createButton = toolbar.ui.buttons.eq(0).find('a');
            createButton.trigger(toolbar.click);
            expect(toolbar._delegate).toHaveBeenCalled();
        });

        it('attaches event handlers to buttons without data-rel', function () {
            var createButton = toolbar.ui.buttons.eq(1).find('a:first');
            spyOn($.Event.prototype, 'stopPropagation');
            createButton.trigger(toolbar.click);
            expect($.Event.prototype.stopPropagation).toHaveBeenCalled();
        });

        it('attaches a handler to publish page button', function () {
            spyOn($, 'ajax');
            spyOn($.Event.prototype, 'preventDefault');
            spyOn(CMS.API.Helpers, 'secureConfirm').and.returnValues(false, true);

            var publishButton = toolbar.ui.buttons.eq(3).find('.cms-publish-page');
            publishButton.trigger(toolbar.click);
            expect($.Event.prototype.preventDefault).toHaveBeenCalledTimes(2); // two handlers on same button
            publishButton.trigger(toolbar.click);
            expect($.Event.prototype.preventDefault).toHaveBeenCalledTimes(3); // one handler on same button
        });

        it('attaches a handler to publish button');
    });

    describe('._screenBlock()', function () {
        var toolbar;
        beforeEach(function (done) {
            fixture.load('toolbar.html');
            CMS.config = {};
            CMS.settings = $.extend(CMS.settings, {
                toolbar: 'expanded'
            });
            spyOn(CMS.Navigation.prototype, 'initialize').and.callFake(function () {
                return {};
            });
            $(function () {
                spyOn(CMS.Toolbar.prototype, '_initialStates');
                toolbar = new CMS.Toolbar();
                spyOn(toolbar, 'setSettings').and.callFake(function (input) {
                    return $.extend(true, CMS.settings, input);
                });
                toolbar.ui.window = $('<div></div>');
                toolbar.ui.screenBlock = $('<div></div>');
                spyOn($.fn, 'css').and.callThrough();
                done();
            });
        });

        afterEach(function () {
            var timeoutId = setInterval(function () {
            }, 10);

            for (var i; i <= timeoutId; i++) {
                clearInterval(i);
            }
            fixture.cleanup();
        });
    });

    describe('._delegate()', function () {
        var toolbar;
        var fakeWindow;
        beforeEach(function (done) {
            fixture.load('toolbar.html');
            CMS.config = {};
            CMS.settings = $.extend(CMS.settings, {
                toolbar: 'expanded'
            });
            fakeWindow = {
                location: {
                    href: '',
                    pathname: '/context.html',
                    search: ''
                }
            };
            spyOn(CMS.Navigation.prototype, 'initialize').and.callFake(function () {
                return {};
            });
            $(function () {
                spyOn(CMS.Toolbar.prototype, '_initialStates');
                toolbar = new CMS.Toolbar();
                spyOn(CMS.Modal.prototype, 'initialize');
                spyOn(CMS.Sideframe.prototype, 'initialize');
                spyOn(toolbar, 'openAjax');
                spyOn(CMS.API.Helpers, '_getWindow').and.returnValue(fakeWindow);
                spyOn(CMS.API.Messages, 'open');
                spyOn(toolbar, 'setSettings').and.callFake(function (input) {
                    return $.extend(true, CMS.settings, input);
                });
                done();
            });
        });

        afterEach(function (done) {
            fixture.cleanup();
            setTimeout(function () {
                done();
            }, 200);
        });

        it('return false if item is disabled', function () {
            expect(toolbar._delegate($('<div class="cms-btn-disabled"></div>'))).toEqual(false);
        });
        it('opens modal if item is "modal"', function () {
            var modalOpen = jasmine.createSpy();
            CMS.Modal.prototype.initialize.and.callFake(function (opts) {
                expect(opts.onClose).toEqual('test');
                return {
                    open: modalOpen
                };
            });

            toolbar._delegate($('<div href="href" data-name="modal" data-rel="modal" data-on-close="test"></div>'));

            expect(modalOpen).toHaveBeenCalledWith({
                url: 'href?cms_path=%2Fcontext.html',
                title: 'modal'
            });
        });

        it('opens sideframe if item is "sideframe"', function () {
            var sideframeOpen = jasmine.createSpy();
            CMS.Sideframe.prototype.initialize.and.callFake(function (opts) {
                expect(opts.onClose).toEqual('test2');
                return {
                    open: sideframeOpen
                };
            });

            toolbar._delegate(
                $('<div href="href2" data-name="modal" data-rel="sideframe" data-on-close="test2"></div>')
            );

            expect(sideframeOpen).toHaveBeenCalledWith({
                url: 'href2',
                animate: true
            });
        });

        it('opens message if item is "message"', function () {
            toolbar._delegate($('<div data-rel="message" data-text="message!"></div>'));

            expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                message: 'message!'
            });
        });

        it('opens ajax request if item is "ajax"', function () {
            toolbar._delegate(
                $('<div href="href" data-rel="ajax" ' +
                  'data-post=\'{ "test": "shmest" }\' data-text="text" data-on-success="REFRESH"></div>')
            );

            expect(toolbar.openAjax).toHaveBeenCalledWith({
                url: 'href',
                post: '{"test":"shmest"}',
                text: 'text',
                onSuccess: 'REFRESH'
            });
        });

        it('just redirects to the page if nothing else', function () {
            expect(fakeWindow.location.href).toEqual('');
            toolbar._delegate(
                $('<div href="href"></div>')
            );
            expect(fakeWindow.location.href).toEqual('href');
        });
    });

    describe('._debug()', function () {
        var toolbar;
        beforeEach(function (done) {
            fixture.load('toolbar.html');
            CMS.config = {
                lang: {
                    debug: 'DEBUG!'
                }
            };
            CMS.settings = $.extend(CMS.settings, {
                toolbar: 'expanded'
            });
            spyOn(CMS.Navigation.prototype, 'initialize').and.callFake(function () {
                return {};
            });
            $(function () {
                spyOn(CMS.Toolbar.prototype, '_initialStates');
                toolbar = new CMS.Toolbar();
                toolbar.ui.container.append('<div class="cms-debug-bar"></div>');
                spyOn(toolbar, 'setSettings').and.callFake(function (input) {
                    return $.extend(true, CMS.settings, input);
                });

                spyOn(CMS.API.Messages, 'open');
                jasmine.clock().install();
                done();
            });
        });

        afterEach(function (done) {
            jasmine.clock().uninstall();
            fixture.cleanup();
            setTimeout(function () {
                done();
            }, 200);
        });

        it('shows debug information after timeout', function () {
            toolbar._debug();

            toolbar.ui.container.find('.cms-debug-bar').trigger(toolbar.mouseEnter);
            jasmine.clock().tick(10000);

            expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                message: 'DEBUG!'
            });
        });

        it('does not show debug information if not hovering after timeout', function () {
            toolbar._debug();

            toolbar.ui.container.find('.cms-debug-bar').trigger(toolbar.mouseEnter);
            jasmine.clock().tick(500);
            toolbar.ui.container.find('.cms-debug-bar').trigger(toolbar.mouseLeave);
            jasmine.clock().tick(10000);

            expect(CMS.API.Messages.open).not.toHaveBeenCalled();
        });
    });
});
