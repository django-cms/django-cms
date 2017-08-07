// polyfills
import './polyfills/function.prototype.bind.js';
import './libs/pep';

import PageTree from './modules/cms.pagetree';

window.CMS.PageTree = PageTree;
