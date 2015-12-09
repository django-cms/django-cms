/* globals $ */

'use strict';

describe('CMS.Modal', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a Modal class when document is ready', function () {
        expect(CMS.Modal).toBeDefined();
    });

    it('has public API', function () {
        expect(CMS.Modal.prototype.open).toEqual(jasmine.any(Function));
        expect(CMS.Modal.prototype.close).toEqual(jasmine.any(Function));
        expect(CMS.Modal.prototype.minimize).toEqual(jasmine.any(Function));
        expect(CMS.Modal.prototype.maximize).toEqual(jasmine.any(Function));
    });

    describe('instance', function () {
        it('has ui', function (done) {
            $(function () {
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

        it('has options', function (done) {
            $(function () {
                var modal = new CMS.Modal();
                expect(modal.options).toEqual({
                    onClose: false,
                    minHeight: 400,
                    minWidth: 800,
                    modalDuration: 200,
                    newPlugin: false,
                    resizable: true,
                    maximizable: true,
                    minimizable: true
                });

                var modal2 = new CMS.Modal({ minHeight: 300, minWidth: 100 });
                expect(modal2.options).toEqual({
                    onClose: false,
                    minHeight: 300,
                    minWidth: 100,
                    modalDuration: 200,
                    newPlugin: false,
                    resizable: true,
                    maximizable: true,
                    minimizable: true
                });

                done();
            });
        });
    });

    describe('.open()', function () {
        beforeEach(function (done) {
            fixture.load('modal.html');
            delete CMS._newPlugin;
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy(),
                showLoader: jasmine.createSpy(),
                hideLoader: jasmine.createSpy()
            };
            $(function () {
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('throws an error when no url or html options were passed', function () {
            var modal = new CMS.Modal();

            expect(modal.open.bind(modal, {})).toThrowError(
                Error, 'The arguments passed to "open" were invalid.'
            );
            expect(modal.open.bind(modal, { html: '' })).toThrowError(
                Error, 'The arguments passed to "open" were invalid.'
            );
            expect(modal.open.bind(modal, { url: '' })).toThrowError(
                Error, 'The arguments passed to "open" were invalid.'
            );
            expect(modal.open.bind(modal, { html: '<div></div>' })).not.toThrow();
            expect(modal.open.bind(modal, {
                url: '/base/cms/tests/frontend/unit/html/modal_iframe.html'
            })).not.toThrow();
        });

        it('does not open if there is a plugin creation in process', function () {
            var modal = new CMS.Modal();
            CMS._newPlugin = true;
            spyOn(modal, '_deletePlugin').and.callFake(function () {
                return false;
            });

            expect(modal.open({ html: '<div></div>' })).toEqual(false);
        });

        it('confirms if the user wants to remove freshly created plugin when opening new modal', function () {
            var modal = new CMS.Modal();
            spyOn(CMS.Navigation.prototype, 'initialize').and.callFake(function () {
                return {};
            });
            jasmine.clock().install(); // stop timeout that does initialStates
            CMS.API.Toolbar = new CMS.Toolbar();
            CMS._newPlugin = {
                delete: '/delete-url',
                breadcrumb: [{ title: 'Fresh plugin' }]
            };

            CMS.config = $.extend(CMS.config, {
                csrf: 'custom-token',
                lang: {
                    confirmEmpty: 'Question about {1}?'
                }
            });

            spyOn(modal, '_deletePlugin').and.callThrough();
            jasmine.Ajax.install();
            spyOn(CMS.API.Toolbar, 'openAjax').and.callThrough();
            spyOn(CMS.API.Helpers, 'secureConfirm').and.callFake(function () {
                return false;
            });

            expect(modal.open({ html: '<div></div>' })).toEqual(false);
            expect(CMS.API.Toolbar.openAjax).toHaveBeenCalledWith({
                url: '/delete-url',
                post: '{ "csrfmiddlewaretoken": "custom-token" }',
                text: 'Question about Fresh plugin?',
                callback: jasmine.any(Function)
            });
            jasmine.Ajax.uninstall();
            jasmine.clock().uninstall();
        });

        it('should be chainable', function () {
            var modal = new CMS.Modal();

            expect(modal.open({ html: '<div></div>' })).toEqual(modal);
        });

        it('hides the tooltip', function () {
            var modal = new CMS.Modal();

            modal.open({ html: '<div></div>' });
            expect(CMS.API.Tooltip.hide).toHaveBeenCalled();
        });

        it('triggers load events on instance and the DOM node', function () {
            var modal = new CMS.Modal();

            spyOn(modal, 'trigger');
            var spyEvent = spyOnEvent(modal.ui.modal, 'cms.modal.load');
            modal.open({ html: '<div></div>' });

            expect(modal.trigger).toHaveBeenCalledWith('cms.modal.load');
            expect(spyEvent).toHaveBeenTriggered();
            expect(modal.trigger).toHaveBeenCalledWith('cms.modal.loaded');
        });

        it('sets CMS._newPlugin if we are opening a plugin creation modal', function () {
            var modal = new CMS.Modal({
                newPlugin: {
                    something: true
                }
            });

            modal.open({ html: '<div></div>' });
            expect(CMS._newPlugin).toEqual({ something: true });
        });

        it('applies correct state to modal controls', function () {
            var modal;
            modal = new CMS.Modal();
            modal.open({ html: '<div></div>' });
            expect(modal.ui.resize).toBeVisible();
            expect(modal.ui.minimizeButton).toBeVisible();
            expect(modal.ui.maximizeButton).toBeVisible();

            modal = new CMS.Modal({ resizable: false });
            modal.open({ html: '<div></div>' });
            expect(modal.ui.resize).not.toBeVisible();
            expect(modal.ui.minimizeButton).toBeVisible();
            expect(modal.ui.maximizeButton).toBeVisible();

            modal = new CMS.Modal({ resizable: true });
            modal.open({ html: '<div></div>' });
            expect(modal.ui.resize).toBeVisible();
            expect(modal.ui.minimizeButton).toBeVisible();
            expect(modal.ui.maximizeButton).toBeVisible();

            modal = new CMS.Modal({ minimizable: false });
            modal.open({ html: '<div></div>' });
            expect(modal.ui.resize).toBeVisible();
            expect(modal.ui.minimizeButton).not.toBeVisible();
            expect(modal.ui.maximizeButton).toBeVisible();

            modal = new CMS.Modal({ minimizable: true });
            modal.open({ html: '<div></div>' });
            expect(modal.ui.resize).toBeVisible();
            expect(modal.ui.minimizeButton).toBeVisible();
            expect(modal.ui.maximizeButton).toBeVisible();

            modal = new CMS.Modal({ maximizable: false });
            modal.open({ html: '<div></div>' });
            expect(modal.ui.resize).toBeVisible();
            expect(modal.ui.minimizeButton).toBeVisible();
            expect(modal.ui.maximizeButton).not.toBeVisible();

            modal = new CMS.Modal({ maximizable: true });
            modal.open({ html: '<div></div>' });
            expect(modal.ui.resize).toBeVisible();
            expect(modal.ui.minimizeButton).toBeVisible();
            expect(modal.ui.maximizeButton).toBeVisible();
        });

        it('resets minimized state if the modal was already minimized', function () {
            var modal = new CMS.Modal();

            modal.open({ html: '<div></div>' });
            modal.minimize();
            expect(modal.minimized).toEqual(true);

            spyOn(modal, 'minimize').and.callThrough();

            modal.open({ html: '<span></span>' });
            expect(modal.minimized).toEqual(false);
            expect(modal.minimize).toHaveBeenCalled();
            expect(modal.minimize.calls.count()).toEqual(1);
        });

        it('clears breadcrumbs and buttons if they exist', function () {
            var modal = new CMS.Modal();
            modal.ui.modal.addClass('cms-modal-has-breadcrumb');
            modal.ui.modalButtons.html('<div>button</div>');
            modal.ui.breadcrumb.html('<div>breadcrumbs</div>');

            modal.open({ html: '<div></div>' });
            expect(modal.ui.modal).not.toHaveClass('cms-modal-has-breadcrumb');
            expect(modal.ui.modalButtons).toBeEmpty();
            expect(modal.ui.breadcrumb).toBeEmpty();
        });
    });

    describe('.minimize()', function () {
        beforeEach(function (done) {
            fixture.load('modal.html');
            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };
            CMS.API.Toolbar = {
                open: jasmine.createSpy(),
                showLoader: jasmine.createSpy(),
                hideLoader: jasmine.createSpy()
            };
            $(function () {
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('minimizes the modal', function () {
            var modal = new CMS.Modal();

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

        it('opens the toolbar', function () {
            var modal = new CMS.Modal();

            modal.open({ html: '<div></div>' });
            modal.minimize();

            expect(CMS.API.Toolbar.open).toHaveBeenCalled();
            modal.minimize(); // restore
        });

        it('stores the css data to be able to restore a modal', function () {
            var modal = new CMS.Modal();

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

        it('doesnt minimize maximized modal', function () {
            var modal = new CMS.Modal();

            modal.maximized = true;
            expect(modal.minimize()).toEqual(false);
            expect(CMS.API.Toolbar.open).not.toHaveBeenCalled();
            expect(modal.ui.body).not.toHaveClass('cms-modal-minimized');
        });

        it('restores modal if it was already minimized', function () {
            var modal = new CMS.Modal();
            modal.open({ html: '<div></div>' });
            modal.minimize();

            expect(modal.minimized).toEqual(true);
            expect(modal.ui.body).toHaveClass('cms-modal-minimized');

            modal.minimize();

            expect(modal.minimized).toEqual(false);
            expect(modal.ui.body).not.toHaveClass('cms-modal-minimized');
        });
    });

    describe('.maximize()', function () {

    });

    describe('.close()', function () {

    });
});
