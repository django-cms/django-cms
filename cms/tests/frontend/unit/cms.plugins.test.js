/* globals window */
'use strict';

describe('CMS.Plugin', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a Plugin class', function () {
        expect(CMS.Plugin).toBeDefined();
    });

    it('has public API', function () {
        expect(CMS.Plugin.prototype.addPlugin).toEqual(jasmine.any(Function));
        expect(CMS.Plugin.prototype.editPlugin).toEqual(jasmine.any(Function));
        expect(CMS.Plugin.prototype.copyPlugin).toEqual(jasmine.any(Function));
        expect(CMS.Plugin.prototype.cutPlugin).toEqual(jasmine.any(Function));
        expect(CMS.Plugin.prototype.pastePlugin).toEqual(jasmine.any(Function));
        expect(CMS.Plugin.prototype.movePlugin).toEqual(jasmine.any(Function));
        expect(CMS.Plugin.prototype.deletePlugin).toEqual(jasmine.any(Function));
        expect(CMS.Plugin.prototype.editPluginPostAjax).toEqual(jasmine.any(Function));
    });

    describe('instance', function () {
        var plugin1;
        var plugin2;
        var placeholder1;
        var generic;
        beforeEach(function (done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                lang: {}
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };

            $(function () {
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

        afterEach(function () {
            fixture.cleanup();
        });

        it('has ui depending on the type', function () {
            expect(plugin1.ui).toEqual(jasmine.any(Object));
            expect(plugin2.ui).toEqual(jasmine.any(Object));
            expect(placeholder1.ui).toEqual(jasmine.any(Object));
            expect(generic.ui).toEqual(jasmine.any(Object));

            expect(plugin1.ui.container).toExist();
            expect(plugin1.ui.publish).toExist();
            expect(plugin1.ui.save).toExist();
            expect(plugin1.ui.window).toExist();
            expect(plugin1.ui.revert).toExist();
            expect(plugin1.ui.dragbar).toEqual(null);
            expect(plugin1.ui.draggable).toExist();
            expect(plugin1.ui.draggables).not.toExist();
            expect(plugin1.ui.submenu).toExist();
            expect(plugin1.ui.dropdown).toExist();
            expect(plugin1.ui.dragitem).toExist();

            expect(plugin2.ui.container).toExist();
            expect(plugin2.ui.publish).toExist();
            expect(plugin2.ui.save).toExist();
            expect(plugin2.ui.window).toExist();
            expect(plugin2.ui.revert).toExist();
            expect(plugin2.ui.dragbar).toEqual(null);
            expect(plugin2.ui.draggable).toExist();
            expect(plugin2.ui.draggables).toExist();
            expect(plugin2.ui.submenu).toExist();
            expect(plugin2.ui.dropdown).toExist();
            expect(plugin2.ui.dragitem).toExist();

            expect(placeholder1.ui.container).toExist();
            expect(placeholder1.ui.publish).toExist();
            expect(placeholder1.ui.save).toExist();
            expect(placeholder1.ui.window).toExist();
            expect(placeholder1.ui.revert).toExist();
            expect(placeholder1.ui.dragbar).toExist();
            expect(placeholder1.ui.draggable.selector).toEqual('.cms-draggable-null');
            expect(placeholder1.ui.draggables).toExist();
            expect(placeholder1.ui.submenu).toExist();
            expect(placeholder1.ui.dropdown).toExist();
            expect(placeholder1.ui.dragitem).not.toBeDefined();

            expect(generic.ui.container).toExist();
            expect(generic.ui.publish).toExist();
            expect(generic.ui.save).toExist();
            expect(generic.ui.window).toExist();
            expect(generic.ui.revert).toExist();
            expect(generic.ui.dragbar).toEqual(null);
            expect(generic.ui.draggable).toEqual(null);
            expect(generic.ui.draggables).toEqual(null);
            expect(generic.ui.submenu).toEqual(null);
            expect(generic.ui.dropdown).toEqual(null);
            expect(generic.ui.dragitem).not.toBeDefined();
        });

        it('has options', function () {
            expect(plugin1.options).toEqual({
                type: 'plugin',
                placeholder_id: 1,
                plugin_type: 'TextPlugin',
                plugin_id: 1,
                plugin_language: '',
                plugin_parent: null,
                plugin_order: null,
                plugin_breadcrumb: [],
                plugin_restriction: [],
                plugin_parent_restriction: [],
                urls: {
                    add_plugin: '/en/admin/cms/page/add-plugin/',
                    edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                    move_plugin: '/en/admin/cms/page/move-plugin/',
                    delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                    copy_plugin: '/en/admin/cms/page/copy-plugins/'
                }
            });

            expect(plugin2.options).toEqual({
                type: 'plugin',
                placeholder_id: 1,
                plugin_type: 'RandomPlugin',
                plugin_id: 2,
                plugin_language: '',
                plugin_parent: null,
                plugin_order: null,
                plugin_breadcrumb: [],
                plugin_restriction: [],
                plugin_parent_restriction: [],
                urls: {
                    add_plugin: '/en/admin/cms/page/add-plugin/',
                    edit_plugin: '/en/admin/cms/page/edit-plugin/2/',
                    move_plugin: '/en/admin/cms/page/move-plugin/',
                    delete_plugin: '/en/admin/cms/page/delete-plugin/2/',
                    copy_plugin: '/en/admin/cms/page/copy-plugins/'
                }
            });

            expect(placeholder1.options).toEqual({
                type: 'placeholder',
                placeholder_id: 1,
                plugin_type: '',
                plugin_id: null,
                plugin_language: '',
                plugin_parent: null,
                plugin_order: null,
                plugin_breadcrumb: [],
                plugin_restriction: [],
                plugin_parent_restriction: [],
                urls: {
                    add_plugin: '',
                    edit_plugin: '',
                    move_plugin: '',
                    copy_plugin: '',
                    delete_plugin: ''
                }
            });

            expect(generic.options).toEqual({
                type: '',
                placeholder_id: null,
                plugin_type: '',
                plugin_id: null,
                plugin_language: '',
                plugin_parent: null,
                plugin_order: null,
                plugin_breadcrumb: [],
                plugin_restriction: [],
                plugin_parent_restriction: [],
                urls: {
                    add_plugin: '',
                    edit_plugin: '',
                    move_plugin: '',
                    copy_plugin: '',
                    delete_plugin: ''
                }
            });
        });

        it('sets its options to the dom node', function () {
            expect(plugin1.ui.container.data('settings')).toEqual(plugin1.options);
            expect(plugin2.ui.container.data('settings')).toEqual(plugin2.options);
            expect(placeholder1.ui.container.data('settings')).toEqual(placeholder1.options);
            expect(generic.ui.container.data('settings')).toEqual(generic.options);
        });

        it('checks if pasting into this plugin is allowed', function () {
            spyOn(CMS.Plugin.prototype, '_checkIfPasteAllowed');

            plugin1 = new CMS.Plugin('cms-plugin-1', {
                type: 'plugin',
                plugin_id: 1
            });
            expect(CMS.Plugin.prototype._checkIfPasteAllowed.calls.count()).toEqual(1);
            placeholder1 = new CMS.Plugin('cms-placeholder-1', {
                type: 'placeholder',
                placeholder_id: 1
            });
            expect(CMS.Plugin.prototype._checkIfPasteAllowed.calls.count()).toEqual(2);
            generic = new CMS.Plugin('cms-plugin-cms-page-changelist-33');
            expect(CMS.Plugin.prototype._checkIfPasteAllowed.calls.count()).toEqual(2);
        });
    });

    describe('.addPlugin()', function () {
        var plugin;
        beforeEach(function (done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                lang: {}
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            jasmine.Ajax.install();

            $(function () {
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

        afterEach(function () {
            fixture.cleanup();
            jasmine.Ajax.uninstall();
        });

        it('makes a request to the API', function () {
            expect(plugin.addPlugin('TestPlugin', 'Test Plugin', 1)).toEqual(undefined);
            var request = jasmine.Ajax.requests.mostRecent();
            expect(request.url).toEqual('/en/admin/cms/page/add-plugin/');
            expect(request.method).toEqual('POST');
            expect(request.data()).toEqual({
                placeholder_id: ['1'],
                plugin_type: ['TestPlugin'],
                plugin_parent: ['1'],
                plugin_language: [''],
                csrfmiddlewaretoken: ['CSRF_TOKEN']
            });
        });

        it('does not make a request if CMS.API is locked', function () {
            CMS.API.locked = true;
            expect(plugin.addPlugin('TestPlugin', 'Test Plugin', 1)).toEqual(false);
            expect(jasmine.Ajax.requests.count()).toEqual(0);
            CMS.API.locked = false;
        });

        it('edits newly created plugin if request succeeded', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
                ajax.success({
                    url: 'edit-url',
                    breadcrumb: 'does not matter yet'
                });
            });
            spyOn(plugin, 'editPlugin');

            plugin.addPlugin('TestPlugin', 'Test Plugin', 1);

            expect(plugin.editPlugin).toHaveBeenCalledWith('edit-url', 'Test Plugin', 'does not matter yet');
        });

        it('sets newPlugin option if request succeeded', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
                ajax.success({
                    url: 'edit-url',
                    breadcrumb: 'does not matter yet',
                    whatever: 'whatever'
                });
            });
            spyOn(plugin, 'editPlugin');

            expect(plugin.newPlugin).toEqual(undefined);
            plugin.addPlugin('TestPlugin', 'Test Plugin', 1);
            expect(plugin.newPlugin).toEqual({
                url: 'edit-url',
                breadcrumb: 'does not matter yet',
                whatever: 'whatever'
            });
        });

        it('locks/unlocks the CMS.API if request is successful', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
                expect(CMS.API.locked).toEqual(true);
                ajax.success({});
                expect(CMS.API.locked).toEqual(false);
            });
            spyOn(plugin, 'editPlugin');

            plugin.addPlugin('TestPlugin', 'Test Plugin', 1);
        });

        it('locks/unlocks the CMS.API if request is not successful', function () {
            CMS.API.Messages = new CMS.Messages();
            spyOn($, 'ajax').and.callFake(function (ajax) {
                expect(CMS.API.locked).toEqual(true);
                ajax.error({});
                expect(CMS.API.locked).toEqual(false);
            });
            spyOn(plugin, 'editPlugin');

            plugin.addPlugin('TestPlugin', 'Test Plugin', 1);
        });

        it('shows the error message if request failed', function () {
            CMS.API.Messages = new CMS.Messages();
            CMS.config.lang.error = 'Following error occured: ';
            spyOn(CMS.API.Messages, 'open');
            spyOn($, 'ajax').and.callFake(function (ajax) {
                ajax.error({
                    responseText: 'Failed to add plugin'
                });
            });
            spyOn(plugin, 'editPlugin');

            plugin.addPlugin('TestPlugin', 'Test Plugin', 1);

            expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                message: 'Following error occured: Failed to add plugin',
                error: true
            });
        });

        // this is not really supposed to happen
        it('shows generic error message if request failed', function () {
            CMS.API.Messages = new CMS.Messages();
            CMS.config.lang.error = '';
            spyOn(CMS.API.Messages, 'open');
            spyOn($, 'ajax').and.callFake(function (ajax) {
                ajax.error({
                    responseText: '',
                    status: '418',
                    statusText: "I'm a teapot"
                });
            });
            spyOn(plugin, 'editPlugin');

            plugin.addPlugin('TestPlugin', 'Test Plugin');

            expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                message: "418 I'm a teapot",
                error: true
            });
        });
    });

    describe('.editPlugin()', function () {
        var plugin;
        var fakeModal;

        beforeEach(function (done) {
            fakeModal = {
                on: jasmine.createSpy(),
                open: jasmine.createSpy()
            };
            spyOn(CMS.Modal.prototype, 'initialize').and.callFake(function () {
                return fakeModal;
            });
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                lang: {}
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            $(function () {
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

        afterEach(function () {
            fixture.cleanup();
        });

        it('creates and opens a modal to edit a plugin', function () {
            plugin.editPlugin('/edit-url', 'Test Plugin', 'breadcrumb');
            expect(fakeModal.open).toHaveBeenCalledWith({
                url: '/edit-url',
                title: 'Test Plugin',
                breadcrumbs: 'breadcrumb',
                width: 850
            });
        });

        it('creates and opens a modal to edit freshly created plugin', function () {
            plugin.newPlugin = true;
            plugin.editPlugin('/edit-plugin-url', 'Random Plugin', ['breadcrumb']);
            expect(fakeModal.open).toHaveBeenCalledWith({
                url: '/edit-plugin-url',
                title: 'Random Plugin',
                breadcrumbs: ['breadcrumb'],
                width: 850
            });
        });
        it('adds events to remove the "add plugin" placeholder', function () {
            plugin.editPlugin('/edit-plugin-url', 'Random Plugin', ['breadcrumb']);

            expect(fakeModal.on).toHaveBeenCalledWith('cms.modal.loaded', jasmine.any(Function));
            expect(fakeModal.on).toHaveBeenCalledWith('cms.modal.closed', jasmine.any(Function));

            $('<div class="cms-add-plugin-placeholder"></div>').prependTo('body');
            fakeModal.on.calls.argsFor(0)[1]();
            expect($('.cms-add-plugin-placeholder')).not.toExist();

            $('<div class="cms-add-plugin-placeholder"></div>').prependTo('body');
            fakeModal.on.calls.argsFor(1)[1]();
            expect($('.cms-add-plugin-placeholder')).not.toExist();
        });
    });

    describe('.copyPlugin()', function () {
        var plugin;
        beforeEach(function (done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
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

            $(function () {
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

        afterEach(function () {
            fixture.cleanup();
            jasmine.Ajax.uninstall();
        });

        it('makes a request to the API', function () {
            expect(plugin.copyPlugin(plugin.options)).toEqual(undefined);
            var request = jasmine.Ajax.requests.mostRecent();
            expect(request.url).toEqual('/en/admin/cms/page/copy-plugins/');
            expect(request.method).toEqual('POST');
            expect(request.data()).toEqual({
                source_placeholder_id: ['1'],
                source_plugin_id: ['1'],
                source_language: [''],
                target_plugin_id: [''],
                target_placeholder_id: ['clipboardId'],
                target_language: [''],
                csrfmiddlewaretoken: ['CSRF_TOKEN']
            });
        });

        it('does not make a request if CMS.API is locked', function () {
            CMS.API.locked = true;
            expect(plugin.copyPlugin(plugin.options)).toEqual(false);
            expect(jasmine.Ajax.requests.count()).toEqual(0);
            CMS.API.locked = false;
        });

        it('shows the success message if request succeeds', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
                ajax.success();
                CMS.API.locked = false;
            });
            plugin.copyPlugin(plugin.options);
            expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                message: 'Voila!'
            });
            expect(CMS.API.Helpers.reloadBrowser).toHaveBeenCalledWith();
        });

        it('reloads the browser if request succeeds', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
                ajax.success();
                CMS.API.locked = false;
            });
            plugin.copyPlugin(plugin.options);
            expect(CMS.API.Helpers.reloadBrowser).toHaveBeenCalled();
        });

        it('shows the error message if request failed', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
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
        it('shows generic error message if request failed', function () {
            CMS.config.lang.error = '';
            spyOn($, 'ajax').and.callFake(function (ajax) {
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

        it('locks but does not unlock the CMS.API if request is successful', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
                expect(CMS.API.locked).toEqual(true);
                ajax.success();
                expect(CMS.API.locked).toEqual(true);
            });
            CMS.API.locked = false;
            plugin.copyPlugin(plugin.options);
        });

        it('locks/unlocks the CMS.API if request is not successful', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
                expect(CMS.API.locked).toEqual(true);
                ajax.error({});
                expect(CMS.API.locked).toEqual(false);
            });
            CMS.API.locked = false;
            plugin.copyPlugin(plugin.options);
        });

        it('clears the clipboard first if no options were passed', function () {
            CMS.API.Clipboard = new CMS.Clipboard();
            spyOn(CMS.API.Clipboard, 'clear').and.callFake(function (callback) {
                callback();
            });
            spyOn($, 'ajax').and.callFake(function (ajax) {
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

            plugin.options.plugin_language = 'es';
            plugin.copyPlugin();
        });

        it('clears the clipboard first if source language was passed', function () {
            CMS.API.Clipboard = new CMS.Clipboard();
            spyOn(CMS.API.Clipboard, 'clear').and.callFake(function (callback) {
                callback();
            });
            spyOn($, 'ajax').and.callFake(function (ajax) {
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

            plugin.options.page_language = 'es';
            plugin.copyPlugin(undefined, 'de');
        });
    });

    describe('.cutPlugin()', function () {
        var plugin;
        beforeEach(function (done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
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

            $(function () {
                CMS.API.Messages = new CMS.Messages();
                spyOn(CMS.API.Messages, 'open');

                CMS.API.Clipboard = new CMS.Clipboard();
                spyOn(CMS.API.Clipboard, 'clear').and.callFake(function (callback) {
                    CMS.API.locked = false; // it happens as part of CMS.API.Toolbar.openAjax
                    callback();
                });

                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    placeholder_id: 1,
                    page_language: 'en',
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

        afterEach(function () {
            fixture.cleanup();
            jasmine.Ajax.uninstall();
        });

        it('makes a request to the API', function () {
            expect(plugin.cutPlugin()).toEqual(undefined);
            var request = jasmine.Ajax.requests.mostRecent();
            expect(request.url).toEqual('/en/admin/cms/page/move-plugin/');
            expect(request.method).toEqual('POST');
            expect(request.data()).toEqual({
                placeholder_id: ['clipboardId'],
                plugin_id: ['1'],
                plugin_language: ['en'],
                plugin_parent: [''],
                'plugin_order[]': ['1'],
                csrfmiddlewaretoken: ['CSRF_TOKEN']
            });
            CMS.API.locked = false;
        });

        it('clears the clipboard before making the request', function () {
            plugin.cutPlugin();
            expect(CMS.API.Clipboard.clear).toHaveBeenCalled();
            CMS.API.locked = false;
        });

        it('shows the success message if request succeeds', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
                ajax.success();
                CMS.API.locked = false;
            });
            plugin.cutPlugin();
            expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                message: 'Voila!'
            });
        });

        it('reloads the browser if request succeeds', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
                ajax.success();
                CMS.API.locked = false;
            });
            plugin.cutPlugin();
            expect(CMS.API.Helpers.reloadBrowser).toHaveBeenCalled();
        });

        it('shows the error message if request failed', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
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
        it('shows generic error message if request failed', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
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

        it('does not make a request if CMS.API is locked', function () {
            CMS.API.locked = true;
            expect(plugin.cutPlugin()).toEqual(false);
            expect(CMS.API.Clipboard.clear).not.toHaveBeenCalled();
            expect(jasmine.Ajax.requests.count()).toEqual(0);
            CMS.API.locked = false;
        });

        it('does not make a request if CMS.API is locked after clearing the clipboard', function () {
            CMS.API.Clipboard.clear.and.callFake(function (callback) {
                CMS.API.locked = true;
                expect(callback()).toEqual(false);
            });
            spyOn($, 'ajax');
            expect(plugin.cutPlugin()).toEqual(undefined);
            expect(CMS.API.Clipboard.clear).toHaveBeenCalled();
            expect(jasmine.Ajax.requests.count()).toEqual(0);
            expect($.ajax).not.toHaveBeenCalled();
            CMS.API.locked = false;
        });

        it('locks the CMS.API before making the request', function () {
            CMS.API.locked = false;
            CMS.API.Clipboard.clear.and.callFake($.noop);
            plugin.cutPlugin();
            expect(CMS.API.locked).toEqual(true);
            CMS.API.locked = false;
        });

        it('does not unlock the CMS.API if request is successful', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
                expect(CMS.API.locked).toEqual(true);
                ajax.success();
                expect(CMS.API.locked).toEqual(true);
            });
            CMS.API.locked = false;
            plugin.cutPlugin();
        });

        it('unlocks the CMS.API if request is not successful', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
                expect(CMS.API.locked).toEqual(true);
                ajax.error({});
                expect(CMS.API.locked).toEqual(false);
            });
            CMS.API.locked = false;
            plugin.cutPlugin();
        });
    });

    describe('.pastePlugin()', function () {
        var plugin;
        var clipboardPlugin;
        var placeholder;

        beforeEach(function (done) {
            fixture.load('plugins.html', 'clipboard.html', true);
            CMS.config = {
                csrf: 'CSRF_TOKEN',
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

            $(function () {
                CMS.Plugin._initializeGlobalHandlers();
                CMS.API.StructureBoard = {
                    getId: function () {
                        return 2;
                    },
                    getIds: function () {
                        return [];
                    }
                };

                clipboardPlugin = new CMS.Plugin('cms-plugin-3', {
                    type: 'plugin',
                    plugin_id: 3,
                    plugin_type: 'ClipboardPlugin',
                    plugin_parent_restriction: ['RandomPlugin']
                });

                plugin = new CMS.Plugin('cms-plugin-2', {
                    type: 'plugin',
                    plugin_id: 2,
                    plugin_type: 'RandomPlugin',
                    placeholder_id: 2,
                    page_language: 'en',
                    urls: {
                        add_plugin: '/en/admin/cms/page/add-plugin/',
                        edit_plugin: '/en/admin/cms/page/edit-plugin/2/',
                        move_plugin: '/en/admin/cms/page/move-plugin/',
                        delete_plugin: '/en/admin/cms/page/delete-plugin/2/',
                        copy_plugin: '/en/admin/cms/page/copy-plugins/'
                    }
                });

                placeholder = new CMS.Plugin('cms-placeholder-2', {
                    type: 'placeholder',
                    placeholder_id: 2
                });
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it("moves the clipboard draggable dom node to plugin's child list", function () {
            var clipboard = $('.cms-clipboard');
            var clipboardDraggable = clipboard.find('.cms-draggable:first');
            var clipboardPluginDOM = clipboard.find('.cms-plugin:first');
            expect(clipboard).toExist();
            expect(clipboardDraggable).toExist();
            expect(clipboardPluginDOM).toExist();
            plugin.pastePlugin();
            expect(plugin.ui.draggables).toContainElement('.cms-draggable-3');
        });

        it("moves the clipboard draggable dom node placeholder's child list", function () {
            var clipboard = $('.cms-clipboard');
            var clipboardDraggable = clipboard.find('.cms-draggable:first');
            var clipboardPluginDOM = clipboard.find('.cms-plugin:first');
            expect(clipboard).toExist();
            expect(clipboardDraggable).toExist();
            expect(clipboardPluginDOM).toExist();
            placeholder.pastePlugin();
            expect(placeholder.ui.draggables).toContainElement('.cms-draggable-3');
        });

        it('triggers correct events on a freshly pasted clipboard plugin', function (done) {
            var clipboardPluginDOM = $('.cms-clipboard .cms-plugin:first');
            clipboardPluginDOM.on('cms.plugin.update', function () {
                done();
            });
            plugin.pastePlugin();
        });

        it('triggers correct events on a child list where the plugin was just moved', function (done) {
            plugin.ui.draggables.on('cms.update', function () {
                done();
            });
            plugin.pastePlugin();
        });

        it('triggers movePlugin on clipboard plugin eventually', function () {
            spyOn(clipboardPlugin, 'movePlugin');
            plugin.pastePlugin();
            expect(clipboardPlugin.movePlugin).toHaveBeenCalledWith({
                type: 'plugin',
                placeholder_id: null,
                plugin_type: 'ClipboardPlugin',
                plugin_id: 3,
                plugin_language: '',
                plugin_parent: null,
                plugin_order: null,
                plugin_breadcrumb: [],
                plugin_restriction: [],
                plugin_parent_restriction: ['RandomPlugin'],
                urls: {
                    add_plugin: '',
                    edit_plugin: '',
                    move_plugin: '',
                    copy_plugin: '',
                    delete_plugin: ''
                },
                target: 2,
                parent: 2,
                move_a_copy: true
            });
        });
    });

    describe('.movePlugin()', function () {
        var plugin;
        beforeEach(function (done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
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

            $(function () {
                CMS.API.Messages = new CMS.Messages();
                spyOn(CMS.API.Messages, 'open');

                CMS.API.StructureBoard = {
                    getId: function (el) {
                        if (el.is('.cms-dragbar')) {
                            return 1;
                        }
                        if (el.is('.cms-draggable')) {
                            return false;
                        }
                    },
                    getIds: function () {
                        return [3, 2, 1];
                    }
                };

                plugin = new CMS.Plugin('cms-plugin-1', {
                    type: 'plugin',
                    plugin_id: 1,
                    plugin_type: 'TextPlugin',
                    placeholder_id: 1,
                    page_language: 'en',
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

        afterEach(function () {
            fixture.cleanup();
            jasmine.Ajax.uninstall();
        });

        it('makes a request to the API', function () {
            CMS.API.locked = false;
            expect(plugin.movePlugin()).toEqual(undefined);
            var request = jasmine.Ajax.requests.mostRecent();
            expect(request.url).toEqual('/en/admin/cms/page/move-plugin/');
            expect(request.method).toEqual('POST');
            expect(request.data()).toEqual({
                placeholder_id: ['1'],
                plugin_id: ['1'],
                plugin_parent: [''],
                'plugin_order[]': ['3', '2', '1'],
                plugin_language: ['en'],
                csrfmiddlewaretoken: ['CSRF_TOKEN']
            });
            CMS.API.locked = false;
        });

        it('does not make a request if CMS.API is locked', function () {
            CMS.API.locked = true;
            expect(plugin.movePlugin()).toEqual(false);
            expect(jasmine.Ajax.requests.count()).toEqual(0);
            CMS.API.locked = false;
        });

        it('does not make a request if there is no placeholder in chain of parents', function () {
            CMS.API.StructureBoard.getId = function () {
                return false;
            };

            expect(plugin.movePlugin()).toEqual(false);
            expect(jasmine.Ajax.requests.count()).toEqual(0);
            CMS.API.locked = false;
        });

        it('moves the plugin dom to a new place', function () {
            spyOn(plugin, '_setPosition');
            plugin.movePlugin();
            expect(plugin._setPosition).toHaveBeenCalled();
            expect(plugin._setPosition.calls.argsFor(0)[0]).toEqual(1);
            expect(plugin._setPosition.calls.argsFor(0)[1]).toBeMatchedBy('.cms-plugin-1');
            expect(plugin._setPosition.calls.argsFor(0)[2]).toBeMatchedBy('.cms-draggable-1');
        });

        it('uses modified plugin order if we are moving a copy', function () {
            CMS.API.locked = false;
            spyOn($, 'ajax').and.callFake(function (ajax) {
                expect(ajax.data).toEqual(jasmine.objectContaining({
                    plugin_order: [3, 2, '__COPY__']
                }));
            });
            plugin.movePlugin($.extend(plugin.options, { move_a_copy: true }));
        });

        it('reloads browser if response requires it', function () {
            CMS.API.locked = false;
            spyOn($, 'ajax').and.callFake(function (ajax) {
                ajax.success({
                    reload: true
                });
            });
            plugin.movePlugin();
            expect(CMS.API.Helpers.reloadBrowser).toHaveBeenCalled();
        });

        it('does not reload browser if response does not require it', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
                ajax.success({
                    reload: false
                });
            });

            plugin.movePlugin();
            expect(CMS.API.Helpers.reloadBrowser).not.toHaveBeenCalled();
        });

        it('updates the plugin urls if response requires it', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
                ajax.success({
                    urls: {
                        copy_plugin: 'new-copy-url',
                        newObject: true
                    }
                });
            });

            plugin.movePlugin();
            expect(plugin.options.urls).toEqual({
                add_plugin: '/en/admin/cms/page/add-plugin/',
                edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                move_plugin: '/en/admin/cms/page/move-plugin/',
                delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                copy_plugin: 'new-copy-url',
                newObject: true
            });
            expect(plugin.ui.container.data('settings').urls).toEqual({
                add_plugin: '/en/admin/cms/page/add-plugin/',
                edit_plugin: '/en/admin/cms/page/edit-plugin/1/',
                move_plugin: '/en/admin/cms/page/move-plugin/',
                delete_plugin: '/en/admin/cms/page/delete-plugin/1/',
                copy_plugin: 'new-copy-url',
                newObject: true
            });
        });

        it('shows success animation', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
                ajax.success({});
            });
            spyOn(plugin, '_showSuccess');

            plugin.movePlugin();
            expect(plugin._showSuccess).toHaveBeenCalledWith(plugin.ui.draggable);
        });

        it('shows the error message if request failed', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
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
        it('shows generic error message if request failed', function () {
            spyOn($, 'ajax').and.callFake(function (ajax) {
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

        it('locks the CMS.API before making the request', function () {
            CMS.API.locked = false;
            spyOn($, 'ajax').and.callFake(function () {
                expect(CMS.API.locked).toEqual(true);
            });
            plugin.movePlugin();
        });

        it('unlocks the CMS.API if request is successful', function () {
            CMS.API.locked = false;
            spyOn($, 'ajax').and.callFake(function (ajax) {
                expect(CMS.API.locked).toEqual(true);
                ajax.success({});
                expect(CMS.API.locked).toEqual(false);
            });
            plugin.movePlugin();
        });

        it('unlocks the CMS.API if request is not successful', function () {
            CMS.API.locked = false;
            spyOn($, 'ajax').and.callFake(function (ajax) {
                expect(CMS.API.locked).toEqual(true);
                ajax.error({});
                expect(CMS.API.locked).toEqual(false);
            });
            plugin.movePlugin();
        });

        it('triggers window resize', function () {
            spyOnEvent(window, 'resize');
            plugin.movePlugin();
            expect('resize').toHaveBeenTriggeredOn(window);
        });

        it('shows publish page button optimistically', function () {
            CMS.API.locked = false;
            expect(plugin.ui.publish).not.toHaveClass('cms-btn-publish-active');
            expect(plugin.ui.publish).toHaveClass('cms-btn-disabled');
            expect(plugin.ui.publish.parent()).not.toBeVisible();
            plugin.movePlugin();
            expect(plugin.ui.publish).toHaveClass('cms-btn-publish-active');
            expect(plugin.ui.publish).not.toHaveClass('cms-btn-disabled');
            expect(plugin.ui.publish.parent()).toBeVisible();
        });

        it('enables "revert to live" button optimistically', function () {
            CMS.API.locked = false;
            expect(plugin.ui.revert).toHaveClass('cms-toolbar-item-navigation-disabled');
            plugin.movePlugin();
            expect(plugin.ui.publish).not.toHaveClass('cms-toolbar-item-navigation-disabled');
        });

        it('does not hide publish page button if request actually failed', function (done) {
            spyOn($, 'ajax').and.callFake(function (ajax) {
                // have to simulate async
                setTimeout(function () {
                    ajax.error({});
                    expect(plugin.ui.publish).toHaveClass('cms-btn-publish-active');
                    expect(plugin.ui.publish).not.toHaveClass('cms-btn-disabled');
                    expect(plugin.ui.publish.parent()).toBeVisible();
                    done();
                }, 0);
            });

            CMS.API.locked = false;
            expect(plugin.ui.publish).not.toHaveClass('cms-btn-publish-active');
            expect(plugin.ui.publish).toHaveClass('cms-btn-disabled');
            expect(plugin.ui.publish.parent()).not.toBeVisible();
            plugin.movePlugin();
            expect(plugin.ui.publish).toHaveClass('cms-btn-publish-active');
            expect(plugin.ui.publish).not.toHaveClass('cms-btn-disabled');
            expect(plugin.ui.publish.parent()).toBeVisible();
        });

        it('does not disable "revert to live" button if request actually failed', function (done) {
            spyOn($, 'ajax').and.callFake(function (ajax) {
                // have to simulate async
                setTimeout(function () {
                    ajax.error({});
                    expect(plugin.ui.publish).not.toHaveClass('cms-toolbar-item-navigation-disabled');
                    done();
                }, 0);
            });

            CMS.API.locked = false;
            expect(plugin.ui.revert).toHaveClass('cms-toolbar-item-navigation-disabled');
            plugin.movePlugin();
            expect(plugin.ui.publish).not.toHaveClass('cms-toolbar-item-navigation-disabled');
        });
    });

    describe('.deletePlugin()', function () {
        var plugin;
        var fakeModal;

        beforeEach(function (done) {
            fakeModal = {
                on: jasmine.createSpy(),
                open: jasmine.createSpy()
            };
            spyOn(CMS.Modal.prototype, 'initialize').and.callFake(function (params) {
                expect(params).toEqual({
                    newPlugin: false,
                    onClose: false,
                    redirectOnClose: false
                });
                return fakeModal;
            });
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                lang: {}
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            $(function () {
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

        afterEach(function () {
            fixture.cleanup();
        });

        it('creates and opens a modal for plugin deletion', function () {
            plugin.deletePlugin('delete-url', 'Delete name', 'breadcrumb');
            expect(fakeModal.open).toHaveBeenCalledWith({
                url: 'delete-url',
                title: 'Delete name',
                breadcrumbs: 'breadcrumb'
            });
        });

        it('adds events to remove any existing "add plugin" placeholders', function () {
            plugin.deletePlugin();
            expect(fakeModal.on).toHaveBeenCalledWith('cms.modal.loaded', jasmine.any(Function));

            $('<div class="cms-add-plugin-placeholder"></div>').prependTo('body');
            fakeModal.on.calls.argsFor(0)[1]();
            expect($('.cms-add-plugin-placeholder')).not.toExist();
        });
    });

    describe('.editPluginPostAjax()', function () {
        var plugin;

        beforeEach(function (done) {
            fixture.load('plugins.html');
            CMS.config = {
                csrf: 'CSRF_TOKEN',
                lang: {}
            };
            CMS.settings = {
                dragbars: [],
                states: []
            };
            $(function () {
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

        afterEach(function () {
            fixture.cleanup();
        });

        it('delegates to editPlugin with url coming from response', function () {
            spyOn(plugin, 'editPlugin');
            plugin.editPluginPostAjax({}, { url: 'test-url', breadcrumb: 'whatever' });
            expect(plugin.editPlugin).toHaveBeenCalledWith(
                'test-url',
                'Test Text Plugin',
                'whatever'
            );
        });
    });
});
