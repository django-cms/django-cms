/* global document */
'use strict';
var CMS = require('../../../static/cms/js/modules/cms.base').default;
var Modal = require('../../../static/cms/js/modules/cms.modal').default;
var $ = require('jquery');
var Helpers = Modal.__GetDependency__('Helpers');
var KEYS = Modal.__GetDependency__('KEYS');
var showLoader;
var hideLoader;

window.CMS = window.CMS || CMS;
CMS.Modal = Modal;

describe('CMS.Modal', function() {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    beforeEach(() => {
        showLoader = jasmine.createSpy();
        hideLoader = jasmine.createSpy();
        Modal.__Rewire__('showLoader', showLoader);
        Modal.__Rewire__('hideLoader', hideLoader);
        CMS._eventRoot = $('#cms-top');
        CMS.ChangeTracker = function() {
            return {
                isFormChanged: function() {
                    return false;
                }
            };
        };
    });

    afterEach(() => {
        Modal.__ResetDependency__('showLoader');
        Modal.__ResetDependency__('hideLoader');
    });

    it('creates a Modal class', function() {
        expect(CMS.Modal).toBeDefined();
    });

    it('has public API', function() {
        expect(CMS.Modal.prototype.open).toEqual(jasmine.any(Function));
        expect(CMS.Modal.prototype.close).toEqual(jasmine.any(Function));
        expect(CMS.Modal.prototype.minimize).toEqual(jasmine.any(Function));
        expect(CMS.Modal.prototype.maximize).toEqual(jasmine.any(Function));
        expect(CMS.Modal._setupCtrlEnterSave).toEqual(jasmine.any(Function));
    });

    describe('instance', function() {
        it('has ui', function(done) {
            $(function() {
                var modal = new CMS.Modal();
                expect(modal.ui).toEqual(jasmine.any(Object));
                expect(Object.keys(modal.ui)).toContain('modal');
                expect(Object.keys(modal.ui)).toContain('body');
                expect(Object.keys(modal.ui)).toContain('window');
                expect(Object.keys(modal.ui)).toContain('toolbarLeftPart');
                expect(Object.keys(modal.ui)).toContain('minimizeButton');
                expect(Object.keys(modal.ui)).toContain('maximizeButton');
                expect(Object.keys(modal.ui)).toContain('title');
                expect(Object.keys(modal.ui)).toContain('titlePrefix');
                expect(Object.keys(modal.ui)).toContain('titleSuffix');
                expect(Object.keys(modal.ui)).toContain('resize');
                expect(Object.keys(modal.ui)).toContain('breadcrumb');
                expect(Object.keys(modal.ui)).toContain('closeAndCancel');
                expect(Object.keys(modal.ui)).toContain('modalButtons');
                expect(Object.keys(modal.ui)).toContain('modalBody');
                expect(Object.keys(modal.ui)).toContain('frame');
                expect(Object.keys(modal.ui)).toContain('shim');
                expect(Object.keys(modal.ui).length).toEqual(16);
                done();
            });
        });

        it('has options', function(done) {
            $(function() {
                var modal = new CMS.Modal();
                expect(modal.options).toEqual({
                    onClose: false,
                    minHeight: 400,
                    minWidth: 800,
                    modalDuration: 200,
                    resizable: true,
                    maximizable: true,
                    minimizable: true,
                    closeOnEsc: true
                });

                var modal2 = new CMS.Modal({ minHeight: 300, minWidth: 100 });
                expect(modal2.options).toEqual({
                    onClose: false,
                    minHeight: 300,
                    minWidth: 100,
                    modalDuration: 200,
                    resizable: true,
                    maximizable: true,
                    minimizable: true,
                    closeOnEsc: true
                });

                done();
            });
        });
    });

    describe('.open()', function() {
        var modal;
        beforeEach(function(done) {
            fixture.load('modal.html');
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Messages = {
                open: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                modal = new CMS.Modal();
                done();
            });
        });

        afterEach(function() {
            window.removeEventListener('beforeunload', modal._beforeUnloadHandler);
            fixture.cleanup();
        });

        it('throws an error when no url or html options were passed', function() {
            spyOn(modal, '_loadIframe');
            expect(modal.open.bind(modal)).toThrowError(Error, 'The arguments passed to "open" were invalid.');
            expect(modal.open.bind(modal, {})).toThrowError(Error, 'The arguments passed to "open" were invalid.');
            expect(modal.open.bind(modal, { html: '' })).toThrowError(
                Error,
                'The arguments passed to "open" were invalid.'
            );
            expect(modal.open.bind(modal, { url: '' })).toThrowError(
                Error,
                'The arguments passed to "open" were invalid.'
            );
            expect(modal.open.bind(modal, { html: '<div></div>' })).not.toThrow();
            expect(
                modal.open.bind(modal, {
                    url: '/base/cms/tests/frontend/unit/html/modal_iframe.html'
                })
            ).not.toThrow();
        });

        it('should be chainable', function() {
            expect(modal.open({ html: '<div></div>' })).toEqual(modal);
        });

        it('hides the tooltip', function() {
            modal.open({ html: '<div></div>' });
            expect(CMS.API.Tooltip.hide).toHaveBeenCalled();
        });

        it('triggers load events via helpers', function() {
            jasmine.clock().install();
            spyOn(Helpers, 'dispatchEvent');
            modal.open({ html: '<div></div>' });

            expect(Helpers.dispatchEvent).toHaveBeenCalledWith(
                'modal-load',
                jasmine.objectContaining({ instance: modal })
            );

            jasmine.clock().tick(modal.options.duration);

            expect(Helpers.dispatchEvent).toHaveBeenCalledWith(
                'modal-loaded',
                jasmine.objectContaining({ instance: modal })
            );
            jasmine.clock().uninstall();
        });

        it('applies correct state to modal controls 1', function() {
            modal.open({ html: '<div></div>' });
            // here and in others we cannot use `.toBeVisible` matcher,
            // because it uses jQuery's `:visible` selector which relies
            // on an element having offsetWidth/offsetHeight, but
            // Safari reports it to be 0 if an element is scaled with transform
            expect(modal.ui.resize).toHaveCss({ display: 'block' });
            expect(modal.ui.minimizeButton).toHaveCss({ display: 'block' });
            expect(modal.ui.maximizeButton).toHaveCss({ display: 'block' });
        });

        it('applies correct state to modal controls 2', function() {
            modal = new CMS.Modal({ resizable: false });
            modal.open({ html: '<div></div>' });
            expect(modal.ui.resize).toHaveCss({ display: 'none' });
            expect(modal.ui.minimizeButton).toHaveCss({ display: 'block' });
            expect(modal.ui.maximizeButton).toHaveCss({ display: 'block' });
        });

        it('applies correct state to modal controls 3', function() {
            modal = new CMS.Modal({ resizable: true });
            modal.open({ html: '<div></div>' });
            expect(modal.ui.resize).toHaveCss({ display: 'block' });
            expect(modal.ui.minimizeButton).toHaveCss({ display: 'block' });
            expect(modal.ui.maximizeButton).toHaveCss({ display: 'block' });
        });

        it('applies correct state to modal controls 4', function() {
            modal = new CMS.Modal({ minimizable: false });
            modal.open({ html: '<div></div>' });
            expect(modal.ui.resize).toHaveCss({ display: 'block' });
            expect(modal.ui.minimizeButton).toHaveCss({ display: 'none' });
            expect(modal.ui.maximizeButton).toHaveCss({ display: 'block' });
        });

        it('applies correct state to modal controls 5', function() {
            modal = new CMS.Modal({ minimizable: true });
            modal.open({ html: '<div></div>' });
            expect(modal.ui.resize).toHaveCss({ display: 'block' });
            expect(modal.ui.minimizeButton).toHaveCss({ display: 'block' });
            expect(modal.ui.maximizeButton).toHaveCss({ display: 'block' });
        });

        it('applies correct state to modal controls 6', function() {
            modal = new CMS.Modal({ maximizable: false });
            modal.open({ html: '<div></div>' });
            expect(modal.ui.resize).toHaveCss({ display: 'block' });
            expect(modal.ui.minimizeButton).toHaveCss({ display: 'block' });
            expect(modal.ui.maximizeButton).toHaveCss({ display: 'none' });
        });

        it('applies correct state to modal controls 7', function() {
            modal = new CMS.Modal({ maximizable: true });
            modal.open({ html: '<div></div>' });
            expect(modal.ui.resize).toHaveCss({ display: 'block' });
            expect(modal.ui.minimizeButton).toHaveCss({ display: 'block' });
            expect(modal.ui.maximizeButton).toHaveCss({ display: 'block' });
        });

        it('resets minimized state if the modal was already minimized', function() {
            modal.open({ html: '<div></div>' });
            modal.minimize();
            expect(modal.minimized).toEqual(true);

            spyOn(modal, 'minimize').and.callThrough();

            modal.open({ html: '<span></span>' });
            expect(modal.minimized).toEqual(false);
            expect(modal.minimize).toHaveBeenCalled();
            expect(modal.minimize.calls.count()).toEqual(1);
        });

        it('clears breadcrumbs and buttons if they exist', function() {
            modal.ui.modal.addClass('cms-modal-has-breadcrumb');
            modal.ui.modalButtons.html('<div>button</div>');
            modal.ui.breadcrumb.html('<div>breadcrumbs</div>');

            modal.open({ html: '<div></div>' });
            expect(modal.ui.modal).not.toHaveClass('cms-modal-has-breadcrumb');
            expect(modal.ui.modalButtons).toBeEmpty();
            expect(modal.ui.breadcrumb).toBeEmpty();
        });
    });

    describe('.minimize()', function() {
        var modal;
        beforeEach(function(done) {
            fixture.load('modal.html');
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                modal = new CMS.Modal();
                done();
            });
        });

        afterEach(function() {
            window.removeEventListener('beforeunload', modal._beforeUnloadHandler);
            fixture.cleanup();
        });

        it('minimizes the modal', function() {
            expect(modal.minimized).toEqual(false);
            modal.open({ html: '<div></div>' });
            modal.minimize();

            expect(modal.minimized).toEqual(true);
            expect(modal.ui.body).toHaveClass('cms-modal-minimized');
            expect(modal.ui.modal).toHaveCss({
                left: '50px'
            });

            modal.minimize(); // restore
        });

        it('stores the css data to be able to restore a modal', function() {
            modal.open({ html: '<div></div>' });
            modal.minimize();

            var css = modal.ui.modal.data('css');
            expect(css).toEqual(jasmine.any(Object));
            expect(Object.keys(css)).toContain('margin-left');
            expect(Object.keys(css)).toContain('margin-top');
            expect(Object.keys(css)).toContain('top');
            expect(Object.keys(css)).toContain('left');

            modal.minimize(); // restore
        });

        it('does not minimize maximized modal', function() {
            modal.maximized = true;
            expect(modal.minimize()).toEqual(false);
            expect(CMS.API.Toolbar.open).not.toHaveBeenCalled();
            expect(modal.ui.body).not.toHaveClass('cms-modal-minimized');
        });

        it('restores modal if it was already minimized', function() {
            modal.open({ html: '<div></div>' });
            modal.minimize();

            expect(modal.minimized).toEqual(true);
            expect(modal.ui.body).toHaveClass('cms-modal-minimized');

            modal.minimize();

            expect(modal.minimized).toEqual(false);
            expect(modal.ui.modal).toHaveCss(modal.ui.modal.data('css'));
            expect(modal.ui.body).not.toHaveClass('cms-modal-minimized');
        });
    });

    describe('.maximize()', function() {
        var modal;
        beforeEach(function(done) {
            fixture.load('modal.html');
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                modal = new CMS.Modal();
                done();
            });
        });

        afterEach(function() {
            window.removeEventListener('beforeunload', modal._beforeUnloadHandler);
            modal.close();
            fixture.cleanup();
        });

        it('maximizes the modal', function() {
            modal.open({ html: '<div></div>' });

            modal.maximize();
            expect(modal.ui.body).toHaveClass('cms-modal-maximized');
            expect(modal.maximized).toEqual(true);
            modal.maximize(); // restore
        });

        it('stores the css data to be able to restore a modal', function() {
            modal.open({ html: '<div></div>' });
            modal.maximize();

            var css = modal.ui.modal.data('css');
            expect(css).toEqual(jasmine.any(Object));
            expect(Object.keys(css)).toContain('margin-left');
            expect(Object.keys(css)).toContain('margin-top');
            expect(Object.keys(css)).toContain('width');
            expect(Object.keys(css)).toContain('height');
            expect(Object.keys(css)).toContain('top');
            expect(Object.keys(css)).toContain('left');

            modal.maximize(); // restore
        });

        it('dispatches the modal-maximized event', function(done) {
            modal.open({ html: '<div></div>' });

            CMS._eventRoot = $('#cms-top');
            Helpers.addEventListener('modal-maximized', function(e, data) {
                Helpers.removeEventListener('modal-maximized');
                expect(data.instance).toEqual(modal);
                done();
            });

            modal.maximize();
            modal.maximize(); // restore
        });

        it('does not maximize minimized modal', function() {
            modal.open({ html: '<div></div>' });
            modal.minimize();

            expect(modal.maximize()).toEqual(false);
            expect(modal.maximized).toEqual(false);
            expect(modal.minimized).toEqual(true);
            modal.minimize(); // restore
        });

        it('restores modal if it was already maximized', function() {
            modal.open({ html: '<div></div>' });

            modal.maximize();
            modal.maximize(); // restore
            expect(modal.ui.body).not.toHaveClass('cms-modal-maximized');
            expect(modal.ui.modal).toHaveCss(modal.ui.modal.data('css'));
            expect(modal.maximized).toEqual(false);
        });

        it('dispatches modal-restored event when it restores the modal', function(done) {
            modal.open({ html: '<div></div>' });

            CMS._eventRoot = $('#cms-top');
            Helpers.addEventListener('modal-restored', function(e, data) {
                Helpers.removeEventListener('modal-restored');
                expect(true).toEqual(true);
                expect(data.instance).toEqual(modal);
                done();
            });

            modal.maximize();
            modal.maximize(); // restore
        });
    });

    describe('.close()', function() {
        var modal;
        beforeEach(function(done) {
            fixture.load('modal.html');
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                modal = new CMS.Modal({
                    modalDuration: 0
                });
                done();
            });
        });

        afterEach(function() {
            window.removeEventListener('beforeunload', modal._beforeUnloadHandler);
            fixture.cleanup();
        });

        it('returns false if modal-close event is prevented', function() {
            CMS._eventRoot = $('#cms-top');
            Helpers.addEventListener('modal-close', function(e, opts) {
                e.preventDefault();
                expect(opts.instance).toEqual(modal);
            });

            spyOn(modal, '_hide').and.callThrough();
            modal.open({ html: '<div></div>' });
            expect(modal.close()).toEqual(false);
            expect(modal._hide).not.toHaveBeenCalled();
            Helpers.removeEventListener('modal-close');
        });

        it('removes content preserving handlers', function() {
            var removeEventListener = jasmine.createSpy();

            spyOn(Helpers, '_getWindow').and.returnValue({
                removeEventListener: removeEventListener
            });

            modal.open({ html: '<div></div>' });
            modal.close();
            expect(removeEventListener).toHaveBeenCalledTimes(1);
            expect(removeEventListener).toHaveBeenCalledWith('beforeunload', modal._beforeUnloadHandler);
        });

        it('closes the modal', function(done) {
            modal.open({ html: '<div></div>' });

            spyOn(modal, '_hide').and.callThrough();

            setTimeout(function() {
                modal.close();
                expect(modal._hide).toHaveBeenCalled();
                setTimeout(function() {
                    expect(modal.ui.modal).not.toHaveClass('cms-modal-open');
                    expect(modal.ui.modal).toHaveCss({ display: 'none' });
                    done();
                }, 10);
            }, 10);
        });

        it('reloads the browser if onClose is provided', function(done) {
            modal = new CMS.Modal({ onClose: '/this-url' });
            modal.open({ html: '<div></div>' });
            spyOn(Helpers, 'reloadBrowser').and.callFake(function(url, timeout, ajax) {
                expect(url).toEqual('/this-url');
                expect(timeout).toEqual(false);
                expect(ajax).toEqual(true);
                done();
            });
            modal.close();
        });
    });

    describe('._events()', function() {
        var modal;
        beforeEach(function(done) {
            fixture.load('modal.html');
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                modal = new CMS.Modal({
                    modalDuration: 0
                });
                spyOn(modal, 'minimize');
                spyOn(modal, 'maximize');
                spyOn(modal, '_startMove');
                spyOn(modal, '_startResize');
                spyOn(modal, 'close');
                spyOn(modal, '_changeIframe');
                done();
            });
        });

        afterEach(function() {
            window.removeEventListener('beforeunload', modal._beforeUnloadHandler);
            fixture.cleanup();
        });

        it('attaches new events', function() {
            expect(modal.ui.minimizeButton).not.toHandle(modal.click);
            expect(modal.ui.minimizeButton).not.toHandle(modal.touchEnd);
            expect(modal.ui.maximizeButton).not.toHandle(modal.click);
            expect(modal.ui.maximizeButton).not.toHandle(modal.touchEnd);
            expect(modal.ui.title).not.toHandle(modal.pointerDown.split(' ')[0]);
            expect(modal.ui.title).not.toHandle(modal.pointerDown.split(' ')[1]);
            expect(modal.ui.title).not.toHandle(modal.doubleClick);
            expect(modal.ui.resize).not.toHandle(modal.pointerDown.split(' ')[0]);
            expect(modal.ui.resize).not.toHandle(modal.pointerDown.split(' ')[1]);
            expect(modal.ui.closeAndCancel).not.toHandle(modal.click);
            expect(modal.ui.closeAndCancel).not.toHandle(modal.touchEnd);
            expect(modal.ui.breadcrumb).not.toHandle(modal.click);
            modal._events();
            expect(modal.ui.minimizeButton).toHandle(modal.click);
            expect(modal.ui.minimizeButton).toHandle(modal.touchEnd);
            expect(modal.ui.maximizeButton).toHandle(modal.click);
            expect(modal.ui.maximizeButton).toHandle(modal.touchEnd);
            expect(modal.ui.title).toHandle(modal.pointerDown.split(' ')[0]);
            expect(modal.ui.title).toHandle(modal.pointerDown.split(' ')[1]);
            expect(modal.ui.title).toHandle(modal.doubleClick);
            expect(modal.ui.resize).toHandle(modal.pointerDown.split(' ')[0]);
            expect(modal.ui.resize).toHandle(modal.pointerDown.split(' ')[1]);
            expect(modal.ui.closeAndCancel).toHandle(modal.click);
            expect(modal.ui.closeAndCancel).toHandle(modal.touchEnd);
            expect(modal.ui.breadcrumb).toHandle(modal.click);
        });

        it('removes previous events', function() {
            var spy = jasmine.createSpy();

            modal.ui.breadcrumb.html('<a></a>');

            modal.ui.minimizeButton.on(modal.click + ' ' + modal.touchEnd, spy);
            modal.ui.maximizeButton.on(modal.click + ' ' + modal.touchEnd, spy);
            modal.ui.title.on(modal.pointerDown + ' ' + modal.doubleClick, spy);
            modal.ui.resize.on(modal.pointerDown, spy);
            modal.ui.closeAndCancel.on(modal.click + ' ' + modal.touchEnd, spy);
            modal.ui.breadcrumb.on(modal.click, 'a', spy);

            modal._events();

            modal.ui.minimizeButton.trigger(modal.click);
            modal.ui.minimizeButton.trigger(modal.touchEnd);
            modal.ui.maximizeButton.trigger(modal.click);
            modal.ui.maximizeButton.trigger(modal.touchEnd);
            modal.ui.title.trigger(modal.pointerDown.split(' ')[0]);
            modal.ui.title.trigger(modal.pointerDown.split(' ')[1]);
            modal.ui.title.trigger(modal.doubleClick);
            modal.ui.resize.trigger(modal.pointerDown.split(' ')[0]);
            modal.ui.resize.trigger(modal.pointerDown.split(' ')[1]);
            modal.ui.closeAndCancel.trigger(modal.click);
            modal.ui.closeAndCancel.trigger(modal.touchEnd);
            modal.ui.breadcrumb.find('a').trigger(modal.click);

            expect(spy).not.toHaveBeenCalled();
        });

        it('calls correct methods', function() {
            modal.ui.breadcrumb.html('<a></a>');

            modal._events();

            modal.ui.minimizeButton.trigger(modal.click);
            modal.ui.minimizeButton.trigger(modal.touchEnd);
            expect(modal.minimize.calls.count()).toEqual(2);

            modal.ui.maximizeButton.trigger(modal.click);
            modal.ui.maximizeButton.trigger(modal.touchEnd);
            expect(modal.maximize.calls.count()).toEqual(2);

            modal.ui.title.trigger(modal.pointerDown.split(' ')[0]);
            modal.ui.title.trigger(modal.pointerDown.split(' ')[1]);
            expect(modal._startMove.calls.count()).toEqual(2);

            modal.ui.title.trigger(modal.doubleClick);
            expect(modal.maximize.calls.count()).toEqual(3);

            modal.ui.resize.trigger(modal.pointerDown.split(' ')[0]);
            modal.ui.resize.trigger(modal.pointerDown.split(' ')[1]);
            expect(modal._startResize.calls.count()).toEqual(2);

            modal.ui.closeAndCancel.trigger(modal.click);
            modal.ui.closeAndCancel.trigger(modal.touchEnd);
            expect(modal.close.calls.count()).toEqual(2);

            modal.ui.breadcrumb.find('a').trigger(modal.click);
            expect(modal._changeIframe.calls.count()).toEqual(1);
        });
    });

    describe('_calculateNewPosition()', function() {
        var modal;
        beforeEach(function(done) {
            fixture.load('modal.html');
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                modal = new CMS.Modal({
                    modalDuration: 0
                });
                $('html').removeClass('cms-modal-maximized');
                modal.ui.window = $('<div style="width: 2000px; height: 2000px;"></div>').prependTo(fixture.el);
                // have to show the modal so the css values can be retrieved
                modal.ui.modal.show();
                modal.ui.modal.addClass('cms-modal-open');
                done();
            });
        });

        afterEach(function() {
            window.removeEventListener('beforeunload', modal._beforeUnloadHandler);
            fixture.cleanup();
        });

        it('fits the modal to the screen if there is enough space', function() {
            spyOn($.fn, 'css').and.returnValue(0);

            expect(modal._calculateNewPosition({})).toEqual({
                width: 1700,
                height: 1700,
                top: 1000,
                left: 1000
            });

            $.fn.css.and.callThrough();

            modal.ui.window.css({
                width: 1500,
                height: 1500
            });

            $.fn.css.and.returnValue(0);

            expect(modal._calculateNewPosition({})).toEqual({
                width: 1200,
                height: 1200,
                top: 750,
                left: 750
            });
        });

        it('respects params', function() {
            modal.ui.window.css({
                width: 900,
                height: 500
            });
            // so it resets to middle of the screen
            spyOn($.fn, 'css').and.returnValue(0);

            expect(
                modal._calculateNewPosition({
                    width: 300,
                    height: 300
                })
            ).toEqual({
                width: 300,
                height: 300,
                top: 250,
                left: 450
            });

            expect(
                modal._calculateNewPosition({
                    width: 1000,
                    height: 500
                })
            ).toEqual({
                width: 1000,
                height: 500,
                top: 250,
                left: 450
            });
        });

        it('respects minWidth and minHeight', function() {
            modal.ui.window.css({
                width: 900,
                height: 500
            });
            // so it resets to middle of the screen
            spyOn($.fn, 'css').and.returnValue(0);
            expect(modal._calculateNewPosition({})).toEqual({
                width: 800,
                height: 400,
                top: 250,
                left: 450
            });
        });

        it('handles 50% left and top position case', function() {
            spyOn($.fn, 'css').and.returnValue('50%');

            expect(modal._calculateNewPosition({})).toEqual({
                width: 1700,
                height: 1700,
                top: undefined,
                left: undefined
            });
        });

        it('moves modal to the middle of the screen if it does not fit the screen', function() {
            spyOn($.fn, 'css').and.returnValue(850);
            expect(modal._calculateNewPosition({})).toEqual({
                width: 1700,
                height: 1700,
                top: undefined,
                left: undefined
            });

            $.fn.css.and.returnValue(2000 - 850);
            expect(modal._calculateNewPosition({})).toEqual({
                width: 1700,
                height: 1700,
                top: undefined,
                left: undefined
            });

            $.fn.css.and.callFake(function(prop) {
                return {
                    left: 850,
                    top: 2000 - 850
                }[prop];
            });
            expect(modal._calculateNewPosition({})).toEqual({
                width: 1700,
                height: 1700,
                top: undefined,
                left: undefined
            });

            $.fn.css.and.callFake(function(prop) {
                return {
                    left: 2000 - 850,
                    top: 850
                }[prop];
            });
            expect(modal._calculateNewPosition({})).toEqual({
                width: 1700,
                height: 1700,
                top: undefined,
                left: undefined
            });

            $.fn.css.and.callFake(function(prop) {
                return {
                    left: 849,
                    top: 849
                }[prop];
            });
            expect(modal._calculateNewPosition({})).toEqual({
                width: 1700,
                height: 1700,
                top: 1000,
                left: 1000
            });

            $.fn.css.and.callFake(function(prop) {
                return {
                    left: 2000 - 849,
                    top: 2000 - 849
                }[prop];
            });
            expect(modal._calculateNewPosition({})).toEqual({
                width: 1700,
                height: 1700,
                top: 1000,
                left: 1000
            });

            $.fn.css.and.callFake(function(prop) {
                return {
                    left: 849,
                    top: 2000 - 849
                }[prop];
            });
            expect(modal._calculateNewPosition({})).toEqual({
                width: 1700,
                height: 1700,
                top: 1000,
                left: 1000
            });

            $.fn.css.and.callFake(function(prop) {
                return {
                    left: 2000 - 849,
                    top: 849
                }[prop];
            });
            expect(modal._calculateNewPosition({})).toEqual({
                width: 1700,
                height: 1700,
                top: 1000,
                left: 1000
            });
        });

        it('maximizes the modal if it goes out of the screen', function() {
            expect(modal.triggerMaximized).not.toEqual(true);
            modal.ui.window.css({
                width: 900,
                height: 500
            });
            // so it resets to middle of the screen
            spyOn($.fn, 'css').and.returnValue(0);
            expect(modal._calculateNewPosition({})).toEqual({
                width: 800,
                height: 400,
                top: 250,
                left: 450
            });
            expect(modal.triggerMaximized).not.toEqual(true);

            expect(modal._calculateNewPosition({ width: 900 })).toEqual({
                width: 900,
                height: 400,
                top: 250,
                left: 450
            });
            expect(modal.triggerMaximized).toEqual(true);

            modal.triggerMaximized = false;

            expect(modal._calculateNewPosition({ height: 500 })).toEqual({
                width: 800,
                height: 500,
                top: 250,
                left: 450
            });
            expect(modal.triggerMaximized).toEqual(true);
        });
    });

    describe('_show()', function() {
        var modal;
        beforeEach(function(done) {
            fixture.load('modal.html');
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                modal = new CMS.Modal({
                    modalDuration: 0
                });
                spyOn(modal, 'maximize');
                spyOn(modal, 'close');
                done();
            });
        });

        afterEach(function() {
            window.removeEventListener('beforeunload', modal._beforeUnloadHandler);
            fixture.cleanup();
        });

        it('add morphing class if modal is already open', function(done) {
            modal.ui.modal.show();
            expect(modal.ui.modal).not.toHaveClass('cms-modal-morphing');
            expect(modal.ui.modal).not.toHaveClass('cms-modal-open');

            modal.ui.modal.addClass('cms-modal-open');
            modal.ui.modal.one('cmsTransitionEnd', function() {
                setTimeout(function() {
                    expect(modal.ui.modal).not.toHaveClass('cms-modal-morphing');
                    done();
                }, 0);
            });
            modal._show({});
            expect(modal.ui.modal).toHaveClass('cms-modal-morphing');
        });

        it('positions modal by given params', function(done) {
            spyOn($.fn, 'css');
            modal.ui.modal.one('cmsTransitionEnd', function() {
                setTimeout(function() {
                    expect($.fn.css).toHaveBeenCalledWith({
                        'margin-left': -10,
                        'margin-top': -1.5
                    });
                    done();
                }, 0);
            });
            modal._show({
                width: 20,
                height: 3,
                top: 123,
                left: 456
            });

            expect($.fn.css).toHaveBeenCalledWith({
                display: 'block',
                width: 20,
                height: 3,
                top: 123,
                left: 456,
                'margin-left': -10,
                'margin-top': -1.5
            });
        });

        it('maximizes the modal if required', function(done) {
            modal.ui.modal.one('cmsTransitionEnd', function() {
                setTimeout(function() {
                    expect(modal.maximize).toHaveBeenCalled();
                    done();
                }, 0);
            });
            modal.triggerMaximized = true;
            modal._show({});
        });

        it('does not maximize the modal if not required', function(done) {
            modal.ui.modal.one('cmsTransitionEnd', function() {
                setTimeout(function() {
                    expect(modal.maximize).not.toHaveBeenCalled();
                    done();
                }, 0);
            });
            modal.triggerMaximized = false;
            modal._show({});
        });

        it('triggers cms-modal-shown', function(done) {
            spyOn(Helpers, 'dispatchEvent');
            modal.ui.modal.one('cmsTransitionEnd', function() {
                setTimeout(function() {
                    expect(Helpers.dispatchEvent).toHaveBeenCalledWith(
                        'modal-shown',
                        jasmine.objectContaining({ instance: modal })
                    );
                    done();
                }, 0);
            });
            modal._show({});
        });

        it('adds an event handler to close the modal by pressing ESC', function() {
            var spy = jasmine.createSpy();

            modal.ui.body.on('keydown.cms.close', spy);
            modal.options.onClose = 'stuff';

            modal._show({});

            var wrongEvent = new $.Event('keydown.cms.close', { keyCode: KEYS.SPACE });
            modal.ui.body.trigger(wrongEvent);
            expect(spy).not.toHaveBeenCalled();
            expect(modal.close).not.toHaveBeenCalled();
            expect(modal.options.onClose).toEqual('stuff');

            var correctEvent = new $.Event('keydown.cms.close', { keyCode: KEYS.ESC });
            modal.ui.body.trigger(correctEvent);
            expect(spy).not.toHaveBeenCalled();
            expect(modal.close).toHaveBeenCalled();
            expect(modal.options.onClose).toEqual(null);
        });

        it('adds an event handler to close the modal by pressing ESC if closeOnEsc is set', function() {
            var spy = jasmine.createSpy();

            modal.ui.body.on('keydown.cms.close', spy);
            modal.options.onClose = 'stuff';
            modal.options.closeOnEsc = false;

            modal._show({});

            var wrongEvent = new $.Event('keydown.cms.close', { keyCode: KEYS.SPACE });
            modal.ui.body.trigger(wrongEvent);
            expect(spy).not.toHaveBeenCalled();
            expect(modal.close).not.toHaveBeenCalled();
            expect(modal.options.onClose).toEqual('stuff');

            var correctEvent = new $.Event('keydown.cms.close', { keyCode: KEYS.ESC });
            modal.ui.body.trigger(correctEvent);
            expect(spy).not.toHaveBeenCalled();
            expect(modal.close).not.toHaveBeenCalled();
            expect(modal.options.onClose).toEqual('stuff');
        });

        it('adds an event handler to close the modal by pressing ESC if confirmed', function() {
            var spy = jasmine.createSpy();

            modal.ui.body.on('keydown.cms.close', spy);
            modal.options.onClose = 'stuff';
            spyOn(modal, '_confirmDirtyEscCancel').and.returnValue(true);

            modal._show({});

            var correctEvent = new $.Event('keydown.cms.close', { keyCode: KEYS.ESC });
            modal.ui.body.trigger(correctEvent);
            expect(spy).not.toHaveBeenCalled();
            expect(modal.close).toHaveBeenCalled();
            expect(modal.options.onClose).toEqual(null);
        });

        it('adds an event handler to not close the modal by pressing ESC if not confirmed', function() {
            var spy = jasmine.createSpy();

            modal.ui.body.on('keydown.cms.close', spy);
            modal.options.onClose = 'stuff';
            spyOn(modal, '_confirmDirtyEscCancel').and.returnValue(false);

            modal._show({});

            var correctEvent = new $.Event('keydown.cms.close', { keyCode: KEYS.ESC });
            modal.ui.body.trigger(correctEvent);
            expect(spy).not.toHaveBeenCalled();
            expect(modal.close).not.toHaveBeenCalled();
            expect(modal.options.onClose).toEqual('stuff');
        });

        it('focuses the modal', function() {
            spyOn($.fn, 'focus');

            modal._show({});
            expect($.fn.focus).toHaveBeenCalled();
            expect($.fn.focus.calls.mostRecent().object).toEqual(modal.ui.modal);
        });
    });

    describe('_hide()', function() {
        var modal;
        beforeEach(function(done) {
            fixture.load('modal.html');
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                jasmine.clock().install();
                modal = new CMS.Modal({
                    modalDuration: 0
                });
                spyOn(modal, 'minimize');
                spyOn(modal, 'maximize');
                done();
            });
        });
        afterEach(function() {
            window.removeEventListener('beforeunload', modal._beforeUnloadHandler);
            fixture.cleanup();
            jasmine.clock().uninstall();
        });

        it('empties the frame', function() {
            modal.ui.frame.html('<div></div>');
            expect(modal.ui.frame).not.toBeEmpty();
            modal._hide();
            expect(modal.ui.frame).toBeEmpty();
        });

        it('removes loader', function() {
            modal.ui.modalBody.addClass('cms-loader');
            expect(modal.ui.modalBody).toHaveClass('cms-loader');
            modal._hide();
            expect(modal.ui.modalBody).not.toHaveClass('cms-loader');
        });

        it('triggers cms-modal-closed', function() {
            spyOn(Helpers, 'dispatchEvent');
            modal._hide({ duration: 10000000 });
            expect(Helpers.dispatchEvent).not.toHaveBeenCalledWith(
                'modal-closed',
                jasmine.objectContaining({ instance: modal })
            );
            jasmine.clock().tick(modal.options.duration);
            expect(Helpers.dispatchEvent).toHaveBeenCalledWith(
                'modal-closed',
                jasmine.objectContaining({ instance: modal })
            );
        });

        it('hides tooblar loader', function() {
            modal._hide({ duration: 10000000 });
            jasmine.clock().tick(modal.options.duration);
            expect(hideLoader).toHaveBeenCalled();
        });

        it('resets minimize state', function() {
            modal.minimized = true;
            modal._hide();
            expect(modal.minimize).not.toHaveBeenCalled();
            jasmine.clock().tick(modal.options.duration);
            expect(modal.minimize).toHaveBeenCalled();
        });

        it('resets maximize state', function() {
            modal.maximized = true;
            modal._hide();
            expect(modal.maximize).not.toHaveBeenCalled();
            jasmine.clock().tick(modal.options.duration);
            expect(modal.maximize).toHaveBeenCalled();
        });

        it('removes the handler to close by ESC', function() {
            var spy = jasmine.createSpy();

            modal.ui.body.on('keydown.cms.close', spy);
            expect(modal.ui.body).toHandle('keydown.cms.close');

            modal._hide();
            expect(modal.ui.body).not.toHandle('keydown.cms.close');
            modal.ui.body.trigger('keydown.cms.close');
            expect(spy).not.toHaveBeenCalled();
        });
    });

    describe('_startMove()', function() {
        var modal;
        beforeEach(function(done) {
            fixture.load('modal.html');
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                modal = new CMS.Modal({
                    modalDuration: 0
                });
                modal.ui.modal.show();
                spyOn(modal, '_stopMove');
                done();
            });
        });
        afterEach(function() {
            window.removeEventListener('beforeunload', modal._beforeUnloadHandler);
            modal.ui.body.removeAttr('data-touch-action');
            modal.ui.body.off(modal.pointerMove);
            modal.ui.body.off(modal.pointerUp);
            fixture.cleanup();
        });

        it('returns false if modal is maximized', function() {
            modal.maximized = true;
            expect(modal._startMove()).toEqual(false);
        });

        it('returns false if modal is minimized', function() {
            modal.minimized = true;
            expect(modal._startMove()).toEqual(false);
        });

        it('shows the shim', function() {
            expect(modal.ui.shim).not.toBeVisible();
            modal._startMove();
            expect(modal.ui.shim).toBeVisible();
        });

        it('adds stopMove handler', function() {
            modal._startMove();
            modal.ui.body.trigger(modal.pointerUp.split(' ')[0]);
            expect(modal._stopMove).toHaveBeenCalled();
            modal.ui.body.trigger(modal.pointerUp.split(' ')[1]);
            expect(modal._stopMove).toHaveBeenCalledTimes(2);
        });

        it('adds mousemove handler that repositions the modal', function(done) {
            var event = new $.Event(modal.pointerMove, {
                originalEvent: {
                    pageX: 23,
                    pageY: 28
                }
            });

            spyOn($.fn, 'position').and.returnValue({
                left: 20,
                top: 30
            });

            spyOn($.fn, 'css').and.callFake(function(props) {
                if (
                    props &&
                    typeof props.left !== 'undefined' &&
                    typeof props.top !== 'undefined' &&
                    Object.keys(props).length === 2
                ) {
                    expect(props).toEqual({
                        left: 20 - (100 - 23),
                        top: 30 - (100 - 28)
                    });
                    done();
                }
            });

            modal._startMove({
                originalEvent: {
                    pageX: 100,
                    pageY: 100
                }
            });

            setTimeout(function() {
                modal.ui.body.trigger(event);
            }, 1000);
        });

        it('adds data-touch-action attribute', function() {
            expect(modal.ui.body).not.toHaveAttr('data-touch-action');
            modal._startMove();
            expect(modal.ui.body).toHaveAttr('data-touch-action');
        });
    });

    describe('_stopMove()', function() {
        var modal;
        beforeEach(function(done) {
            fixture.load('modal.html');
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                modal = new CMS.Modal({
                    modalDuration: 0
                });
                modal.ui.modal.show();
                modal._startMove();
                done();
            });
        });
        afterEach(function() {
            window.removeEventListener('beforeunload', modal._beforeUnloadHandler);
            fixture.cleanup();
        });

        it('hides the shim', function() {
            expect(modal.ui.shim).toBeVisible();
            modal._stopMove();
            expect(modal.ui.shim).not.toBeVisible();
        });

        it('removes event handlers', function() {
            expect(modal.ui.body).toHandle(modal.pointerMove);
            expect(modal.ui.body).toHandle(modal.pointerUp.split(' ')[0]);
            expect(modal.ui.body).toHandle(modal.pointerUp.split(' ')[1]);
            modal._stopMove();
            expect(modal.ui.body).not.toHandle(modal.pointerMove);
            expect(modal.ui.body).not.toHandle(modal.pointerUp.split(' ')[0]);
            expect(modal.ui.body).not.toHandle(modal.pointerUp.split(' ')[1]);
        });

        it('removes data-touch-action attribute', function() {
            expect(modal.ui.body).toHaveAttr('data-touch-action');
            modal._stopMove();
            expect(modal.ui.body).not.toHaveAttr('data-touch-action');
        });
    });

    describe('_startResize()', function() {
        var modal;
        beforeEach(function(done) {
            fixture.load('modal.html');
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                modal = new CMS.Modal({
                    modalDuration: 0
                });
                modal.ui.modal.show();
                spyOn(modal, '_stopResize');
                spyOn(modal, 'close');
                done();
            });
        });
        afterEach(function() {
            window.removeEventListener('beforeunload', modal._beforeUnloadHandler);
            modal.ui.body.removeAttr('data-touch-action');
            modal.ui.body.off(modal.pointerMove);
            modal.ui.body.off(modal.pointerUp);
            fixture.cleanup();
        });

        it('returns false if the modal is maximized', function() {
            modal.maximized = true;
            expect(modal._startResize()).toEqual(false);
        });

        it('shows the shim', function() {
            expect(modal.ui.shim).not.toBeVisible();
            modal._startResize();
            expect(modal.ui.shim).toBeVisible();
        });

        it('adds handler for pointermove to reposition the modal', function() {
            expect(modal.ui.body).not.toHandle(modal.pointerMove);
            modal._startResize();
            expect(modal.ui.body).toHandle(modal.pointerMove);
        });

        it('does not let the modal to be resized smaller than min height or min width', function(done) {
            var events = [
                new $.Event(modal.pointerMove, {
                    originalEvent: {
                        pageX: 900,
                        pageY: 900
                    }
                }),
                new $.Event(modal.pointerMove, {
                    originalEvent: {
                        pageX: 950,
                        pageY: 700
                    }
                }),
                new $.Event(modal.pointerMove, {
                    originalEvent: {
                        pageX: 999,
                        pageY: 999
                    }
                })
            ];

            modal.ui.modal.hide();

            spyOn($.fn, 'width').and.returnValue(1000);
            spyOn($.fn, 'height').and.returnValue(1000);
            spyOn($.fn, 'show');
            spyOn($.fn, 'position').and.returnValue({
                left: 0,
                top: 0
            });

            modal._startResize({
                originalEvent: {
                    pageX: 1000,
                    pageY: 1000
                }
            });

            var eventsHappened = 0;
            spyOn($.fn, 'css').and.callFake(function(props) {
                switch (eventsHappened) {
                    case 0: {
                        expect(props).toEqual({
                            width: 1000 - 100 * 2,
                            height: 1000 - 100 * 2,
                            left: 100,
                            top: 100
                        });
                        break;
                    }
                    case 1: {
                        expect(props).toEqual({
                            width: 1000 - 50 * 2,
                            height: 1000 - 300 * 2,
                            left: 50,
                            top: 300
                        });
                        break;
                    }
                    case 2: {
                        expect(props).toEqual({
                            width: 1000 - 1 * 2,
                            height: 1000 - 1 * 2,
                            left: 1,
                            top: 1
                        });
                        done();
                        break;
                    }
                    default: {
                        // do nothing
                    }
                }
                eventsHappened++;
            });

            events.forEach(function(event) {
                modal.ui.body.trigger(event);
            });
        });

        it('adds handler for pointerup to stop resizing', function() {
            expect(modal.ui.body).not.toHandle(modal.pointerUp.split(' ')[0]);
            expect(modal.ui.body).not.toHandle(modal.pointerUp.split(' ')[1]);
            modal._startResize();
            expect(modal.ui.body).toHandle(modal.pointerUp.split(' ')[0]);
            expect(modal.ui.body).toHandle(modal.pointerUp.split(' ')[1]);
            modal.ui.body.trigger(modal.pointerUp.split(' ')[0]);
            modal.ui.body.trigger(modal.pointerUp.split(' ')[1]);
            expect(modal._stopResize).toHaveBeenCalledTimes(2);
        });

        it('adds data-touch-action attribute', function() {
            expect(modal.ui.body).not.toHaveAttr('data-touch-action');
            modal._startResize();
            expect(modal.ui.body).toHaveAttr('data-touch-action');
        });
    });

    describe('_stopResize()', function() {
        var modal;
        beforeEach(function(done) {
            fixture.load('modal.html');
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                modal = new CMS.Modal({
                    modalDuration: 0
                });
                modal.ui.modal.show();
                modal._startResize();
                done();
            });
        });
        afterEach(function() {
            window.removeEventListener('beforeunload', modal._beforeUnloadHandler);
            fixture.cleanup();
        });

        it('hides the shim', function() {
            expect(modal.ui.shim).toBeVisible();
            modal._stopResize();
            expect(modal.ui.shim).not.toBeVisible();
        });

        it('removes event handlers', function() {
            expect(modal.ui.body).toHandle(modal.pointerMove);
            expect(modal.ui.body).toHandle(modal.pointerUp.split(' ')[0]);
            expect(modal.ui.body).toHandle(modal.pointerUp.split(' ')[1]);
            modal._stopResize();
            expect(modal.ui.body).not.toHandle(modal.pointerMove);
            expect(modal.ui.body).not.toHandle(modal.pointerUp.split(' ')[0]);
            expect(modal.ui.body).not.toHandle(modal.pointerUp.split(' ')[1]);
        });

        it('removes data-touch-action attribute', function() {
            expect(modal.ui.body).toHaveAttr('data-touch-action');
            modal._stopResize();
            expect(modal.ui.body).not.toHaveAttr('data-touch-action');
        });
    });

    describe('_setBreadcrumb()', function() {
        var modal;
        var validBreadcrumbs = [
            { title: 'first', url: '#first' },
            { title: 'second', url: '#second' },
            { title: 'last', url: '#last' }
        ];
        beforeEach(function(done) {
            fixture.load('modal.html');
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                modal = new CMS.Modal({
                    modalDuration: 0
                });
                modal.ui.modal.show();
                done();
            });
        });
        afterEach(function() {
            window.removeEventListener('beforeunload', modal._beforeUnloadHandler);
            fixture.cleanup();
        });

        it('returns false if there is no breadcrumbs', function() {
            expect(modal._setBreadcrumb()).toEqual(false);
        });

        it('returns false if there is only one breadcrumb', function() {
            expect(modal._setBreadcrumb([])).toEqual(false);
            expect(modal._setBreadcrumb([{}])).toEqual(false);
        });

        it('returns false if first breadcrumb does not have title', function() {
            expect(modal._setBreadcrumb([{}, { title: 'breadcrumb', url: '#' }])).toEqual(false);
        });

        it('adds class to the modal', function() {
            expect(modal.ui.modal).not.toHaveClass('cms-modal-has-breadcrumb');
            modal._setBreadcrumb(validBreadcrumbs);
            expect(modal.ui.modal).toHaveClass('cms-modal-has-breadcrumb');
        });

        it('creates appropriate markup for breadcrumbs', function() {
            expect(modal.ui.breadcrumb.html()).toEqual('');
            modal._setBreadcrumb(validBreadcrumbs);
            // depending on the browser classes can be in different places or
            // not exist at all
            expect(modal.ui.breadcrumb.html()).toMatch(
                new RegExp(
                    [
                        '<a href="#first"( class="")?><span>first</span></a>',
                        '<a href="#second"( class="")?><span>second</span></a>',
                        '<a( class="active")? href="#last"( class="active")?><span>last</span></a>'
                    ].join('')
                )
            );
        });

        it('makes last breadcrumb active', function() {
            modal._setBreadcrumb(validBreadcrumbs);
            expect(modal.ui.breadcrumb.find('a:last')).toHaveClass('active');
        });
    });

    describe('_setButtons()', function() {
        var modal;
        beforeEach(function(done) {
            fixture.load('modal.html');
            CMS.config = {
                lang: {
                    cancel: 'Cancel!'
                }
            };
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                modal = new CMS.Modal({
                    modalDuration: 0
                });
                modal.ui.modal.show();
                spyOn(modal, '_loadIframe');
                spyOn(modal, 'close');
                done();
            });
        });
        afterEach(function() {
            window.removeEventListener('beforeunload', modal._beforeUnloadHandler);
            fixture.cleanup();
        });

        it('renders buttons from the iframe to the modal', function() {
            expect(modal.ui.modalButtons).toBeEmpty();
            modal._setButtons($('.buttons-test-iframe'));
            expect(modal.ui.modalButtons).not.toBeEmpty();
            /* eslint-disable indent */
            expect(modal.ui.modalButtons.html()).toMatch(
                new RegExp(
                    [
                        '<div class="cms-modal-buttons-inner">',
                        '<div class="cms-modal-item-buttons">',
                        '<a( href="#")? class="cms-btn cms-btn-action default"( href="#")?>default</a>',
                        '</div>',
                        '<div class="cms-modal-item-buttons">',
                        '<a( href="#")? class="cms-btn undefined"( href="#")?>whatever correct</a>',
                        '</div>',
                        '<div class="cms-modal-item-buttons">',
                        '<a( href="#")? class="cms-btn undefined"( href="#")?>link</a>',
                        '</div>',
                        '<div class="cms-modal-item-buttons">',
                        '<a( href="#")? class="cms-btn cms-btn-caution deletelink"( href="#")?>caution</a>',
                        '</div>',
                        '<div class="cms-modal-item-buttons">',
                        '<a( href="#")? class="cms-btn"( href="#")?>Cancel!</a>',
                        '</div>',
                        '</div>'
                    ].join('')
                )
            );
            /* eslint-enable indent */
        });

        it('adds handlers to the newly created buttons', function() {
            modal._setButtons($('.buttons-test-iframe'));
            expect(modal.ui.modalButtons.find('a')).toHandle(modal.click);
            expect(modal.ui.modalButtons.find('a')).toHandle(modal.touchEnd);
            var spy = jasmine.createSpy();
            spyOn($.fn, 'hide');

            $('.buttons-test-iframe').find('a, input, button').on('click', function(e) {
                e.preventDefault();
                spy();
            });

            modal.ui.modalButtons.find('.cms-modal-item-buttons:eq(2) a').trigger(modal.click);
            expect(modal._loadIframe).toHaveBeenCalledWith({
                url: jasmine.stringMatching(/cms_path[^#]*?#go/),
                name: 'link'
            });
            expect(spy).not.toHaveBeenCalled();
            expect(modal.saved).toEqual(false);
            expect(modal.hideFrame).toEqual(undefined);

            modal.ui.modalButtons.find('.cms-modal-item-buttons:eq(0) a').trigger(modal.touchEnd);
            expect(spy).toHaveBeenCalledTimes(1);
            expect(modal.saved).toEqual(false);
            expect(modal.hideFrame).toEqual(true);

            modal.saved = false;
            modal.hideFrame = undefined;
            modal.ui.modalButtons.find('.cms-modal-item-buttons:eq(1) a').trigger(modal.touchEnd);
            expect(spy).toHaveBeenCalledTimes(2);
            expect(modal.saved).toEqual(false);
            expect(modal.hideFrame).toEqual(undefined);

            expect($.fn.hide).not.toHaveBeenCalled();
            modal.saved = false;
            modal.hideFrame = undefined;
            modal.ui.modalButtons.find('.cms-modal-item-buttons:eq(3) a').trigger(modal.touchEnd);
            expect(spy).toHaveBeenCalledTimes(2);
            expect(modal.saved).toEqual(true);
            expect(modal.hideFrame).toEqual(undefined);
            expect($.fn.hide.calls.mostRecent().object.selector).toEqual(
                modal.ui.modal.find('.cms-modal-frame iframe').selector
            );

            modal.saved = false;
            modal.hideFrame = undefined;
            modal.options = {
                onClose: 'something'
            };
            expect(modal.close).not.toHaveBeenCalled();
            modal.ui.modalButtons.find('.cms-modal-item-buttons:eq(4) a').trigger(modal.click);
            expect(spy).toHaveBeenCalledTimes(2);
            expect(modal.saved).toEqual(false);
            expect(modal.hideFrame).toEqual(undefined);
            expect(modal.close).toHaveBeenCalled();
            expect(modal.options.onClose).toEqual(null);
            expect($.fn.hide).toHaveBeenCalledTimes(1);
        });

        it('submits the form vs clicking on button if there is only one submit button', function() {
            $('.buttons-test-iframe').find('input, a').remove();

            modal._setButtons($('.buttons-test-iframe'));

            var clickSpy = jasmine.createSpy();
            var submitSpy = jasmine.createSpy();

            $('.buttons-test-iframe').find('button').on('click', function(e) {
                e.preventDefault();
                clickSpy();
            });
            $('#iframe-form').on('submit', function(e) {
                e.preventDefault();
                submitSpy();
            });

            modal.ui.modalButtons.find('.cms-modal-item-buttons:eq(0) a').trigger(modal.click);
            expect(clickSpy).not.toHaveBeenCalled();
            expect(submitSpy).toHaveBeenCalledTimes(1);
        });

        it('adds submit handlers to the form', function() {
            modal._setButtons($('.buttons-test-iframe'));
            var form = $('#iframe-form').on('submit', function(e) {
                e.preventDefault();
            });

            expect(modal.saved).toEqual(false);
            expect(modal.hideFrame).toEqual(undefined);

            form.trigger('submit');
            expect(modal.saved).toEqual(false);
            expect(modal.hideFrame).toEqual(undefined);

            modal.hideFrame = true;
            form.trigger('submit');
            expect(modal.saved).toEqual(true);
            expect(modal.hideFrame).toEqual(true);
        });
    });

    describe('_changeIframe()', function() {
        var modal;
        var breadcrumbs = [
            { title: 'first', url: '#first' },
            { title: 'second', url: '#second' },
            { title: 'last', url: '#last' }
        ];
        beforeEach(function(done) {
            fixture.load('modal.html');
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                modal = new CMS.Modal({
                    modalDuration: 0
                });
                modal.ui.modal.show();
                modal._setBreadcrumb(breadcrumbs);
                spyOn(modal, '_loadIframe');
                done();
            });
        });
        afterEach(function() {
            window.removeEventListener('beforeunload', modal._beforeUnloadHandler);
            fixture.cleanup();
        });

        it('returns false if element was active', function() {
            expect(modal._changeIframe(modal.ui.breadcrumb.find('a:last'))).toEqual(false);
        });
        it('changes the class if element was not active', function() {
            expect(modal.ui.breadcrumb.find('a:last')).toHaveClass('active');
            modal._changeIframe(modal.ui.breadcrumb.find('a:first'));
            expect(modal.ui.breadcrumb.find('a:last')).not.toHaveClass('active');
            expect(modal.ui.breadcrumb.find('a:first')).toHaveClass('active');
        });
        it('loads the iframe', function() {
            modal._changeIframe(modal.ui.breadcrumb.find('a:first'));
            expect(modal._loadIframe).toHaveBeenCalledWith({
                url: '#first'
            });
        });
        it('changes titlePrefix', function() {
            expect(modal.ui.titlePrefix.text()).toEqual('');
            modal._changeIframe(modal.ui.breadcrumb.find('a:eq(1)'));
            expect(modal.ui.titlePrefix.text()).toEqual('second');
        });
    });

    describe('CMS.Modal._setupCtrlEnterSave()', function() {
        var spy;
        var button;
        var doc = $(document);
        beforeEach(function(done) {
            fixture.load('modal.html');
            $(function() {
                spy = jasmine.createSpy();
                button = $('<div class="cms-btn-action"></div>').on('click', spy);
                button.appendTo('.cms-modal-buttons');
                done();
            });
        });
        afterEach(function() {
            doc.off('keydown.cms.submit keyup.cms.submit');
            fixture.cleanup();
        });

        it('adds handlers to the document', function() {
            expect(doc).not.toHandle('keydown.cms.submit');
            expect(doc).not.toHandle('keyup.cms.submit');
            CMS.Modal._setupCtrlEnterSave(document);
            expect(doc).toHandle('keydown.cms.submit');
            expect(doc).toHandle('keyup.cms.submit');
        });

        it('triggers modal action if ctrl+enter is pressed on win', function() {
            spyOn(String.prototype, 'toLowerCase').and.returnValue('win');
            CMS.Modal._setupCtrlEnterSave(document);

            doc.trigger(new $.Event('keydown', { ctrlKey: false, keyCode: KEYS.ENTER }));
            doc.trigger(new $.Event('keyup', { ctrlKey: false, keyCode: KEYS.ENTER }));
            expect(spy).not.toHaveBeenCalled();

            doc.trigger(new $.Event('keydown', { ctrlKey: true, keyCode: KEYS.ENTER }));
            doc.trigger(new $.Event('keyup', { ctrlKey: true, keyCode: KEYS.ENTER }));
            expect(spy).toHaveBeenCalledTimes(1);
        });

        it('does not trigger modal action if ctrl+enter is pressed on mac', function() {
            spyOn(String.prototype, 'toLowerCase').and.returnValue('mac');
            CMS.Modal._setupCtrlEnterSave(document);

            doc.trigger(new $.Event('keydown', { ctrlKey: false, keyCode: KEYS.ENTER }));
            doc.trigger(new $.Event('keyup', { ctrlKey: false, keyCode: KEYS.ENTER }));
            expect(spy).not.toHaveBeenCalled();

            doc.trigger(new $.Event('keydown', { ctrlKey: true, keyCode: KEYS.ENTER }));
            doc.trigger(new $.Event('keyup', { ctrlKey: true, keyCode: KEYS.ENTER }));
            expect(spy).not.toHaveBeenCalled();
        });

        it('triggers modal action if cmd+enter is pressed on mac', function() {
            spyOn(String.prototype, 'toLowerCase').and.returnValue('mac');
            CMS.Modal._setupCtrlEnterSave(document);

            doc.trigger(new $.Event('keydown', { keyCode: KEYS.CMD_LEFT }));
            doc.trigger(new $.Event('keydown', { keyCode: KEYS.ENTER }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.CMD_LEFT }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.ENTER }));
            expect(spy).toHaveBeenCalledTimes(1);

            doc.trigger(new $.Event('keydown', { keyCode: KEYS.CMD_RIGHT }));
            doc.trigger(new $.Event('keydown', { keyCode: KEYS.ENTER }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.CMD_RIGHT }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.ENTER }));
            expect(spy).toHaveBeenCalledTimes(2);

            doc.trigger(new $.Event('keydown', { keyCode: KEYS.CMD_FIREFOX }));
            doc.trigger(new $.Event('keydown', { keyCode: KEYS.ENTER }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.CMD_FIREFOX }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.ENTER }));
            expect(spy).toHaveBeenCalledTimes(3);
        });

        it('does not trigger modal action if cmd enter was pressed on mac through subsequent keystrokes', function() {
            spyOn(String.prototype, 'toLowerCase').and.returnValue('mac');
            CMS.Modal._setupCtrlEnterSave(document);

            doc.trigger(new $.Event('keydown', { keyCode: KEYS.CMD_LEFT }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.CMD_LEFT }));
            doc.trigger(new $.Event('keydown', { keyCode: KEYS.ENTER }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.ENTER }));
            expect(spy).not.toHaveBeenCalled();

            doc.trigger(new $.Event('keydown', { keyCode: KEYS.CMD_RIGHT }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.CMD_RIGHT }));
            doc.trigger(new $.Event('keydown', { keyCode: KEYS.ENTER }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.ENTER }));
            expect(spy).not.toHaveBeenCalled();

            doc.trigger(new $.Event('keydown', { keyCode: KEYS.CMD_FIREFOX }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.CMD_FIREFOX }));
            doc.trigger(new $.Event('keydown', { keyCode: KEYS.ENTER }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.ENTER }));
            expect(spy).not.toHaveBeenCalled();
        });

        it('does not trigger modal action if cmd+enter is pressed on win', function() {
            spyOn(String.prototype, 'toLowerCase').and.returnValue('win');
            CMS.Modal._setupCtrlEnterSave(document);

            doc.trigger(new $.Event('keydown', { keyCode: KEYS.CMD_LEFT }));
            doc.trigger(new $.Event('keydown', { keyCode: KEYS.ENTER }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.CMD_LEFT }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.ENTER }));
            expect(spy).not.toHaveBeenCalled();

            doc.trigger(new $.Event('keydown', { keyCode: KEYS.CMD_RIGHT }));
            doc.trigger(new $.Event('keydown', { keyCode: KEYS.ENTER }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.CMD_RIGHT }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.ENTER }));
            expect(spy).not.toHaveBeenCalled();

            doc.trigger(new $.Event('keydown', { keyCode: KEYS.CMD_FIREFOX }));
            doc.trigger(new $.Event('keydown', { keyCode: KEYS.ENTER }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.CMD_FIREFOX }));
            doc.trigger(new $.Event('keyup', { keyCode: KEYS.ENTER }));
            expect(spy).not.toHaveBeenCalled();
        });
    });

    describe('_loadIframe()', function() {
        var modal;
        beforeEach(function(done) {
            fixture.load('modal.html');
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Messages = {
                open: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            $(function() {
                modal = new CMS.Modal();
                modal.ui.modal.show();
                spyOn(Helpers, 'reloadBrowser');
                spyOn(modal, '_setBreadcrumb');
                spyOn(modal, '_setButtons');
                spyOn(CMS.Modal, '_setupCtrlEnterSave');
                spyOn(modal, 'close');
                done();
            });
        });

        afterEach(function() {
            window.removeEventListener('beforeunload', modal._beforeUnloadHandler);
            fixture.cleanup();
        });

        it('adds appropriate classes', function() {
            jasmine.clock().install();
            expect(modal.ui.modal).not.toHaveClass('cms-modal-iframe');
            expect(modal.ui.modal).not.toHaveClass('cms-modal-markup');
            expect(modal.ui.modalBody).not.toHaveClass('cms-loader');

            modal.ui.modal.addClass('cms-modal-markup');
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe.html'
            });

            expect(modal.ui.modal).toHaveClass('cms-modal-iframe');
            expect(modal.ui.modal).not.toHaveClass('cms-modal-markup');
            expect(modal.ui.modalBody).not.toHaveClass('cms-loader');
            jasmine.clock().tick(501);
            expect(modal.ui.modalBody).toHaveClass('cms-loader');
            jasmine.clock().uninstall();
        });

        it('adds correct title while loading', function() {
            expect(modal.ui.titlePrefix.text()).toEqual('');
            expect(modal.ui.titleSuffix.text()).toEqual('');

            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe.html'
            });

            expect(modal.ui.titlePrefix.text()).toEqual('');
            expect(modal.ui.titleSuffix.text()).toEqual('');

            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe.html',
                title: 'Test title'
            });

            expect(modal.ui.titlePrefix.text()).toEqual('Test title');
            expect(modal.ui.titleSuffix.text()).toEqual('');
        });

        it('opens error message and closes the iframe if its contents cannot be accessed', function(done) {
            CMS.config.lang.errorLoadingEditForm = 'Cannot access contents';
            spyOn($.fn, 'contents').and.callFake(function() {
                throw new Error('Cannot access contents');
            });
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(modal.close).toHaveBeenCalled();
                expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                    message: '<strong>Cannot access contents</strong>',
                    error: true,
                    delay: 0
                });
                done();
            });
        });

        it('sets up ctrl + enter save', function(done) {
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(CMS.Modal._setupCtrlEnterSave).toHaveBeenCalledWith(
                    modal.ui.frame.find('iframe')[0].contentDocument
                );
                done();
            });
        });

        it('shows and hides the loader', function(done) {
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe.html'
            });
            expect(hideLoader).not.toHaveBeenCalled();
            expect(showLoader).toHaveBeenCalledTimes(1);
            modal.ui.modal.find('iframe').on('load', function() {
                expect(hideLoader).toHaveBeenCalledTimes(1);
                expect(showLoader).toHaveBeenCalledTimes(1);
                done();
            });
        });

        it('shows messages if iframe contains them', function(done) {
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_messages.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                    message: 'Django CMS is amazing!'
                });
                done();
            });
        });

        it('adds cms-admin cms-admin-modal classes to the iframe body', function(done) {
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_messages.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect($(this).contents().find('body')).toHaveClass('cms-admin');
                expect($(this).contents().find('body')).toHaveClass('cms-admin-modal');
                done();
            });
        });

        it('removes cms-loader class when iframe is loaded', function(done) {
            jasmine.clock().install();
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_messages.html'
            });
            jasmine.clock().tick(501);
            expect(modal.ui.modalBody).toHaveClass('cms-loader');
            modal.ui.modal.find('iframe').on('load', function() {
                expect(modal.ui.modalBody).not.toHaveClass('cms-loader');
                jasmine.clock().uninstall();
                done();
            });
        });

        describe('reloading', function() {
            it('does not reload the page if not required', function(done) {
                modal._loadIframe({
                    url: '/base/cms/tests/frontend/unit/html/modal_iframe_messages.html'
                });
                modal.ui.modal.find('iframe').on('load', function() {
                    expect(Helpers.reloadBrowser).not.toHaveBeenCalled();
                    done();
                });
            });
            it('does not reload the page if not required', function(done) {
                modal.enforceReload = true;
                modal._loadIframe({
                    url: '/base/cms/tests/frontend/unit/html/modal_iframe.html'
                });
                modal.ui.modal.find('iframe').on('load', function() {
                    expect(Helpers.reloadBrowser).not.toHaveBeenCalled();
                    done();
                });
            });

            xit('does reload the page if required', function(done) {
                modal.enforceReload = true;
                modal._loadIframe({
                    url: '/base/cms/tests/frontend/unit/html/modal_iframe_messages.html'
                });
                modal.ui.modal.find('iframe').on('load', function() {
                    expect(Helpers.reloadBrowser).toHaveBeenCalledWith();
                    done();
                });
            });

            xit('does show loaders if reload the page if required', function(done) {
                modal.enforceReload = true;
                expect(modal.ui.modalBody).not.toHaveClass('cms-loader');
                modal._loadIframe({
                    url: '/base/cms/tests/frontend/unit/html/modal_iframe_messages.html'
                });
                modal.ui.modal.find('iframe').on('load', function() {
                    expect(showLoader).toHaveBeenCalledTimes(2);
                    expect(modal.ui.modalBody).toHaveClass('cms-loader');
                    done();
                });
            });
        });

        it('does not close the modal if not required', function(done) {
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_messages.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(modal.close).not.toHaveBeenCalled();
                done();
            });
        });
        it('does not close the modal if not required', function(done) {
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(modal.close).not.toHaveBeenCalled();
                done();
            });
        });

        it('does not close the modal if not required', function(done) {
            modal.enforceClose = true;
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(modal.close).not.toHaveBeenCalled();
                done();
            });
        });

        it('closes the modal if required', function(done) {
            modal.enforceClose = true;
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_messages.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(modal.close).toHaveBeenCalledTimes(1);
                done();
            });
        });

        it('resets django viewsitelink to open in the top level window', function(done) {
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_messages.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(modal.close).not.toHaveBeenCalled();
                expect($(this).contents().find('.viewsitelink')).toHaveAttr('target', '_top');
                done();
            });
        });

        it('sets the buttons', function(done) {
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_messages.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(modal._setButtons).toHaveBeenCalledWith($(this));
                done();
            });
        });

        it('does not reset the saved state if there is no form errors', function(done) {
            modal.saved = 'custom';
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_messages.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(modal.saved).toEqual('custom');
                done();
            });
        });

        it('resets the saved state if there is a form error loaded in the iframe', function(done) {
            modal.saved = true;
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_errornote.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(modal.saved).toEqual(false);
                done();
            });
        });

        it('resets the saved state if there was no success message in the frame', function(done) {
            modal.saved = true;
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_no_success.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(modal.saved).toEqual(false);
                done();
            });
        });

        it('resets the saved state if there is a form error loaded in the iframe', function(done) {
            modal.saved = true;
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_errorlist.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(modal.saved).toEqual(false);
                done();
            });
        });

        xit('reloads browser if iframe was saved and there is no delete confirmation', function(done) {
            modal.saved = true;
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_messages.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(Helpers.reloadBrowser).toHaveBeenCalledWith(jasmine.any(String), false, true);
                done();
            });
        });

        xit('reloads browser if iframe was saved and there is no delete confirmation', function(done) {
            modal.saved = true;
            modal.options.onClose = '/custom-on-close';
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_messages.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(Helpers.reloadBrowser).toHaveBeenCalledWith('/custom-on-close', false, true);
                done();
            });
        });

        xit('shows loaders when reloads browser if iframe was saved', function(done) {
            modal.saved = true;
            expect(modal.ui.modalBody).not.toHaveClass('cms-loader');
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_messages.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(showLoader).toHaveBeenCalledTimes(2);
                expect(modal.ui.modalBody).toHaveClass('cms-loader');
                done();
            });
        });

        it('updates the title of the modal if required', function(done) {
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_title.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(modal.ui.titlePrefix.text()).toEqual('I am a title');
                expect(modal.ui.titleSuffix.text()).toEqual('');
                expect($(this).contents().find('h1').length).toEqual(1);
                done();
            });
        });

        it('updates the title of the modal if required', function(done) {
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_title.html',
                title: 'Test title'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(modal.ui.titlePrefix.text()).toEqual('Test title');
                expect(modal.ui.titleSuffix.text()).toEqual('I am a title');
                expect($(this).contents().find('h1').length).toEqual(1);
                done();
            });
        });

        it('updates the title of the modal if required', function(done) {
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_title.html',
                title: '     '
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(modal.ui.titlePrefix.text()).toEqual('I am a title');
                expect(modal.ui.titleSuffix.text()).toEqual('');
                expect($(this).contents().find('h1').length).toEqual(1);
                done();
            });
        });

        it('sets iframe data ready', function(done) {
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_title.html'
            });
            expect(modal.ui.frame.find('iframe').data('ready')).toEqual(undefined);
            modal.ui.modal.find('iframe').on('load', function() {
                expect($(this).data('ready')).toEqual(true);
                done();
            });
        });

        it('adds keydown event to close the modal if ESC is pressed inside of the iframe', function(done) {
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_title.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                var body = $(this).contents().find('body');
                expect(body).toHandle('keydown.cms');

                body.on('keydown.cms', function() {
                    if (modal.close.calls.count()) {
                        // have to wait till next frame here
                        // because Edge is too fast and it cleans up
                        // the test case _before_ second trigger call finishes
                        setTimeout(function() {
                            done();
                        }, 0);
                    }
                });

                body.trigger(new $.Event('keydown', { keyCode: KEYS.SPACE }));
                body.trigger(new $.Event('keydown', { keyCode: KEYS.ESC }));
            });
        });

        it('adds keydown event that does not close if not confirmed', function(done) {
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_title.html'
            });
            spyOn(modal, '_confirmDirtyEscCancel').and.returnValue(false);
            modal.ui.modal.find('iframe').on('load', function() {
                var body = $(this).contents().find('body');
                expect(body).toHandle('keydown.cms');

                body.on('keydown.cms', function() {
                    expect(modal._confirmDirtyEscCancel).toHaveBeenCalledTimes(1);
                    expect(modal.close).not.toHaveBeenCalled();
                    done();
                });

                body.trigger(new $.Event('keydown', { keyCode: KEYS.ESC }));
            });
        });

        it('does not adjust content if object-tools are not available', function(done) {
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_messages.html'
            });
            spyOn($.fn, 'css');
            modal.ui.modal.find('iframe').on('load', function() {
                expect($.fn.css).not.toHaveBeenCalledWith('padding-top', 38);
                done();
            });
        });

        it('adjusts content if object-tools available', function(done) {
            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_title.html'
            });
            spyOn($.fn, 'css');
            modal.ui.modal.find('iframe').on('load', function() {
                expect($.fn.css).toHaveBeenCalledWith('padding-top', 38);
                done();
            });
        });

        it('attaches content preserving handlers', function(done) {
            spyOn(modal, '_attachContentPreservingHandlers');

            modal._loadIframe({
                url: '/base/cms/tests/frontend/unit/html/modal_iframe_title.html'
            });
            modal.ui.modal.find('iframe').on('load', function() {
                expect(modal._attachContentPreservingHandlers).toHaveBeenCalledTimes(1);
                expect(modal._attachContentPreservingHandlers).toHaveBeenCalledWith(this);
                done();
            });
        });
    });

    describe('_attachContentPreservingHandlers', function() {
        var modal;
        beforeEach(function(done) {
            fixture.load('modal.html');
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Messages = {
                open: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy()
            };
            CMS.config = {
                lang: {
                    confirmDirty: 'Smth changed!',
                    confirmDirtyESC: 'Smth changed and you are pressing ESC'
                }
            };
            $(function() {
                modal = new CMS.Modal();
                modal.ui.modal.show();
                spyOn(Helpers, 'reloadBrowser');
                spyOn(modal, '_setBreadcrumb');
                spyOn(modal, '_setButtons');
                spyOn(CMS.Modal, '_setupCtrlEnterSave');
                spyOn(modal, 'close');
                done();
            });
        });

        afterEach(function() {
            window.removeEventListener('beforeunload', modal._beforeUnloadHandler);
            fixture.cleanup();
        });

        it('creates the tracker', function() {
            expect(modal.tracker).not.toBeDefined();
            modal._attachContentPreservingHandlers($());
            expect(modal.tracker).toEqual(jasmine.any(Object));
        });

        it('adds the evnet listener to the window', function() {
            var addEventListener = jasmine.createSpy();
            spyOn(Helpers, '_getWindow').and.returnValue({
                addEventListener: addEventListener
            });

            modal._attachContentPreservingHandlers($());
            expect(addEventListener).toHaveBeenCalledTimes(1);
            expect(addEventListener).toHaveBeenCalledWith('beforeunload', modal._beforeUnloadHandler);
        });

        describe('_beforeUnloadHandler', function() {
            it('returns a warning if form has changed', function() {
                modal.tracker = {
                    isFormChanged: function() {
                        return true;
                    }
                };

                expect(modal._beforeUnloadHandler({})).toEqual('Smth changed!');
            });

            it('assigns return value to the event if form has changed', function() {
                modal.tracker = {
                    isFormChanged: function() {
                        return true;
                    }
                };
                var event = {};
                modal._beforeUnloadHandler(event);
                expect(event.returnValue).toEqual('Smth changed!');
            });

            it('does not do anything if form did not change', function() {
                modal.tracker = {
                    isFormChanged: function() {
                        return false;
                    }
                };
                expect(modal._beforeUnloadHandler({})).not.toBeDefined();
            });
        });

        describe('_confirmDirtyEscCancel', function() {
            beforeEach(function() {
                spyOn(Helpers, 'secureConfirm');
            });

            it('returns true if there is no tracker', function() {
                expect(modal._confirmDirtyEscCancel()).toEqual(true);
                expect(Helpers.secureConfirm).not.toHaveBeenCalled();
            });

            it('returns true if there is a tracker but form did not change', function() {
                modal.tracker = {
                    isFormChanged: function() {
                        return false;
                    }
                };

                expect(modal._confirmDirtyEscCancel()).toEqual(true);
                expect(Helpers.secureConfirm).not.toHaveBeenCalled();
            });

            it('returns result of the confirmation if there is a tracker and form changed', function() {
                Helpers.secureConfirm.and.returnValue(true);

                modal.tracker = {
                    isFormChanged: function() {
                        return true;
                    }
                };

                expect(modal._confirmDirtyEscCancel()).toEqual(true);
                expect(Helpers.secureConfirm).toHaveBeenCalledTimes(1);
                expect(Helpers.secureConfirm).toHaveBeenCalledWith(
                    'Smth changed!\n\nSmth changed and you are pressing ESC'
                );

                Helpers.secureConfirm.and.returnValue(false);

                expect(modal._confirmDirtyEscCancel()).toEqual(false);
                expect(Helpers.secureConfirm).toHaveBeenCalledTimes(2);
            });
        });
    });
});
