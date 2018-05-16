import $ from 'jquery';

import 'bootstrap-sass/assets/javascripts/bootstrap/transition';
import 'bootstrap-sass/assets/javascripts/bootstrap/tooltip';
import 'bootstrap-sass/assets/javascripts/bootstrap/popover'

import './libs/iconset/iconset-fontawesome-all.js';
import './libs/bootstrap-iconpicker';

var staticUrl = '/static/';

try {
    staticUrl = window.top.CMS.config.urls.static;
} catch (e) {}

function override(originalFunction, functionBuilder) {
    var newFn = functionBuilder(originalFunction);

    newFn.prototype = originalFunction.prototype;
    return newFn;
}

// so if you want to use an iconset that uses modern svg inlining,
// you have to provide your own custom iconset similar to this:
// {
//     "svg": true,
//     "spritePath": "sprites/icons.svg",
//     "iconClass": "svg-icon",
//     "iconClassFix": "svg-icon-",
//     "icons": [
//         ...
//     ]
// }
$.fn.iconpicker.Constructor.prototype.select = override($.fn.iconpicker.Constructor.prototype.select, function (originalSelect) {
    return function(icon) {
        if (this.options.iconset !== '_custom' || !$.fn.iconpicker.Constructor.ICONSET._custom ||
            !$.fn.iconpicker.Constructor.ICONSET._custom.svg) {
            this.$element.find('i').html('');
            return originalSelect.call(this, icon);
        }

        var op = this.options;
        var el = this.$element;
        op.selected = $.inArray(icon, op.icons);
        if (op.selected === -1) {
            op.selected = 0;
            icon = op.icons[op.selected];
        }
        if (icon !== '' && op.selected >= 0) {
            op.icon = icon;
            if (op.inline === false) {
                var v = op.icons[op.selected];

                el.find('input').val(icon);
                el
                    .find('i')
                    .attr('class', '')
                    .html(
                        '<span data-svg="true" class="' + op.iconClass + ' ' + v + '">' +
                            '<span class="djangocms-svg-icon ' + op.iconClass + ' ' + v + '">' +
                                (op.spritePath ? (
                                '<svg role="presentation">' +
                                '<use xlink:href="' + staticUrl + op.spritePath + '#' + v + '"></use></svg>' ) : '') +
                            '</span>' +
                        '</span>'
                    );
            }
            if (icon === op.iconClassFix) {
                el.trigger({ type: 'change', icon: 'empty' });
            } else {
                el.trigger({ type: 'change', icon: icon });
            }
            op.table.find('button.' + op.selectedClass).removeClass(op.selectedClass);
        }
    };
});

$.fn.iconpicker.Constructor.prototype.updateIcons = override($.fn.iconpicker.Constructor.prototype.updateIcons, function (originalUpdateIcons) {
    return function(page) {
        if (this.options.iconset !== '_custom' || !$.fn.iconpicker.Constructor.ICONSET._custom ||
            !$.fn.iconpicker.Constructor.ICONSET._custom.svg) {
            return originalUpdateIcons.call(this, page);
        }
        var op = this.options;
        var tbody = op.table.find('tbody').empty();
        var offset = (page - 1) * this.totalIconsPerPage();
        var length = op.rows;
        if (op.rows === 0) {
            length = op.icons.length;
        }
        for (var i = 0; i < length; i++) {
            var tr = $('<tr></tr>');
            for (var j = 0; j < op.cols; j++) {
                var pos = offset + i * op.cols + j;
                var btn = $('<button class="btn ' + op.unselectedClass + ' btn-icon"></button>').hide();
                if (pos < op.icons.length) {
                    var v = op.icons[pos];
                    btn
                        .val(v)
                        .attr('title', v)
                        .append(
                            '<span class="djangocms-svg-icon ' + op.iconClass + ' ' + v + '">' +
                                (op.spritePath ? (
                                '<svg role="presentation">' +
                                '<use xlink:href="' + staticUrl + op.spritePath + '#' + v + '"></use></svg>' ) : '') +
                            '</span>'
                        )
                        .show();
                    if (op.icon === v) {
                        btn.addClass(op.selectedClass).addClass('btn-icon-selected');
                    }
                }
                tr.append($('<td></td>').append(btn));
            }
            tbody.append(tr);
        }
    };
});
