import { trap, untrap } from '../trap.js';
import keyboard from '../keyboard.js';


const queryAll = (selector, root = document) => Array.from(root.querySelectorAll(selector));
const query = (selector, root = document) => root?.querySelector(selector);
const triggerPointerUp = el => { if (el) el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true })); };
const triggerClick = el => { if (el) el.click(); };
const setTabIndex = (elements, value) => elements.forEach(el => el.setAttribute('tabindex', value));
const removeTabIndex = elements => elements.forEach(el => el.removeAttribute('tabindex'));
const focusElement = el => { if (el) el.focus(); };

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
        queryAll('.cms-structure .cms-dragarea').forEach(el => el.removeAttribute('tabindex'));
        untrap(query('.cms-structure-content'));
        focusElement(document.documentElement);
        keyboard.setContext('cms');
    });

    keyboard.bind('enter', function () {
        keyboard.setContext('plugins');
        const area = document.activeElement.closest('.cms-dragarea');
        if (!area) return;
        const plugins = queryAll('.cms-dragitem', area);
        if (!plugins.length) return;
        setTabIndex(plugins, '0');
        focusElement(plugins[0]);
        trap(area);
        keyboard.setContext('plugins');
    });

    keyboard.bind(['+', 'a'], function () {
        const area = document.activeElement.closest('.cms-dragarea');
        if (!area) return;
        const addBtn = query('.cms-submenu-add', area);
        triggerPointerUp(addBtn);
    });

    keyboard.bind('x', function () {
        const area = document.activeElement.closest('.cms-dragarea');
        if (!area) return;
        const toggler = query('.cms-dragbar-toggler a', area);
        triggerClick(toggler);
    });

    keyboard.bind(['!', 's'], function () {
        const area = document.activeElement.closest('.cms-dragarea');
        if (!area) return;
        const settingsBtn = query('.cms-submenu-settings', area);
        triggerPointerUp(settingsBtn);
        keyboard.setContext('placeholder-actions');
        const submenuItem = query('.cms-submenu-item a', area);
        focusElement(submenuItem);
        const dropdownInner = query('.cms-dropdown-inner', area);
        trap(dropdownInner);
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
        const dropdown = query('.cms-dropdown-inner');
        if (!dropdown) return;
        const area = dropdown.closest('.cms-dragarea');
        const settingsBtn = query('.cms-submenu-settings', area);
        // Helper functions for DOM operations
        untrap(dropdown);
        focusElement(area);
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
        const plugin = document.activeElement.closest('.cms-dragitem');
        if (!plugin) return;
        const area = plugin.closest('.cms-dragarea');
        removeTabIndex(queryAll('.cms-dragitem'));
        untrap(area);
        focusElement(area);
        keyboard.setContext('placeholders');
    });

    keyboard.bind('e', function () {
        const plugin = document.activeElement.closest('.cms-dragitem');
        if (!plugin) return;
        const editBtn = query('.cms-submenu-edit', plugin);
        triggerClick(editBtn);
    });
    keyboard.bind(['+', 'a'], function () {
        const plugin = document.activeElement.closest('.cms-dragitem');
        if (!plugin) return;
        const addBtn = query('.cms-submenu-add', plugin);
        triggerPointerUp(addBtn);
    });
    keyboard.bind('x', function () {
        const plugin = document.activeElement.closest('.cms-dragitem');
        if (!plugin) return;
        const textBtn = query('.cms-dragitem-text', plugin);
        triggerClick(textBtn);
    });
    keyboard.bind(['!', 's'], function () {
        const plugin = document.activeElement.closest('.cms-dragitem');
        if (!plugin) return;
        const settingsBtn = query('.cms-submenu-settings', plugin);
        triggerPointerUp(settingsBtn);
        keyboard.setContext('plugin-actions');
        const submenuItem = query('.cms-submenu-item a', plugin);
        focusElement(submenuItem);
        const dropdownInner = query('.cms-dropdown-inner', plugin);
        trap(dropdownInner);
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
        const dropdown = query('.cms-dropdown-inner');
        if (!dropdown) return;
        const plugin = dropdown.closest('.cms-dragitem');
        const settingsBtn = query('.cms-submenu-settings', plugin);
        triggerPointerUp(settingsBtn);
        untrap(dropdown);
        focusElement(plugin);
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
    const data = CMS.config.lang.shortcutAreas[1].shortcuts.placeholders;

    bindPlaceholderKeys();
    bindPlaceholderActionKeys();
    bindPluginKeys();
    bindPluginActionKeys();

    keyboard.setContext('cms');

    keyboard.bind(data.shortcut.split(' / '), function () {
        if (CMS.settings.mode !== 'structure') {
            return;
        }
        const dragareas = queryAll('.cms-structure .cms-dragarea');
        setTabIndex(dragareas, '0');
        focusElement(dragareas[0]);
        trap(query('.cms-structure-content'));
        keyboard.setContext('placeholders');
    });
}
