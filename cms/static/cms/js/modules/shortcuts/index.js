var $ = require('jquery');
var initHelpModal = require('./help');
var initFocusPlaceholders = require('./placeholders');
var initCreateModal = require('./create-modal');
var initFocusToolbar = require('./toolbar');

module.exports = function () {
    // istanbul ignore next
    $(function () {
        initHelpModal();
        initFocusPlaceholders();
        initCreateModal();
        initFocusToolbar();
    });
};
