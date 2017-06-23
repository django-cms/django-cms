// polyfills
import './polyfills/function.prototype.bind.js';
import './libs/pep';

import { Helpers, KEYS } from './modules/cms.base';
import $ from 'jquery';
import Class from 'classjs';
import PageTree from './modules/cms.pagetree';

const CMS = {
    $,
    Class,
    API: {
        Helpers
    },
    KEYS
};

window.CMS = CMS;
CMS.PageTree = PageTree;
