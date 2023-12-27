(function ($, CMS) {
    'use strict';
    window.CKEDITOR_BASEPATH = $('[data-ckeditor-basepath]').attr('data-ckeditor-basepath');

    // CMS.$ will be passed for $
    /**
     * CMS.CKEditor
     *
     * @description: Adds cms specific plugins to CKEditor
     */
    CMS.CKEditor = {

        options: {
            // ckeditor default settings, will be overwritten by CKEDITOR_SETTINGS
            language: 'en',
            skin: 'moono-lisa',
            toolbar_CMS: [
                ['Undo', 'Redo'],
                ['cmsplugins', 'cmswidget', '-', 'ShowBlocks'],
                ['Format', 'Styles'],
                ['TextColor', 'BGColor', '-', 'PasteText', 'PasteFromWord'],
                ['Scayt'],
                ['Maximize', ''],
                '/',
                ['Bold', 'Italic', 'Underline', 'Strike', '-', 'Subscript', 'Superscript', '-', 'RemoveFormat'],
                ['JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
                ['HorizontalRule'],
                ['NumberedList', 'BulletedList'],
                ['Outdent', 'Indent', '-', 'Blockquote', '-', 'Link', 'Unlink', '-', 'Table'],
                ['Source']
            ],
            toolbar_HTMLField: [
                ['Undo', 'Redo'],
                ['ShowBlocks'],
                ['Format', 'Styles'],
                ['TextColor', 'BGColor', '-', 'PasteText', 'PasteFromWord'],
                ['Scayt'],
                ['Maximize', ''],
                '/',
                ['Bold', 'Italic', 'Underline', 'Strike', '-', 'Subscript', 'Superscript', '-', 'RemoveFormat'],
                ['JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
                ['HorizontalRule'],
                ['Link', 'Unlink'],
                ['NumberedList', 'BulletedList'],
                ['Outdent', 'Indent', '-', 'Blockqote', '-', 'Link', 'Unlink', '-', 'Table'],
                ['Source']
            ],

            allowedContent: true,
            toolbarCanCollapse: false,
            removePlugins: 'resize',
            extraPlugins: ''
        },

        // Meaningful default, overwritten by the backend
        static_url: '/static/djangocms-text-ckeditor',

        CSS: [],
        editors: {},


        init: function (element, mode, options, settings, callback) {
            var container = $(element);

            container.data('ckeditor-initialized', true);
            container.attr('contenteditable', true);
            // add additional settings to options
            this.options.toolbar = settings.toolbar;
            this.options = $.extend(false, {
                settings: settings
            }, this.options, options);

            // add extra plugins that we absolutely must have
            this.options.extraPlugins = this.options.extraPlugins +=
                ',cmsplugins,cmswidget,cmsdialog,cmsresize,widget';

            document.createElement('cms-plugin');
            CKEDITOR.dtd['cms-plugin'] = CKEDITOR.dtd.div;
            CKEDITOR.dtd.$inline['cms-plugin'] = 1;
            // has to be here, otherwise extra <p> tags appear
            CKEDITOR.dtd.$nonEditable['cms-plugin'] = 1;
            CKEDITOR.dtd.$transparent['cms-plugin'] = 1;
            CKEDITOR.dtd.body['cms-plugin'] = 1;

            // add additional plugins (autoloads plugins.js)
            CKEDITOR.skin.addIcon('cmsplugins', settings.static_url +
                '/ckeditor_plugins/cmsplugins/icons/cmsplugins.svg');

            var editor;
            if (mode === 'admin') {
                // render ckeditor
                editor = CKEDITOR.replace(container[0], this.options);
            } else {
                editor = CKEDITOR.inline(container[0], this.options);
            }

            CMS.CKEditor.editors[editor.id] = {
                editor: editor,
                options: options,
                settings: settings,
                container: container,
                changed: false,
                child_changed: false
            };
            editor.on('instanceReady', callback);
        },

        initInlineEditors: function () {
            if (CMS._plugins === undefined) {
                // no plugins -> no inline editors
                return;
            }

            CMS.CKEditor.observer = CMS.CKEditor.observer || new IntersectionObserver(function (entries, opts) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        var target = $(entry.target);
                        var plugin_id = target.data('cms_plugin_id');
                        var url = target.data('cms_edit_url');

                        CMS.CKEditor.startInlineEditor(plugin_id, url);
                    }
                });
            }, {
                root: null,
                threshold: 0.05
            });

            CMS._plugins.forEach(function (plugin) {
                if (plugin[1].plugin_type === 'TextPlugin') {
                    var url = plugin[1].urls.edit_plugin;
                    var id = plugin[1].plugin_id;
                    var elements = $('.cms-plugin.cms-plugin-' + id);
                    var wrapper;

                    if (elements.length > 0) {
                        if (elements.length === 1 && elements.prop('tagName') === 'DIV') {  // already wrapped?
                            wrapper = elements.addClass('cms-ckeditor-inline-wrapper');
                        } else {  // no, wrap now!
                            wrapper = elements
                                .wrapAll('<div class="cms-ckeditor-inline-wrapper wrapped"></div>')
                                .parent();
                            elements
                                .removeClass('cms-plugin')
                                .removeClass('cms-plugin-' + id);
                            wrapper.addClass('cms-plugin').addClass('cms-plugin-' + id);
                        }
                        wrapper.data('cms_edit_url', url);
                        wrapper.data('cms_plugin_id', id);
                        wrapper.on('dblclick.cms-ckeditor', function (event) {
                            // Double-click is needed by CKEditor
                            event.stopPropagation();
                        });
                        wrapper.on('pointerover.cms-ckeditor', function (event) {
                            // use time out to let other event handlers (CMS' !) run first.
                            setTimeout(function () {
                                // do not show tooltip on inline editing text fields.
                                CMS.API.Tooltip.displayToggle(false, event.target, '', id);
                            }, 0);
                        });
                        CMS.CKEditor.observer.observe(wrapper[0]);
                    }
                }
            });
            $(window).on('beforeunload.cms-ckeditor', function () {
                for (var editor_id in CMS.CKEditor.editors) {
                    if (CMS.CKEditor.editors.hasOwnProperty(editor_id) &&
                        CMS.CKEditor.editors[editor_id].changed) {
                        return 'Do you really want to leave this page?';
                    }
                }
            });
        },

        startInlineEditor: function (plugin_id, url) {
            var options;
            var settings = JSON.parse(document.getElementById('ck-cfg-' + plugin_id).textContent);
            var wrapper = $('.cms-plugin.cms-plugin-' + plugin_id);

            if (wrapper.data('ckeditor-initialized')) {
                return;
            }

            settings.plugin_id = plugin_id;
            settings.url = url;
            options = settings.options;
            delete settings.options;

            CMS.CKEditor.init(
                wrapper[0],
                'inline',
                options,
                settings,
                function (callback) {
                    callback.editor.element.removeAttribute('title');
                    callback.editor.on('change', function () {
                        CMS.CKEditor.editors[callback.editor.id].changed = true;
                    });
                    wrapper.on('blur.cms-ckeditor', function () {
                        setTimeout(function () {
                            // avoid save when clicking on editor dialogs or toolbar
                            if (!document.activeElement.classList.contains('cke_panel_frame') &&
                                !document.activeElement.classList.contains('cke_dialog_ui_button')) {
                                CMS.CKEditor.save_data(callback.editor.id);
                            }
                        }, 0);
                    });
                    wrapper.on('click.cms-ckeditor', function () {
                        // Highlight plugin in structure board
                        // Needs to be done manually, since the tooltip is suppressed and django CMS
                        // only automatically highlights the plugin if the tooltip is visible
                        CMS.CKEditor._highlight_Textplugin(plugin_id);
                    });
                    // store css that ckeditor loaded before save
                    CMS.CKEditor.storeCSSlinks();
                }
            );
        },

        save_data: function (editor_id, action) {
            var instance = CMS.CKEditor.editors[editor_id];

            if (instance && instance.changed) {
                CMS.CKEditor.storeCSSlinks();  // store css that ckeditor loaded before save
                var data = instance.editor.getData();

                CMS.API.Toolbar.showLoader();
                $.post(CMS.API.Helpers.updateUrlWithPath(instance.settings.url), {  // send changes
                    csrfmiddlewaretoken: CMS.config.csrf,
                    body: data,
                    _save: 'Save'
                }, function (response) {
                    instance.changed = false;
                    CMS.API.Toolbar.hideLoader();
                    if (action !== undefined) {
                        action(instance, response);
                    }
                    if (instance.child_changed) {
                        var scripts = $(response).find('script:not([src])').addClass('cms-ckeditor-result');

                        CMS.CKEditor._destroyAll();
                        scripts.each(function (item, element) {
                            $('body').append(element);
                        });
                    } else {
                        CMS.CKEditor.loadToolbar();
                    }
                }).fail(function (error) {
                    instance.changed = true;
                    CMS.API.Messages.open({
                        message: error.message,
                        error: true
                    });
                });
            }
        },

        loadToolbar: function () {
            if (CMS.settings && CMS.settings.version && this._toolbar_bug_version(CMS.settings.version)) {
                // Before django CMS 3.10 a bug prevents the toolbar to be loaded correctly
                // Refresh whole page instead
                CMS.API.Helpers.reloadBrowser();
            } else {
                CMS.API.StructureBoard._loadToolbar()
                    .done(function (newToolbar) {
                        CMS.API.Toolbar._refreshMarkup($(newToolbar).find('.cms-toolbar'));
                    })
                    .fail(CMS.API.Helpers.reloadBrowser);
            }
        },

        _toolbar_bug_version: function (version) {
            var parts = version.split('.');

            return parts[0] === '3' && parts[1].length < 2;
        },

        storeCSSlinks: function () {
            $("link[rel='stylesheet'][type='text/css'][href*='ckeditor']").each(
                function (index, element) {
                    if (!CMS.CKEditor.CSS.includes(element.href)) {
                        CMS.CKEditor.CSS.push(element.href);
                    }
                }
            );
        },


        // setup is called after ckeditor has been initialized
        setupAdmin: function (editor) {
            // auto maximize modal if alone in a modal
            var that = this;
            var win = window.parent || window;
            // 70px is hardcoded to make it more performant. 20px + 20px - paddings, 30px label height
            var TOOLBAR_HEIGHT_WITH_PADDINGS = 70;

            if (this._isAloneInModal(CMS.CKEditor.editors[editor.id].container)) {
                editor.resize('100%', win.CMS.$('.cms-modal-frame').height() - TOOLBAR_HEIGHT_WITH_PADDINGS);
                editor.execCommand('maximize');

                $(window).on('resize.ckeditor', function () {
                    that._repositionDialog(CKEDITOR.dialog.getCurrent(), win);
                }).trigger('resize.ckeditor');

                win.CMS.API.Helpers.addEventListener('modal-maximized modal-restored', function () {
                    try {
                        if (!$('.cke_maximized').length) {
                            editor.resize(
                                '100%',
                                win.CMS.$('.cms-modal-frame').height() - TOOLBAR_HEIGHT_WITH_PADDINGS
                            );
                            setTimeout(function () {
                                that._repositionDialog(CKEDITOR.dialog.getCurrent(), win);
                            }, 0);
                        }
                    } catch (e) {
                        // sometimes throws errors if modal with text plugin is closed too fast
                    }
                });
            }

            // add css tweks to the editor
            this.styles();
            this._resizing();
        },

        styles: function () {
            // add styling to source and fullscreen view
            $('.cke_button__maximize, .cke_button__source').parent()
                .css('margin-right', 0).parent()
                .css('float', 'right');
        },

        _resizing: function () {
            $(document).on('pointerdown', '.cms-ckeditor-resizer', function (e) {
                e.preventDefault();
                var event = new CMS.$.Event('mousedown');

                $.extend(event, {
                    screenX: e.originalEvent.screenX,
                    screenY: e.originalEvent.screenY
                });
                $(this).trigger(event);
            });
        },

        _isAloneInModal: function (container) {
            var body = container.closest('body');

            // return true if the ckeditor is alone in a modal popup
            return body.is('.app-djangocms_text_ckeditor.model-text');
        },

        /**
         * @method _repositionDialog
         * @private
         * @param {CKEDITOR.dialog} dialog instance
         */
        _repositionDialog: function (dialog) {
            var OFFSET = 80;

            if (!dialog) {
                return;
            }
            var size = dialog.getSize();
            var position = dialog.getPosition();
            var win = CKEDITOR.document.getWindow();
            var viewSize = win.getViewPaneSize();
            var winWidth = viewSize.width;
            var winHeight = viewSize.height;

            if (position.x < 0) {
                dialog.move(0, position.y);
                position.x = 0;
            }

            if (position.y < 0) {
                dialog.move(position.x, 0);
                position.y = 0;
            }

            if (position.y + size.height > winHeight) {
                dialog.resize(size.width, winHeight - position.y - OFFSET);
            }

            if (position.x + size.width > winWidth) {
                dialog.resize(winWidth - position.x, size.height);
            }
        },

        initAdminEditors: function () {
            window._cmsCKEditors = window._cmsCKEditors || [];
            var dynamics = [];
            var settings;
            var options;

            window._cmsCKEditors.forEach(function (editorConfig) {
                var elementId = 'ck-cfg-' + (editorConfig[1] ? editorConfig[1] : editorConfig[0]);

                settings = JSON.parse(document.getElementById(elementId).textContent);
                options = settings.options;
                delete settings.options;

                if (editorConfig[0].match(/__prefix__/)) {
                    dynamics.push(editorConfig);
                } else {
                    CMS.CKEditor.init(
                        document.getElementById(editorConfig[0]),
                        'admin',
                        options,
                        settings,
                        function (callback) {
                            return CMS.CKEditor.setupAdmin(callback.editor);
                        }
                    );
                }
            });

            $('.add-row a').on('click', function () {
                $('.CMS_CKEditor').each(function (i, el) {
                    var container = $(el);

                    if (container.data('ckeditor-initialized')) {
                        return;
                    }

                    var containerId = container.attr('id');

                    // in case there are multiple different inlines we need to check
                    // newly added one against all of them
                    dynamics.forEach(function (config) {
                        var selector = config[0].id;
                        var regex = new RegExp(selector.replace('__prefix__', '\\d+'));

                        if (containerId.match(regex)) {
                            CMS.CKEditor.init(
                                document.getElementById(containerId),
                                options,
                                settings
                            );
                        }
                    });
                });
            });
        },

        _highlight_Textplugin: function (pluginId) {
            var HIGHLIGHT_TIMEOUT = 10;

            var draggable = $('.cms-draggable-' + pluginId);
            var doc = $(document);
            var currentExpandmode = doc.data('expandmode');


            // expand necessary parents
            doc.data('expandmode', false);
            draggable
                .parents('.cms-draggable')
                .find('> .cms-dragitem-collapsable:not(".cms-dragitem-expanded") > .cms-dragitem-text')
                .each(function (i, el) {
                    $(el).triggerHandler(CMS.Plugin.click);
                });
            if (draggable.length > 0) {  // Expanded elements available
                setTimeout(function () {
                    doc.data('expandmode', currentExpandmode);
                });
                setTimeout(function () {
                    CMS.Plugin._highlightPluginStructure(draggable.find('.cms-dragitem:first'),
                        {successTimeout: 200, delay: 2000, seeThrough: true});
                }, HIGHLIGHT_TIMEOUT);
            }
        },

        _initAll: function () {
            CMS.CKEditor.touchdevice = 'ontouchstart' in window || navigator.msMaxTouchPoints;  // on touch device?
            if (!CMS.CKEditor.touchdevice) {  // no inline editing on touch devices to not interfere with scrolling
                CMS.CKEditor.initInlineEditors();
                $('div.cms a.cms-btn.cms-edit-toggle').show();
            } else {
                $('div.cms a.cms-btn.cms-edit-toggle').hide();
            }
            CMS.CKEditor.initAdminEditors();
        },

        _destroyAll: function () {
            for (var id in CMS.CKEditor.editors) {
                if (CMS.CKEditor.editors.hasOwnProperty(id)) {
                    CMS.CKEditor.editors[id].editor.destroy();
                    $(CMS.CKEditor.editors[id].container).off('.cms-ckeditor');
                    delete CMS.CKEditor.editors[id];
                }
            }
            $(window).off('.cms-ckeditor');
        },

        _resetInlineEditors: function () {
            CMS.CKEditor.CSS.forEach(function (stylefile) {
                if ($("link[href='" + stylefile + "']").length === 0) {
                    $('head').append($("<link rel='stylesheet' type='text/css' href='" + stylefile + "'>"));
                }
            });
            CMS.CKEditor._destroyAll();
            CMS.CKEditor._initAll();
        }
    };

    setTimeout(function init() {
        CMS.CKEditor._initAll();
    }, 0);
    $(window).on('cms-content-refresh', CMS.CKEditor._resetInlineEditors);
})(window.CMS.$, window.CMS);
