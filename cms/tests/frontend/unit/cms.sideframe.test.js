/* global window, document */
'use strict';

var CMS = require('../../../static/cms/js/modules/cms.base').default;
var Sideframe = require('../../../static/cms/js/modules/cms.sideframe').default;
var $ = require('jquery');
var showLoader;
var hideLoader;

window.CMS = window.CMS || CMS;
CMS.Sideframe = Sideframe;

describe('CMS.Sideframe', function() {
    beforeEach(() => {
        CMS.API.Helpers._isStorageSupported = true;
        showLoader = jasmine.createSpy();
        hideLoader = jasmine.createSpy();
        Sideframe.__Rewire__('showLoader', showLoader);
        Sideframe.__Rewire__('hideLoader', hideLoader);
    });

    afterEach(() => {
        Sideframe.__ResetDependency__('showLoader');
        Sideframe.__ResetDependency__('hideLoader');
    });

    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a Sideframe class', function() {
        expect(CMS.Sideframe).toBeDefined();
    });

    it('has public API', function() {
        expect(CMS.Sideframe.prototype.open).toEqual(jasmine.any(Function));
        expect(CMS.Sideframe.prototype.close).toEqual(jasmine.any(Function));
    });

    describe('instance', function() {
        var sideframe;
        beforeEach(function(done) {
            $(function() {
                CMS.settings = {
                    sideframe: {}
                };
                sideframe = new CMS.Sideframe();
                done();
            });
        });

        it('has ui', function() {
            expect(sideframe.ui).toEqual(jasmine.any(Object));
            expect(Object.keys(sideframe.ui)).toContain('sideframe');
            expect(Object.keys(sideframe.ui)).toContain('body');
            expect(Object.keys(sideframe.ui)).toContain('window');
            expect(Object.keys(sideframe.ui)).toContain('dimmer');
            expect(Object.keys(sideframe.ui)).toContain('close');
            expect(Object.keys(sideframe.ui)).toContain('frame');
            expect(Object.keys(sideframe.ui)).toContain('shim');
            expect(Object.keys(sideframe.ui)).toContain('historyBack');
            expect(Object.keys(sideframe.ui)).toContain('historyForward');
            expect(Object.keys(sideframe.ui).length).toEqual(9);
        });

        it('has options', function() {
            expect(sideframe.options).toEqual({
                onClose: false,
                sideframeDuration: 300
            });

            sideframe = new CMS.Sideframe({
                onClose: 'something',
                sideframeDuration: 310,
                something: 'else'
            });

            expect(sideframe.options).toEqual({
                onClose: 'something',
                sideframeDuration: 310,
                something: 'else'
            });
        });
    });

    describe('.open()', function() {
        var sideframe;
        var url;

        beforeEach(function(done) {
            fixture.load('sideframe.html');
            CMS.config = {
                request: {}
            };
            CMS.settings = {
                sideframe: {}
            };
            // mocking up messages, because
            // in most of the tests the iframe is thrown away
            // before it's loaded and in IE that results in an
            // error when trying to access iframe contents, which
            // results in failing tests
            CMS.API.Messages = {
                open: $.noop
            };
            spyOn(CMS.API.Helpers, 'reloadBrowser');
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                sideframe = new CMS.Sideframe();
                spyOn(CMS.API.Helpers, 'setSettings').and.callFake(function(input) {
                    return input;
                });
                spyOn(CMS.API.Helpers, 'getSettings').and.callFake(function() {
                    return { sideframe: {}, edit_off: 1 };
                });
                url = '/base/cms/tests/frontend/unit/html/sideframe_iframe.html';
                done();
            });
        });

        afterEach(function() {
            sideframe.ui.body.off();
            fixture.cleanup();
        });

        it('throws an error if no url was passed', function() {
            expect(sideframe.open.bind(sideframe)).toThrowError(Error, 'The arguments passed to "open" were invalid.');
            expect(sideframe.open.bind(sideframe, {})).toThrowError(
                Error,
                'The arguments passed to "open" were invalid.'
            );
            expect(
                sideframe.open.bind(sideframe, {
                    url: url
                })
            ).not.toThrow();
        });

        it('shows the dimmer', function() {
            expect(sideframe.ui.dimmer).not.toBeVisible();
            sideframe.open({ url: url });
            expect(sideframe.ui.dimmer).toBeVisible();
        });

        it('shows the toolbar loader', function() {
            expect(showLoader).not.toHaveBeenCalled();
            sideframe.open({ url: url });
            expect(showLoader).toHaveBeenCalled();
        });

        it('shows the loader on the sideframe', function() {
            expect(sideframe.ui.frame).not.toHaveClass('cms-loader');
            sideframe.open({ url: url });
            expect(sideframe.ui.frame).toHaveClass('cms-loader');
        });

        it('animates the sideframe to correct width', function() {
            spyOn($.fn, 'animate');
            sideframe.ui.body = $('<div></div>', {
                width: '9000px'
            });

            sideframe.open({ url: url, animate: true });
            expect($.fn.animate).toHaveBeenCalledWith(
                {
                    width: '95%',
                    overflow: 'visible'
                },
                300
            );
        });

        it('adds "close by escape" handler', function(done) {
            spyOn(sideframe, 'close');
            sideframe.options.onClose = 'mock';
            sideframe.open({ url: url });
            expect(sideframe.ui.body).toHandle('keydown.cms.close');
            sideframe.ui.body.on('keydown', function(e) {
                if (e.keyCode === CMS.KEYS.ESC) {
                    // second
                    expect(sideframe.options.onClose).toEqual(null);
                    expect(sideframe.close).toHaveBeenCalled();
                    done();
                } else {
                    // first
                    expect(sideframe.options.onClose).toEqual('mock');
                    expect(sideframe.close).not.toHaveBeenCalled();
                }
            });

            var spaceEvent = new $.Event('keydown', { keyCode: CMS.KEYS.SPACE });
            sideframe.ui.body.trigger(spaceEvent);

            var escEvent = new $.Event('keydown', { keyCode: CMS.KEYS.ESC });
            sideframe.ui.body.trigger(escEvent);
        });

        it('prevents scrolling of the outer body for mobile devices', function() {
            spyOn(CMS.API.Helpers, 'preventTouchScrolling');
            spyOn(CMS.API.Helpers, 'allowTouchScrolling');
            sideframe.ui.body.removeClass('cms-prevent-scrolling');

            sideframe.open({ url: url });
            expect(sideframe.ui.body).toHaveClass('cms-prevent-scrolling');
            expect(CMS.API.Helpers.preventTouchScrolling).toHaveBeenCalledWith($(document), 'sideframe');
            expect(CMS.API.Helpers.allowTouchScrolling).not.toHaveBeenCalled();
        });

        it('is chainable', function() {
            spyOn(sideframe, '_content');
            expect(sideframe.open({ url: url })).toEqual(sideframe);
        });

        it('empties frame holder before injecting iframe (to remove events)', function(done) {
            spyOn($.fn, 'empty').and.callThrough();
            sideframe.ui.frame.append('<div>I should not be here</div>');
            expect(sideframe.ui.frame).toHaveText('I should not be here');
            sideframe.open({ url: url });
            expect(sideframe.ui.frame).not.toHaveText('I should not be here');
            expect($.fn.empty).toHaveBeenCalled();

            sideframe.ui.frame.find('iframe').on('load', function() {
                done();
            });
        });

        it('adds specific classes on the iframe body', function(done) {
            sideframe.open({ url: url });
            expect(sideframe.ui.frame).toContainElement('iframe');

            sideframe.ui.frame.find('iframe').on('load', function() {
                expect($(this.contentDocument.body)).toHaveClass('cms-admin');
                expect($(this.contentDocument.body)).toHaveClass('cms-admin-sideframe');
                done();
            });
        });

        it('hides loader', function(done) {
            sideframe.open({ url: url });
            expect(sideframe.ui.frame).toContainElement('iframe');

            sideframe.ui.frame.find('iframe').on('load', function() {
                expect(hideLoader).toHaveBeenCalled();
                done();
            });
        });

        it('adds specific classes on the iframe body if debug mode is on', function(done) {
            CMS.config.debug = true;
            sideframe.open({ url: url });

            expect(CMS.settings.sideframe).toEqual(jasmine.objectContaining({ hidden: false }));
            sideframe.ui.frame.find('iframe').on('load', function() {
                expect($(this.contentDocument.body)).toHaveClass('cms-debug');
                done();
            });
        });

        it('saves the url in settings', function(done) {
            sideframe.open({ url: url });

            expect(CMS.settings.sideframe).toEqual(jasmine.objectContaining({ hidden: false }));
            sideframe.ui.frame.find('iframe').on('load', function() {
                expect(CMS.API.Helpers.setSettings).toHaveBeenCalled();
                // actual url would be http://localhost:port/${url}
                expect(CMS.settings.sideframe.url).toMatch(new RegExp(url));
                done();
            });
        });

        it('shows iframe after it has been loaded', function(done) {
            sideframe.open({ url: url });

            var iframe = sideframe.ui.frame.find('iframe');
            iframe.on('load', function() {
                expect(iframe).toBeVisible();
                done();
            });
            expect(iframe).not.toBeVisible();
        });

        it('adds target=_top to "view site" links', function(done) {
            sideframe.open({ url: url });

            sideframe.ui.frame.find('iframe').on('load', function() {
                expect($(this.contentDocument.body).find('.viewsitelink')).toHaveAttr('target', '_top');
                done();
            });
        });
    });

    describe('.close()', function() {
        var sideframe;
        var url;
        beforeEach(function(done) {
            fixture.load('sideframe.html');
            CMS.config = {
                request: {}
            };
            CMS.settings = {
                sideframe: {}
            };
            CMS.API.Messages = {
                open: jasmine.createSpy()
            };
            spyOn(CMS.API.Helpers, 'reloadBrowser');
            // fake _content that loads the iframe since
            // we do not really care, and things fail in IE
            spyOn(CMS.Sideframe.prototype, '_content');
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                sideframe = new CMS.Sideframe();
                spyOn(CMS.API.Helpers, 'setSettings').and.callFake(function(input) {
                    return input;
                });
                spyOn(CMS.API.Helpers, 'getSettings').and.callFake(function() {
                    return { sideframe: {} };
                });
                url = '/base/cms/tests/frontend/unit/html/sideframe_iframe.html';
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it('hides the dimmer', function() {
            sideframe.open({ url: url });
            expect(sideframe.ui.dimmer).toBeVisible();
            sideframe.close();
            expect(sideframe.ui.dimmer).not.toBeVisible();
        });

        it('sets correct state', function() {
            sideframe.open({ url: url });
            sideframe.close();
            expect(CMS.settings.sideframe).toEqual({
                url: null,
                hidden: true
            });
            expect(CMS.API.Helpers.setSettings).toHaveBeenCalled();
        });

        it('checks if page requires reloading', function() {
            sideframe.open({ url: url });
            sideframe.close();
            expect(CMS.API.Helpers.reloadBrowser).toHaveBeenCalledWith(false, false, true);

            sideframe = new CMS.Sideframe({ onClose: 'REFRESH_PAGE' });
            sideframe.open({ url: url });
            sideframe.close();
            expect(CMS.API.Helpers.reloadBrowser).toHaveBeenCalledWith('REFRESH_PAGE', false, true);
        });

        it('removes the loader from sideframe', function() {
            sideframe.open({ url: url });
            expect(sideframe.ui.frame).toHaveClass('cms-loader');
            sideframe.close();
            expect(sideframe.ui.frame).not.toHaveClass('cms-loader');
        });

        it('removes "close by escape" handler', function() {
            sideframe.open({ url: url });
            expect(sideframe.ui.body).toHandle('keydown.cms.close');
            sideframe.close();
            expect(sideframe.ui.frame).not.toHandle('keydown.cms.close');
        });

        it('restores scrolling of the outer body for mobile devices', function() {
            spyOn(CMS.API.Helpers, 'allowTouchScrolling');
            sideframe.ui.body.removeClass('cms-prevent-scrolling');
            sideframe.open({ url: url });
            expect(sideframe.ui.body).toHaveClass('cms-prevent-scrolling');
            expect(CMS.API.Helpers.allowTouchScrolling).not.toHaveBeenCalled();
            sideframe.close();
            expect(sideframe.ui.frame).not.toHaveClass('cms-prevent-scrolling');
            expect(CMS.API.Helpers.allowTouchScrolling).toHaveBeenCalledWith($(document), 'sideframe');
        });

        it('animates the sideframe to 0 and then hides it', function() {
            sideframe.open({ url: url });
            spyOn($.fn, 'animate');
            sideframe.close();
            expect($.fn.animate).toHaveBeenCalledWith({ width: 0 }, 150, jasmine.any(Function));
            expect(sideframe.ui.sideframe).toBeVisible();
            $.fn.animate.calls.mostRecent().args[2].bind(sideframe.ui.sideframe)();
            expect(sideframe.ui.sideframe).not.toBeVisible();
        });
    });

    describe('._events()', function() {
        var sideframe;
        beforeEach(function(done) {
            fixture.load('sideframe.html');
            CMS.config = {
                request: {}
            };
            CMS.settings = {
                sideframe: {}
            };
            CMS.API.Messages = {
                open: jasmine.createSpy()
            };
            spyOn(CMS.API.Helpers, 'reloadBrowser');
            // fake _content that loads the iframe since
            // we do not really care, and things fail in IE
            spyOn(CMS.Sideframe.prototype, '_content');
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                sideframe = new CMS.Sideframe();
                spyOn(sideframe, 'close');
                spyOn(sideframe, '_goToHistory');
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it('resets history', function() {
            sideframe.history = 'MOCKED';
            sideframe._events();
            expect(sideframe.history).toEqual({
                back: [],
                forward: []
            });
        });

        it('attaches new events', function() {
            expect(sideframe.ui.close).not.toHandle(sideframe.click);
            expect(sideframe.ui.dimmer).not.toHandle(sideframe.click);
            expect(sideframe.ui.historyBack).not.toHandle(sideframe.click);
            expect(sideframe.ui.historyForward).not.toHandle(sideframe.click);

            sideframe._events();

            expect(sideframe.ui.close).toHandle(sideframe.click);
            expect(sideframe.ui.dimmer).toHandle(sideframe.click);
            expect(sideframe.ui.historyBack).toHandle(sideframe.click);
            expect(sideframe.ui.historyForward).toHandle(sideframe.click);
        });

        it('removes old events', function() {
            var spy = jasmine.createSpy();
            sideframe.ui.close.on(sideframe.click, spy);
            sideframe.ui.dimmer.on(sideframe.click, spy);
            sideframe.ui.historyBack.on(sideframe.click, spy);
            sideframe.ui.historyForward.on(sideframe.click, spy);

            sideframe._events();

            sideframe.ui.close.trigger(sideframe.click);
            sideframe.ui.dimmer.trigger(sideframe.click);
            sideframe.ui.historyBack.trigger(sideframe.click);
            sideframe.ui.historyForward.trigger(sideframe.click);

            expect(spy).not.toHaveBeenCalled();
        });

        it('calls correct methods', function() {
            sideframe._events();

            sideframe.ui.close.trigger(sideframe.click);
            expect(sideframe.close).toHaveBeenCalledTimes(1);

            sideframe.ui.dimmer.trigger(sideframe.click);
            expect(sideframe.close).toHaveBeenCalledTimes(2);

            sideframe.ui.historyBack.addClass('cms-icon-disabled');
            sideframe.ui.historyForward.addClass('cms-icon-disabled');

            sideframe.ui.historyBack.trigger(sideframe.click);
            sideframe.ui.historyForward.trigger(sideframe.click);

            expect(sideframe._goToHistory).not.toHaveBeenCalled();

            sideframe.ui.historyBack.removeClass('cms-icon-disabled');
            sideframe.ui.historyForward.removeClass('cms-icon-disabled');

            sideframe.ui.historyBack.trigger(sideframe.click);
            expect(sideframe._goToHistory).toHaveBeenCalledWith('back');
            expect(sideframe._goToHistory).toHaveBeenCalledTimes(1);

            sideframe.ui.historyForward.trigger(sideframe.click);
            expect(sideframe._goToHistory).toHaveBeenCalledWith('forward');
            expect(sideframe._goToHistory).toHaveBeenCalledTimes(2);
        });
    });

    describe('._content()', function() {
        var sideframe;
        var url;
        beforeEach(function(done) {
            fixture.load('sideframe.html');
            CMS.config = {
                request: {}
            };
            CMS.settings = {
                sideframe: {}
            };
            CMS.API.Messages = {
                open: jasmine.createSpy()
            };
            spyOn(CMS.API.Helpers, 'reloadBrowser');
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                url = '/base/cms/tests/frontend/unit/html/sideframe_iframe.html';
                sideframe = new CMS.Sideframe();
                sideframe.history = {
                    back: [],
                    forward: []
                };
                spyOn(sideframe, 'close');
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it('closes the iframe if it cannot be loaded correctly', function(done) {
            spyOn($.fn, 'contents').and.throwError('Could not read iframe contents');
            sideframe._content(url);

            sideframe.ui.frame.find('iframe').on('load', function() {
                expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                    error: true,
                    message: jasmine.stringMatching('Could not read iframe contents')
                });
                expect(sideframe.close).toHaveBeenCalled();
                done();
            });
        });

        it('adds click handlers to pass through from iframe body', function(done) {
            sideframe._content(url);
            sideframe.ui.frame.find('iframe').on('load', function() {
                var doc = $(this.contentDocument);
                var spy = jasmine.createSpy();

                expect(doc).toHandle('click.cms');
                $(document).on('click.cms.toolbar', spy);
                doc.trigger(sideframe.click);
                expect(spy).toHaveBeenCalled();

                done();
            });
        });

        it('adds close handler to iframe body', function(done) {
            sideframe._content(url);
            sideframe.ui.frame.find('iframe').on('load', function() {
                var body = $(this.contentDocument.body);

                expect(body).toHandle('keydown.cms');

                var wrongEvent = new $.Event('keydown.cms', { keyCode: 132882173 });
                var correctEvent = new $.Event('keydown.cms', { keyCode: CMS.KEYS.ESC });

                body.trigger(wrongEvent);
                expect(sideframe.close).not.toHaveBeenCalled();

                body.trigger(correctEvent);
                expect(sideframe.close).toHaveBeenCalledTimes(1);

                done();
            });
        });

        it('updates history', function(done) {
            sideframe._content(url);

            sideframe.ui.frame.find('iframe').on('load', function() {
                expect(sideframe.history).toEqual({
                    back: jasmine.arrayContaining([jasmine.stringMatching(url)]),
                    forward: []
                });
                done();
            });
        });
    });

    describe('._goToHistory()', function() {
        var sideframe;
        var urls = [
            '/base/cms/tests/frontend/unit/html/sideframe_iframe.html',
            '/base/cms/tests/frontend/unit/html/modal_iframe.html'
        ];
        var iframe;
        beforeEach(function(done) {
            fixture.load('sideframe.html');
            CMS.config = {
                request: {}
            };
            CMS.settings = {
                sideframe: {}
            };
            $(function() {
                sideframe = new CMS.Sideframe();
                sideframe.history = {
                    back: [urls[0], urls[1]],
                    forward: []
                };
                iframe = $('<iframe />').prependTo(sideframe.ui.frame);
                spyOn(sideframe, '_updateHistoryButtons');
                done();
            });
        });

        afterEach(function() {
            sideframe.ui.body.off();
            fixture.cleanup();
        });

        it('updates history object', function() {
            sideframe._goToHistory('back');
            expect(sideframe.history).toEqual({
                back: [urls[0]],
                forward: [urls[1]]
            });
            sideframe._goToHistory('back');
            expect(sideframe.history).toEqual({
                back: [],
                forward: [urls[1], urls[0]]
            });
            sideframe._goToHistory('forward');
            expect(sideframe.history).toEqual({
                back: [urls[0]],
                forward: [urls[1]]
            });
            sideframe._goToHistory('forward');
            expect(sideframe.history).toEqual({
                back: [urls[0], urls[1]],
                forward: []
            });
        });

        it('sets correct iframe src', function() {
            expect(iframe.attr('src')).toBeFalsy();
            sideframe._goToHistory('back');
            expect(iframe.attr('src')).toEqual(urls[0]);
            sideframe._goToHistory('forward');
            expect(iframe.attr('src')).toEqual(urls[1]);
        });

        it('updates history buttons', function() {
            sideframe._goToHistory('back');
            expect(sideframe._updateHistoryButtons).toHaveBeenCalledTimes(1);
            sideframe._goToHistory('forward');
            expect(sideframe._updateHistoryButtons).toHaveBeenCalledTimes(2);
        });
    });

    describe('._goToHistory()', function() {
        var sideframe;

        beforeEach(function(done) {
            fixture.load('sideframe.html');
            CMS.config = {
                request: {}
            };
            CMS.settings = {
                sideframe: {}
            };
            $(function() {
                sideframe = new CMS.Sideframe();
                sideframe.history = {
                    back: [],
                    forward: []
                };
                spyOn(sideframe, '_updateHistoryButtons');
                done();
            });
        });

        afterEach(function() {
            sideframe.ui.body.off();
            fixture.cleanup();
        });

        it('updates history object', function() {
            sideframe._addToHistory('wut');
            expect(sideframe.history.back).toEqual(['wut']);
            sideframe._addToHistory('wut1');
            expect(sideframe.history.back).toEqual(['wut', 'wut1']);
            sideframe._addToHistory('wut');
            expect(sideframe.history.back).toEqual(['wut', 'wut1', 'wut']);
            sideframe._addToHistory('wut');
            expect(sideframe.history.back).toEqual(['wut', 'wut1', 'wut']);
        });

        it('updates history buttons', function() {
            sideframe._addToHistory('wut');
            expect(sideframe._updateHistoryButtons).toHaveBeenCalledTimes(1);
            sideframe._addToHistory('wut1');
            expect(sideframe._updateHistoryButtons).toHaveBeenCalledTimes(2);
            sideframe._addToHistory('wut');
            expect(sideframe._updateHistoryButtons).toHaveBeenCalledTimes(3);
            sideframe._addToHistory('wut');
            expect(sideframe._updateHistoryButtons).toHaveBeenCalledTimes(4);
        });
    });

    describe('._updateHistoryButtons()', function() {
        var sideframe;

        beforeEach(function(done) {
            fixture.load('sideframe.html');
            CMS.config = {
                request: {}
            };
            CMS.settings = {
                sideframe: {}
            };
            $(function() {
                sideframe = new CMS.Sideframe();
                sideframe.history = {
                    back: [],
                    forward: []
                };
                done();
            });
        });

        afterEach(function() {
            sideframe.ui.body.off();
            fixture.cleanup();
        });

        it('updates the buttons state based on history object', function() {
            sideframe._updateHistoryButtons();
            expect(sideframe.ui.historyBack).toHaveClass('cms-icon-disabled');
            expect(sideframe.ui.historyForward).toHaveClass('cms-icon-disabled');

            sideframe.history = {
                back: ['1'],
                forward: []
            };

            sideframe._updateHistoryButtons();
            expect(sideframe.ui.historyBack).toHaveClass('cms-icon-disabled');
            expect(sideframe.ui.historyForward).toHaveClass('cms-icon-disabled');

            sideframe.history = {
                back: ['1', '2'],
                forward: []
            };

            sideframe._updateHistoryButtons();
            expect(sideframe.ui.historyBack).not.toHaveClass('cms-icon-disabled');
            expect(sideframe.ui.historyForward).toHaveClass('cms-icon-disabled');

            sideframe.history = {
                back: ['1'],
                forward: ['1']
            };

            sideframe._updateHistoryButtons();
            expect(sideframe.ui.historyBack).toHaveClass('cms-icon-disabled');
            expect(sideframe.ui.historyForward).not.toHaveClass('cms-icon-disabled');
        });
    });
});
