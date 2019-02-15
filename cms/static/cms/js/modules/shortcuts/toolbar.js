import keyboard from '../keyboard';
import $ from 'jquery';

// eslint-disable-next-line require-jsdoc
export default function () {
    var data = CMS.config.lang.shortcutAreas[0].shortcuts.toolbar;

    keyboard.setContext('cms');
    keyboard.bind(data.shortcut.split(' / '), function () {
        if (CMS.settings.toolbar === 'expanded') {
            $('.cms-toolbar-item-navigation:first a:first').focus();
        } else {
            $('.cms-toolbar-trigger a').focus();
        }
    });
}
