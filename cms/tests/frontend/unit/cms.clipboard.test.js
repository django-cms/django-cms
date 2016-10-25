/* global document */
'use strict';
var CMS = require('../../../static/cms/js/modules/cms.base');
var Clipboard = require('../../../static/cms/js/modules/cms.clipboard');
var $ = require('jquery');

window.CMS = window.CMS || CMS;
CMS.Clipboard = Clipboard;

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
            spyOn(clipboard, '_isClipboardModalOpen').and.returnValue(true);
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

        it('sets up events to clear the clipboard (enabled) 2', function () {
            spyOn(clipboard, 'clear').and.callFake(function (callback) {
                callback();
            });
            spyOn(clipboard.modal, 'close');
            spyOn(clipboard, '_isClipboardModalOpen').and.returnValue(false);
            expect(clipboard.ui.triggerRemove).toHandle('click.cms.clipboard');
            expect(clipboard.ui.triggers.parent()).not.toHaveClass('cms-toolbar-item-navigation-disabled');
            expect(clipboard.ui.triggerRemove.parent()).not.toHaveClass('cms-toolbar-item-navigation-disabled');
            var click = spyOnEvent(clipboard.ui.document, 'click.cms.toolbar');

            clipboard.ui.triggerRemove.trigger('click');
            expect(clipboard.clear).toHaveBeenCalled();
            expect(clipboard.modal.close).not.toHaveBeenCalled();
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

        it('sets up events to clear "add plugin" placeholder', function () {
            $('<div class="cms-add-plugin-placeholder"></div>').prependTo('body');
            clipboard.modal.trigger('cms.modal.loaded');
            expect($('.cms-add-plugin-placeholder')).not.toExist();

            $('<div class="cms-add-plugin-placeholder"></div>').prependTo('body');
            clipboard.modal.trigger('cms.modal.closed');
            expect($('.cms-add-plugin-placeholder')).not.toExist();
        });

        it('sets up events to move pluginList back to the modal', function () {
            $('<div class="cms-modal"></div>').prependTo(fixture.el);
            clipboard = new CMS.Clipboard();

            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };

            clipboard.ui.triggers.trigger('click');
            expect(clipboard.ui.clipboard).not.toContainElement(clipboard.ui.pluginList);

            // modal is closed
            clipboard.modal.trigger('cms.modal.closed');
            expect(clipboard.ui.clipboard).toContainElement(clipboard.ui.pluginsList);

            clipboard.ui.triggers.trigger('click');
            expect(clipboard.ui.clipboard).not.toContainElement(clipboard.ui.pluginList);

            // this modal instance is being opened again
            clipboard.modal.trigger('cms.modal.load');
            expect(clipboard.ui.clipboard).toContainElement(clipboard.ui.pluginsList);

            clipboard.ui.triggers.trigger('click');
            expect(clipboard.ui.clipboard).not.toContainElement(clipboard.ui.pluginList);

            // new modal instance overtook and is opening
            clipboard.modal.ui.modal.trigger('cms.modal.load');
            expect(clipboard.ui.clipboard).toContainElement(clipboard.ui.pluginsList);

            // manually cleaning up, otherwise PhantomJS fails
            $('.cms-modal').remove();
        });
    });

    describe('.clear()', function () {
        var clipboard;
        beforeEach(function (done) {
            fixture.load('clipboard.html');
            CMS.API.Toolbar = {
                openAjax: jasmine.createSpy()
            };
            CMS.config = {
                csrf: 'test_csrf',
                clipboard: {
                    url: 'clear-clipboard'
                }
            };
            $(function () {
                clipboard = new CMS.Clipboard();
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('makes a request to the API', function () {
            clipboard.clear();
            expect(CMS.API.Toolbar.openAjax).toHaveBeenCalledWith({
                url: 'clear-clipboard?cms_path=%2Fcontext.html',
                post: '{ "csrfmiddlewaretoken": "test_csrf" }',
                callback: undefined
            });

            clipboard.clear($.noop);
            expect(CMS.API.Toolbar.openAjax).toHaveBeenCalledWith({
                url: 'clear-clipboard?cms_path=%2Fcontext.html',
                post: '{ "csrfmiddlewaretoken": "test_csrf" }',
                callback: $.noop
            });
        });

        it('resets plugins "paste" menu item to show correct tooltip', function () {
            var statesBefore = [
                {
                    empty: 'none',
                    restricted: 'block',
                    disabled: 'none'
                },
                {
                    empty: 'none',
                    restricted: 'none',
                    disabled: 'block'
                },
                {
                    empty: 'block',
                    restricted: 'none',
                    disabled: 'none'
                },
                {
                    empty: 'none',
                    restricted: 'none',
                    disabled: 'none'
                }
            ];

            var stateAfter = {
                empty: 'block',
                restricted: 'none',
                disabled: 'none'
            };

            statesBefore.forEach(function (obj, index) {
                var el = $('#submenu-item-' + (index + 1));
                Object.keys(obj).forEach(function (key) {
                    var value = obj[key];
                    expect(el.find('.cms-submenu-item-paste-tooltip-' + key)).toHaveCss({
                        display: value
                    });
                });
            });

            clipboard.clear();

            statesBefore.forEach(function (obj, index) {
                var el = $('#submenu-item-' + (index + 1));
                Object.keys(stateAfter).forEach(function (key) {
                    var value = stateAfter[key];
                    expect(el.find('.cms-submenu-item-paste-tooltip-' + key)).toHaveCss({
                        display: value
                    });
                });
            });
        });
    });

    describe('_isClipboardModalOpen()', function () {
        var clipboard;
        beforeEach(function (done) {
            fixture.load('clipboard.html');
            CMS.API.Toolbar = {
                openAjax: jasmine.createSpy()
            };
            CMS.config = {
                csrf: 'test_csrf',
                clipboard: {
                    url: 'clear-clipboard'
                }
            };
            $(function () {
                $('<div class="cms-modal"><div class="cms-modal-body"></div></div>').prependTo(fixture.el);
                clipboard = new CMS.Clipboard();
                done();
            });
        });

        afterEach(function () {
            $('.cms-modal').remove();
            fixture.cleanup();
        });

        it('returns true if modal is open', function () {
            clipboard.modal.ui.modalBody.append('<div class="cms-clipboard-containers"></div>');
            expect(clipboard._isClipboardModalOpen()).toEqual(true);
        });

        it('returns false if modal is closed', function () {
            expect(clipboard._isClipboardModalOpen()).toEqual(false);
        });
    });
});
