/* global files */
'use strict';

require('../../../static/cms/js/polyfills/function.prototype.bind');
require('../../../static/cms/js/polyfills/array.prototype.findindex');
require('jquery');
require('./helpers/mock-ajax');
require('./helpers/jasmine-jquery');

if (files[0] === '*') {
    require('./cms.base.test');
    require('./cms.messages.test');
    require('./cms.changetracker.test');
    require('./cms.modal.test');
    require('./cms.sideframe.test');
    require('./cms.clipboard.test');
    require('./cms.plugins.test');
    require('./cms.structureboard.test');
    require('./cms.navigation.test');
    require('./cms.toolbar.test');
    require('./cms.tooltip.test');
    require('./cms.pagetree.dropdown.test');
    require('./cms.pagetree.stickyheader.test');
    require('./cms.pagetree.test');
    require('./shortcuts.test');
    require('./keyboard.test');
} else {
    files.forEach(function (file) {
        require('./' + file + '.test');
    });
}
