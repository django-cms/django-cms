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

// expose to browser
if (typeof window !== 'undefined') {
    window.CMS = CMS;
}

import './modules/cms.changeform';

export default CMS;
