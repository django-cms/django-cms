var keyboard = require('../keyboard');
var $ = require('jquery');

module.exports = function () {
    var data = CMS.config.lang.shortcutAreas[0].shortcuts['create-dialog'];

    keyboard.setContext('cms');

    keyboard.bind(data.shortcut, function () {
        $('.cms-btn[href*="wizard"]').trigger('click');
    });
};
