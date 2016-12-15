var keyboard = require('../keyboard');
var tmpl = require('../tmpl');
var Modal = require('../cms.modal');
var template = require('./help.html');

/**
 * Binds [?] to open modal with shorcuts listing.
 *
 * @function initHelpShortcut
 * @public
 */
module.exports = function initHelpShortcut() {
    var shortcutAreas = CMS.config.lang.shortcutAreas;
    var modal = new Modal({
        width: 600,
        height: 600,
        resizable: false,
        minimizable: false,
        maximizable: false
    });

    keyboard.setContext('cms');
    keyboard.bind('?', function () {
        modal.open({
            title: CMS.config.lang.shortcuts,
            width: 600,
            height: 660,
            html: tmpl(template, { shortcutAreas: shortcutAreas })
        });
    });
};
