/* globals window, document */
'use strict';
import Plugin from '../../../static/cms/js/modules/cms.plugins';

var CMS = require('../../../static/cms/js/modules/cms.base').default;
var Modal = require('../../../static/cms/js/modules/cms.modal').default;
var Messages = require('../../../static/cms/js/modules/cms.messages').default;
var Clipboard = require('../../../static/cms/js/modules/cms.clipboard').default;
var $ = require('jquery');

window.CMS = window.CMS || CMS;
CMS.API = CMS.API || {};
CMS.API.Helpers = Plugin.__GetDependency__('Helpers');
CMS.KEYS = Plugin.__GetDependency__('KEYS');
CMS.$ = $;
CMS.Plugin = Plugin;
CMS.Modal = Modal;
CMS.Messages = Messages;
CMS.Clipboard = Clipboard;
CMS.API.Clipboard = new CMS.Clipboard();
var showLoader;
var hideLoader;

describe('CMS.Plugin', function() {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a Plugin class', function() {
        expect(CMS.Plugin).toBeDefined();
    });

    it('has public API', function() {
        expect(CMS.Plugin.prototype.addPlugin).toEqual(jasmine.any(Function));
        expect(CMS.Plugin.prototype.editPlugin).toEqual(jasmine.any(Function));
        expect(CMS.Plugin.prototype.copyPlugin).toEqual(jasmine.any(Function));
        expect(CMS.Plugin.prototype.cutPlugin).toEqual(jasmine.any(Function));
        expect(CMS.Plugin.prototype.pastePlugin).toEqual(jasmine.any(Function));
        expect(CMS.Plugin.prototype.movePlugin).toEqual(jasmine.any(Function));
        expect(CMS.Plugin.prototype.deletePlugin).toEqual(jasmine.any(Function));
        expect(CMS.Plugin.prototype.destroy).toEqual(jasmine.any(Function));
        expect(CMS.Plugin.prototype.cleanup).toEqual(jasmine.any(Function));
        expect(CMS.Plugin.prototype.editPluginPostAjax).toEqual(jasmine.any(Function));
    });

    beforeEach(function(done) {
        showLoader = jasmine.createSpy();
        hideLoader = jasmine.createSpy();
        Plugin.__Rewire__('showLoader', showLoader);
        Plugin.__Rewire__('hideLoader', hideLoader);
        $(function() {
            CMS.settings = {
                dragbars: [],
                states: []
            };

            Plugin.__Rewire__('isStructureReady', () => true);
            Plugin.__Rewire__('isContentReady', () => true);

            spyOn(CMS.API.Helpers, 'setSettings').and.callFake(function(value) {
                CMS.settings = $.extend(true, {}, CMS.settings, value);
            });
            done();
        });
    });

    afterEach(function() {
        Plugin.aliasPluginDuplicatesMap = {};
        Plugin.staticPlaceholderDuplicatesMap = {};
        $(document).off('dblclick.cms.plugin pointerover.cms.plugin pointerout.cms.plugin');
        Plugin.__ResetDependency__('isStructureReady');
        Plugin.__ResetDependency__('isContentReady');
        Plugin.__ResetDependency__('showLoader');
        Plugin.__ResetDependency__('hideLoader');
    });

    describe('instance', function() {
        var plugin1;
        var plugin2;
        var placeholder1;
        var generic;
        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                request: {
                    language: 'en'
                },
                lang: {}
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };

            $(function() {
                plugin1 = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                plugin2 = new CMS.Plugin('cms-plugin-2', {
                    type: 'plugin',
                    plugin_id: 2,
                    plugin_type: 'RandomPlugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/2/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/2/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                placeholder1 = new CMS.Plugin('cms-placeholder-1', {
                    type: 'placeholder',
                    placeholder_id: 1
                });
                generic = new CMS.Plugin('cms-plugin-cms-page-changelist-33');

                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it('has ui depending on the type', function() {
            expect(plugin1.ui).toEqual(jasmine.any(Object));
            expect(plugin2.ui).toEqual(jasmine.any(Object));
            expect(placeholder1.ui).toEqual(jasmine.any(Object));
            expect(generic.ui).toEqual(jasmine.any(Object));

            expect(plugin1.ui.container).toExist();
            expect(plugin1.ui.dragbar).not.toBeDefined();
            expect(plugin1.ui.draggable).toExist();
            expect(plugin1.ui.draggables).not.toExist();
            expect(plugin1.ui.submenu).toExist();
            expect(plugin1.ui.dropdown).toExist();
            expect(plugin1.ui.dragitem).toExist();

            expect(plugin2.ui.container).toExist();
            expect(plugin2.ui.dragbar).not.toBeDefined();
            expect(plugin2.ui.draggable).toExist();
            expect(plugin2.ui.draggables).toExist();
            expect(plugin2.ui.submenu).toExist();
            expect(plugin2.ui.dropdown).toExist();
            expect(plugin2.ui.dragitem).toExist();

            expect(placeholder1.ui.container).toExist();
            expect(placeholder1.ui.dragbar).toExist();
            expect(placeholder1.ui.draggable.selector).toEqual('.cms-draggable-null');
            expect(placeholder1.ui.draggables).toExist();
            expect(placeholder1.ui.submenu).toExist();
            expect(placeholder1.ui.dropdown).toExist();
            expect(placeholder1.ui.dragitem).not.toBeDefined();

            expect(generic.ui.container).toExist();
            expect(generic.ui.dragbar).not.toBeDefined();
            expect(generic.ui.draggable).not.toBeDefined();
            expect(generic.ui.draggables).not.toBeDefined();
            expect(generic.ui.submenu).not.toBeDefined();
            expect(generic.ui.dropdown).not.toBeDefined();
            expect(generic.ui.dragitem).not.toBeDefined();
        });

        it('has options', function() {
            expect(plugin1.options).toEqual({
                type: 'plugin',
                placeholder_id: 1,
                plugin_type: 'TextPlugin',
                plugin_id: 1,
                plugin_parent: null,
                plugin_order: null,
                plugin_restriction: jasmine.any(Array),
                plugin_parent_restriction: jasmine.any(Array),
                urls: {
                    add_plugin: '/en/admin/cms/page/add-plugin/',
                    edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                    move_plugin: '/en/admin/cms/page/move-plugin/',
                    delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                    copy_plugin: '/en/admin/cms/page/copy-plugins/'
                }
            });
            expect(plugin1.options.plugin_restriction.length).toEqual(0);
            expect(plugin1.options.plugin_parent_restriction.length).toEqual(0);

            expect(plugin2.options).toEqual({
                type: 'plugin',
                placeholder_id: 1,
                plugin_type: 'RandomPlugin',
                plugin_id: 2,
                plugin_parent: null,
                plugin_order: null,
                plugin_restriction: jasmine.any(Array),
                plugin_parent_restriction: jasmine.any(Array),
                urls: {
                    add_plugin: '/en/admin/cms/page/add-plugin/',
                    edit_plugin: '/en/admin/cms/page/edit-plugin/2/',
                    move_plugin: '/en/admin/cms/page/move-plugin/',
                    delete_plugin: '/en/admin/cms/page/delete-plugin/2/',
                    copy_plugin: '/en/admin/cms/page/copy-plugins/'
                }
            });
            expect(plugin2.options.plugin_restriction.length).toEqual(0);
            expect(plugin2.options.plugin_parent_restriction.length).toEqual(0);

            expect(placeholder1.options).toEqual({
                type: 'placeholder',
                placeholder_id: 1,
                plugin_type: '',
                plugin_id: null,
                plugin_parent: null,
                plugin_order: null,
                plugin_restriction: jasmine.any(Array),
                plugin_parent_restriction: jasmine.any(Array),
                urls: {
                    add_plugin: '',
                    edit_plugin: '',
                    move_plugin: '',
                    copy_plugin: '',
                    delete_plugin: ''
                }
            });
            expect(placeholder1.options.plugin_restriction.length).toEqual(0);
            expect(placeholder1.options.plugin_parent_restriction.length).toEqual(0);

            expect(generic.options).toEqual({
                type: '',
                placeholder_id: null,
                plugin_type: '',
                plugin_id: null,
                plugin_parent: null,
                plugin_order: null,
                plugin_restriction: jasmine.any(Array),
                plugin_parent_restriction: jasmine.any(Array),
                urls: {
                    add_plugin: '',
                    edit_plugin: '',
                    move_plugin: '',
                    copy_plugin: '',
                    delete_plugin: ''
                }
            });
            expect(generic.options.plugin_restriction.length).toEqual(0);
            expect(generic.options.plugin_parent_restriction.length).toEqual(0);
        });

        it('sets its options to the dom node', function() {
            expect(plugin1.ui.container.data('cms')).toEqual(jasmine.arrayContaining([plugin1.options]));
            expect(plugin2.ui.container.data('cms')).toEqual(jasmine.arrayContaining([plugin2.options]));
            expect(placeholder1.ui.container.data('cms')).toEqual(placeholder1.options);
            expect(generic.ui.container.data('cms')).toEqual(jasmine.arrayContaining([generic.options]));
        });

        it('doesnt reset the ui if the same plugin is initialized twice (alias case)', function() {
            spyOn(Plugin.prototype, '_setPlugin');
            spyOn(Plugin.prototype, '_setPlaceholder');
            spyOn(Plugin.prototype, '_setGeneric');
            expect(Plugin.aliasPluginDuplicatesMap[plugin1.options.plugin_id]).toEqual(true);

            new CMS.Plugin('cms-plugin-1', {
                type: 'plugin',
                plugin_id: 1,
                plugin_type: 'TextPlugin',
                placeholder_id: 1,
                urls: {
                    add_plugin: '/en/admin/cms/page/add-plugin/',
                    edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                    move_plugin: '/en/admin/cms/page/move-plugin/',
                    delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                    copy_plugin: '/en/admin/cms/page/copy-plugins/'
                }
            });

            expect(Plugin.aliasPluginDuplicatesMap[plugin1.options.plugin_id]).toEqual(true);
            expect(Plugin.prototype._setPlugin).not.toHaveBeenCalled();
            expect(Plugin.prototype._setPlaceholder).not.toHaveBeenCalled();
            expect(Plugin.prototype._setGeneric).not.toHaveBeenCalled();
        });

        it('doesnt reset the ui if the same placeholder is initialized twice (static placeholders)', function() {
            spyOn(Plugin.prototype, '_setPlugin');
            spyOn(Plugin.prototype, '_setPlaceholder');
            spyOn(Plugin.prototype, '_setGeneric');
            expect(Plugin.staticPlaceholderDuplicatesMap[placeholder1.options.placeholder_id]).toEqual(true);

            new CMS.Plugin('cms-placeholder-1', {
                type: 'placeholder',
                placeholder_id: 1
            });

            expect(Plugin.staticPlaceholderDuplicatesMap[placeholder1.options.placeholder_id]).toEqual(true);
            expect(Plugin.prototype._setPlugin).not.toHaveBeenCalled();
            expect(Plugin.prototype._setPlaceholder).not.toHaveBeenCalled();
            expect(Plugin.prototype._setGeneric).not.toHaveBeenCalled();
        });

        it('checks if pasting into this plugin is allowed', function() {
            jasmine.clock().install();
            spyOn(CMS.Plugin.prototype, '_checkIfPasteAllowed');
            Plugin.aliasPluginDuplicatesMap = {};
            Plugin.staticPlaceholderDuplicatesMap = {};

            plugin1 = new CMS.Plugin('cms-plugin-1', {
                type: 'plugin',
                plugin_id: 1
            });
            jasmine.clock().tick(1);
            expect(CMS.Plugin.prototype._checkIfPasteAllowed.calls.count()).toEqual(1);

            placeholder1 = new CMS.Plugin('cms-placeholder-1', {
                type: 'placeholder',
                placeholder_id: 1
            });
            jasmine.clock().tick(1);
            expect(CMS.Plugin.prototype._checkIfPasteAllowed.calls.count()).toEqual(2);
            generic = new CMS.Plugin('cms-plugin-cms-page-changelist-33');
            jasmine.clock().tick(1);
            expect(CMS.Plugin.prototype._checkIfPasteAllowed.calls.count()).toEqual(2);
            jasmine.clock().uninstall();
        });

        it('removes the temlpate tags around the plugin markup', function() {
            expect($('template')).not.toBeInDOM();
        });

        it('adds correct classes to the markup of the plugin', function() {
            expect($('.plugin1')).toHaveClass('cms-plugin cms-plugin-1');
            expect($('.plugin2')).toHaveClass('cms-plugin cms-plugin-2');
            expect($('.generic')).toHaveClass(
                'cms-plugin cms-plugin-cms-page-changelist-33 cms-render-model cms-render-model-block'
            );
        });

        describe('handles no top-level element in plugin markup', function() {
            var plugin;

            beforeEach(function(done) {
                fixture.load('plugins_complex_markup.html');
                $(function() {
                    done();
                });
            });

            var testsMap = [
                {
                    pluginId: 99,
                    name: 'element + element',
                    expected: [
                        '<div class="plugin99-1 cms-plugin cms-plugin-99">element</div>',
                        '<div class="plugin99-2 cms-plugin cms-plugin-99">and another element</div>'
                    ]
                },
                {
                    pluginId: 100,
                    name: 'textnode + element',
                    expected: [
                        '<cms-plugin class="cms-plugin-text-node cms-plugin cms-plugin-100">\n' +
                            '        text </cms-plugin>',
                        '<div class="plugin100 cms-plugin cms-plugin-100">and element</div>'
                    ]
                },
                {
                    pluginId: 101,
                    name: 'textnode + element + textnode',
                    expected: [
                        '<cms-plugin class="cms-plugin-text-node cms-plugin cms-plugin-101">text </cms-plugin>',
                        '<div class="plugin101 cms-plugin cms-plugin-101">element</div>',
                        '<cms-plugin class="cms-plugin-text-node cms-plugin cms-plugin-101"> another text</cms-plugin>'
                    ]
                },
                {
                    pluginId: 102,
                    name: 'element + textnode',
                    expected: [
                        '<div class="plugin102 cms-plugin cms-plugin-102">element</div>',
                        '<cms-plugin class="cms-plugin-text-node cms-plugin cms-plugin-102"> and text\n' +
                            '        </cms-plugin>'
                    ]
                },
                {
                    pluginId: 103,
                    name: 'textnode',
                    expected: [
                        '<cms-plugin class="cms-plugin-text-node cms-plugin cms-plugin-103">\n' +
                            '        only text node\n    </cms-plugin>'
                    ]
                },
                {
                    pluginId: 104,
                    name: 'textnode + comment',
                    expected: [
                        '<cms-plugin class="cms-plugin-text-node cms-plugin cms-plugin-104">\n' +
                            '        text node </cms-plugin>'
                    ]
                },
                {
                    pluginId: 105,
                    name: 'comment + textnode',
                    expected: [
                        '<cms-plugin class="cms-plugin-text-node cms-plugin cms-plugin-105">' +
                            ' and a text node\n' +
                            '    </cms-plugin>'
                    ]
                },
                {
                    pluginId: 106,
                    name: 'textnode + comment + textnode',
                    expected: [
                        '<cms-plugin class="cms-plugin-text-node cms-plugin cms-plugin-106">' +
                            'text node </cms-plugin>',
                        '<cms-plugin class="cms-plugin-text-node cms-plugin cms-plugin-106">' +
                            ' and a text node\n' +
                            '    </cms-plugin>'
                    ]
                },
                {
                    pluginId: 107,
                    name: 'whitespace textnode + comment + textnode',
                    expected: [
                        '<cms-plugin class="cms-plugin-text-node cms-plugin cms-plugin-107">' +
                            ' and a text node\n' +
                            '    </cms-plugin>'
                    ]
                }
            ];

            testsMap.forEach(function(test) {
                it('handles ' + test.name, function() {
                    plugin = new CMS.Plugin('cms-plugin-' + test.pluginId, {
                        type: 'plugin',
                        plugin_id: test.pluginId
                    });

                    expect(
                        plugin.ui.container.map(function(i, el) {
                            return el.outerHTML;
                        })
                    ).toEqual(test.expected);
                });
            });
        });
    });

    describe('multiple instances of the same plugin', function() {
        var plugin;
        beforeEach(function(done) {
            fixture.load('plugins_complex_markup.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                request: {
                    language: 'en'
                },
                lang: {}
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };

            $(function() {
                plugin = new CMS.Plugin('cms-plugin-108', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });

                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it('handles it correctly', function() {
            expect(plugin.ui.container.length).toEqual(2);
        });
    });

    describe('.addPlugin()', function() {
        var plugin;
        var modalConstructor = jasmine.createSpy();
        class FakeModal {
            constructor(...args) {
                modalConstructor(...args);
            }
        }

        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                request: {
                    language: 'en'
                },
                lang: {}
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            jasmine.Ajax.install();

            $(function() {
                spyOn(CMS.API.Helpers, 'addEventListener');
                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                Plugin.__Rewire__('Modal', FakeModal);
                FakeModal.prototype.on = jasmine.createSpy();
                FakeModal.prototype.open = jasmine.createSpy();
                done();
            });
        });

        afterEach(function() {
            Plugin.__ResetDependency__('Modal');
            jasmine.Ajax.uninstall();
            fixture.cleanup();
        });

        it('opens the modal with correct url', function() {
            plugin.addPlugin('TextPlugin', 'Text plugin', 12);

            expect(modalConstructor).toHaveBeenCalledWith({
                onClose: false,
                redirectOnClose: false
            });

            expect(FakeModal.prototype.open).toHaveBeenCalledWith({
                url: jasmine.any(String),
                title: 'Text plugin'
            });

            expect(FakeModal.prototype.open.calls.mostRecent().args[0].url).toMatch('/en/admin/cms/page/add-plugin?');
            expect(FakeModal.prototype.open.calls.mostRecent().args[0].url).toMatch('placeholder_id=1');
            expect(FakeModal.prototype.open.calls.mostRecent().args[0].url).toMatch('plugin_type=TextPlugin');
            expect(FakeModal.prototype.open.calls.mostRecent().args[0].url).toMatch('plugin_language=en');
            expect(FakeModal.prototype.open.calls.mostRecent().args[0].url).toMatch('plugin_parent=12');
            expect(FakeModal.prototype.open.calls.mostRecent().args[0].url).toMatch('cms_path=');
        });

        it('opens the modal with correct url', function() {
            plugin.options.onClose = 'mock';
            plugin.options.redirectOnClose = 'another mock';

            plugin.addPlugin('TextPlugin', 'Text plugin');

            expect(modalConstructor).toHaveBeenCalledWith({
                onClose: 'mock',
                redirectOnClose: 'another mock'
            });

            expect(FakeModal.prototype.open).toHaveBeenCalledWith({
                url:
                    '/en/admin/cms/page/add-plugin/' +
                        '?placeholder_id=1&plugin_type=TextPlugin&cms_path=%2Fcontext.html&plugin_language=en',
                title: 'Text plugin'
            });
        });

        it('adds event to remove any existing "add plugin" placeholders', function() {
            plugin.addPlugin('TextPlugin', 'Text plugin');
            expect(CMS.API.Helpers.addEventListener).toHaveBeenCalledWith(
                'modal-closed.add-plugin',
                jasmine.any(Function)
            );

            $('<div class="cms-add-plugin-placeholder"></div>').prependTo('body');
            CMS.API.Helpers.addEventListener.calls.argsFor(0)[1]({}, { instance: plugin.modal });
            expect($('.cms-add-plugin-placeholder')).not.toExist();
        });
    });

    describe('.editPlugin()', function() {
        var plugin;
        var modalConstructor = jasmine.createSpy();
        class FakeModal {
            constructor(...args) {
                modalConstructor(...args);
            }
        }

        beforeEach(function(done) {
            Plugin.__Rewire__('Modal', FakeModal);
            spyOn(CMS.API.Helpers, 'addEventListener');
            FakeModal.prototype.open = jasmine.createSpy();
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                request: {
                    language: 'en'
                },
                lang: {}
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            $(function() {
                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                done();
            });
        });

        afterEach(function() {
            Plugin.__ResetDependency__('Modal');
            fixture.cleanup();
        });

        it('creates and opens a modal to edit a plugin', function() {
            plugin.editPlugin('/edit-url', 'Test Plugin', 'breadcrumb');
            expect(FakeModal.prototype.open).toHaveBeenCalledWith({
                url: '/edit-url',
                title: 'Test Plugin',
                breadcrumbs: 'breadcrumb',
                width: 850
            });
        });

        it('creates and opens a modal to edit freshly created plugin', function() {
            plugin.editPlugin('/edit-plugin-url', 'Random Plugin', ['breadcrumb']);
            expect(FakeModal.prototype.open).toHaveBeenCalledWith({
                url: '/edit-plugin-url',
                title: 'Random Plugin',
                breadcrumbs: ['breadcrumb'],
                width: 850
            });
        });
        it('adds events to remove the "add plugin" placeholder', function() {
            plugin.editPlugin('/edit-plugin-url', 'Random Plugin', ['breadcrumb']);

            expect(CMS.API.Helpers.addEventListener).toHaveBeenCalledWith(
                'modal-closed.edit-plugin modal-loaded.edit-plugin',
                jasmine.any(Function)
            );

            $('<div class="cms-add-plugin-placeholder"></div>').prependTo('body');
            CMS.API.Helpers.addEventListener.calls.argsFor(0)[1]({}, { instance: plugin.modal });
            expect($('.cms-add-plugin-placeholder')).not.toExist();
        });
    });

    describe('.copyPlugin()', function() {
        var plugin;
        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                request: {
                    language: 'en'
                },
                clipboard: {
                    id: 'clipboardId'
                },
                lang: {
                    success: 'Voila!',
                    error: 'Test error occured: '
                }
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            spyOn(CMS.API.Helpers, 'reloadBrowser');
            jasmine.Ajax.install();

            $(function() {
                CMS.API.Messages = new CMS.Messages();
                CMS.API.StructureBoard = {
                    invalidateState: jasmine.createSpy()
                };
                CMS.API.Toolbar = {
                    hideLoader: jasmine.createSpy()
                };
                spyOn(CMS.API.Messages, 'open');
                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
            jasmine.Ajax.uninstall();
        });

        it('makes a request to the API', function() {
            expect(plugin.copyPlugin(plugin.options)).toEqual(undefined);
            var request = jasmine.Ajax.requests.mostRecent();
            expect(request.url).toEqual('/en/admin/cms/page/copy-plugins/?cms_path=%2Fcontext.html');
            expect(request.method).toEqual('POST');
            expect(request.data()).toEqual({
                source_placeholder_id: ['1'],
                source_plugin_id: ['1'],
                source_language: ['en'],
                target_plugin_id: [''],
                target_placeholder_id: ['clipboardId'],
                target_language: ['en'],
                csrfmiddlewaretoken: ['CSRF_TOKEN']
            });
        });

        it('does not make a request if CMS.API is locked', function() {
            CMS.API.locked = true;
            expect(plugin.copyPlugin(plugin.options)).toEqual(false);
            expect(jasmine.Ajax.requests.count()).toEqual(0);
            CMS.API.locked = false;
        });

        it('shows the success message if request succeeds', function() {
            spyOn($, 'ajax').and.callFake(function(ajax) {
                ajax.success();
                CMS.API.locked = false;
            });
            plugin.copyPlugin(plugin.options);
            expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                message: 'Voila!'
            });
            expect(CMS.API.Helpers.reloadBrowser).not.toHaveBeenCalledWith();
            expect(CMS.API.StructureBoard.invalidateState).toHaveBeenCalledWith('COPY', undefined);
        });

        it('shows the error message if request failed', function() {
            spyOn($, 'ajax').and.callFake(function(ajax) {
                ajax.error({
                    responseText: 'everything is wrong'
                });
            });
            plugin.copyPlugin(plugin.options);
            expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                message: 'Test error occured: everything is wrong',
                error: true
            });
        });

        // not supposed to happen
        it('shows generic error message if request failed', function() {
            CMS.config.lang.error = '';
            spyOn($, 'ajax').and.callFake(function(ajax) {
                ajax.error({
                    responseText: '',
                    status: 418,
                    statusText: "I'm a teapot"
                });
            });
            plugin.copyPlugin(plugin.options);
            expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                message: "418 I'm a teapot",
                error: true
            });
        });

        it('locks/unlocks the CMS.API if request is successful', function() {
            spyOn($, 'ajax').and.callFake(function(ajax) {
                expect(CMS.API.locked).toEqual(true);
                ajax.success();
                expect(CMS.API.locked).toEqual(false);
            });
            CMS.API.locked = false;
            plugin.copyPlugin(plugin.options);
        });

        it('locks/unlocks the CMS.API if request is not successful', function() {
            spyOn($, 'ajax').and.callFake(function(ajax) {
                expect(CMS.API.locked).toEqual(true);
                ajax.error({});
                expect(CMS.API.locked).toEqual(false);
            });
            CMS.API.locked = false;
            plugin.copyPlugin(plugin.options);
        });

        it('clears the clipboard first if no options were passed', function() {
            CMS.API.Clipboard = new CMS.Clipboard();
            spyOn(CMS.API.Clipboard, 'clear').and.callFake(function(callback) {
                callback();
            });
            spyOn($, 'ajax').and.callFake(function(ajax) {
                expect(ajax.data).toEqual({
                    source_placeholder_id: 1,
                    source_plugin_id: 1,
                    source_language: 'es',
                    target_plugin_id: '',
                    target_placeholder_id: 'clipboardId',
                    target_language: 'es',
                    csrfmiddlewaretoken: 'CSRF_TOKEN'
                });
                CMS.API.locked = false;
            });

            CMS.config.request.language = 'es';
            plugin.copyPlugin();
        });

        it('clears the clipboard first if source language was passed', function() {
            CMS.API.Clipboard = new CMS.Clipboard();
            spyOn(CMS.API.Clipboard, 'clear').and.callFake(function(callback) {
                callback();
            });
            spyOn($, 'ajax').and.callFake(function(ajax) {
                expect(ajax.data).toEqual({
                    source_placeholder_id: 1,
                    source_plugin_id: '',
                    source_language: 'de',
                    target_plugin_id: '',
                    target_placeholder_id: 1,
                    target_language: 'es',
                    csrfmiddlewaretoken: 'CSRF_TOKEN'
                });
                CMS.API.locked = false;
            });

            CMS.config.request.language = 'es';
            plugin.copyPlugin(undefined, 'de');
        });
    });

    describe('.cutPlugin()', function() {
        var plugin;
        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                request: {
                    language: 'en'
                },
                clipboard: {
                    id: 'clipboardId'
                },
                lang: {
                    success: 'Voila!',
                    error: 'Test error occured: '
                }
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            spyOn(CMS.API.Helpers, 'reloadBrowser');

            $(function() {
                CMS.API.Messages = new CMS.Messages();
                spyOn(CMS.API.Messages, 'open');

                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it('makes a request to the API', function() {
            spyOn($, 'ajax').and.callFake(function(ajax) {
                ajax.success();
            });
            expect(plugin.cutPlugin()).toEqual(undefined);

            expect($.ajax).toHaveBeenCalledWith({
                url: '/en/admin/cms/page/move-plugin/?cms_path=%2Fcontext.html',
                type: 'POST',
                data: {
                    placeholder_id: 'clipboardId',
                    plugin_id: 1,
                    plugin_parent: '',
                    plugin_order: [1],
                    target_language: 'en',
                    csrfmiddlewaretoken: 'CSRF_TOKEN'
                },
                success: jasmine.any(Function),
                error: jasmine.any(Function)
            });
            CMS.API.locked = false;
        });

        it('shows the success message if request succeeds', function() {
            spyOn($, 'ajax').and.callFake(function(ajax) {
                ajax.success();
                CMS.API.locked = false;
            });
            plugin.cutPlugin();
            expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                message: 'Voila!'
            });
        });

        it('does not reload the browser if request succeeds', function() {
            spyOn($, 'ajax').and.callFake(function(ajax) {
                ajax.success();
                CMS.API.locked = false;
            });
            plugin.cutPlugin();
            expect(CMS.API.Helpers.reloadBrowser).not.toHaveBeenCalled();
        });

        it('shows the error message if request failed', function() {
            spyOn($, 'ajax').and.callFake(function(ajax) {
                ajax.error({
                    responseText: 'Cannot cut a plugin'
                });
            });
            plugin.cutPlugin();
            expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                message: 'Test error occured: Cannot cut a plugin',
                error: true
            });
        });

        // not supposed to happen
        it('shows generic error message if request failed', function() {
            spyOn($, 'ajax').and.callFake(function(ajax) {
                ajax.error({
                    responseText: '',
                    status: 418,
                    statusText: "I'm a teapot"
                });
            });
            CMS.config.lang.error = '';
            plugin.cutPlugin();
            expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                message: "418 I'm a teapot",
                error: true
            });
        });

        it('does not make a request if CMS.API is locked', function() {
            CMS.API.locked = true;
            expect(plugin.cutPlugin()).toEqual(false);
            expect(jasmine.Ajax.requests.count()).toEqual(0);
            CMS.API.locked = false;
        });

        it('locks the CMS.API before making the request', function() {
            CMS.API.locked = false;
            spyOn($, 'ajax');
            plugin.cutPlugin();
            expect(CMS.API.locked).toEqual(true);
            CMS.API.locked = false;
        });

        it('unlocks the CMS.API if request is successful', function() {
            spyOn($, 'ajax').and.callFake(function(ajax) {
                expect(CMS.API.locked).toEqual(true);
                ajax.success();
                expect(CMS.API.locked).toEqual(false);
            });
            CMS.API.locked = false;
            plugin.cutPlugin();
        });

        it('unlocks the CMS.API if request is not successful', function() {
            spyOn($, 'ajax').and.callFake(function(ajax) {
                expect(CMS.API.locked).toEqual(true);
                ajax.error({});
                expect(CMS.API.locked).toEqual(false);
            });
            CMS.API.locked = false;
            plugin.cutPlugin();
        });
    });

    describe('.pastePlugin()', function() {
        var plugin;
        var clipboardPlugin;
        var placeholder;

        beforeEach(function(done) {
            fixture.load('plugins.html', 'clipboard.html', true);
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                request: {
                    language: 'en'
                },
                clipboard: {
                    id: 'clipboardId'
                },
                lang: {
                    success: 'Voila!',
                    error: 'Test error occured: '
                }
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            $(function() {
                CMS.Plugin._initializeGlobalHandlers();
                CMS.API.StructureBoard = {
                    getId: function() {
                        return 2;
                    },
                    getIds: function() {
                        return [];
                    }
                };
                Plugin.__Rewire__('StructureBoard', {
                    actualizePluginCollapseStatus: jasmine.createSpy()
                });
                spyOn(CMS.Plugin.prototype, 'movePlugin');

                CMS._plugins = [
                    [
                        'cms-plugin-3',
                        {
                            type: 'plugin',
                            plugin_id: 3,
                            plugin_type: 'ClipboardPlugin',
                            plugin_parent_restriction: ['RandomPlugin']
                        }
                    ],
                    [
                        'cms-plugin-2',
                        {
                            type: 'plugin',
                            plugin_id: 2,
                            plugin_type: 'RandomPlugin',
                            placeholder_id: 2,
                            urls: {
                                add_plugin: '/en/admin/cms/page/add-plugin/',
                                edit_plugin: '/en/admin/cms/page/edit-plugin/2/',
                                move_plugin: '/en/admin/cms/page/move-plugin/',
                                delete_plugin: '/en/admin/cms/page/delete-plugin/2/',
                                copy_plugin: '/en/admin/cms/page/copy-plugins/'
                            }
                        }
                    ]
                ];

                clipboardPlugin = new CMS.Plugin(...CMS._plugins[0]);

                plugin = new CMS.Plugin(...CMS._plugins[1]);

                placeholder = new CMS.Plugin('cms-placeholder-2', {
                    type: 'placeholder',
                    placeholder_id: 2
                });
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it("moves the clipboard draggable dom node to plugin's child list", function() {
            var clipboard = $('.cms-clipboard');
            var clipboardDraggable = clipboard.find('.cms-draggable:first');
            var clipboardPluginDOM = clipboard.find('.cms-plugin:first');
            expect(clipboard).toExist();
            expect(clipboardDraggable).toExist();
            expect(clipboardPluginDOM).toExist();
            plugin.pastePlugin();
            expect(plugin.ui.draggables).toContainElement('.cms-draggable-3');
        });

        it("moves the clipboard draggable dom node placeholder's child list", function() {
            var clipboard = $('.cms-clipboard');
            var clipboardDraggable = clipboard.find('.cms-draggable:first');
            var clipboardPluginDOM = clipboard.find('.cms-plugin:first');
            expect(clipboard).toExist();
            expect(clipboardDraggable).toExist();
            expect(clipboardPluginDOM).toExist();
            placeholder.pastePlugin();
            expect(placeholder.ui.draggables).toContainElement('.cms-draggable-3');
        });

        it('triggers correct events on a freshly pasted clipboard plugin', function(done) {
            var clipboardPluginDOM = $('.cms-clipboard .cms-draggable:first');
            clipboardPluginDOM.on('cms-paste-plugin-update', function() {
                done();
            });
            plugin.pastePlugin();
        });

        it('triggers correct events on a child list where the plugin was just moved', function(done) {
            plugin.ui.draggables.on('cms-structure-update', function() {
                setTimeout(function() {
                    done();
                }, 10);
            });
            plugin.pastePlugin();
        });

        it('triggers movePlugin on paste plugin eventually', function() {
            plugin.pastePlugin();
            expect(clipboardPlugin.movePlugin).toHaveBeenCalledWith({
                type: 'plugin',
                placeholder_id: 2,
                plugin_type: 'RandomPlugin',
                plugin_id: 2,
                plugin_parent: null,
                plugin_order: null,
                plugin_restriction: jasmine.arrayContaining([]),
                plugin_parent_restriction: jasmine.arrayContaining([]),
                urls: {
                    add_plugin: '/en/admin/cms/page/add-plugin/',
                    edit_plugin: '/en/admin/cms/page/edit-plugin/2/',
                    move_plugin: '/en/admin/cms/page/move-plugin/',
                    copy_plugin: '/en/admin/cms/page/copy-plugins/',
                    delete_plugin: '/en/admin/cms/page/delete-plugin/2/'
                },
                target: 2,
                parent: 2,
                move_a_copy: true
            });
        });
    });

    describe('.movePlugin()', function() {
        var plugin;
        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                request: {
                    language: 'en'
                },
                clipboard: {
                    id: 'clipboardId'
                },
                lang: {
                    success: 'Voila!',
                    error: 'Test error occured: '
                }
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            spyOn(CMS.API.Helpers, 'reloadBrowser');
            jasmine.Ajax.install();

            $(function() {
                CMS.API.Messages = new CMS.Messages();
                spyOn(CMS.API.Messages, 'open');

                CMS.API.StructureBoard = {
                    getId: function(el) {
                        if (el.is('.cms-dragbar')) {
                            return 1;
                        }
                        if (el.is('.cms-draggable')) {
                            return false;
                        }
                    },
                    getIds: function() {
                        return [3, 2, 1];
                    },
                    invalidateState: jasmine.createSpy()
                };

                CMS.API.Toolbar = {
                    ui: {
                        revert: $('.cms-toolbar-revert'),
                        window: $(window)
                    },
                    onPublishAvailable: jasmine.createSpy()
                };

                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
            jasmine.Ajax.uninstall();
        });

        it('makes a request to the API', function() {
            CMS.API.locked = false;
            expect(plugin.movePlugin()).toEqual(undefined);
            var request = jasmine.Ajax.requests.mostRecent();
            expect(request.url).toEqual('/en/admin/cms/page/move-plugin/?cms_path=%2Fcontext.html');
            expect(request.method).toEqual('POST');
            expect(request.data()).toEqual({
                placeholder_id: ['1'],
                plugin_id: ['1'],
                plugin_parent: [''],
                'plugin_order[]': ['3', '2', '1'],
                target_language: ['en'],
                csrfmiddlewaretoken: ['CSRF_TOKEN']
            });
            CMS.API.locked = false;
        });

        it('does not make a request if CMS.API is locked', function() {
            CMS.API.locked = true;
            expect(plugin.movePlugin()).toEqual(false);
            expect(jasmine.Ajax.requests.count()).toEqual(0);
            CMS.API.locked = false;
        });

        it('does not make a request if there is no placeholder in chain of parents', function() {
            CMS.API.StructureBoard.getId = function() {
                return false;
            };

            expect(plugin.movePlugin()).toEqual(false);
            expect(jasmine.Ajax.requests.count()).toEqual(0);
            CMS.API.locked = false;
        });

        it('uses modified plugin order if we are moving a copy', function() {
            CMS.API.locked = false;
            spyOn($, 'ajax').and.callFake(function(ajax) {
                expect(ajax.data).toEqual(
                    jasmine.objectContaining({
                        plugin_order: [3, 2, '__COPY__']
                    })
                );
            });
            plugin.movePlugin($.extend(plugin.options, { move_a_copy: true }));
        });

        it('does not reload the browser', function() {
            CMS.API.locked = false;
            spyOn($, 'ajax').and.callFake(function(ajax) {
                ajax.success();
            });
            plugin.movePlugin();
            expect(CMS.API.Helpers.reloadBrowser).not.toHaveBeenCalled();
            expect(CMS.API.StructureBoard.invalidateState).toHaveBeenCalledWith('MOVE', {
                placeholder_id: 1,
                plugin_id: 1,
                plugin_parent: '',
                target_language: 'en',
                plugin_order: [3, 2, 1],
                csrfmiddlewaretoken: 'CSRF_TOKEN'
            });
        });

        it('shows and hides the loader if success', function(done) {
            spyOn($, 'ajax').and.callFake(function(ajax) {
                ajax.success({});
                expect(hideLoader).toHaveBeenCalledTimes(1);
                done();
            });
            plugin.movePlugin();
            expect(showLoader).toHaveBeenCalledTimes(1);
        });

        it('shows and hides the loader if error', function(done) {
            spyOn($, 'ajax').and.callFake(function(ajax) {
                ajax.error({});
                expect(hideLoader).toHaveBeenCalledTimes(1);
                done();
            });
            plugin.movePlugin();
            expect(showLoader).toHaveBeenCalledTimes(1);
        });

        it('does not show success animation', function() {
            spyOn($, 'ajax').and.callFake(function(ajax) {
                ajax.success({});
            });
            spyOn(Plugin, '_highlightPluginStructure');

            plugin.movePlugin();
            expect(Plugin._highlightPluginStructure).not.toHaveBeenCalled();
        });

        it('shows the error message if request failed', function() {
            spyOn($, 'ajax').and.callFake(function(ajax) {
                ajax.error({
                    responseText: 'Cannot cut a plugin'
                });
            });
            plugin.movePlugin();
            expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                message: 'Test error occured: Cannot cut a plugin',
                error: true
            });
        });

        // not supposed to happen
        it('shows generic error message if request failed', function() {
            spyOn($, 'ajax').and.callFake(function(ajax) {
                ajax.error({
                    responseText: '',
                    status: 418,
                    statusText: "I'm a teapot"
                });
            });
            CMS.config.lang.error = '';
            plugin.movePlugin();
            expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                message: "418 I'm a teapot",
                error: true
            });
        });

        it('locks the CMS.API before making the request', function() {
            CMS.API.locked = false;
            spyOn($, 'ajax').and.callFake(function() {
                expect(CMS.API.locked).toEqual(true);
            });
            plugin.movePlugin();
        });

        it('unlocks the CMS.API if request is successful', function() {
            CMS.API.locked = false;
            spyOn($, 'ajax').and.callFake(function(ajax) {
                expect(CMS.API.locked).toEqual(true);
                ajax.success({});
                expect(CMS.API.locked).toEqual(false);
            });
            plugin.movePlugin();
        });

        it('unlocks the CMS.API if request is not successful', function() {
            CMS.API.locked = false;
            spyOn($, 'ajax').and.callFake(function(ajax) {
                expect(CMS.API.locked).toEqual(true);
                ajax.error({});
                expect(CMS.API.locked).toEqual(false);
            });
            plugin.movePlugin();
        });
    });

    describe('.deletePlugin()', function() {
        var plugin;
        var modalConstructor = jasmine.createSpy();
        class FakeModal {
            constructor(...args) {
                modalConstructor(...args);
            }
        }
        FakeModal.prototype.open = jasmine.createSpy();

        beforeEach(function(done) {
            Plugin.__Rewire__('Modal', FakeModal);
            fixture.load('plugins.html');
            spyOn(CMS.API.Helpers, 'addEventListener').and.callThrough();
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                request: {
                    language: 'en'
                },
                lang: {}
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            $(function() {
                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                done();
            });
        });

        afterEach(function() {
            Plugin.__ResetDependency__('Modal');
            fixture.cleanup();
        });

        it('creates and opens a modal for plugin deletion', function() {
            plugin.deletePlugin('delete-url', 'Delete name', 'breadcrumb');
            expect(FakeModal.prototype.open).toHaveBeenCalledWith({
                url: 'delete-url',
                title: 'Delete name',
                breadcrumbs: 'breadcrumb'
            });
        });

        it('adds events to remove any existing "add plugin" placeholders', function() {
            plugin.deletePlugin();
            expect(CMS.API.Helpers.addEventListener).toHaveBeenCalledWith(
                'modal-loaded.delete-plugin',
                jasmine.any(Function)
            );

            $('<div class="cms-add-plugin-placeholder"></div>').prependTo('body');
            CMS.API.Helpers.addEventListener.calls.argsFor(0)[1]({}, { instance: plugin.modal });
            expect($('.cms-add-plugin-placeholder')).not.toExist();
        });
    });

    describe('.destroy()', function() {
        var plugin;

        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                request: {
                    language: 'en'
                },
                lang: {}
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            $(function() {
                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    plugin_name: 'Test Text Plugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                done();
            });
        });

        it('removes all the plugin markup', function() {
            plugin.destroy({ mustCleanup: true });
            expect($('.cms-plugin-1').length).toBe(0);
        });

        it('removes all the plugin events', function() {
            CMS.API.Helpers.$document.on(plugin._getNamepacedEvent(Plugin.click), function() {
                throw new Error('This event should never be triggered');
            });

            plugin.destroy();
            CMS.API.Helpers.$document.trigger(plugin._getNamepacedEvent(Plugin.click));
        });
    });

    describe('.cleanup()', function() {
        var plugin;

        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                request: {
                    language: 'en'
                },
                lang: {}
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            $(function() {
                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    plugin_name: 'Test Text Plugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                done();
            });
        });

        it('removes all the plugin markup', function() {
            plugin.cleanup();
            expect($('.cms-plugin-1').length).toBe(0);
        });
    });

    describe('.editPluginPostAjax()', function() {
        var plugin;

        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                request: {
                    language: 'en'
                },
                lang: {}
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            $(function() {
                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    plugin_name: 'Test Text Plugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it('delegates to editPlugin with url coming from response', function() {
            spyOn(plugin, 'editPlugin');
            plugin.editPluginPostAjax({}, { url: 'test-url', breadcrumb: 'whatever' });
            expect(plugin.editPlugin).toHaveBeenCalledWith(
                'test-url?cms_path=%2Fcontext.html',
                'Test Text Plugin',
                'whatever'
            );
        });
    });

    describe('._scrollToElement', function() {
        var plugin;

        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                request: {
                    language: 'en'
                },
                lang: {}
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            $(function() {
                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    plugin_name: 'Test Text Plugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it('does nothing if element is in viewport already', function() {
            spyOn($.fn, 'animate');
            plugin._scrollToElement($('.cms-draggable-2'), { duration: 100, offset: 20 });
            expect($.fn.animate).not.toHaveBeenCalled();
        });

        it('animates structureboard to the point when it is in viewport', function() {
            // window, element
            spyOn($.fn, 'height').and.returnValues(200, 20);
            spyOn($.fn, 'position').and.returnValues({
                top: 300
            });
            spyOn($.fn, 'scrollTop').and.returnValues(30);
            spyOn($.fn, 'animate');
            plugin._scrollToElement($('<div></div>'), { duration: 100, offset: 20 });

            expect($.fn.animate).toHaveBeenCalledWith(
                {
                    scrollTop: 300 + 20 + 20 + 30 - 200
                },
                100
            );
        });

        it('has default values', function() {
            // window, element
            spyOn($.fn, 'height').and.returnValues(200, 20);
            spyOn($.fn, 'position').and.returnValues({
                top: 300
            });
            spyOn($.fn, 'scrollTop').and.returnValues(30);
            spyOn($.fn, 'animate');
            plugin._scrollToElement($('<div></div>'));

            expect($.fn.animate).toHaveBeenCalledWith(
                {
                    scrollTop: 300 + 20 + 50 + 30 - 200
                },
                200
            );
        });
    });

    describe('._setupActions()', function() {
        var plugin;
        var tmpl =
            '<div class="cms-plugin-picker" data-parent-id="mock"><div class="cms-submenu-item {1}">' +
            '<a href="{2}">Submenu item</a>' +
            '</div></div>';

        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                request: {
                    language: 'en'
                },
                lang: {}
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            $(function() {
                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    plugin_name: 'Test Text Plugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                CMS.API.Toolbar = {
                    _delegate: jasmine.createSpy(),
                    openAjax: jasmine.createSpy(),
                    onPublishAvailable: jasmine.createSpy()
                };
                spyOn(CMS.Plugin, '_hideSettingsMenu');
                jasmine.clock().install();
                jasmine.clock().tick(1);
                done();
            });
        });

        afterEach(function() {
            jasmine.clock().uninstall();
            fixture.cleanup();
        });

        it('sets up touch event stopper', function() {
            expect(plugin.ui.submenu.parent().find('.cms-submenu-edit')).toHandle(Plugin.touchStart);
            spyOn($.Event.prototype, 'stopPropagation');
            plugin.ui.submenu.parent().find('.cms-submenu-edit').trigger(Plugin.touchStart);
            expect($.Event.prototype.stopPropagation).toHaveBeenCalled();
        });

        it('sets up click handlers on submenu items', function() {
            var nav = $(tmpl.replace('{1}', '').replace('{2}', '#href')).find('> div');
            var link = nav.find('a');

            plugin._setupActions(nav);

            expect(link).toHandle(Plugin.click);

            spyOn($.Event.prototype, 'preventDefault');
            spyOn($.Event.prototype, 'stopPropagation');

            link.trigger(Plugin.click);
            expect($.Event.prototype.stopPropagation).toHaveBeenCalledTimes(1);
            expect($.Event.prototype.preventDefault).toHaveBeenCalledTimes(1);
        });

        it('by default delegates to toolbar', function() {
            var nav = $(tmpl.replace('{1}', '').replace('{2}', '#href')).find('> div');
            var link = nav.find('a');
            plugin._setupActions(nav);
            link.trigger(Plugin.click);
            expect(showLoader).toHaveBeenCalledTimes(1);
            expect(hideLoader).toHaveBeenCalledTimes(1);
            expect(CMS.API.Toolbar._delegate).toHaveBeenCalledTimes(1);
            expect(CMS.API.Toolbar._delegate).toHaveBeenCalledWith(link);
        });

        it('delegates to add plugin', function() {
            spyOn(plugin, 'addPlugin');
            var nav = $(tmpl.replace('{1}', '').replace('{2}', '#shmock')).find('> div');
            var link = nav.find('a');
            link.attr('data-rel', 'add');
            plugin._setupActions(nav);
            link.trigger(Plugin.click);
            expect(plugin.addPlugin).toHaveBeenCalledTimes(1);
            expect(plugin.addPlugin).toHaveBeenCalledWith('shmock', 'Submenu item', 'mock');
        });

        it('delegates to add ajax plugin', function() {
            var nav = $(tmpl.replace('{1}', '').replace('{2}', '#shmock')).find('> div');
            var link = nav.find('a');
            link.attr('data-rel', 'ajax_add');
            link.data('on-success', 'ON_SUCCESS');
            link.data('post', { data: 'data' });
            link.data('text', 'TEXT');
            plugin._setupActions(nav);
            link.trigger(Plugin.click);
            expect(CMS.API.Toolbar.openAjax).toHaveBeenCalledTimes(1);
            expect(CMS.API.Toolbar.openAjax).toHaveBeenCalledWith({
                url: '#shmock',
                post: JSON.stringify({ data: 'data' }),
                text: 'TEXT',
                callback: jasmine.any(Function),
                onSuccess: 'ON_SUCCESS'
            });
        });

        it('delegates to edit plugin', function() {
            var nav = $(tmpl.replace('{1}', '').replace('{2}', '#shmock')).find('> div');
            var link = nav.find('a');
            link.attr('data-rel', 'edit');
            spyOn(plugin, 'editPlugin');
            spyOn(plugin, '_getPluginBreadcrumbs').and.returnValue('MockBreadcrumb');
            plugin.options = {
                urls: { edit_plugin: 'edit_plugin_url' },
                plugin_name: 'MockPlugin'
            };
            plugin._setupActions(nav);
            link.trigger(Plugin.click);
            expect(plugin.editPlugin).toHaveBeenCalledTimes(1);
            expect(plugin.editPlugin).toHaveBeenCalledWith(
                'edit_plugin_url?cms_path=%2Fcontext.html',
                'MockPlugin',
                'MockBreadcrumb'
            );
        });

        it('delegates to copy-from-language', function() {
            var nav = $(tmpl.replace('{1}', '').replace('{2}', '#shmock')).find('> div');
            var link = nav.find('a');
            link.attr('data-rel', 'copy-lang');
            link.attr('data-language', 'MOCK LANGUAGE');
            spyOn(plugin, 'copyPlugin');
            plugin.options = 'MOCKED OPTIONS';
            plugin._setupActions(nav);
            link.trigger(Plugin.click);
            expect(plugin.copyPlugin).toHaveBeenCalledTimes(1);
            expect(plugin.copyPlugin).toHaveBeenCalledWith('MOCKED OPTIONS', 'MOCK LANGUAGE');
        });

        it('delegates to copyPlugin', function() {
            var nav = $(tmpl.replace('{1}', '').replace('{2}', '#shmock')).find('> div');
            var link = nav.find('a');
            link.attr('data-rel', 'copy');
            link.parent().addClass('cms-submenu-item-disabled');
            spyOn(plugin, 'copyPlugin');
            plugin.options = 'MOCKED OPTIONS';
            plugin._setupActions(nav);
            link.trigger(Plugin.click);
            expect(plugin.copyPlugin).not.toHaveBeenCalled();
            expect(hideLoader).toHaveBeenCalledTimes(1);

            link.parent().removeClass('cms-submenu-item-disabled');
            link.trigger(Plugin.click);
            expect(plugin.copyPlugin).toHaveBeenCalledTimes(1);
            expect(hideLoader).toHaveBeenCalledTimes(1);
        });

        it('delegates to cutPlugin', function() {
            var nav = $(tmpl.replace('{1}', '').replace('{2}', '#shmock')).find('> div');
            var link = nav.find('a');
            link.attr('data-rel', 'cut');
            spyOn(plugin, 'cutPlugin');
            plugin._setupActions(nav);
            link.trigger(Plugin.click);
            expect(plugin.cutPlugin).toHaveBeenCalledTimes(1);
        });

        it('delegates to pastePlugin', function() {
            var nav = $(tmpl.replace('{1}', '').replace('{2}', '#shmock')).find('> div');
            var link = nav.find('a');
            link.attr('data-rel', 'paste');
            link.parent().addClass('cms-submenu-item-disabled');
            spyOn(plugin, 'pastePlugin');
            plugin.options = 'MOCKED OPTIONS';
            plugin._setupActions(nav);
            link.trigger(Plugin.click);
            expect(plugin.pastePlugin).not.toHaveBeenCalled();
            expect(hideLoader).toHaveBeenCalledTimes(1);

            link.parent().removeClass('cms-submenu-item-disabled');
            link.trigger(Plugin.click);
            expect(plugin.pastePlugin).toHaveBeenCalledTimes(1);
            expect(hideLoader).toHaveBeenCalledTimes(2);
        });

        it('delegates to deletePlugin', function() {
            var nav = $(tmpl.replace('{1}', '').replace('{2}', '#shmock')).find('> div');
            var link = nav.find('a');
            link.attr('data-rel', 'delete');
            spyOn(plugin, 'deletePlugin');
            spyOn(plugin, '_getPluginBreadcrumbs').and.returnValue('Breadcrumb');
            plugin._setupActions(nav);
            plugin.options = {
                urls: { delete_plugin: 'DELETE_URL' },
                plugin_name: 'MockPlugin'
            };
            link.trigger(Plugin.click);

            expect(plugin.deletePlugin).toHaveBeenCalledTimes(1);
            expect(plugin.deletePlugin).toHaveBeenCalledWith(
                'DELETE_URL?cms_path=%2Fcontext.html',
                'MockPlugin',
                'Breadcrumb'
            );
        });
    });

    describe('_setupKeyBoardTraversing()', function() {
        var plugin;

        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                request: {
                    language: 'en'
                },
                lang: {}
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            $(function() {
                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    plugin_name: 'Test Text Plugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                CMS.API.Toolbar = {
                    _delegate: jasmine.createSpy(),
                    openAjax: jasmine.createSpy(),
                    onPublishAvailable: jasmine.createSpy()
                };
                done();
            });
        });

        afterEach(function() {
            $(document).off('.traverse');
            fixture.cleanup();
        });

        it('returns if there is no plugin picker in the modal', function() {
            expect(plugin._setupKeyboardTraversing()).toEqual(undefined);
            expect($(document)).not.toHandle(plugin._getNamepacedEvent(Plugin.keyDown, 'traverse'));
        });

        it('unbinds old traversing keydown events', function() {
            $(fixture.el).append('<div class="cms-modal-markup"></div>');
            plugin.ui.dragitem.find('.cms-plugin-picker').appendTo('.cms-modal-markup');
            var spy = jasmine.createSpy();
            $(document).on(plugin._getNamepacedEvent(Plugin.keyDown, 'traverse'), spy);
            plugin._setupKeyboardTraversing();
            $(document).trigger(plugin._getNamepacedEvent(Plugin.keyDown, 'traverse'));
            expect(spy).not.toHaveBeenCalled();
        });

        it('binds traversing keydown events', function() {
            $(fixture.el).append('<div class="cms-modal-markup"></div>');
            plugin.ui.dragitem.find('.cms-plugin-picker').show().appendTo('.cms-modal-markup');
            plugin._setupKeyboardTraversing();

            var down = new $.Event(plugin._getNamepacedEvent(Plugin.keyDown, 'traverse'), {
                keyCode: CMS.KEYS.DOWN
            });
            var down1 = new $.Event(plugin._getNamepacedEvent(Plugin.keyDown, 'traverse'), {
                keyCode: CMS.KEYS.TAB
            });
            var up = new $.Event(plugin._getNamepacedEvent(Plugin.keyDown, 'traverse'), {
                keyCode: CMS.KEYS.UP
            });
            var up1 = new $.Event(plugin._getNamepacedEvent(Plugin.keyDown, 'traverse'), {
                keyCode: CMS.KEYS.TAB,
                shiftKey: true
            });

            spyOn($.Event.prototype, 'preventDefault');
            $(document).trigger(down);
            expect($.Event.prototype.preventDefault).toHaveBeenCalledTimes(1);
            $(document).trigger(down1);
            expect($.Event.prototype.preventDefault).toHaveBeenCalledTimes(2);
            $(document).trigger(up);
            expect($.Event.prototype.preventDefault).toHaveBeenCalledTimes(3);
            $(document).trigger(up1);
            expect($.Event.prototype.preventDefault).toHaveBeenCalledTimes(4);
        });
    });

    describe('_filterPluginsList()', function() {
        var plugin;
        var picker;
        var items;
        var titles;

        beforeEach(function(done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                request: {
                    language: 'en'
                },
                lang: {}
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            $(function() {
                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    plugin_name: 'Test Text Plugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                picker = $('.cms-plugin-picker');
                picker.appendTo(fixture.el).show();
                items = picker.find('.cms-submenu-item');
                titles = picker.find('.cms-submenu-item-title');
                CMS.API.Toolbar = {
                    _delegate: jasmine.createSpy(),
                    openAjax: jasmine.createSpy()
                };
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it('shows everything if empty query is given', function() {
            expect(items.add(titles)).toBeVisible();
            items.add(titles).hide();
            expect(items.add(titles)).not.toBeVisible();
            expect(plugin._filterPluginsList(picker, $('<input value="">'))).toEqual(false);
            expect(items.add(titles)).toBeVisible();
        });

        it('shows nothing if non-matching query is given', function() {
            expect(items.add(titles)).toBeVisible();
            items.add(titles).hide();
            expect(items.add(titles)).not.toBeVisible();
            expect(plugin._filterPluginsList(picker, $('<input value="ask;dfjha;ksjdfhaksjdhf">'))).not.toEqual(false);
            expect(items.add(titles)).not.toBeVisible();
        });

        it('filters plugins', function() {
            expect(plugin._filterPluginsList(picker, $('<input value="Text">'))).not.toEqual(false);
            expect(items.filter(':visible').length).toEqual(2);
            expect(titles.filter(':visible').length).toEqual(1);
            expect(titles.filter(':visible').text()).toMatch(/Generic/);

            expect(plugin._filterPluginsList(picker, $('<input value="Style">'))).not.toEqual(false);
            expect(items.filter(':visible').length).toEqual(2);
            expect(titles.filter(':visible').length).toEqual(1);
            expect(titles.filter(':visible').text()).toMatch(/Generic/);
        });

        it('filters categories', function() {
            expect(plugin._filterPluginsList(picker, $('<input value="Bootstrap">'))).not.toEqual(false);
            expect(items.filter(':visible').length).toEqual(15);
            expect(titles.filter(':visible').length).toEqual(1);
            expect(titles.filter(':visible').text()).toMatch(/Bootstrap/);
        });
    });

    describe('_getPluginBreadcrumbs()', function() {
        var plugin;
        beforeEach(function(done) {
            fixture.load('plugins.html');
            $(function() {
                CMS.config = {
                    csrf: 'CSRF_TOKEN',
                    request: {
                        language: 'en'
                    },
                    lang: {}
                };
                CMS.settings = {
                    dragbars: [],
                    states: []
                };
                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    plugin_name: 'Test Text Plugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                done();
            });
        });

        it('returns own breadcrumb if plugin has no parents', function() {
            expect(plugin._getPluginBreadcrumbs()).toEqual([
                {
                    url: '/en/admin/cms/page/edit-plugin/1/',
                    title: 'Test Text Plugin'
                }
            ]);
        });

        // although this shouldn't happen
        it('returns own breadcrumb if plugin has a parent but it does not exist in the registry', function() {
            CMS._plugins = null;
            plugin.options.plugin_parent = 140;
            expect(plugin._getPluginBreadcrumbs()).toEqual([
                {
                    url: '/en/admin/cms/page/edit-plugin/1/',
                    title: 'Test Text Plugin'
                }
            ]);
        });

        it('returns array of breadcrumbs if plugin has parent', function() {
            CMS._plugins = [
                ['cms-placeholder-140', {}],
                [
                    'cms-plugin-140',
                    {
                        plugin_name: 'Parent plugin',
                        plugin_parent: 'None',
                        urls: {
                            edit_plugin: 'parent-edit-url'
                        }
                    }
                ]
            ];
            plugin.options.plugin_parent = 140;
            expect(plugin._getPluginBreadcrumbs()).toEqual([
                {
                    url: 'parent-edit-url',
                    title: 'Parent plugin'
                },
                {
                    url: '/en/admin/cms/page/edit-plugin/1/',
                    title: 'Test Text Plugin'
                }
            ]);
        });

        it('returns array of breadcrumbs if plugin has multiple parents', function() {
            CMS._plugins = [
                ['cms-placeholder-140', {}],
                [
                    'cms-plugin-140',
                    {
                        plugin_name: 'Parent plugin',
                        plugin_parent: 130,
                        urls: {
                            edit_plugin: 'parent-edit-url'
                        }
                    }
                ],
                [
                    'cms-plugin-130',
                    {
                        plugin_name: 'Parent Parent plugin',
                        urls: {
                            edit_plugin: 'parent-parent-edit-url'
                        }
                    }
                ]
            ];
            plugin.options.plugin_parent = 140;
            expect(plugin._getPluginBreadcrumbs()).toEqual([
                {
                    url: 'parent-parent-edit-url',
                    title: 'Parent Parent plugin'
                },
                {
                    url: 'parent-edit-url',
                    title: 'Parent plugin'
                },
                {
                    url: '/en/admin/cms/page/edit-plugin/1/',
                    title: 'Test Text Plugin'
                }
            ]);
        });

        it('is not lazy', function() {
            spyOn($, 'grep').and.callThrough();
            CMS._plugins = [
                [
                    'cms-plugin-140',
                    {
                        plugin_name: 'Parent plugin',
                        plugin_parent: 'None',
                        urls: {
                            edit_plugin: 'parent-edit-url'
                        }
                    }
                ]
            ];
            plugin.options.plugin_parent = 140;
            expect(plugin._getPluginBreadcrumbs()).toEqual([
                {
                    url: 'parent-edit-url',
                    title: 'Parent plugin'
                },
                {
                    url: '/en/admin/cms/page/edit-plugin/1/',
                    title: 'Test Text Plugin'
                }
            ]);

            expect($.grep).toHaveBeenCalledTimes(1);

            expect(plugin._getPluginBreadcrumbs()).toEqual([
                {
                    url: 'parent-edit-url',
                    title: 'Parent plugin'
                },
                {
                    url: '/en/admin/cms/page/edit-plugin/1/',
                    title: 'Test Text Plugin'
                }
            ]);

            expect($.grep).toHaveBeenCalledTimes(2);
        });
    });

    describe('_getNamepacedEvent', function() {
        it('returns a valid namespaced string', function() {
            expect(CMS.Plugin.prototype._getNamepacedEvent('click')).toEqual(jasmine.any(String));
            expect(CMS.Plugin.prototype._getNamepacedEvent('click', 'traverse')).toMatch(/\.traverse/);
        });
    });

    describe('_getPossibleChildClasses()', function() {
        var plugin;
        beforeEach(function(done) {
            fixture.load('plugins.html');
            fixture.load('plugin_child_classes.html');
            $(function() {
                CMS.config = {
                    csrf: 'CSRF_TOKEN',
                    request: {
                        language: 'en'
                    },
                    lang: {}
                };
                CMS.settings = {
                    dragbars: [],
                    states: []
                };
                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    plugin_name: 'Test Text Plugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                spyOn(plugin, '_getId').and.returnValue(1);
                done();
            });
        });

        it('returns markup for child classes based on current plugin/placeholder restrictions', function() {
            expect(plugin._getPossibleChildClasses().length).toEqual(163);
            expect(plugin._getPossibleChildClasses()).toEqual(jasmine.any($));
        });

        it('returns markup for child classes based on current plugin/placeholder restrictions', function() {
            plugin.options.plugin_restriction = ['Bootstrap3AlertCMSPlugin'];
            expect(plugin._getPossibleChildClasses().length).toEqual(2);
            expect(plugin._getPossibleChildClasses()).toEqual(jasmine.any($));
            expect(plugin._getPossibleChildClasses().eq(0)).toHaveClass('cms-submenu-item-title');
            expect(plugin._getPossibleChildClasses().eq(0)).toHaveClass('cms-submenu-item');
            expect(plugin._getPossibleChildClasses().eq(1)).not.toHaveClass('cms-submenu-item-title');
            expect(plugin._getPossibleChildClasses().eq(1)).toHaveClass('cms-submenu-item');
            expect(plugin._getPossibleChildClasses().eq(0)).toHaveText('Bootstrap3');
            expect(plugin._getPossibleChildClasses().eq(1)).toHaveText('Alert');
        });

        it('returns markup for child classes based on current plugin/placeholder restrictions', function() {
            plugin.options.plugin_restriction = ['UpcomingPlugin', 'CalendarPlugin', 'TextPlugin'];
            expect(plugin._getPossibleChildClasses().length).toEqual(5);
            expect(plugin._getPossibleChildClasses()).toEqual(jasmine.any($));
            expect(plugin._getPossibleChildClasses().eq(0)).toHaveClass('cms-submenu-item-title');
            expect(plugin._getPossibleChildClasses().eq(0)).toHaveClass('cms-submenu-item');
            expect(plugin._getPossibleChildClasses().eq(1)).not.toHaveClass('cms-submenu-item-title');
            expect(plugin._getPossibleChildClasses().eq(1)).toHaveClass('cms-submenu-item');
            expect(plugin._getPossibleChildClasses().eq(2)).not.toHaveClass('cms-submenu-item-title');
            expect(plugin._getPossibleChildClasses().eq(2)).toHaveClass('cms-submenu-item');
            expect(plugin._getPossibleChildClasses().eq(3)).toHaveClass('cms-submenu-item-title');
            expect(plugin._getPossibleChildClasses().eq(3)).toHaveClass('cms-submenu-item');
            expect(plugin._getPossibleChildClasses().eq(4)).not.toHaveClass('cms-submenu-item-title');
            expect(plugin._getPossibleChildClasses().eq(4)).toHaveClass('cms-submenu-item');
            expect(plugin._getPossibleChildClasses().eq(0)).toHaveText('Events');
            expect(plugin._getPossibleChildClasses().eq(1)).toHaveText('Calendar');
            expect(plugin._getPossibleChildClasses().eq(2)).toHaveText('Upcoming or Past Events');
            expect(plugin._getPossibleChildClasses().eq(3)).toHaveText('Generic');
            expect(plugin._getPossibleChildClasses().eq(4)).toHaveText('Text');
        });

        it('attaches event handlers for adding these plugins', function() {
            spyOn(CMS.Plugin.prototype, 'addPlugin');
            expect(plugin._getPossibleChildClasses().find('a')).toHandle(Plugin.click);
            plugin._getPossibleChildClasses().find('a').eq(1).trigger(Plugin.click);
            expect(plugin.addPlugin).toHaveBeenCalledTimes(1);
        });

        it('is not lazy', function() {
            plugin.options.plugin_restriction = ['Bootstrap3AlertCMSPlugin'];
            spyOn($.fn, 'filter').and.callThrough();
            plugin._getPossibleChildClasses();
            expect($.fn.filter).toHaveBeenCalledTimes(2);
            plugin._getPossibleChildClasses();
            plugin._getPossibleChildClasses();
            plugin._getPossibleChildClasses();
            expect($.fn.filter).toHaveBeenCalledTimes(8);
        });
    });

    describe('CMS.Plugin._highlightPluginContent()', function() {
        var plugin;
        beforeEach(function(done) {
            fixture.load('plugins.html');
            $(function() {
                CMS.config = {
                    csrf: 'CSRF_TOKEN',
                    request: {
                        language: 'en'
                    },
                    lang: {}
                };
                CMS.settings = {
                    dragbars: [],
                    states: []
                };
                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    plugin_name: 'Test Text Plugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });
                spyOn(plugin, '_getId').and.returnValue(1);
                done();
            });
        });

        it('appends / deletes success overlay', function(done) {
            spyOn($.fn, 'fadeOut').and.callFake(function(timeout, callback) {
                // race condition :(
                if (timeout !== 200) {
                    return;
                }
                expect(timeout).toEqual(200);
                setTimeout(function() {
                    callback.bind($('.cms-plugin-overlay'))();
                    expect($('.cms-plugin-overlay')).not.toBeInDOM();
                    done();
                }, 1600);
            });
            Plugin._highlightPluginContent(1);
            expect($('.cms-plugin-overlay')).toBeInDOM();
        });
    });
});
