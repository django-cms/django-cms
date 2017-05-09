import keyboard from '../keyboard';
import $ from 'jquery';

import '../jquery.trap';

/**
 * Binds shortcuts:
 * [esc] go back to global "cms" context
 * [enter] when focusing the placeholder - go to it's first plugin
 * [+] / [a] add plugin to placeholder
 * [x] expand all / collapse all
 * [s] open settings menu for current placeholder
 *
 * @function bindPlaceholderKeys
 * @private
 */
var bindPlaceholderKeys = function () {
    keyboard.setContext('placeholders');
    keyboard.bind('escape', function () {
        $('.cms-structure .cms-dragarea').removeAttr('tabindex');
        $('.cms-structure-content').untrap();
        $('html').focus();
        keyboard.setContext('cms');
    });

    keyboard.bind('enter', function () {
        keyboard.setContext('plugins');
        var area = $('.cms-dragarea:focus');
        var plugins = area.find('.cms-dragitem');

        if (!plugins.length) {
            return;
        }

        plugins.attr('tabindex', '0');
        area.find('.cms-dragitem:first').focus();
        area.trap();
        keyboard.setContext('plugins');
    });

    keyboard.bind(['+', 'a'], function () {
        var area = $('.cms-dragarea:focus');

        area.find('.cms-submenu-add:first').trigger('pointerup');
    });

    keyboard.bind('x', function () {
        var area = $('.cms-dragarea:focus');

        area.find('.cms-dragbar-toggler a:visible').trigger('click');
    });

    keyboard.bind(['!', 's'], function () {
        var area = $('.cms-dragarea:focus');

        area.find('.cms-submenu-settings:first').trigger('pointerup');
        keyboard.setContext('placeholder-actions');
        area.find('.cms-submenu-item a:first').focus();
        area.find('.cms-dropdown-inner').trap();
    });
};


/**
 * Binds shortcuts:
 * [esc] go back to "placeholders" context
 *
 * @function bindPlaceholderActionKeys
 * @private
 */
var bindPlaceholderActionKeys = function () {
    keyboard.setContext('placeholder-actions');
    keyboard.bind('escape', function () {
        var dropdown = $('.cms-dropdown-inner:visible');
        var area = dropdown.closest('.cms-dragarea');

        area.find('.cms-submenu-settings:first').trigger('pointerup');
        dropdown.untrap();
        area.focus();
        keyboard.setContext('placeholders');
    });
};

/**
 * Binds shortcuts:
 * [esc] go back to "placeholders" context
 * [e] edit plugin
 * [+] / [a] add child plugin
 * [x] expand / collapse plugin
 * [s] open settings menu
 *
 * @function bindPluginKeys
 * @private
 */
var bindPluginKeys = function () {
    keyboard.setContext('plugins');
    keyboard.bind('escape', function () {
        var plugin = $('.cms-dragitem:focus');
        var area = plugin.closest('.cms-dragarea');

        $('.cms-dragitem').removeAttr('tabindex');
        area.untrap();
        area.focus();
        keyboard.setContext('placeholders');
    });

    keyboard.bind('e', function () {
        var plugin = $('.cms-dragitem:focus');

        plugin.find('.cms-submenu-edit').trigger('click');
    });
    keyboard.bind(['+', 'a'], function () {
        var plugin = $('.cms-dragitem:focus');

        plugin.find('.cms-submenu-add:first').trigger('pointerup');
    });
    keyboard.bind('x', function () {
        var plugin = $('.cms-dragitem:focus');

        plugin.find('.cms-dragitem-text').trigger('click');
    });
    keyboard.bind(['!', 's'], function () {
        var plugin = $('.cms-dragitem:focus');

        plugin.find('.cms-submenu-settings:first').trigger('pointerup');
        keyboard.setContext('plugin-actions');
        plugin.find('.cms-submenu-item a:first').focus();
        plugin.find('.cms-dropdown-inner').trap();
    });
};

/**
 * Binds shortcuts:
 * [esc] go back to "plugins" context
 *
 * @function bindPluginActionKeys
 * @private
 */
var bindPluginActionKeys = function () {
    keyboard.setContext('plugin-actions');
    keyboard.bind('escape', function () {
        var dropdown = $('.cms-dropdown-inner:visible');
        var plugin = dropdown.closest('.cms-dragitem');

        plugin.find('.cms-submenu-settings:first').trigger('pointerup');
        dropdown.untrap();
        plugin.focus();
        keyboard.setContext('plugins');
    });
};

/**
 * Binds [f p] / [alt+p] shortcuts to focus first placeholder.
 * Only works in structure mode.
 *
 * @function initPlaceholders
 * @public
 */
export default function initPlaceholders() {
    var data = CMS.config.lang.shortcutAreas[1].shortcuts.placeholders;

    bindPlaceholderKeys();
    bindPlaceholderActionKeys();
    bindPluginKeys();
    bindPluginActionKeys();

    keyboard.setContext('cms');

    keyboard.bind(data.shortcut.split(' / '), function () {
        if (CMS.settings.mode !== 'structure') {
            return;
        }

        $('.cms-structure .cms-dragarea').attr('tabindex', '0');
        $('.cms-structure .cms-dragarea:first').focus();
        $('.cms-structure-content').trap();
        keyboard.setContext('placeholders');
    });
}
