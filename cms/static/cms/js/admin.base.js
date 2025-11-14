import { Helpers, KEYS } from './modules/cms.base';
import $ from 'jquery';

const CMS = {
    $,
    API: {
        Helpers
    },
    KEYS
};

// in case some data is already attached to the global CMS
// we must not override it
if (typeof window !== 'undefined') {
    window.CMS = CMS.$.extend(window.CMS || {}, CMS);
}

// make sure that jQuery is available as $ and jQuery
if (typeof window !== 'undefined' && !window.jQuery) {
    window.$ = window.jQuery = CMS.$;
}

export default CMS;
