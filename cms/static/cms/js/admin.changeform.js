import { Helpers, KEYS } from './modules/cms.base';
import $ from 'jquery';

const CMS = {
    $,
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
