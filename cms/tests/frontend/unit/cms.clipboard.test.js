/* global document */
'use strict';

describe('CMS.Clipboard', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a Clipboard class', function () {
        expect(CMS.Clipboard).toBeDefined();
    });

    it('has public API', function () {
        expect(CMS.Clipboard.prototype.clear).toEqual(jasmine.any(Function));
    });

    describe('instance', function () {
        var clipboard;
        beforeEach(function (done) {
            fixture.load('clipboard.html');
            $(function () {
                clipboard = new CMS.Clipboard();
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('has no options', function () {
            expect(clipboard.options).toEqual(undefined);
        });

        it('has ui', function () {
            expect(clipboard.ui).toEqual(jasmine.any(Object));
            expect(Object.keys(clipboard.ui)).toContain('clipboard');
            expect(Object.keys(clipboard.ui)).toContain('triggers');
            expect(Object.keys(clipboard.ui)).toContain('triggerRemove');
            expect(Object.keys(clipboard.ui)).toContain('pluginsList');
            expect(Object.keys(clipboard.ui)).toContain('document');
            expect(Object.keys(clipboard.ui).length).toEqual(5);
        });

        it('has its own private modal instance', function () {
            expect(clipboard.modal).toEqual(jasmine.any(Object));
            // there's no reliable way to check if it's really modal,
            // since Class.js has no instanceof, but this will suffice
            expect(clipboard.modal.ui.modal).toEqual(jasmine.any(Object));
        });

        it('sets up events to open the modal (enabled)', function () {
            expect(clipboard.ui.triggers).toHandle('click.cms.clipboard');

            spyOn(clipboard.modal, 'open');
            clipboard.ui.triggers.trigger('click.cms.clipboard');
            expect(clipboard.modal.open).toHaveBeenCalledWith({
                html: clipboard.ui.pluginsList,
                title: 'Clipboard',
                width: 400,
                height: 117
            });
        });

        it('sets up events to open the modal (disabled)', function () {
            expect(clipboard.ui.triggers).toHandle('click.cms.clipboard');
            spyOn(clipboard.modal, 'open');
            clipboard.ui.triggers.parent().addClass('cms-toolbar-item-navigation-disabled');
            clipboard.ui.triggers.trigger('click.cms.clipboard');
            expect(clipboard.modal.open).not.toHaveBeenCalled();
        });

        it('sets up events to open the modal which trigger click on document', function (done) {
            expect(clipboard.ui.triggers).toHandle('click.cms.clipboard');
            spyOn(clipboard.modal, 'open');
            $(document).on('click.cms.toolbar', function () {
                $(this).off('click.cms.toolbar');
                done();
            });

            clipboard.ui.triggers.trigger('click.cms.clipboard');
        });


        it('sets up events to clear the clipboard (enabled)', function () {
            spyOn(clipboard, 'clear').and.callFake(function (callback) {
                callback();
            });
            spyOn(clipboard.modal, 'close');
            expect(clipboard.ui.triggerRemove).toHandle('click.cms.clipboard');
            expect(clipboard.ui.triggers.parent()).not.toHaveClass('cms-toolbar-item-navigation-disabled');
            expect(clipboard.ui.triggerRemove.parent()).not.toHaveClass('cms-toolbar-item-navigation-disabled');
            var click = spyOnEvent(clipboard.ui.document, 'click.cms.toolbar');

            clipboard.ui.triggerRemove.trigger('click');
            expect(clipboard.clear).toHaveBeenCalled();
            expect(clipboard.modal.close).toHaveBeenCalled();
            expect(clipboard.ui.triggers.parent()).toHaveClass('cms-toolbar-item-navigation-disabled');
            expect(clipboard.ui.triggerRemove.parent()).toHaveClass('cms-toolbar-item-navigation-disabled');
            expect(click).toHaveBeenTriggered();
        });

        it('sets up events to clear the clipboard (disabled)', function () {
            spyOn(clipboard, 'clear').and.callFake(function (callback) {
                callback();
            });
            spyOn(clipboard.modal, 'close');
            var click = spyOnEvent(clipboard.ui.document, 'click.cms.toolbar');

            clipboard.ui.triggerRemove.parent().addClass('cms-toolbar-item-navigation-disabled');

            clipboard.ui.triggerRemove.trigger('click');
            expect(clipboard.clear).not.toHaveBeenCalled();
            expect(clipboard.modal.close).not.toHaveBeenCalled();
            expect(click).not.toHaveBeenTriggered();
        });
    });

    describe('.clear()', function () {
        it('makes a request to the API');
    });
});
