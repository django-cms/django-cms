/*
 * Copyright https://github.com/divio/django-cms
 */

// #############################################################################
// ALDRYN-BOOTSTRAP3
(function ($) {
    'use strict';

    // shorthand for jQuery(document).ready();
    $(function () {
        /**
         * Handles all reauired JavaScript for the aldryn-bootstrap3 addon.
         *
         * @class bootstrap3
         */
        var bootstrap3 = {

            /**
             * Widget used in aldryn_bootstrap3/widgets/context.html.
             * Provides a button group list and enables the user
             * to select one of the choices.
             *
             * @method contextWidget
             * @param {jQuery} element context element to render
             */
            contextWidget: function contextWidget(element) {
                var data = element.data();
                var fieldName = data.context;
                var contextInputs = element.find('.js-btn-group-context-' + fieldName + ' label');
                var selectedContextInput;

                contextInputs.find('input').each(function (index, item) {
                    var input = $(item);
                    var label = input.parent();
                    var element = contextInputs.find('input[value="default"]');

                    // initial active state
                    if (input.prop('checked')) {
                        selectedContextInput = input;
                        label.addClass('active');
                    }

                    if (!selectedContextInput) {
                        selectedContextInput = element;
                    }

                    // set color context
                    if (item.value && item.value !== 'muted') {
                        label.addClass('btn btn-' + item.value);
                    } else {
                        label.addClass('btn btn-default');
                    }

                    // set active states
                    label.on('click', function () {
                        var input = $(this).find('input');

                        selectedContextInput.prop('checked', false);
                        input.prop('checked', true).trigger('change');

                        selectedContextInput = input;
                    });

                });
            },

            /**
             * Widget used in aldryn_bootstrap3/widgets/icon.html.
             * Renders a selectable icon dropdown where you can choose
             * from font-awesome or glyphicons depending on your settings.
             *
             * @method iconWidget
             * @param {jQuery} element context element to render
             */
            iconWidget: function iconWidget(element) {
                var data = element.data();
                var name = data.name;
                var iconPicker = element.find('.js-icon-' + name + ' .js-icon-picker');
                var iconSet = element.find('.js-icon-' + name + ' .js-iconset');
                var enableIconCheckbox = element.find('.js-icon-' + name + ' .js-icon-enable');
                var widgets = element.find('.js-icon-' + name + ' .js-icon-widgets');
                var iconPickerButton = iconPicker.find('button');
                var initialValue = iconPickerButton.data('icon');
                var initialIconset = iconSet.find('option[data-prefix=' + data.iconset + ']').attr('value');

                try {
                    // in case custom iconset is used
                    initialIconset = JSON.parse(initialIconset);
                } catch (e) {
                }

                // initialize bootstrap iconpicker functionality
                iconPickerButton.iconpicker({
                    arrowClass: 'btn-default',
                    icon: initialValue,
                    iconset: initialIconset
                });

                // show label instead of dropdown if there is only one choice available
                if (iconSet.find('option').length === 1) {
                    iconSet.hide();
                    iconSet.parent().prepend('' +
                        '<label class="form-control-static">' +
                            iconSet.find('option').text() +
                        '</label>');
                }

                // set correct iconset when switching the font via dropdown
                iconSet.on('change', function () {
                    iconPickerButton.iconpicker('setIconset', $(this).val());
                });

                // checkbox is shown if field is not required, switches visibility
                // of icon selection to on/off
                enableIconCheckbox.on('change', function () {
                    if ($(this).prop('checked')) {
                        widgets.removeClass('hidden');
                        iconPicker.trigger('change');
                    } else {
                        widgets.addClass('hidden');
                        iconPickerButton.find('input').val('');
                    }
                }).trigger('change');
            },

            /**
             * Renders the preview on top of the button/ling widget page.
             * Only one button widget allowed per page.
             *
             * @method buttonPreview
             */
            buttonPreview: function buttonPreview() {
                var container = $('.aldryn-bootstrap3-button');
                var previewBtn = container.find('.js-preview-btn .js-button');
                var previewBtnText = previewBtn.find('span');
                var defaultBtnText = previewBtn.text();
                var typeState = '';
                var blockClass = '';
                var sizeClass = '';
                var timer = function () {};
                var timeout = 50;

                // helper references
                var labelContext = $('#id_label');
                var typeContext = $('#id_type_0, #id_type_1');
                var sizeContext = $('.field-btn_size');
                var btnContext = $('.field-btn_context');
                var colorContext = $('.field-txt_context');
                var blockContext = $('.field-btn_block');
                var iconContext = $('.js-icon-picker button');

                // attach event to the label
                labelContext.on('keydown', function () {
                    clearTimeout(timer);
                    timer = setTimeout(function () {
                        updatePreview({
                            type: 'text',
                            text: labelContext.val()
                        });
                    }, timeout);
                }).trigger('keydown');

                // attach event to the link/button switch
                typeContext.on('change', function () {
                    updatePreview({
                        type: 'markup',
                        context: $(this).val()
                    });
                });

                // handle button context selection
                // autotrigger will be handled by link/button switcher
                btnContext.find('label').on('click', function () {
                    updatePreview({
                        type: 'context',
                        cls: cleanClass($(this).attr('class'))
                    });
                });

                // handle text color button context selection
                colorContext.find('label').on('click', function () {
                    updatePreview({
                        type: 'context',
                        cls: cleanClass($(this).attr('class'))
                    });
                });

                // handle block checkbox
                blockContext.find('input').on('change', function () {
                    updatePreview({
                        type: 'block',
                        state: $(this).prop('checked')
                    });
                });

                // handle size selection
                sizeContext.find('label').on('click', function () {
                    updatePreview({
                        type: 'size',
                        cls: cleanClass($(this).attr('class'))
                    });
                });

                // handle icon picker
                iconContext.on('change', function () {
                    var el = $(this);
                    if (el.attr('name') === 'icon_left') {
                        // icon left alignment
                        previewBtn.find('.pre').attr('class', 'pre ' + el.find('i').attr('class'));
                    } else {
                        // icon right alignment
                        previewBtn.find('.post').attr('class', 'post ' + el.find('i').attr('class'));
                    }
                }).trigger('change');

                // control visibility of icons
                $('#id_icon_left').on('change', function () {
                    if ($(this).is(':checked')) {
                        previewBtn.find('.pre').show();
                    } else {
                        previewBtn.find('.pre').hide();
                    }
                }).trigger('change');

                $('#id_icon_right').on('change', function () {
                    if ($(this).is(':checked')) {
                        previewBtn.find('.post').show();
                    } else {
                        previewBtn.find('.post').hide();
                    }
                }).trigger('change');

                // certain elements can only be loaded after a timeout
                setTimeout(function () {
                    blockContext.find('input:checked').trigger('change');
                    typeContext.filter(':checked').trigger('change');
                    sizeContext.find('input:checked').parent().trigger('click');
                }, 0);

                // every event fires updatePreview passing in arguments what
                // has to be done
                function updatePreview(obj) {
                    // handle "label" inputs
                    if (obj.type === 'text') {
                        if (obj.text !== '') {
                            previewBtnText.text(obj.text);
                        } else {
                            previewBtnText.text(defaultBtnText);
                        }
                    }

                    // handle link/button selection which hides/shows text context
                    if (obj.type === 'markup') {
                        if (obj.context === 'lnk') {
                            typeState = obj.context;
                            blockContext.hide();
                            btnContext.hide();
                            colorContext.show();
                            colorContext.find('label.active').trigger('click');
                        } else {
                            typeState = obj.context;
                            blockContext.show();
                            colorContext.hide();
                            btnContext.show();
                            btnContext.find('label.active').trigger('click');
                        }
                    }

                    // update context
                    if (obj.type === 'context') {
                        if (typeState === 'lnk') {
                            previewBtn.attr('class', 'text text-' + obj.cls + blockClass + sizeClass);
                        } else {
                            previewBtn.attr('class', 'btn btn-' + obj.cls + blockClass + sizeClass);
                        }
                    }

                    // change block type
                    if (obj.type === 'block') {
                        if (obj.state) {
                            blockClass = ' btn-block';
                            previewBtn.addClass(blockClass);
                        } else {
                            blockClass = '';
                            previewBtn.removeClass('btn-block');
                        }
                    }

                    // change text size
                    if (obj.type === 'size') {
                        if ($('#id_type_0').is('checked')) {
                            sizeClass = ' text-' + obj.cls;
                        } else {
                            sizeClass = ' btn-' + obj.cls;
                        }
                        previewBtn.removeClass('text-lg text-md text-sm text-xs');
                        previewBtn.removeClass('btn-lg btn-md btn-sm btn-xs');
                        previewBtn.addClass(sizeClass);
                    }
                }

                // make sure we only pass the required class argument
                function cleanClass(cls) {
                    cls = cls
                        .replace('btn btn-', '')
                        .replace('active', '')
                        .replace('default ', '')
                        .replace('text-', '')
                        .replace(' ', '');
                    return cls;
                }

            },

            /**
             * Widget used in aldryn_bootstrap3/widgets/size.html.
             * Provides the choice to select the size of the element.
             * It can large, medium, small or extra small
             *
             * @method sizeWidget
             * @param {jQuery} element context element to render
             */
            sizeWidget: function sizeWidget(element) {
                var sizesInputs = element.find('label input');
                var selectedSizesInput;

                sizesInputs.each(function (index, item) {
                    var input = $(item);
                    var label = input.parent();

                    // Initial active state
                    if (input.prop('checked')) {
                        selectedSizesInput = input;
                        label.addClass('active');
                    }

                    // Set sizes
                    label.addClass('btn btn-default text-' + item.value);

                    // Add icon
                    $('<span class="glyphicon glyphicon-record"></span>')
                        .insertAfter(input);

                    // Set active states
                    label.on('click', function () {
                        var input = $(this).find('input');

                        selectedSizesInput.prop('checked', false);
                        input.prop('checked', true);

                        selectedSizesInput = input;
                    });

                });
            },

            /**
             * Widget used in aldryn_bootstrap3/widgets/responsive.html and
             * aldryn_bootstrap3/widgets/responsive_print.html.
             * Allows to show or hide certain elements depending on the
             * viewport size.
             *
             * @method responsiveWidget
             * @param {jQuery} element context element to render
             */
            responsiveWidget: function responsiveWidget(element) {
                var currentChoice = [];
                var inputElement = element.find('textarea');
                var choiceElements = element.find('.js-responsive-choice');
                var configElement = element.find('.js-responsive-config');
                var configElementDropdown = element.find('.js-responsive-config-dropdown');
                var value = inputElement.val();

                // remove block and inline additions
                function getCleanCSS(string) {
                    var tmp = string.split(' ');

                    tmp.forEach(function (item, index) {
                        tmp[index] = tmp[index].replace('-block', '');
                        tmp[index] = tmp[index].replace('-inline', '');
                    });

                    return tmp;
                }

                // get the different states, up to four
                function getChoice() {
                    // tmpChoices represent the active states of:
                    // ------------------------
                    // XS | SM | MD | LG | Type
                    // x    x    x    x    choice (0 = off, 1 = on)
                    // visible-xs | visible-sm | visible-md | visible-lg
                    var tmpChoices = [0, 0, 0, 0];
                    var tmp = inputElement.val();

                    tmp = getCleanCSS(tmp);

                    // loop through items
                    tmp.forEach(function (item) {
                        switch (item) {
                            case 'visible-xs':
                                tmpChoices[0] = 1;
                                break;
                            case 'visible-sm':
                                tmpChoices[1] = 1;
                                break;
                            case 'visible-md':
                                tmpChoices[2] = 1;
                                break;
                            case 'visible-lg':
                                tmpChoices[3] = 1;
                                break;
                            case 'visible-print':
                                tmpChoices[0] = 1;
                                break;
                            default:
                                break;
                        }
                    });

                    return tmpChoices;
                }

                // get the dropdown config
                function getConfig() {
                    var tmpConfig = 0;
                    var tmpCls = inputElement.val().split(' ');
                    var tmpVal = tmpCls[0].split('-');

                    if (tmpVal.length === 3) {
                        switch (tmpVal[2]) {
                            case 'block':
                                tmpConfig = 1;
                                break;
                            case 'inline':
                                tmpConfig = 2;
                                break;
                            default:
                                break;
                        }
                    // if its longer then 4 it's inline-block
                    } else if (tmpVal.length === 4) {
                        tmpConfig = 3;
                    }

                    return tmpConfig;
                }

                // general update function for the UI
                function update(choices, config) {
                    var cls = [];
                    currentChoice = choices;

                    choices.forEach(function (choice, index) {
                        if (choice) {
                            var tmp = choiceElements.eq(index).data('cls');

                            // in case of print don't store undefined values
                            if (tmp === undefined) {
                                return;
                            }

                            switch(config) {
                                case 1:
                                    tmp = tmp + '-block';
                                    break;
                                case 2:
                                    tmp = tmp + '-inline';
                                    break;
                                case 3:
                                    tmp = tmp + '-inline-block';
                                    break;
                                default:
                                    break;
                            }
                            cls.push(tmp);
                        }
                    });

                    inputElement.val(cls.join(' '));

                    updateConfig(choices, config);
                }

                // config update function for the UI
                function updateConfig(choices, config) {
                    // update settings
                    var els = configElementDropdown.find('li');

                    // update choices
                    choices.forEach(function (choice, index) {
                        // reset the element
                        choiceElements.eq(index)
                            .removeClass('btn-default')
                            .removeClass('btn-danger')
                            .removeClass('btn-success')
                            .find('.js-on, .js-off').addClass('hidden')
                        if (choice) {
                            choiceElements.eq(index)
                                .addClass('btn-success')
                                .find('.js-on').removeClass('hidden');
                        } else {
                            choiceElements.eq(index)
                                .addClass('btn-danger')
                                .find('.js-off').removeClass('hidden');
                        }
                    });

                    // update dropdown
                    els.removeClass('active').eq(config).addClass('active');
                    configElement.find('.text').text(els.eq(config).text());
                }

                // attach event handler to size buttons
                choiceElements.on('click', function (e) {
                    e.preventDefault();

                    var choiceIndex = choiceElements.index(this);
                    var configIndex = configElementDropdown.find('li')
                        .index(configElementDropdown.find('li.active'));

                    if (currentChoice[choiceIndex] >= 1) {
                        currentChoice[choiceIndex] = 0;
                    } else {
                        currentChoice[choiceIndex] = 1;
                    }

                    update(currentChoice, configIndex)
                });

                // attach event handler to config button
                configElementDropdown.find('a').on('click', function(e) {
                    e.preventDefault();

                    var configIndex = configElementDropdown.find('a').index(this);

                    update(currentChoice, configIndex);
                });

                // set initial state from current values
                update(getChoice(), getConfig());
            },

            /**
             * Plugin used in aldryn_bootstrap3/plugins/column and
             * aldryn_bootstrap3/plugins/row.
             *
             * @method rowColumnPlugin
             */
            rowColumnPlugin: function rowColumnPlugin() {
                var container = $('.aldryn-bootstrap3-grid');
                var formRows = container.find('.form-row');
                var fieldBoxes = container.find('.field-box');
                var form = $('#bootstrap3rowplugin_form');
                var tpl = $('<span class="form-row-icon fa fa-fw"></span>');

                // set tooltips and labels
                fieldBoxes.each(function (index, item) {
                    var el = $(item);
                    var tooltip = el.find('.help');
                    var label = el.find('label');
                    var labelText = label.text();

                    label.html(labelText.replace(':', ''));

                    // only create tooltip if one is present
                    if (tooltip.length) {
                        el.append('' +
                            '<span class="fa fa-question-circle" ' +
                            '   data-toggle="tooltip" ' +
                            '   data-placement="right" ' +
                            '   title="' + tooltip.text() + '">' +
                            '</span>');
                    }
                });

                formRows.each(function (index, item) {
                    var el = $(item);
                    // set fieldbox icons
                    if (el.hasClass('field-create_xs_col')) {
                        el.prepend(tpl.clone().addClass('fa-mobile'));
                    }
                    if (el.hasClass('field-create_sm_col')) {
                        el.prepend(tpl.clone().addClass('fa-tablet'));
                    }
                    if (el.hasClass('field-create_md_col')) {
                        el.prepend(tpl.clone().addClass('fa-laptop'));
                    }
                    if (el.hasClass('field-create_lg_col')) {
                        el.prepend(tpl.clone().addClass('fa-desktop'));
                    }
                    if (el.hasClass('field-create')) {
                        el.prepend(tpl.clone().addClass('fa-columns text-primary'));
                    }
                });

                // initialize tooltip
                $('[data-toggle="tooltip"]').tooltip();

                // browser validation gets in the way of the ajax
                // form submission from django-cms
                form.attr('novalidate', 'novalidate');
            },

            /**
             * Plugin used in aldryn_bootstrap3/plugins/label.
             *
             * @method labelPlugin
             */
            labelPlugin: function labelPlugin() {
                var container = $('.aldryn-bootstrap3-label');
                var previewBtn = container.find('.js-label-preview span');
                var defaultBtnText = previewBtn.text();
                var timer = function () {};
                var timeout = 50;

                // helper references
                var labelContext = $('#id_label');
                var btnContext = $('.field-context');

                // attach event to the label
                labelContext.on('keydown', function () {
                    clearTimeout(timer);
                    timer = setTimeout(function () {
                        updatePreview({
                            type: 'text',
                            text: labelContext.val()
                        });
                    }, timeout);
                }).trigger('keydown');

                // handle button context selection
                // autotrigger will be handled by link/button switcher
                btnContext.find('label').on('click', function () {
                    updatePreview({
                        type: 'context',
                        cls: cleanClass($(this).attr('class'))
                    });
                });

                // initial state
                btnContext.find('label.active').trigger('click');

                // every event fires updatePreview passing in arguments what
                // has to be done
                function updatePreview(obj) {
                    // handle "label" inputs
                    if (obj.type === 'text') {
                        if (obj.text !== '') {
                            previewBtn.text(obj.text);
                        } else {
                            previewBtn.text(defaultBtnText);
                        }
                    }

                    // update context
                    if (obj.type === 'context') {
                        previewBtn.attr('class', 'label label-' + obj.cls);
                    }
                }

                // make sure we only pass the required class argument
                function cleanClass(cls) {
                    cls = cls
                        .replace('btn btn-', '')
                        .replace('active', '')
                        .replace('text-', '')
                        .replace(' ', '');
                    return cls;
                }
            }
        };

        // auto initialize widgets
        if ($('.aldryn-bootstrap3-context').length) {
            $('.aldryn-bootstrap3-context').each(function () {
                bootstrap3.contextWidget($(this));
            });
        }
        if ($('.aldryn-bootstrap3-icon').length) {
            $('.aldryn-bootstrap3-icon').each(function () {
                bootstrap3.iconWidget($(this));
            });
        }
        if ($('.aldryn-bootstrap3-button').length) {
            bootstrap3.buttonPreview();
        }
        if ($('.js-btn-group-sizes').length) {
            $('.js-btn-group-sizes').each(function () {
                bootstrap3.sizeWidget($(this));
            });
        }
        if ($('.js-aldryn-bootstrap3-responsive').length) {
            $('.js-aldryn-bootstrap3-responsive').each(function () {
                bootstrap3.responsiveWidget($(this));
            });
        }
        // auto initialize plugins
        if ($('.aldryn-bootstrap3-grid').length) {
            bootstrap3.rowColumnPlugin();
        }
        if ($('.aldryn-bootstrap3-label').length) {
            bootstrap3.labelPlugin();
        }
    });
})(window.jQuery || django.jQuery);
