import keyboard from '../keyboard';
import $ from 'jquery';

/**
 * createModal
 *
 * @public
 */
export default function createModal() {
    var data = CMS.config.lang.shortcutAreas[0].shortcuts['create-dialog'];

    keyboard.setContext('cms');

    keyboard.bind(data.shortcut, function () {
        $('.cms-btn[href*="wizard"]').trigger('click');
    });
}
