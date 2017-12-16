'use strict';
var CMS = require('../../../static/cms/js/modules/cms.base').default;
var Sideframe = require('../../../static/cms/js/modules/cms.sideframe').default;
var Messages = require('../../../static/cms/js/modules/cms.messages').default;
var $ = require('jquery');
import Toolbar from '../../../static/cms/js/modules/cms.toolbar';
import Modal from '../../../static/cms/js/modules/cms.modal';

CMS.API = CMS.API || {};
CMS.API.Helpers = Toolbar.__GetDependency__('Helpers');
CMS.KEYS = Toolbar.__GetDependency__('KEYS');

window.CMS = window.CMS || CMS;
CMS.Toolbar = Toolbar;
CMS.Modal = Modal;
CMS.Sideframe = Sideframe;
CMS.Messages = Messages;
var showLoader;
var hideLoader;

class Navigation {}

describe('CMS.Toolbar', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    beforeEach(() => {
        showLoader = jasmine.createSpy();
        hideLoader = jasmine.createSpy();
        Toolbar.__Rewire__('showLoader', showLoader);
        Toolbar.__Rewire__('hideLoader', hideLoader);
        Toolbar.__Rewire__('Navigation', Navigation);
    });

    afterEach(() => {
        Toolbar.__ResetDependency__('Navigation');
        Toolbar.__ResetDependency__('showLoader');
        Toolbar.__ResetDependency__('hideLoader');
    });

    it('creates a Toolbar class', function () {
        expect(CMS.Toolbar).toBeDefined();
    });

    it('has public API', function () {
        expect(CMS.Toolbar.prototype.showLoader).toEqual(jasmine.any(Function));
        expect(CMS.Toolbar.prototype.hideLoader).toEqual(jasmine.any(Function));
        expect(CMS.Toolbar.prototype.openAjax).toEqual(jasmine.any(Function));
    });

    describe('instance', function () {
        var toolbar;
        beforeEach(function (done) {
            fixture.load('toolbar.html');

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

        it('has ui', function () {
            expect(toolbar.ui).toEqual(jasmine.any(Object));
            expect(Object.keys(toolbar.ui)).toContain('container');
            expect(Object.keys(toolbar.ui)).toContain('body');
            expect(Object.keys(toolbar.ui)).toContain('window');
            expect(Object.keys(toolbar.ui)).toContain('document');
            expect(Object.keys(toolbar.ui)).toContain('toolbar');
            expect(Object.keys(toolbar.ui)).toContain('navigations');
            expect(Object.keys(toolbar.ui)).toContain('buttons');
            expect(Object.keys(toolbar.ui)).toContain('messages');
            expect(Object.keys(toolbar.ui)).toContain('structureBoard');
            expect(Object.keys(toolbar.ui)).toContain('revert');
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
            CMS.Toolbar.prototype._initialStates.and.callThrough();
            CMS.Toolbar.prototype._initialStates.calls.reset();
            CMS.settings = { sideframe: {}, version: 'fake' };
            CMS.config = { settings: { version: 'fake' }, auth: true };
            toolbar.ui.document.on('cms-ready', function () {
                // expect this to happen
                done();
            });
            toolbar = new CMS.Toolbar();
            expect(CMS.Toolbar.prototype._initialStates).toHaveBeenCalled();
            expect(toolbar.ui.body).toHaveClass('cms-ready');
        });

        it('sets the "ready" data on the toolbar ui', function () {
            expect(toolbar.ui.toolbar.data('ready')).toEqual(true);

            toolbar.ui.toolbar.data('ready', false);
            new CMS.Toolbar();
            expect(toolbar.ui.toolbar.data('ready')).toEqual(true);
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
            expect(toolbar.openAjax({ url: '/url' })).toEqual(jasmine.any(Object));
            expect(showLoader).toHaveBeenCalled();
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

            var callback = jasmine.createSpy();

            toolbar.openAjax({
                url: '/url',
                callback: callback
            });

            expect(callback).toHaveBeenCalled();
            expect(callback).toHaveBeenCalledWith(toolbar, 'response');
            expect(hideLoader).toHaveBeenCalled();
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

            toolbar.openAjax({
                url: '/url',
                onSuccess: '/another-url'
            });

            expect(showLoader).toHaveBeenCalled();
            expect(hideLoader).not.toHaveBeenCalled();
        });

        it('uses custom onSuccess url from request success', function () {
            spyOn($, 'ajax').and.callFake(function () {
                return {
                    done: function (callback) {
                        callback({ url: '/redirect-url' });
                        return { fail: $.noop };
                    }
                };
            });

            spyOn(CMS.API.Helpers, 'reloadBrowser');

            toolbar.openAjax({
                url: '/url',
                onSuccess: 'FOLLOW_REDIRECT'
            });

            expect(CMS.API.Helpers.reloadBrowser).toHaveBeenCalledWith('/redirect-url');
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
            spyOn($.Event.prototype, 'preventDefault').and.callThrough();
            spyOn($.Event.prototype, 'stopImmediatePropagation').and.callThrough();
            spyOn(CMS.API.Helpers, 'secureConfirm').and.returnValues(false, true);

            var publishButton = toolbar.ui.buttons.eq(2).find('.cms-publish-page');
            publishButton.trigger(toolbar.click);
            expect($.Event.prototype.preventDefault).toHaveBeenCalledTimes(1);
            expect($.Event.prototype.stopImmediatePropagation).toHaveBeenCalledTimes(1);
            publishButton.trigger(toolbar.click);
            expect($.Event.prototype.preventDefault).toHaveBeenCalledTimes(2);
            expect($.Event.prototype.stopImmediatePropagation).toHaveBeenCalledTimes(1);
        });
    });

    describe('._screenBlock()', function () {
        var toolbar;
        beforeEach(function (done) {
            fixture.load('toolbar.html');
            CMS.config = {};
            CMS.settings = $.extend(CMS.settings, {
                toolbar: 'expanded'
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
        class FakeModal {
            constructor() {}
        }
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
            $(function () {
                spyOn(CMS.Toolbar.prototype, '_initialStates');
                toolbar = new CMS.Toolbar();
                Toolbar.__Rewire__('Modal', FakeModal);
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
            Toolbar.__ResetDependency__('Modal');
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

            FakeModal.prototype.open = modalOpen;

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
                method: undefined,
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

    describe('_refreshMarkup', () => {
        const diffDOMConstructor = jasmine.createSpy();
        const newToolbar = $('<div></div>');
        let toolbar;

        class DiffDOM {
            constructor() {
                diffDOMConstructor();
            }
        }
        DiffDOM.prototype.diff = jasmine.createSpy();
        DiffDOM.prototype.apply = jasmine.createSpy();

        const trigger = jasmine.createSpy();
        class FakeNavigation {
            constructor() {
                this.ui = {
                    window: {
                        trigger
                    }
                };
            }
        }

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
            $(function () {
                Toolbar.__Rewire__('Navigation', FakeNavigation);
                Toolbar.__Rewire__('DiffDOM', DiffDOM);
                spyOn(CMS.Toolbar.prototype, '_initialStates');
                toolbar = new CMS.Toolbar();
                spyOn(toolbar, 'setSettings').and.callFake(function (input) {
                    return $.extend(true, CMS.settings, input);
                });
                spyOn(toolbar, '_setupUI');
                spyOn(toolbar, '_events');
                CMS.API.Clipboard = {
                    ui: {},
                    _toolbarEvents: jasmine.createSpy()
                };

                jasmine.clock().install();
                done();
            });
        });

        afterEach(function (done) {
            jasmine.clock().uninstall();
            Toolbar.__ResetDependency__('Navigation');
            Toolbar.__ResetDependency__('DiffDOM');
            fixture.cleanup();
            setTimeout(function () {
                done();
            }, 200);
        });

        it('refreshes markup', () => {
            toolbar.navigation = null;
            toolbar._refreshMarkup(newToolbar);
            expect(toolbar._setupUI).toHaveBeenCalledTimes(1);
            expect(toolbar._events).toHaveBeenCalledTimes(1);
            expect(toolbar.navigation instanceof FakeNavigation).toEqual(true);
            expect(DiffDOM.prototype.diff).toHaveBeenCalledTimes(1);
            expect(DiffDOM.prototype.apply).toHaveBeenCalledTimes(1);
            expect(trigger).toHaveBeenCalledWith('resize');
            expect(CMS.API.Clipboard._toolbarEvents).toHaveBeenCalledTimes(1);
        });
    });
});
