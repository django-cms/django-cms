(function ($) {
    if (CKEDITOR && CKEDITOR.plugins && CKEDITOR.plugins.registered && CKEDITOR.plugins.registered.cmsplugins) {
        return;
    }

    /**
     * Determine if we should return `div` or `span` based on the
     * plugin markup.
     *
     * @function getFakePluginElement
     * @private
     * @param {String} pluginMarkup valid html hopefully
     * @returns {String} div|span
     */
    function getFakePluginElement(pluginMarkup) {
        var innerTags = (pluginMarkup.match(/<([\S]*?)\s[\s\S]*?>/) || [0, false]).splice(1);

        var containsAnyBlockLikeElements = innerTags.some(function (tag) {
            return tag && CKEDITOR.dtd.$block[tag];
        });

        var fakeRealType = 'span';

        if (containsAnyBlockLikeElements) {
            fakeRealType = 'div';
        }

        return fakeRealType;
    }

    /**
     * @function replaceTagName
     * @private
     * @param {jQuery} elements
     * @param {String} tagName
     */
    function replaceTagName(elements, tagName) {
        elements.each(function (i, el) {
            var newElement;

            var element = $(el);

            newElement = $('<' + tagName + '>');

            // attributes
            $.each(el.attributes, function (index, attribute) {
                newElement.attr(attribute.nodeName, attribute.nodeValue);
            });

            // content
            newElement.html(element.html());

            element.replaceWith(newElement);
        });
    }

    CKEDITOR.plugins.add('cmsplugins', {

        // Register the icons. They must match command names.
        icons: 'cmsplugins',

        // The plugin initialization logic goes inside this method.
        init: function (editor) {
            var that = this;

            this.options = CMS.CKEditor.options.settings;
            this.editor = editor;

            /**
             * populated with _fresh_ child plugins
             */
            this.child_plugins = [];
            this.setupCancelCleanupCallback(this.options);

            // don't do anything if there are no plugins defined
            if (this.options === undefined || this.options.plugins === undefined) {
                return false;
            }

            this.setupDialog();

            // add the button
            this.editor.ui.add('cmsplugins', CKEDITOR.UI_PANELBUTTON, {
                toolbar: 'cms,0',
                label: this.options.lang.toolbar,
                title: this.options.lang.toolbar,
                className: 'cke_panelbutton__cmsplugins',
                modes: { wysiwyg: 1 },
                editorFocus: 0,

                panel: {
                    css: [CKEDITOR.skin.getPath('editor')].concat(that.editor.config.contentsCss),
                    attributes: { 'role': 'cmsplugins', 'aria-label': this.options.lang.aria }
                },

                // this is called when creating the dropdown list
                onBlock: function (panel, block) {
                    block.element.setHtml(that.editor.plugins.cmsplugins.setupDropdown());

                    var anchors = $(block.element.$).find('.cke_panel_listItem a');

                    anchors.bind('click', function (e) {
                        e.preventDefault();

                        that.addPlugin($(this), panel);
                    });
                }
            });

            // handle edit event via context menu
            if (this.editor.contextMenu) {
                this.setupContextMenu();
            }

            this.editor.addCommand('cmspluginsEdit', {
                exec: function () {
                    var element = that.getElementFromSelection();
                    var plugin = that.getPluginWidget(element);

                    if (plugin) {
                        that.editPlugin(plugin);
                    }
                }
            });

            // handle edit event on double click
            // if event is a jQuery event (touchend), than we mutate
            // event a bit so we make the payload similar to what ckeditor.event produces
            var handleEdit = function (event) {
                var element;

                if (event.type === 'touchend' || event.type === 'click') {
                    var cmsPluginNode = $(event.currentTarget).closest('cms-plugin')[0];

                    // pick cke_widget span
                    // eslint-disable-next-line new-cap
                    element = new CKEDITOR.dom.element(cmsPluginNode).getParent();

                    event.data = event.data || {};
                    // have to fake selection to be able to replace markup after editing
                    that.editor.getSelection().fake(element);
                }

                that.editor.execCommand('cmspluginsEdit');
            };

            this.editor.on('doubleclick', handleEdit);
            this.editor.on('instanceReady', function () {
                CMS.$('cms-plugin', CMS.$('iframe.cke_wysiwyg_frame')[0]
                    .contentWindow.document.documentElement).on('click touchend', handleEdit);
            });

            this.setupDataProcessor();
        },

        getElementFromSelection: function () {
            var selection = this.editor.getSelection();
            var element = selection.getSelectedElement() ||
                selection.getCommonAncestor().getAscendant('cms-plugin', true);

            return element;
        },

        getPluginWidget: function (element) {
            if (!element) {
                return null;
            }
            return element.getAscendant('cms-plugin', true) || element.findOne('cms-plugin');
        },

        setupDialog: function () {
            var that = this;
            var definition = function () {
                return {
                    title: '',
                    minWidth: 200,
                    minHeight: 200,
                    contents: [{
                        elements: [
                            {
                                type: 'html',
                                html: '<iframe style="position:static; width:100%; height:100%; border:none;" />'
                            }
                        ]
                    }],
                    onOk: function () {
                        var iframe = $(CKEDITOR.dialog.getCurrent().parts.contents.$).find('iframe').contents();
                        var iframeUrl = iframe[0].URL;

                        iframe.find('form').submit();

                        // catch the reload event and reattach
                        var reload = CMS.API.Helpers.reloadBrowser;

                        CMS.API.Helpers.reloadBrowser = function () {
                            CKEDITOR.dialog.getCurrent().hide();
                            var data = CMS.API.Helpers.dataBridge;
                            var addedChildPlugin = false;

                            if (iframeUrl.match(/add-plugin/)) {
                                addedChildPlugin = true;
                            }
                            // in case it's a fresh text plugin children don't have to be
                            // deleted separately
                            if (!that.options.delete_on_cancel && addedChildPlugin) {
                                that.child_plugins.push(data.plugin_id);
                            }

                            that.insertPlugin(data);

                            CMS.API.Helpers.reloadBrowser = reload;
                            return false;
                        };
                        return false;
                    }
                };
            };

            // set default definition and open dialog
            CKEDITOR.dialog.add('cmspluginsDialog', definition);
        },

        setupDropdown: function () {
            var tpl = '<div class="cke_panel_block">';

            // loop through the groups
            $.each(this.options.plugins, function (i, group) {
                // add template
                tpl += '<h1 class="cke_panel_grouptitle">' + group.group + '</h1>';
                tpl += '<ul role="presentation" class="cke_panel_list">';
                // loop through the plugins
                $.each(group.items, function (ii, item) {
                    tpl += '<li class="cke_panel_listItem"><a href="#" rel="' + item.type + '">' +
                        item.title + '</a></li>';
                });
                tpl += '</ul>';
            });

            tpl += '</div>';

            return tpl;
        },

        setupContextMenu: function () {
            var that = this;

            this.editor.addMenuGroup('cmspluginsGroup');
            this.editor.addMenuItem('cmspluginsItem', {
                label: this.options.lang.edit,
                icon: CMS.CKEditor.options.settings.static_url + '/ckeditor_plugins/cmsplugins/icons/cmsplugins.png',
                command: 'cmspluginsEdit',
                group: 'cmspluginsGroup'
            });

            this.editor.removeMenuItem('image');

            this.editor.contextMenu.addListener(function (element) {
                var plugin = that.getPluginWidget(element);

                if (plugin) {
                    return { cmspluginsItem: CKEDITOR.TRISTATE_OFF };
                }
            });
        },

        editPlugin: function (element) {
            var id = element.getAttribute('id');

            this.editor.openDialog('cmspluginsDialog');
            var body = CMS.$(document);

            // now tweak in dynamic stuff
            var dialog = CKEDITOR.dialog.getCurrent();

            dialog.resize(body.width() * 0.8, body.height() * 0.7); // eslint-disable-line no-magic-numbers
            $(dialog.getElement().$).addClass('cms-ckeditor-dialog');
            $(dialog.parts.title.$).text(this.options.lang.edit);

            var textPluginUrl = window.location.href;
            var path = encodeURIComponent(window.parent.location.pathname + window.parent.location.search);
            var childPluginUrl = textPluginUrl.replace(
                /(add-plugin|edit-plugin).*$/,
                'edit-plugin/' + id + '/?_popup=1&no_preview&cms_history=0&cms_path=' + path
            );

            $(dialog.parts.contents.$).find('iframe').attr('src', childPluginUrl)
                .bind('load', function () {
                    var contents = $(this).contents();

                    contents.find('body').addClass('ckeditor-popup');
                    contents.find('.submit-row').hide();
                    contents.find('#container').css({
                        'min-width': 0,
                        'padding': 0
                    });
                });
        },

        addPlugin: function (item, panel) {
            var that = this;

            // hide the panel
            panel.hide();

            this.editor.focus();
            this.editor.fire('saveSnapshot');

            // gather data
            var data = {
                placeholder_id: this.options.placeholder_id,
                plugin_type: item.attr('rel'),
                plugin_parent: this.options.plugin_id,
                plugin_language: this.options.plugin_language,
                cms_path: window.parent.location.pathname,
                cms_history: 0
            };

            that.addPluginDialog(item, data);
        },

        addPluginDialog: function (item, data) {
            var body = $(document);
            // open the dialog
            var selected_text = this.editor.getSelection().getSelectedText();

            this.editor.openDialog('cmspluginsDialog');

            // now tweak in dynamic stuff
            var dialog = CKEDITOR.dialog.getCurrent();

            dialog.resize(body.width() * 0.8, body.height() * 0.7); // eslint-disable-line no-magic-numbers
            $(dialog.getElement().$).addClass('cms-ckeditor-dialog');
            $(dialog.parts.title.$).text(this.options.lang.add);
            $(dialog.parts.contents.$).find('iframe').attr('src', this.options.add_plugin_url + '?' + $.param(data))
                .on('load.addplugin', function () {
                    var iframe = $(this);
                    var contents = iframe.contents();

                    contents.find('.submit-row').hide().end()
                        .find('#container').css('min-width', 0).css('padding', 0);

                    var inputs = contents.find('.js-ckeditor-use-selected-text');

                    if (!inputs.length) {
                        inputs = contents.find('#id_name');
                    }

                    if (!(inputs.val() && inputs.val().trim())) {
                        inputs.val(selected_text);
                    }

                    iframe.off('load.addplugin');
                });
        },

        insertPlugin: function (data) {
            var that = this;

            $.ajax({
                method: 'GET',
                url: that.options.render_plugin_url,
                data: {
                    token: that.options.action_token,
                    plugin: data.plugin_id
                }
            }).done(function (res) {
                that.editor.insertHtml(res, 'unfiltered_html');
                that.editor.fire('updateSnapshot');
            });
        },

        /**
         * Sets up cleanup requests. If the plugin itself or child plugin was created and then
         * creation was cancelled - we need to clean up created plugins.
         *
         * @method setupCancelCleanupCallback
         * @public
         * @param {Object} data plugin data
         */
        setupCancelCleanupCallback: function setupCancelCleanupCallback() {
            if (!window.parent || !window.parent.CMS || !window.parent.CMS.API || !window.parent.CMS.API.Helpers) {
                return;
            }
            var that = this;
            var CMS = window.parent.CMS;
            var cancelModalCallback = function cancelModalCallback(e, opts) {
                if (!that.options.delete_on_cancel && !that.child_plugins.length) {
                    return;
                }
                if (that.child_plugins.length) {
                    e.preventDefault();
                    CMS.API.Toolbar.showLoader();
                    var data = {
                        token: that.options.action_token
                    };

                    if (!that.options.delete_on_cancel) {
                        data.child_plugins = that.child_plugins;
                    }
                    $.ajax({
                        method: 'POST',
                        url: that.options.cancel_plugin_url,
                        data: data,
                        // use 'child_plugins' instead of default 'child_plugins[]'
                        traditional: true
                    }).done(function () {
                        CMS.API.Helpers.removeEventListener('modal-close.text-plugin-' + that.options.plugin_id);
                        opts.instance.close();
                    }).fail(function (res) {
                        CMS.API.Messages.open({
                            message: res.responseText + ' | ' + res.status + ' ' + res.statusText,
                            delay: 0,
                            error: true
                        });
                    });
                }
            };

            CMS.API.Helpers.addEventListener(
                'modal-close.text-plugin-' + that.options.plugin_id,
                cancelModalCallback
            );
        },

        setupDataProcessor: function () {
            var that = this;

            // priorities of callback execution, see http://docs.ckeditor.com/#!/api/CKEDITOR.editor-event-toHtml
            var BEFORE_PROCESSING_STARTED = 1;
            var BEFORE_MARKUP_IS_PARSED = 4;

            /**
             * This override is required for the inline plugins that have preceding space, because otherwise CKEditor
             * would remove that space while parsing
             * html.
             *
             * Ref: https://github.com/ckeditor/ckeditor-dev/blob/master/core/htmlparser/fragment.js#L484
             */
            CKEDITOR.htmlParser.element = CKEDITOR.tools.override(CKEDITOR.htmlParser.element, function (original) {
                return function (name, attributes) {
                    original.call(this, name, attributes);

                    if (name === 'cms-plugin' && attributes['data-cke-real-element-type'] === 'span') {
                        this._.isBlockLike = false;
                    }
                };
            });

            /**
             * @function isBlockLikeChildren
             * @public
             * @param {CKEDITOR.htmlParser.element} element
             * @returns {Boolean}
             */
            function isBlockLikeChildren(element) {
                return element.attributes && element.attributes['data-cke-real-element-type'] === 'div';
            }

            this.editor.dataProcessor.dataFilter.addRules(
                {
                    elements: {
                        span: function (element) {
                            if (CKEDITOR.plugins.widget.isParserWidgetWrapper(element)) {
                                var cmsPluginNode = element.getFirst();

                                if (isBlockLikeChildren(cmsPluginNode)) {
                                    // eslint-disable-next-line new-cap
                                    var newWrapper = new CKEDITOR.htmlParser.element(
                                        'div',
                                        $.extend({}, element.attributes)
                                    );

                                    that.editor.widgets.registered.cmswidget.inline = false;
                                    newWrapper.children = element.children;
                                    newWrapper.removeClass('cke_widget_inline');
                                    newWrapper.removeClass('cke_widget_force_block');
                                    newWrapper.addClass('cke_widget_block');
                                    cmsPluginNode.attributes['data-cke-real-element-type'] = 'div';

                                    return newWrapper;
                                }

                                that.editor.widgets.registered.cmswidget.inline = true;
                                cmsPluginNode.attributes['data-cke-real-element-type'] = 'span';
                            }
                            return element;
                        }
                    }
                },
                {
                    priority: 1,
                    applyToAll: true
                }
            );

            // need to update cms-plugin-nodes with fake "real type" so
            // ckeditor treats them as flow / phrasing elements correctly
            // + we check if plugin markup should be rendered or not
            this.editor.on('toHtml', function (e) {
                // now i have two problems
                var newMarkup = e.data.dataValue.replace(
                    /<cms-plugin(.*?)>([\s\S]*?)<\/cms-plugin>/gi,
                    function (all, attributes, pluginMarkup) {
                        var fakeRealType = getFakePluginElement(pluginMarkup);

                        if (attributes.match(/render-plugin=["']?false/gi)) {
                            return '<cms-plugin data-cke-real-element-type="' + fakeRealType + '" ' + attributes + '>' +
                                    '<' + fakeRealType + ' class="cms-ckeditor-plugin-label">' +
                                        attributes.replace(/[\s\S]*alt=["']([\s\S]*?)['"][\s\S]*/, '$1') +
                                    '</' + fakeRealType + '>' +
                                '</cms-plugin>';
                        }

                        return '<cms-plugin data-cke-real-element-type="' + fakeRealType + '" ' + attributes + '>' +
                            pluginMarkup +
                            '</cms-plugin>';
                    }
                );

                // in case we have a stale markup with <p> tag wrapped around
                // we want to avoid a situation where browser would try to unwrap the tags in a way that would
                // break the markup. what we do is we replace <cms-plugin> tags with divs if that is necessary,
                // unwrap them with jQuery (which uses browser mechanism) and then replace the divs back
                if (newMarkup.match(/<cms-plugin[^>]*(?=data-cke-real-element-type=\"div)/)) {
                    // eslint-disable-next-line max-len
                    var blockLevelPluginRegex = /<cms-plugin([^>]*(?=data-cke-real-element-type=\"div).*?>.*?<\/)cms-plugin>/g;

                    var unwrappedMarkup = newMarkup.replace(blockLevelPluginRegex, '<div$1div>');
                    // have to create a wrapper, otherwise we won't be able to return markup back
                    var unwrappedElementsWrapper = $(unwrappedMarkup).wrapAll('<div>').parent();
                    var wrappers = unwrappedElementsWrapper.find('div[data-cke-real-element-type="div"]');

                    replaceTagName(wrappers, 'cms-plugin');

                    newMarkup = unwrappedElementsWrapper.html();
                }

                e.data.dataValue = newMarkup;
            }, null, null, BEFORE_MARKUP_IS_PARSED);

            this.editor.on('toHtml', function () {
                // reset widgets to inline again to avoid creating block-level inline widget
                if (that.editor.widgets && that.editor.widgets.registered && that.editor.widgets.registered.cmswidget) {
                    that.editor.widgets.registered.cmswidget.inline = true;
                }
            }, null, null, BEFORE_PROCESSING_STARTED);
        }
    });
})(CMS.$);
