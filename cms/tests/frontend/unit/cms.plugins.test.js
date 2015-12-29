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
                        add_plugin: "/en/admin/cms/page/add-plugin/",
                        edit_plugin: "/en/admin/cms/page/edit-plugin/1/",
                        move_plugin: "/en/admin/cms/page/move-plugin/",
                        delete_plugin: "/en/admin/cms/page/delete-plugin/1/",
                        copy_plugin: "/en/admin/cms/page/copy-plugins/"
                    }
                });
                plugin2 = new CMS.Plugin('cms-plugin-2', {
                    type: 'plugin',
                    plugin_id: 2,
                    plugin_type: 'RandomPlugin',
                    placeholder_id: 1,
                    urls: {
                        add_plugin: "/en/admin/cms/page/add-plugin/",
                        edit_plugin: "/en/admin/cms/page/edit-plugin/2/",
                        move_plugin: "/en/admin/cms/page/move-plugin/",
                        delete_plugin: "/en/admin/cms/page/delete-plugin/2/",
                        copy_plugin: "/en/admin/cms/page/copy-plugins/"
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
                    add_plugin: "/en/admin/cms/page/add-plugin/",
                    edit_plugin: "/en/admin/cms/page/edit-plugin/1/",
                    move_plugin: "/en/admin/cms/page/move-plugin/",
                    delete_plugin: "/en/admin/cms/page/delete-plugin/1/",
                    copy_plugin: "/en/admin/cms/page/copy-plugins/"
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
                    add_plugin: "/en/admin/cms/page/add-plugin/",
                    edit_plugin: "/en/admin/cms/page/edit-plugin/2/",
                    move_plugin: "/en/admin/cms/page/move-plugin/",
                    delete_plugin: "/en/admin/cms/page/delete-plugin/2/",
                    copy_plugin: "/en/admin/cms/page/copy-plugins/"
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
                plugin_id: 1,
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
        it('makes a request to the API');
        it('does not make a request if CMS.API is locked');
        it('edits newly created plugin if request succeeded');
        it('sets newPlugin option if request succeeded');
        it('locks the CMS.API before making the request');
        it('unlocks the CMS.API if request is successful');
        it('unlocks the CMS.API if request is not successful');
        it('shows the error message if request failed');
    });

    describe('.editPlugin()', function () {
        it('creates and opens a modal to edit a plugin');
        it('creates and opens a modal to edit freshly created plugin');
        it('adds events to remove the "add plugin" placeholder');
    });

    describe('.copyPlugin()', function () {
        it('makes a request to the API');
        it('does not make a request if CMS.API is locked');
        it('shows the success message if request succeeds');
        it('reloads the browser if request succeeds');
        it('shows the error message if request failed');
        it('locks the CMS.API before making the request');
        it('unlocks the CMS.API if request is successful');
        it('unlocks the CMS.API if request is not successful');
        it('clears the clipboard first if custom options were passed');
        it('clears the clipboard first if source language was passed');
    });

    describe('.cutPlugin()', function () {
        it('makes a request to the API');
        it('clears the clipboard before making the request');
        it('shows the success message if request succeeds');
        it('reloads the browser if request succeeds');
        it('shows the error message if request failed');
        it('does not make a request if CMS.API is locked');
        it('locks the CMS.API before making the request');
        it('unlocks the CMS.API if request is successful');
        it('unlocks the CMS.API if request is not successful');
    });

    describe('.pastePlugin()', function () {
        it('moves the clipboard draggable dom node plugins child list');
        it('moves the clipboard draggable dom node placeholders child list');
        it('triggers correct events afterwards');
    });

    describe('.movePlugin()', function () {
        it('makes the request to the API');
        it('does not make a request if CMS.API is locked');
        it('does not make a request if there is no placeholder in chain of parents');
        it('reloads browser if response requires it');
        it('updates the plugin urls if response requires it');
        it('shows success animation');
        it('shows error message if request fails');
        it('locks the CMS.API before making the request');
        it('unlocks the CMS.API if request is successful');
        it('unlocks the CMS.API if request is not successful');
        it('triggers window resize');
        it('shows publish page button optimistically');
        it('enables "revert to live" button optimistically');
    });

    describe('.deletePlugin()', function () {
        it('creates and opens a modal for plugin deletion');
        it('adds events to remove any existing "add plugin" placeholders');
    });

    describe('.editPluginPostAjax()', function () {
        it('delegates to editPlugin with url coming from response');
    });
});
