'use strict';

describe('CMS.Toolbar', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a Toolbar class when document is ready', function () {
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

        it('initializes the states', function () {
            spyOn(CMS.Toolbar.prototype, '_initialStates');
            jasmine.clock().install();
            toolbar = new CMS.Toolbar();
            expect(toolbar._initialStates).not.toHaveBeenCalled();
            jasmine.clock().tick(200);
            expect(toolbar._initialStates).toHaveBeenCalled();
            jasmine.clock().uninstall();
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

        it('animates toolbar to correct position', function () {
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
                'linear'
            );
            // here we have to use toBeCloseTo because different browsers report different values
            // e.g. FF reports 45.16666
            expect($.fn.animate.calls.mostRecent().args[0]['margin-top']).toBeCloseTo(45, 0);
        });

        it('animates toolbar to correct position if debug is true', function () {
            spyOn($.fn, 'css').and.callThrough();
            spyOn($.fn, 'animate').and.callThrough();

            $('<div class="cms-debug-bar"></div>').css({
                height: '5px'
            }).prependTo('#cms-top');

            toolbar.open();
            expect($.fn.css).toHaveBeenCalledWith({
                'transition': 'margin-top 200ms',
                'margin-top': 0
            });
            expect($.fn.animate).toHaveBeenCalledWith(
                jasmine.any(Object),
                200,
                'linear'
            );
            // here we have to use toBeCloseTo because different browsers report different values
            // e.g. FF reports 45.16666
            expect($.fn.animate.calls.mostRecent().args[0]['margin-top']).toBeCloseTo(50, 0);
        });

        it('turns the disclosure triangle into correct position', function () {
            toolbar.ui.toolbarTrigger.removeClass('cms-toolbar-trigger-expanded');
            toolbar.ui.body.removeClass('cms-toolbar-expanded');
            toolbar.open();
            expect(toolbar.ui.toolbarTrigger).toHaveClass('cms-toolbar-trigger-expanded');
            expect(toolbar.ui.body).toHaveClass('cms-toolbar-expanded');
        });
    });

    describe('.close()', function () {
        it('closes toolbar');

        it('does not close toolbar if it is locked');

        it('animates toolbar to correct position if debug is true');

        it('turns the disclosure triangle into correct position');

        it('remembers toolbar state');
    });

    describe('.showLoader()', function () {
        it('shows the loader');
    });

    describe('.hideLoader()', function () {
        it('hides the loader');
    });

    describe('.openAjax()', function () {
        it('makes the request');

        it('does not make the request if there is a confirmation that is not succeeded');
    });
});
