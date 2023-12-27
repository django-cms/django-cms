(function ($) {
    if (CKEDITOR && CKEDITOR.plugins && CKEDITOR.plugins.registered && CKEDITOR.plugins.registered.cmswidget) {
        return;
    }

    /**
     * Returns the focused widget, if of the type specific for this plugin.
     * If no widget is focused, `null` is returned.
     *
     * @param {CKEDITOR.editor} editor
     * @returns {CKEDITOR.plugins.widget|null} widget
     */
    function getSelectedWidget(editor) {
        var widget = editor.widgets.focused;

        if (widget && widget.name === 'cmswidget') {
            return widget;
        }

        widget = editor.widgets.selected;

        if (widget && widget.length) {
            var index = widget.findIndex(function (w) {
                return w.name === 'cmswidget';
            });

            if (index !== -1) {
                return widget[index];
            }
        }

        return null;
    }

    /**
     * Block / inline-but-block widgets can't be aligned properly
     * because CKEDITOR unwraps them and widget markup is then injected incorrectly
     * into resulting markup. This is not the complete solution, but this is what we have.
     *
     * @param {CKEDITOR.plugins.widget} widget widget
     * @returns {Boolean}
     */
    function canWidgetBeAligned(widget) {
        if (widget.inline) {
            if (CMS.$(widget.wrapper.$).hasClass('cke_widget_wrapper_force_block')) {
                return false;
            }

            return true;
        }

        return false;
    }

    var alignCommandIntegrator = function (editor) {
        var execCallbacks = [];

        return function (value) {
            var command = editor.getCommand('justify' + value);

            if (!command) {
                return;
            }

            execCallbacks.push(function () {
                command.refresh(editor, editor.elementPath());
            });

            command.on('exec', function (e) {
                var widget = getSelectedWidget(editor);

                if (widget) {
                    var enabled = canWidgetBeAligned(widget);

                    if (!enabled) {
                        // Once the widget changed its align, all the align commands
                        // must be refreshed: the event is to be cancelled.
                        for (var i = execCallbacks.length; i--;) {
                            execCallbacks[i]();
                        }

                        e.cancel();
                    }
                }
            });

            command.on('refresh', function (e) {
                var widget = getSelectedWidget(editor);

                if (!widget) {
                    return;
                }

                var enabled = canWidgetBeAligned(widget);

                // Don't allow justify commands when widget alignment is disabled
                if (!enabled) {
                    this.setState(CKEDITOR.TRISTATE_DISABLED);
                    e.cancel();
                }
            });
        };
    };

    CKEDITOR.plugins.add('cmswidget', {
        requires: 'widget',
        onLoad: function () {
            CKEDITOR.addCss(
                // when widget contents are inline,
                // but have block-level css
                '.cke_widget_wrapper_force_block{' +
                    'display:block!important;' +
                '}' +
                // empty elements focus outline
                '.cke_widget_block>.cke_widget_element{' +
                    'display:block!important;' +
                '}' +
                'span.cms-ckeditor-plugin-label{' +
                    'display: inline-block !important;' +
                    'padding-left: 8px;' +
                    'padding-right: 8px;' +
                '}' +
                '.cms-ckeditor-plugin-label{' +
                    'background: black;' +
                    'color: white;' +
                    'text-align: center;' +
                    'border-radius: 3px;' +
                    'height: 24px;' +
                    'line-height: 24px;' +
                    'font-size: 14px !important;' +
                '}'
            );
        },

        init: function (editor) {
            this.addWidgetDefinition(editor);
        },

        afterInit: function (editor) {
            // Integrate with align commands (justify plugin).
            var integrate = alignCommandIntegrator(editor);

            ['left', 'right', 'center', 'block'].forEach(integrate);
        },

        addWidgetDefinition: function (editor) {
            editor.widgets.add('cmswidget', {
                button: 'CMS Plugin',

                template:
                    '<cms-plugin style="unset: all">' +
                    '</cms-plugin>',

                allowedContent: 'cms-plugin',
                disallowedContent: 'cms-plugin{float}',

                requiredContent: 'cms-plugin',

                upcast: function (element) {
                    return element.name === 'cms-plugin';
                },

                init: function () {
                    var contents = $(this.element.$).children();
                    var displayProp = contents.css('display') || '';

                    if (!displayProp.includes('inline')) {
                        this.wrapper.addClass('cke_widget_wrapper_force_block');
                    }
                }
            });
        }
    });
})(CMS.$);
