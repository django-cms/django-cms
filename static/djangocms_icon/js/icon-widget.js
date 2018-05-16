import $ from 'jquery';
import './icon-picker';

export default class IconWidget {
    constructor (element) {
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
            iconset: initialIconset,
            arrowNextIconClass: 'djangocms-icon-right',
            arrowPrevIconClass: 'djangocms-icon-left',
            inline: true
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
            var iconset = $(this).val();

            try {
                iconset = JSON.parse(iconset);
            } catch (e) {}

            iconPickerButton.iconpicker('setIconset', iconset);
        });

        // checkbox is shown if field is not required, switches visibility
        // of icon selection to on/off
        enableIconCheckbox.on('change', function () {
            if ($(this).prop('checked')) {
                widgets.removeClass('hidden');
                const val = iconPickerButton.data('bs.iconpicker').options.icon;

                if (val) {
                    iconPickerButton.find('input').val(val).trigger('change');
                }
            } else {
                widgets.addClass('hidden');
                iconPickerButton.find('input').val('').trigger('change');
            }
        }).trigger('change');
    }
}
