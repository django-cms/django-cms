/* global document */
import Clipboard from '../../../static/cms/js/modules/cms.clipboard';
import $ from 'jquery';
var CMS = require('../../../static/cms/js/modules/cms.base').default;

window.CMS = window.CMS || CMS;
CMS.$ = $;
CMS.API = CMS.API || {};
CMS.API.Helpers = Clipboard.__GetDependency__('Helpers');
CMS.Clipboard = Clipboard;
CMS._instances = [];

describe('CMS.Clipboard', function() {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a Clipboard class', function() {
        expect(CMS.Clipboard).toBeDefined();
    });

    it('has public API', function() {
        expect(CMS.Clipboard.prototype.clear).toEqual(jasmine.any(Function));
    });

    describe('instance', function() {
        var clipboard;
        beforeEach(function(done) {
            fixture.load('clipboard.html');
            $(function() {
                clipboard = new CMS.Clipboard();
                spyOn(clipboard, 'populate');
                spyOn(clipboard, '_handleExternalUpdate');
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it('has no options', function() {
            expect(clipboard.options).toEqual(undefined);
        });

        it('has ui', function() {
            expect(clipboard.ui).toEqual(jasmine.any(Object));
            expect(Object.keys(clipboard.ui)).toContain('clipboard');
            expect(Object.keys(clipboard.ui)).toContain('triggers');
            expect(Object.keys(clipboard.ui)).toContain('triggerRemove');
            expect(Object.keys(clipboard.ui)).toContain('pluginsList');
            expect(Object.keys(clipboard.ui)).toContain('document');
            expect(Object.keys(clipboard.ui).length).toEqual(5);
        });

        it('has its own private modal instance', function() {
            expect(clipboard.modal).toEqual(jasmine.any(Object));
            // there's no reliable way to check if it's really modal,
            // since Class.js has no instanceof, but this will suffice
            expect(clipboard.modal.ui.modal).toEqual(jasmine.any(Object));
        });

        it('sets up events to open the modal (enabled)', function() {
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

        it('sets up events to open the modal (disabled)', function() {
            expect(clipboard.ui.triggers).toHandle('click.cms.clipboard');
            spyOn(clipboard.modal, 'open');
            clipboard.ui.triggers.parent().addClass('cms-toolbar-item-navigation-disabled');
            clipboard.ui.triggers.trigger('click.cms.clipboard');
            expect(clipboard.modal.open).not.toHaveBeenCalled();
        });

        it('sets up events to open the modal which trigger click on document', function(done) {
            expect(clipboard.ui.triggers).toHandle('click.cms.clipboard');
            spyOn(clipboard.modal, 'open');
            $(document).on('click.cms.toolbar', function() {
                $(this).off('click.cms.toolbar');
                done();
            });

            clipboard.ui.triggers.trigger('click.cms.clipboard');
        });

        it('sets up events to clear the clipboard (enabled)', function() {
            spyOn(clipboard, 'clear').and.callFake(function(callback) {
                expect(callback).not.toBeDefined();
                clipboard._cleanupDOM();
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

        it('sets up events to clear the clipboard (enabled) 2', function() {
            spyOn(clipboard, 'clear').and.callFake(function(callback) {
                expect(callback).not.toBeDefined();
                clipboard._cleanupDOM();
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

        it('sets up events to clear the clipboard (disabled)', function() {
            spyOn(clipboard, 'clear').and.callFake(function(callback) {
                expect(callback).not.toBeDefined();
                clipboard._cleanupDOM();
            });
            spyOn(clipboard.modal, 'close');
            var click = spyOnEvent(clipboard.ui.document, 'click.cms.toolbar');

            clipboard.ui.triggerRemove.parent().addClass('cms-toolbar-item-navigation-disabled');

            clipboard.ui.triggerRemove.trigger('click');
            expect(clipboard.clear).not.toHaveBeenCalled();
            expect(clipboard.modal.close).not.toHaveBeenCalled();
            expect(click).not.toHaveBeenTriggered();
        });

        it('sets up events to clear "add plugin" placeholder', function() {
            $('<div class="cms-add-plugin-placeholder"></div>').prependTo('body');
            CMS.API.Helpers.dispatchEvent('modal-loaded', { instance: clipboard.modal });
            expect($('.cms-add-plugin-placeholder')).not.toExist();

            $('<div class="cms-add-plugin-placeholder"></div>').prependTo('body');
            CMS.API.Helpers.dispatchEvent('modal-closed', { instance: clipboard.modal });
            expect($('.cms-add-plugin-placeholder')).not.toExist();
        });

        it('sets up events to move pluginList back to the modal', function() {
            $('<div class="cms-modal"></div>').prependTo(fixture.el);
            clipboard = new CMS.Clipboard();

            CMS.API.Tooltip = {
                hide: jasmine.createSpy()
            };

            clipboard.ui.triggers.trigger('click');
            expect(clipboard.ui.clipboard).not.toContainElement(clipboard.ui.pluginList);

            // modal is closed
            CMS.API.Helpers.dispatchEvent('modal-closed', { instance: clipboard.modal });
            expect(clipboard.ui.clipboard).toContainElement(clipboard.ui.pluginsList);

            clipboard.ui.triggers.trigger('click');
            expect(clipboard.ui.clipboard).not.toContainElement(clipboard.ui.pluginList);

            // this modal instance is being opened again
            CMS.API.Helpers.dispatchEvent('modal-load', { instance: clipboard.modal });
            expect(clipboard.ui.clipboard).toContainElement(clipboard.ui.pluginsList);

            clipboard.ui.triggers.trigger('click');
            expect(clipboard.ui.clipboard).not.toContainElement(clipboard.ui.pluginList);

            // new modal instance overtook and is opening
            CMS.API.Helpers.dispatchEvent('modal-load', { instance: clipboard.modal });
            expect(clipboard.ui.clipboard).toContainElement(clipboard.ui.pluginsList);

            // manually cleaning up, otherwise PhantomJS fails
            $('.cms-modal').remove();
        });

        it('sets up event to handle external updates', () => {
            Clipboard.__Rewire__('ls', {
                on(name) {
                    expect(name).toEqual('cms-clipboard');
                }
            });
            spyOn(CMS.Clipboard.prototype, '_handleExternalUpdate');

            clipboard = new CMS.Clipboard();
            expect(CMS.Clipboard.prototype._handleExternalUpdate).not.toHaveBeenCalled();

            Clipboard.__Rewire__('ls', {
                on(name, fn) {
                    expect(name).toEqual('cms-clipboard');
                    fn({ x: 1 });
                }
            });
            clipboard = new CMS.Clipboard();
            expect(CMS.Clipboard.prototype._handleExternalUpdate).toHaveBeenCalledWith({
                x: 1
            });
            Clipboard.__ResetDependency__('ls');
        });
    });

    describe('.clear()', function() {
        var clipboard;
        beforeEach(function(done) {
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
            $(function() {
                clipboard = new CMS.Clipboard();
                spyOn(clipboard, 'populate');
                spyOn(clipboard, '_handleExternalUpdate');
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it('makes a request to the API', function() {
            clipboard.clear();
            expect(CMS.API.Toolbar.openAjax).toHaveBeenCalledWith({
                url: 'clear-clipboard?cms_path=%2Fcontext.html',
                post: '{ "csrfmiddlewaretoken": "test_csrf" }',
                callback: jasmine.any(Function)
            });

            spyOn($, 'noop');
            clipboard.clear($.noop);
            expect(CMS.API.Toolbar.openAjax).toHaveBeenCalledWith({
                url: 'clear-clipboard?cms_path=%2Fcontext.html',
                post: '{ "csrfmiddlewaretoken": "test_csrf" }',
                callback: jasmine.any(Function)
            });
            CMS.API.Toolbar.openAjax.calls.mostRecent().args[0].callback();
            expect($.noop).toHaveBeenCalled();
        });

        it('resets plugins "paste" menu item to show correct tooltip', function() {
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

            statesBefore.forEach(function(obj, index) {
                var el = $('#submenu-item-' + (index + 1));
                Object.keys(obj).forEach(function(key) {
                    var value = obj[key];
                    expect(el.find('.cms-submenu-item-paste-tooltip-' + key)).toHaveCss({
                        display: value
                    });
                });
            });

            clipboard.clear();

            statesBefore.forEach(function(obj, index) {
                var el = $('#submenu-item-' + (index + 1));
                Object.keys(stateAfter).forEach(function(key) {
                    var value = stateAfter[key];
                    expect(el.find('.cms-submenu-item-paste-tooltip-' + key)).toHaveCss({
                        display: value
                    });
                });
            });
        });
    });

    describe('_isClipboardModalOpen()', function() {
        var clipboard;
        beforeEach(function(done) {
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
            $(function() {
                $('<div class="cms-modal"><div class="cms-modal-body"></div></div>').prependTo(fixture.el);
                clipboard = new CMS.Clipboard();
                spyOn(clipboard, 'populate');
                spyOn(clipboard, '_handleExternalUpdate');
                done();
            });
        });

        afterEach(function() {
            $('.cms-modal').remove();
            fixture.cleanup();
        });

        it('returns true if modal is open', function() {
            clipboard.modal.ui.modalBody.append('<div class="cms-clipboard-containers"></div>');
            expect(clipboard._isClipboardModalOpen()).toEqual(true);
        });

        it('returns false if modal is closed', function() {
            expect(clipboard._isClipboardModalOpen()).toEqual(false);
        });
    });

    describe('_handleExternalUpdate()', function() {
        var clipboard;
        const pluginConstructor = jasmine.createSpy();
        class FakePlugin {
            constructor(...args) {
                pluginConstructor(...args);
            }
        }
        FakePlugin._updateClipboard = jasmine.createSpy();
        beforeEach(function(done) {
            fixture.load('clipboard.html');
            $(function() {
                clipboard = new CMS.Clipboard();
                spyOn(clipboard, 'populate');
                spyOn(clipboard, '_cleanupDOM');
                spyOn(clipboard, '_enableTriggers');
                Clipboard.__Rewire__('Plugin', FakePlugin);
                done();
            });
        });

        afterEach(function() {
            pluginConstructor.calls.reset();
            FakePlugin._updateClipboard.calls.reset();
            Clipboard.__ResetDependency__('Plugin');
            fixture.cleanup();
        });

        it('does not do anything if the timestamp is lower', function() {
            clipboard.currentClipboardData = {
                html: 'no matter',
                data: {},
                timestamp: 10
            };

            expect(
                clipboard._handleExternalUpdate(
                    JSON.stringify({
                        timestamp: 1
                    })
                )
            ).not.toBeDefined();

            expect(pluginConstructor).not.toHaveBeenCalled();
            expect(FakePlugin._updateClipboard).not.toHaveBeenCalled();
            expect(clipboard._cleanupDOM).not.toHaveBeenCalled();
            expect(clipboard._enableTriggers).not.toHaveBeenCalled();
            expect(clipboard.currentClipboardData).toEqual({
                timestamp: 1
            });
        });

        it('does not do anything if the plugin id is the same as it currently was', function() {
            clipboard.currentClipboardData = {
                html: 'no matter',
                data: { plugin_id: 1 },
                timestamp: 10
            };

            expect(
                clipboard._handleExternalUpdate(
                    JSON.stringify({
                        timestamp: 15,
                        data: {
                            plugin_id: 1
                        }
                    })
                )
            ).not.toBeDefined();

            expect(pluginConstructor).not.toHaveBeenCalled();
            expect(FakePlugin._updateClipboard).not.toHaveBeenCalled();
            expect(clipboard._cleanupDOM).not.toHaveBeenCalled();
            expect(clipboard._enableTriggers).not.toHaveBeenCalled();
            expect(clipboard.currentClipboardData).toEqual({
                timestamp: 15,
                data: {
                    plugin_id: 1
                }
            });
        });

        it('cleans up the dom if the clipboard was cleared on external update', function() {
            clipboard.currentClipboardData = {
                html: 'no matter',
                data: { plugin_id: 1 },
                timestamp: 10
            };

            expect(
                clipboard._handleExternalUpdate(
                    JSON.stringify({
                        timestamp: 15,
                        data: {},
                        html: ''
                    })
                )
            ).not.toBeDefined();

            expect(pluginConstructor).not.toHaveBeenCalled();
            expect(FakePlugin._updateClipboard).not.toHaveBeenCalled();
            expect(clipboard._cleanupDOM).toHaveBeenCalledTimes(1);
            expect(clipboard._enableTriggers).not.toHaveBeenCalled();
            expect(clipboard.currentClipboardData).toEqual({
                timestamp: 15,
                data: {},
                html: ''
            });
        });

        it('enables the clipboard menu items if the clipboard was updated externally', function() {
            clipboard.currentClipboardData = {
                html: '',
                data: {},
                timestamp: 10
            };

            expect(
                clipboard._handleExternalUpdate(
                    JSON.stringify({
                        timestamp: 15,
                        data: { plugin_id: 1 },
                        html: '<div></div>'
                    })
                )
            ).not.toBeDefined();

            expect(pluginConstructor).toHaveBeenCalled();
            expect(FakePlugin._updateClipboard).toHaveBeenCalled();
            expect(clipboard._cleanupDOM).not.toHaveBeenCalled();
            expect(clipboard._enableTriggers).toHaveBeenCalled();
            expect(clipboard.currentClipboardData).toEqual({
                timestamp: 15,
                data: { plugin_id: 1 },
                html: '<div></div>'
            });
        });

        it('updates the clipboard with the new plugin', function() {
            clipboard.currentClipboardData = {
                html: '<span></span>',
                data: { plugin_id: 10 },
                timestamp: 10
            };

            expect(
                clipboard._handleExternalUpdate(
                    JSON.stringify({
                        timestamp: 15,
                        data: { plugin_id: 11 },
                        html: '<div></div>'
                    })
                )
            ).not.toBeDefined();

            expect(pluginConstructor).toHaveBeenCalled();
            expect(FakePlugin._updateClipboard).toHaveBeenCalled();
            expect(clipboard._cleanupDOM).not.toHaveBeenCalled();
            expect(clipboard._enableTriggers).not.toHaveBeenCalled();
            expect(clipboard.currentClipboardData).toEqual({
                timestamp: 15,
                data: { plugin_id: 11 },
                html: '<div></div>'
            });
        });
    });

    describe('_enableTriggers()', function() {
        var clipboard;
        beforeEach(function(done) {
            fixture.load('clipboard.html');
            $(function() {
                clipboard = new CMS.Clipboard();
                spyOn(clipboard, 'populate');
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it('removes disabled classes from menu items', function() {
            clipboard.ui.triggers.parent().addClass('cms-toolbar-item-navigation-disabled');
            clipboard.ui.triggerRemove.parent().addClass('cms-toolbar-item-navigation-disabled');

            clipboard._enableTriggers();

            expect(clipboard.ui.triggers.parent()).not.toHaveClass('cms-toolbar-item-navigation-disabled');
            expect(clipboard.ui.triggerRemove.parent()).not.toHaveClass('cms-toolbar-item-navigation-disabled');
        });
    });
});
