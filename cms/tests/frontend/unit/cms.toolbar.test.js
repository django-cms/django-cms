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
                toolbar = new CMS.Toolbar();
                done();
            });
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
        it('delegates to `open()`');

        it('delegates to `close()`');
    });

    describe('.open', function () {
        it('opens toolbar');

        it('animates toolbar to correct position if debug is true');

        it('turns the disclosure triangle into correct position');

        it('remembers toolbar state');
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
