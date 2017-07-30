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

// in case some data is already attached to the CMS global
// we shoud not override it
window.CMS = CMS.$.extend(window.CMS || {}, CMS);
