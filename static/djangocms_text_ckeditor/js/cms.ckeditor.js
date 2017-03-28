(function ($) {
    // CMS.$ will be passed for $
    $(function () {
        /**
         * CMS.CKEditor
         *
         * @description: Adds cms specific plugins to CKEditor
         */
        CMS.CKEditor = {

            options: {
                // ckeditor default settings, will be overwritten by CKEDITOR_SETTINGS
                language: 'en',
                skin: 'moono',
                toolbar_CMS: [
                    ['Undo', 'Redo'],
                    ['cmsplugins', 'cmswidget', '-', 'ShowBlocks'],
                    ['Format', 'Styles'],
                    ['TextColor', 'BGColor', '-', 'PasteText', 'PasteFromWord'],
                    ['Maximize', ''],
                    '/',
                    ['Bold', 'Italic', 'Underline', '-', 'Subscript', 'Superscript', '-', 'RemoveFormat'],
                    ['JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
                    ['HorizontalRule'],
                    ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Table'],
                    ['Source']
                ],
                toolbar_HTMLField: [
                    ['Undo', 'Redo'],
                    ['ShowBlocks'],
                    ['Format', 'Styles'],
                    ['TextColor', 'BGColor', '-', 'PasteText', 'PasteFromWord'],
                    ['Maximize', ''],
                    '/',
                    ['Bold', 'Italic', 'Underline', '-', 'Subscript', 'Superscript', '-', 'RemoveFormat'],
                    ['JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
                    ['HorizontalRule'],
                    ['Link', 'Unlink'],
                    ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Table'],
                    ['Source']
                ],

                allowedContent: true,
                toolbarCanCollapse: false,
                removePlugins: 'resize',
                extraPlugins: ''
            },

            init: function (container, options, settings) {
                if ($('#' + container).length > 0) {
                    this.container = $('#' + container);
                    // add additional settings to options
                    this.options.toolbar = settings.toolbar;
                    this.options = $.extend(false, {
                        settings: settings
                    }, this.options, options);

                    // add extra plugins that we absolutely must have
                    this.options.extraPlugins = this.options.extraPlugins +=
                        ',cmsplugins,cmswidget,cmsresize,widget';

                    document.createElement('cms-plugin');
                    CKEDITOR.dtd['cms-plugin'] = CKEDITOR.dtd.div;
                    CKEDITOR.dtd.$inline['cms-plugin'] = 1;
                    // has to be here, otherwise extra <p> tags appear
                    CKEDITOR.dtd.$nonEditable['cms-plugin'] = 1;
                    CKEDITOR.dtd.$transparent['cms-plugin'] = 1;
                    CKEDITOR.dtd.body['cms-plugin'] = 1;

                    // add additional plugins (autoloads plugins.js)
                    CKEDITOR.skin.addIcon('cmsplugins', settings.static_url +
                        '/ckeditor_plugins/cmsplugins/icons/cmsplugins.png');

                    // render ckeditor
                    this.editor = CKEDITOR.replace(container, this.options);

                    // add additional styling
                    CKEDITOR.on('instanceReady', $.proxy(CMS.CKEditor, 'setup'));
                }
            },

            // setup is called after ckeditor has been initialized
            setup: function () {
                // auto maximize modal if alone in a modal
                var that = this;
                var win = window.parent || window;
                // 70px is hardcoded to make it more performant. 20px + 20px - paddings, 30px label height
                var TOOLBAR_HEIGHT_WITH_PADDINGS = 70;

                if (this._isAloneInModal()) {
                    that.editor.resize('100%', win.CMS.$('.cms-modal-frame').height() - TOOLBAR_HEIGHT_WITH_PADDINGS);
                    this.editor.execCommand('maximize');

                    $(window).on('resize.ckeditor', function () {
                        that._repositionDialog(CKEDITOR.dialog.getCurrent(), win);
                    }).trigger('resize.ckeditor');

                    win.CMS.API.Helpers.addEventListener('modal-maximized modal-restored', function () {
                        try {
                            if (!$('.cke_maximized').length) {
                                that.editor.resize(
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

            _isAloneInModal: function () {
                var body = this.container.closest('body');

                // return true if the ckeditor is alone in a modal popup
                return body.is('.app-djangocms_text_ckeditor.model-text') || // Django >= 1.7
                    body.is('.djangocms_text_ckeditor-text'); // Django < 1.7
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
            }
        };
    });
})(CMS.$);
