// polyfills
import './polyfills/function.prototype.bind.js';
import './libs/pep';

import { Helpers, KEYS } from './modules/cms.base';
import $ from 'jquery';
import Class from 'classjs';

const CMS = {
    $,
    Class,
    API: {
        Helpers
    },
    KEYS
};

// in case some data is already attached to the global CMS
// we must not override it
window.CMS = CMS.$.extend(window.CMS || {}, CMS);

// Serve the data bridge:
// We have a special case here cause the CMS namespace
// can be either inside the current window or the parent
if (document.querySelector('body.cms-close-frame script#data-bridge')) {
    (function (Window) {
        // the dataBridge is used to access plugin information from different resources
        // Do NOT move this!!!
        Window.CMS.API.Helpers.dataBridge = JSON.parse(document.getElementById('data-bridge').textContent);
        // make sure we're doing after the "modal" mechanism kicked in
        setTimeout(function () {
            // save current plugin
            Window.CMS.API.Helpers.onPluginSave();
        }, 100); // eslint-disable-line no-magic-numbers
    })(window.parent || window);
}

